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

    def __init__(self, preserve_latex: bool = True, normalize_whitespace: bool = True):
        """
        Initialize HTML parser.

        Args:
            preserve_latex: If True, detect and preserve LaTeX formulas
            normalize_whitespace: If True, normalize whitespace in cell content
        """
        self.preserve_latex = preserve_latex
        self.normalize_whitespace = normalize_whitespace
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
        try:
            tree = lxml_html.fromstring(html_str)
        except Exception as e:
            # Fallback to html5lib for malformed HTML
            try:
                doc = html5lib.parse(html_str, namespaceHTMLElements=False)
                tree = doc.getroot()
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

        if not all_rows:
            raise ValueError("Table has no rows")

        # Determine table dimensions
        num_cols = self._determine_num_cols(all_rows)
        num_rows = len(all_rows)

        # Build cells with occupancy tracking
        cells, occupancy_grid = self._build_cells(all_rows, row_sections, num_rows, num_cols)

        # Identify column and row headers
        column_headers, row_headers = self._identify_headers(cells, row_sections, num_rows, num_cols)

        # Create TableStructure
        table = TableStructure(
            num_rows=num_rows,
            num_cols=num_cols,
            cells=cells,
            caption=caption_content,
            has_border=has_border,
            column_headers=column_headers,
            row_headers=row_headers
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

    def _determine_num_cols(self, rows: List) -> int:
        """
        Determine the number of columns in the table.

        Takes into account colspan attributes.
        """
        max_cols = 0

        for row in rows:
            cols_in_row = 0
            for cell in row.xpath('./td | ./th'):
                colspan = int(cell.get('colspan', 1))
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

                # Get span attributes
                rowspan = int(cell_elem.get('rowspan', 1))
                colspan = int(cell_elem.get('colspan', 1))

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
        """Get text content from element, including tail text."""
        text_parts = []

        # Get text content (recursively)
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
