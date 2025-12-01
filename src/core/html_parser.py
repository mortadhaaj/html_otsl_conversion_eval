"""
HTML table parser.

Converts HTML tables to intermediate representation (IR).
"""

from typing import List, Tuple, Optional
from lxml import html as lxml_html, etree
import html5lib
from src.core.table_structure import TableStructure, Cell, CellContent
from src.core.latex_handler import LaTeXHandler


class HTMLTableParser:
    """Converts HTML tables to intermediate representation."""

    def __init__(self, preserve_latex: bool = True, normalize_whitespace: bool = True, strict: bool = True):
        """
        Initialize HTML parser.

        Args:
            preserve_latex: If True, detect and preserve LaTeX formulas
            normalize_whitespace: If True, normalize whitespace in cell content
            strict: If True, raise errors on malformed tables.
                   If False, attempt to parse malformed tables (empty rows, inconsistent columns).
        """
        self.preserve_latex = preserve_latex
        self.normalize_whitespace = normalize_whitespace
        self.strict = strict
        self.latex_handler = LaTeXHandler() if preserve_latex else None

    def parse(self, html_str: str) -> TableStructure:
        """
        Parse HTML table to intermediate representation.

        Args:
            html_str: HTML string containing a table

        Returns:
            TableStructure object

        Raises:
            ValueError: If no table found or parsing fails
        """
        # Parse HTML using lxml with html5lib fallback
        tree = None
        used_fallback = False

        try:
            tree = lxml_html.fromstring(html_str)
        except Exception as e:
            # Fallback to html5lib for malformed HTML
            try:
                doc = html5lib.parse(html_str, namespaceHTMLElements=False)
                # Convert html5lib's ElementTree.Element to lxml by serializing and re-parsing
                # html5lib uses xml.etree which doesn't support xpath, so we need lxml
                import xml.etree.ElementTree as ET
                html_bytes = ET.tostring(doc, encoding='utf-8', method='html')
                # Decode UTF-8 bytes to string to avoid encoding issues
                html_text = html_bytes.decode('utf-8')
                tree = lxml_html.fromstring(html_text)
                used_fallback = True
            except Exception as e2:
                raise ValueError(f"Failed to parse HTML: {e}, fallback also failed: {e2}")

        # Find table element
        table_elem = self._find_table(tree)
        if table_elem is None:
            raise ValueError("No table element found in HTML")

        # Extract table components
        caption_content = self._extract_caption(table_elem)
        has_border = self._has_border(table_elem)

        # Extract all rows (from thead, tbody, tfoot)
        all_rows, row_sections = self._extract_rows(table_elem)

        # In non-strict mode, filter out empty rows (but do it after building cells)
        # We'll need to do this carefully to avoid rowspan issues
        filter_empty_rows = not self.strict
        empty_row_indices = set()

        if filter_empty_rows:
            # First pass: identify which rows are empty
            for idx, row in enumerate(all_rows):
                cells = row.xpath('./td | ./th')
                if not cells:
                    empty_row_indices.add(idx)

        # If lxml found no rows but html5lib is available, try html5lib fallback
        # This handles cases where lxml misparses malformed HTML (e.g., unclosed tags)
        if not all_rows and not used_fallback:
            try:
                doc = html5lib.parse(html_str, namespaceHTMLElements=False)
                # Convert html5lib's ElementTree.Element to lxml
                import xml.etree.ElementTree as ET
                html_bytes = ET.tostring(doc, encoding='utf-8', method='html')
                # Decode UTF-8 bytes to string to avoid encoding issues
                html_text = html_bytes.decode('utf-8')
                tree = lxml_html.fromstring(html_text)
                table_elem = self._find_table(tree)
                if table_elem is not None:
                    caption_content = self._extract_caption(table_elem)
                    has_border = self._has_border(table_elem)
                    all_rows, row_sections = self._extract_rows(table_elem)
            except Exception:
                pass  # Fallback failed, use original lxml results

        if not all_rows:
            if self.strict:
                raise ValueError("Table has no rows")
            else:
                # In non-strict mode, return a minimal table with one empty cell
                return TableStructure(
                    num_rows=1,
                    num_cols=1,
                    cells=[Cell(row_idx=0, col_idx=0, content=CellContent(text=""))],
                    caption=caption_content
                )

        # Determine table dimensions (before filtering)
        num_cols = self._determine_num_cols(all_rows)
        num_rows_before = len(all_rows)

        # Build cells with occupancy tracking
        cells, occupancy_grid = self._build_cells(all_rows, row_sections, num_rows_before, num_cols)

        # In non-strict mode with empty rows, adjust the structure
        if filter_empty_rows and empty_row_indices:
            # Filter out empty rows and adjust cell positions
            # Create mapping from old row index to new row index
            row_mapping = {}
            new_row_idx = 0
            for old_idx in range(num_rows_before):
                if old_idx not in empty_row_indices:
                    row_mapping[old_idx] = new_row_idx
                    new_row_idx += 1

            # Adjust cell positions and rowspans
            filtered_cells = []
            for cell in cells:
                # Skip cells that start in empty rows
                if cell.row_idx in empty_row_indices:
                    continue

                # Adjust row index
                if cell.row_idx in row_mapping:
                    new_cell_row = row_mapping[cell.row_idx]

                    # Adjust rowspan to account for removed empty rows
                    original_end_row = cell.row_idx + cell.rowspan
                    new_rowspan = 1
                    for r in range(cell.row_idx + 1, original_end_row):
                        if r not in empty_row_indices:
                            new_rowspan += 1

                    # Create adjusted cell
                    adjusted_cell = Cell(
                        row_idx=new_cell_row,
                        col_idx=cell.col_idx,
                        rowspan=new_rowspan,
                        colspan=cell.colspan,
                        content=cell.content,
                        is_header=cell.is_header,
                        header_type=cell.header_type
                    )
                    filtered_cells.append(adjusted_cell)

            cells = filtered_cells
            num_rows = new_row_idx
        else:
            num_rows = num_rows_before

        # In non-strict mode, fill any gaps in occupancy grid with empty cells
        if not self.strict:
            # Rebuild occupancy grid after adjustments
            occupancy_grid = [[-1] * num_cols for _ in range(num_rows)]
            for idx, cell in enumerate(cells):
                for r in range(cell.row_idx, min(cell.row_idx + cell.rowspan, num_rows)):
                    for c in range(cell.col_idx, min(cell.col_idx + cell.colspan, num_cols)):
                        if 0 <= r < num_rows and 0 <= c < num_cols:
                            occupancy_grid[r][c] = idx

            # Fill gaps
            for row_idx in range(num_rows):
                for col_idx in range(num_cols):
                    if occupancy_grid[row_idx][col_idx] == -1:
                        # Create empty cell for unoccupied position
                        cell = Cell(
                            row_idx=row_idx,
                            col_idx=col_idx,
                            rowspan=1,
                            colspan=1,
                            content=CellContent(text=""),
                            is_header=False,
                            header_type=None
                        )
                        cells.append(cell)
                        occupancy_grid[row_idx][col_idx] = len(cells) - 1

        # Identify column and row headers
        column_headers, row_headers = self._identify_headers(cells, row_sections, num_rows, num_cols)

        # Detect explicit thead/tbody/tfoot tags
        has_explicit_thead = table_elem.find('.//thead') is not None
        has_explicit_tbody = table_elem.find('.//tbody') is not None
        has_explicit_tfoot = table_elem.find('.//tfoot') is not None

        # Identify tfoot rows
        tfoot_rows = [i for i, section in enumerate(row_sections) if section == 'tfoot']

        # Create TableStructure
        table = TableStructure(
            num_rows=num_rows,
            num_cols=num_cols,
            cells=cells,
            caption=caption_content,
            has_border=has_border,
            column_headers=column_headers,
            row_headers=row_headers,
            has_explicit_thead=has_explicit_thead,
            has_explicit_tbody=has_explicit_tbody,
            has_explicit_tfoot=has_explicit_tfoot,
            tfoot_rows=tfoot_rows
        )

        return table

    def _find_table(self, tree) -> Optional:
        """Find table element in HTML tree."""
        # If tree is already a table, return it
        if tree.tag == 'table':
            return tree

        # Search for table element
        tables = tree.xpath('.//table')
        if tables:
            return tables[0]  # Return first table

        return None

    def _extract_caption(self, table_elem) -> Optional[CellContent]:
        """Extract table caption if present."""
        captions = table_elem.xpath('./caption')
        if not captions:
            return None

        caption_elem = captions[0]
        text = self._get_element_text(caption_elem)

        if not text.strip():
            return None

        return self._extract_cell_content(caption_elem, text)

    def _has_border(self, table_elem) -> bool:
        """Check if table has border attribute."""
        border = table_elem.get('border')
        if border is None:
            return False
        # Border is present if attribute exists and is not '0'
        return border != '0'

    def _extract_rows(self, table_elem) -> Tuple[List, List[str]]:
        """
        Extract all table rows and track which section each row comes from.

        Returns:
            Tuple of (rows, row_sections) where row_sections[i] is 'thead', 'tbody', or 'tfoot'
        """
        rows = []
        row_sections = []

        # Extract from thead
        for thead in table_elem.xpath('./thead'):
            for tr in thead.xpath('./tr'):
                rows.append(tr)
                row_sections.append('thead')

        # Extract from tbody
        tbodies = table_elem.xpath('./tbody')
        if tbodies:
            for tbody in tbodies:
                for tr in tbody.xpath('./tr'):
                    rows.append(tr)
                    row_sections.append('tbody')
        else:
            # If no tbody, look for direct tr children
            for tr in table_elem.xpath('./tr'):
                rows.append(tr)
                row_sections.append('tbody')  # Treat as tbody

        # Extract from tfoot
        for tfoot in table_elem.xpath('./tfoot'):
            for tr in tfoot.xpath('./tr'):
                rows.append(tr)
                row_sections.append('tfoot')

        return rows, row_sections

    def _sanitize_span_value(self, value: str) -> int:
        """
        Sanitize colspan/rowspan value from HTML attribute.

        Handles cases where values have escaped quotes like colspan=\"2\"
        or other malformed attribute values.

        Args:
            value: Raw attribute value (could be '2', '"2"', '\\"2\\"', etc.)

        Returns:
            Integer span value (default 1 if parsing fails)
        """
        if not value:
            return 1

        # Strip backslashes and quotes
        sanitized = value.strip()
        sanitized = sanitized.replace('\\', '')  # Remove backslashes
        sanitized = sanitized.strip('"\'')  # Remove surrounding quotes

        try:
            return int(sanitized)
        except (ValueError, TypeError):
            # If still can't parse, return 1
            return 1

    def _determine_num_cols(self, rows: List) -> int:
        """
        Determine the number of columns in the table.

        Takes into account colspan attributes.
        """
        max_cols = 0

        for row in rows:
            cols_in_row = 0
            for cell in row.xpath('./td | ./th'):
                colspan_str = cell.get('colspan', '1')
                colspan = self._sanitize_span_value(colspan_str)
                cols_in_row += colspan
            max_cols = max(max_cols, cols_in_row)

        return max_cols

    def _build_cells(self, rows: List, row_sections: List[str],
                     num_rows: int, num_cols: int) -> Tuple[List[Cell], List[List[int]]]:
        """
        Build cell list with proper positioning accounting for spans.

        Returns:
            Tuple of (cells, occupancy_grid) where occupancy_grid[r][c] is the cell index
            occupying position (r, c), or -1 if unoccupied
        """
        # Initialize occupancy grid
        occupancy_grid = [[-1] * num_cols for _ in range(num_rows)]
        cells = []
        cell_idx = 0

        for row_idx, (row_elem, section) in enumerate(zip(rows, row_sections)):
            col_idx = 0

            for cell_elem in row_elem.xpath('./td | ./th'):
                # Find next available column
                while col_idx < num_cols and occupancy_grid[row_idx][col_idx] != -1:
                    col_idx += 1

                if col_idx >= num_cols:
                    # Skip cells that overflow
                    continue

                # Get span attributes (sanitize to handle escaped quotes like colspan=\"2\")
                rowspan_str = cell_elem.get('rowspan', '1')
                colspan_str = cell_elem.get('colspan', '1')
                rowspan = self._sanitize_span_value(rowspan_str)
                colspan = self._sanitize_span_value(colspan_str)

                # Clamp spans to table boundaries (prevents cells extending beyond table)
                # This is essential for malformed HTML where cells have impossible rowspan/colspan
                max_rowspan = num_rows - row_idx
                max_colspan = num_cols - col_idx
                rowspan = min(rowspan, max_rowspan)
                colspan = min(colspan, max_colspan)

                # Determine if header
                is_header = cell_elem.tag == 'th' or section == 'thead'
                header_type = 'column' if section == 'thead' else ('row' if col_idx == 0 and is_header else None)

                # Extract content
                text = self._get_element_text(cell_elem)
                content = self._extract_cell_content(cell_elem, text)

                # Create cell
                cell = Cell(
                    row_idx=row_idx,
                    col_idx=col_idx,
                    rowspan=rowspan,
                    colspan=colspan,
                    content=content,
                    is_header=is_header,
                    header_type=header_type
                )

                cells.append(cell)

                # Mark occupancy grid
                for r in range(row_idx, min(row_idx + rowspan, num_rows)):
                    for c in range(col_idx, min(col_idx + colspan, num_cols)):
                        occupancy_grid[r][c] = cell_idx

                cell_idx += 1
                col_idx += colspan

        return cells, occupancy_grid

    def _get_element_text(self, elem) -> str:
        """
        Get text content from element.

        For cells with inline HTML tags (sup, sub, b, i, etc.),
        preserve the HTML structure. Otherwise extract plain text.
        """
        from lxml import etree

        # Check if element has inline HTML tags we want to preserve
        inline_tags = {'sup', 'sub', 'b', 'i', 'strong', 'em', 'u', 'span', 'a'}
        has_inline_html = False

        for child in elem.iter():
            if child != elem and child.tag in inline_tags:
                has_inline_html = True
                break

        if has_inline_html:
            # Preserve HTML structure - get inner HTML
            text = elem.text or ''
            for child in elem:
                text += etree.tostring(child, encoding='unicode', method='html')
            return text.strip()
        else:
            # Extract plain text only
            text_parts = []

            def collect_text(el):
                if el.text:
                    text_parts.append(el.text)
                for child in el:
                    collect_text(child)
                    if child.tail:
                        text_parts.append(child.tail)

            collect_text(elem)
            text = ''.join(text_parts)

            if self.normalize_whitespace:
                # Normalize whitespace
                import re
                text = re.sub(r'\s+', ' ', text).strip()

            return text

    def _extract_cell_content(self, cell_elem, text: str) -> CellContent:
        """
        Extract cell content with LaTeX preservation.

        Args:
            cell_elem: HTML cell element
            text: Extracted text content

        Returns:
            CellContent object
        """
        latex_formulas = []
        has_math_tags = False

        if self.preserve_latex and self.latex_handler:
            # Check for HTML math tags
            html_str = etree.tostring(cell_elem, encoding='unicode', method='html')
            if any(f'<{tag}' in html_str.lower() for tag in ['math', 'formula', 'equation', 'sup', 'sub']):
                has_math_tags = True

            # Extract LaTeX formulas from text
            latex_formulas = self.latex_handler.extract_formulas(text)

        return CellContent(
            text=text,
            latex_formulas=latex_formulas,
            has_math_tags=has_math_tags
        )

    def _identify_headers(self, cells: List[Cell], row_sections: List[str],
                         num_rows: int, num_cols: int) -> Tuple[List[int], List[int]]:
        """
        Identify column header rows and row header columns.

        Args:
            cells: List of cells
            row_sections: Section for each row ('thead', 'tbody', 'tfoot')
            num_rows: Number of rows
            num_cols: Number of columns

        Returns:
            Tuple of (column_header_rows, row_header_cols)
        """
        column_headers = []
        row_headers = []

        # Identify column headers (rows in thead or first row with all headers)
        for row_idx, section in enumerate(row_sections):
            if section == 'thead':
                column_headers.append(row_idx)

        # If no thead, check if first row is all headers
        if not column_headers:
            first_row_cells = [c for c in cells if c.row_idx == 0]
            if first_row_cells and all(c.is_header for c in first_row_cells):
                column_headers.append(0)

        # Identify row headers (first column if consistently headers)
        first_col_cells = [c for c in cells if c.col_idx == 0 and c.row_idx not in column_headers]
        if first_col_cells and all(c.is_header for c in first_col_cells):
            row_headers.append(0)

        return column_headers, row_headers
