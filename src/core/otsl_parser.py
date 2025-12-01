"""
OTSL table parser.

Converts OTSL format to intermediate representation (IR).
"""

import re
from typing import List, Tuple, Optional
from src.core.table_structure import TableStructure, Cell, CellContent
from src.core.latex_handler import LaTeXHandler
from src.utils.constants import (
    TAG_FILLED_CELL, TAG_EMPTY_CELL, TAG_LEFT_CELL, TAG_UP_CELL, TAG_CROSS_CELL,
    TAG_COL_HEADER, TAG_ROW_HEADER, TAG_NEWLINE
)


class OTSLTableParser:
    """Converts OTSL format to intermediate representation."""

    def __init__(self, preserve_latex: bool = True, strict: bool = True):
        """
        Initialize OTSL parser.

        Args:
            preserve_latex: If True, detect and preserve LaTeX formulas
            strict: If True, raise errors on inconsistent table structure.
                   If False, attempt to parse malformed tables by padding/truncating rows.
        """
        self.preserve_latex = preserve_latex
        self.strict = strict
        self.latex_handler = LaTeXHandler() if preserve_latex else None

    def parse(self, otsl_str: str) -> TableStructure:
        """
        Parse OTSL string to intermediate representation.

        OTSL Format:
        <otsl>[<caption>text</caption>]<loc_X><loc_Y><loc_W><loc_H>CONTENT<nl>...</otsl>

        Where CONTENT is interleaved tags and text:
        - <ched>text - column header
        - <rhed>text - row header
        - <fcel>text - filled cell
        - <ecel> - empty cell (standalone)
        - <lcel> - left cell/colspan continuation (standalone)
        - <ucel> - up cell/rowspan continuation (standalone)
        - <xcel> - cross cell/both spans (standalone)
        - <nl> - newline/row separator

        Args:
            otsl_str: OTSL string to parse

        Returns:
            TableStructure object

        Raises:
            ValueError: If OTSL format is invalid
        """
        # Remove <otsl> wrapper and clean
        content = otsl_str.strip()

        # Check for opening tag
        if not content.startswith('<otsl>'):
            if self.strict:
                raise ValueError("OTSL string must start with <otsl>")
            else:
                # In lenient mode, add missing opening tag
                content = '<otsl>' + content

        # Check for closing tag
        if not content.endswith('</otsl>'):
            if self.strict:
                raise ValueError("OTSL string must end with </otsl>")
            else:
                # In lenient mode, auto-close truncated OTSL
                content = content + '</otsl>'

        content = content[6:-7].strip()  # Remove <otsl> and </otsl>

        # Extract caption if present
        caption_content = None
        caption_match = re.match(r'<caption>(.*?)</caption>', content)
        if caption_match:
            caption_text = caption_match.group(1)
            caption_content = CellContent(
                text=caption_text,
                latex_formulas=self.latex_handler.extract_formulas(caption_text) if self.latex_handler else [],
                has_math_tags=False
            )
            content = content[caption_match.end():].strip()

        # Extract structure metadata (thead/tbody/tfoot flags)
        has_explicit_thead = False
        has_explicit_tbody = False
        has_explicit_tfoot = False
        tfoot_rows = []

        if content.startswith('<has_thead>'):
            has_explicit_thead = True
            content = content[11:].strip()  # Remove <has_thead>
        if content.startswith('<has_tbody>'):
            has_explicit_tbody = True
            content = content[11:].strip()  # Remove <has_tbody>
        if content.startswith('<has_tfoot>'):
            has_explicit_tfoot = True
            content = content[11:].strip()  # Remove <has_tfoot>
            # Extract tfoot row indices
            tfoot_match = re.match(r'<tfoot_rows>([\d,]+)</tfoot_rows>', content)
            if tfoot_match:
                tfoot_indices = tfoot_match.group(1)
                tfoot_rows = [int(x) for x in tfoot_indices.split(',')]
                content = content[tfoot_match.end():].strip()

        # Extract and remove location tags
        loc_pattern = r'(?:<loc_\d+>)+'
        content = re.sub(loc_pattern, '', content, count=1).strip()

        # Split into rows by <nl>
        rows_raw = content.split('<nl>')
        # Remove empty rows (last split after final <nl>)
        rows_raw = [r.strip() for r in rows_raw if r.strip()]

        if not rows_raw:
            raise ValueError("OTSL must have at least one row")

        # Parse rows and build cells
        cells, num_rows, num_cols = self._parse_rows(rows_raw)

        # Identify column and row headers
        column_headers, row_headers = self._identify_headers(cells, num_rows, num_cols)

        # Create TableStructure
        table = TableStructure(
            num_rows=num_rows,
            num_cols=num_cols,
            cells=cells,
            caption=caption_content,
            has_border=True,  # OTSL doesn't specify border, default to True
            column_headers=column_headers,
            row_headers=row_headers,
            has_explicit_thead=has_explicit_thead,
            has_explicit_tbody=has_explicit_tbody,
            has_explicit_tfoot=has_explicit_tfoot,
            tfoot_rows=tfoot_rows
        )

        return table

    def _parse_rows(self, rows_raw: List[str]) -> Tuple[List[Cell], int, int]:
        """
        Parse OTSL rows into cells.

        Args:
            rows_raw: List of row strings (split by <nl>)

        Returns:
            Tuple of (cells, num_rows, num_cols)
        """
        # Parse all rows to get tag lists
        all_row_tags = [self._parse_row_tags(row) for row in rows_raw]

        # Determine grid dimensions
        max_cols = max(len(tags) for tags in all_row_tags) if all_row_tags else 0
        num_rows = len(rows_raw)
        num_cols = max_cols

        # In non-strict mode, normalize row lengths by padding with empty cells
        if not self.strict:
            for row_idx, tag_list in enumerate(all_row_tags):
                if len(tag_list) < max_cols:
                    # Pad short rows with empty cells
                    padding_needed = max_cols - len(tag_list)
                    for _ in range(padding_needed):
                        tag_list.append((TAG_EMPTY_CELL, ''))
                elif len(tag_list) > max_cols:
                    # Truncate long rows
                    all_row_tags[row_idx] = tag_list[:max_cols]

        # Create occupancy grid
        occupancy_grid = [[-1] * num_cols for _ in range(num_rows)]
        cells = []
        cell_idx = 0

        # Build cells
        for row_idx, tag_list in enumerate(all_row_tags):
            tag_idx = 0  # Index into tag_list
            grid_col = 0  # Current grid column

            while tag_idx < len(tag_list):
                tag_type, content_text = tag_list[tag_idx]

                # Check if this is a spanning marker (not an actual cell)
                if tag_type in [TAG_LEFT_CELL, TAG_UP_CELL, TAG_CROSS_CELL]:
                    # Spanning markers mark the current grid position
                    # They correspond to cells that span from previous rows/columns
                    if grid_col < num_cols and occupancy_grid[row_idx][grid_col] == -1:
                        occupancy_grid[row_idx][grid_col] = -2  # Special marker
                    grid_col += 1
                    tag_idx += 1
                    continue

                # For actual cells, skip grid columns occupied by cells from previous rows
                while grid_col < num_cols and occupancy_grid[row_idx][grid_col] != -1:
                    grid_col += 1

                if grid_col >= num_cols:
                    break

                # Empty cells DO create a cell with empty content
                if tag_type == TAG_EMPTY_CELL:
                    # Create empty cell
                    cell_content = CellContent(text="", latex_formulas=[], has_math_tags=False)

                    # Determine spans by looking ahead in tag_list (empty cells can also span!)
                    rowspan, colspan = self._determine_spans_from_tags(
                        row_idx, grid_col, tag_idx, all_row_tags, num_rows, num_cols
                    )

                    cell = Cell(
                        row_idx=row_idx,
                        col_idx=grid_col,
                        rowspan=rowspan,
                        colspan=colspan,
                        content=cell_content,
                        is_header=False,
                        header_type=None
                    )

                    cells.append(cell)

                    # Mark occupancy for all spanned cells
                    for r in range(row_idx, min(row_idx + rowspan, num_rows)):
                        for c in range(grid_col, min(grid_col + colspan, num_cols)):
                            occupancy_grid[r][c] = cell_idx

                    cell_idx += 1
                    grid_col += colspan
                    # Skip over the empty cell tag plus any colspan markers (lcel/xcel)
                    tag_idx += 1 + (colspan - 1)
                    continue

                # Determine if header
                is_header = tag_type in [TAG_COL_HEADER, TAG_ROW_HEADER]
                header_type = 'column' if tag_type == TAG_COL_HEADER else ('row' if tag_type == TAG_ROW_HEADER else None)

                # Create cell content
                cell_content = self._create_cell_content(content_text)

                # Determine spans by looking ahead in tag_list
                rowspan, colspan = self._determine_spans_from_tags(
                    row_idx, grid_col, tag_idx, all_row_tags, num_rows, num_cols
                )

                # Create cell
                cell = Cell(
                    row_idx=row_idx,
                    col_idx=grid_col,
                    rowspan=rowspan,
                    colspan=colspan,
                    content=cell_content,
                    is_header=is_header,
                    header_type=header_type
                )

                cells.append(cell)

                # Mark occupancy
                for r in range(row_idx, min(row_idx + rowspan, num_rows)):
                    for c in range(grid_col, min(grid_col + colspan, num_cols)):
                        occupancy_grid[r][c] = cell_idx

                cell_idx += 1
                grid_col += colspan
                # Skip over the cell tag plus any colspan markers (lcel/xcel)
                tag_idx += 1 + (colspan - 1)

        return cells, num_rows, num_cols

    def _parse_row_tags(self, row_str: str) -> List[Tuple[str, str]]:
        """
        Parse row string into list of (tag_type, content) tuples.

        Args:
            row_str: Row string with interleaved tags and content

        Returns:
            List of (tag_type, content_text) tuples
        """
        results = []

        # Pattern to match OTSL tag and content
        # Content is everything up to the next OTSL tag (or end of string)
        # This preserves HTML tags like <sup>, <sub>, etc. within content
        # Lookahead specifically checks for OTSL tags with closing >, not generic < or </
        pattern = r'<(ched|rhed|fcel|ecel|lcel|ucel|xcel)>(.*?)(?=<(?:ched|rhed|fcel|ecel|lcel|ucel|xcel|nl)>|$)'

        matches = re.findall(pattern, row_str, re.DOTALL)

        for tag_type, content_text in matches:
            results.append((tag_type, content_text.strip()))

        return results

    def _determine_spans_from_tags(self, row_idx: int, grid_col: int, tag_idx: int,
                                   all_row_tags: List[List[Tuple[str, str]]],
                                   num_rows: int, num_cols: int) -> Tuple[int, int]:
        """
        Determine rowspan and colspan by looking ahead in the tag lists.

        Args:
            row_idx: Current row index
            grid_col: Current grid column index
            tag_idx: Current tag index in the row's tag list
            all_row_tags: Parsed tags for all rows
            num_rows: Total rows
            num_cols: Total columns

        Returns:
            Tuple of (rowspan, colspan)
        """
        current_row_tags = all_row_tags[row_idx]

        # Look ahead in current row's tags for <lcel> or <xcel> to determine colspan
        colspan = 1
        check_tag_idx = tag_idx + 1

        while check_tag_idx < len(current_row_tags):
            tag_type = current_row_tags[check_tag_idx][0]
            if tag_type in [TAG_LEFT_CELL, TAG_CROSS_CELL]:
                colspan += 1
                check_tag_idx += 1
            else:
                break

        # Look down in subsequent rows at the same grid column for <ucel> or <xcel>
        # We need to find which tag in each subsequent row corresponds to grid_col
        rowspan = 1
        check_row = row_idx + 1

        while check_row < num_rows:
            check_row_tags = all_row_tags[check_row]

            # Find the tag index that corresponds to grid_col in check_row
            # We do this by counting how many grid columns the tags before it occupy
            current_grid_col = 0
            found_tag_idx = -1

            for idx, (tag_type, _) in enumerate(check_row_tags):
                if current_grid_col == grid_col:
                    found_tag_idx = idx
                    break
                # Each tag occupies at least one grid column
                # (We can't easily determine colspan here without recursion,
                # so we assume each tag corresponds to one grid position)
                current_grid_col += 1

            if found_tag_idx >= 0 and found_tag_idx < len(check_row_tags):
                tag_type = check_row_tags[found_tag_idx][0]
                if tag_type in [TAG_UP_CELL, TAG_CROSS_CELL]:
                    rowspan += 1
                    check_row += 1
                else:
                    break
            else:
                break

        return rowspan, colspan

    def _create_cell_content(self, text: str) -> CellContent:
        """Create CellContent from text."""
        latex_formulas = []
        if self.preserve_latex and self.latex_handler and text:
            latex_formulas = self.latex_handler.extract_formulas(text)

        return CellContent(
            text=text,
            latex_formulas=latex_formulas,
            has_math_tags=False
        )

    def _identify_headers(self, cells: List[Cell], num_rows: int, num_cols: int) -> Tuple[List[int], List[int]]:
        """Identify column header rows and row header columns."""
        column_headers = []
        row_headers = []

        # Find rows with column headers
        for row_idx in range(num_rows):
            row_cells = [c for c in cells if c.row_idx == row_idx and c.header_type == 'column']
            if row_cells:
                column_headers.append(row_idx)

        # Find columns with row headers
        for col_idx in range(num_cols):
            col_cells = [c for c in cells if c.col_idx == col_idx and c.header_type == 'row']
            if col_cells:
                row_headers.append(col_idx)

        return column_headers, row_headers
