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

    def __init__(self, preserve_latex: bool = True):
        """
        Initialize OTSL parser.

        Args:
            preserve_latex: If True, detect and preserve LaTeX formulas
        """
        self.preserve_latex = preserve_latex
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
        if not content.startswith('<otsl>'):
            raise ValueError("OTSL string must start with <otsl>")
        if not content.endswith('</otsl>'):
            raise ValueError("OTSL string must end with </otsl>")

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
            row_headers=row_headers
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
        # First pass: determine grid dimensions
        max_cols = 0
        for row_str in rows_raw:
            tags = self._extract_tags(row_str)
            max_cols = max(max_cols, len(tags))

        num_rows = len(rows_raw)
        num_cols = max_cols

        # Create occupancy grid to track which cells occupy which positions
        # -1 = unoccupied, >= 0 = cell index
        occupancy_grid = [[-1] * num_cols for _ in range(num_rows)]
        cells = []
        cell_idx = 0

        # Second pass: build cells
        for row_idx, row_str in enumerate(rows_raw):
            tags_and_content = self._parse_row_tags(row_str)
            col_idx = 0

            for tag_type, content_text in tags_and_content:
                # Find next available column
                while col_idx < num_cols and occupancy_grid[row_idx][col_idx] != -1:
                    col_idx += 1

                if col_idx >= num_cols:
                    # Skip overflow
                    break

                # Determine if this is a spanning marker
                if tag_type in [TAG_LEFT_CELL, TAG_UP_CELL, TAG_CROSS_CELL, TAG_EMPTY_CELL]:
                    # These are markers, not actual cells
                    # Mark as occupied but don't create cell
                    occupancy_grid[row_idx][col_idx] = -2  # Special marker for span continuation
                    col_idx += 1
                    continue

                # Determine if header
                is_header = tag_type in [TAG_COL_HEADER, TAG_ROW_HEADER]
                header_type = 'column' if tag_type == TAG_COL_HEADER else ('row' if tag_type == TAG_ROW_HEADER else None)

                # Create cell content
                cell_content = self._create_cell_content(content_text)

                # Determine spans by looking ahead for continuation markers
                rowspan, colspan = self._determine_spans(
                    row_idx, col_idx, rows_raw, num_rows, num_cols, occupancy_grid
                )

                # Create cell
                cell = Cell(
                    row_idx=row_idx,
                    col_idx=col_idx,
                    rowspan=rowspan,
                    colspan=colspan,
                    content=cell_content,
                    is_header=is_header,
                    header_type=header_type
                )

                cells.append(cell)

                # Mark occupancy
                for r in range(row_idx, min(row_idx + rowspan, num_rows)):
                    for c in range(col_idx, min(col_idx + colspan, num_cols)):
                        occupancy_grid[r][c] = cell_idx

                cell_idx += 1
                col_idx += colspan

        return cells, num_rows, num_cols

    def _extract_tags(self, row_str: str) -> List[str]:
        """Extract all tags from a row string."""
        tag_pattern = r'<(ched|rhed|fcel|ecel|lcel|ucel|xcel)>'
        return re.findall(tag_pattern, row_str)

    def _parse_row_tags(self, row_str: str) -> List[Tuple[str, str]]:
        """
        Parse row string into list of (tag_type, content) tuples.

        Args:
            row_str: Row string with interleaved tags and content

        Returns:
            List of (tag_type, content_text) tuples
        """
        results = []
        tag_pattern = r'<(ched|rhed|fcel|ecel|lcel|ucel|xcel)>'

        # Split by tags but keep tags
        parts = re.split(tag_pattern, row_str)

        i = 0
        while i < len(parts):
            part = parts[i].strip()
            if not part:
                i += 1
                continue

            # Check if this is a tag name (from split)
            if part in [TAG_COL_HEADER, TAG_ROW_HEADER, TAG_FILLED_CELL,
                       TAG_EMPTY_CELL, TAG_LEFT_CELL, TAG_UP_CELL, TAG_CROSS_CELL]:
                tag_type = part

                # Get content (next part if not a tag)
                content_text = ""
                if i + 1 < len(parts):
                    next_part = parts[i + 1].strip()
                    # Check if next part is not a tag
                    if next_part and next_part not in [TAG_COL_HEADER, TAG_ROW_HEADER, TAG_FILLED_CELL,
                                                        TAG_EMPTY_CELL, TAG_LEFT_CELL, TAG_UP_CELL, TAG_CROSS_CELL]:
                        content_text = next_part
                        i += 1  # Skip next part as we consumed it

                results.append((tag_type, content_text))

            i += 1

        return results

    def _determine_spans(self, row_idx: int, col_idx: int, rows_raw: List[str],
                        num_rows: int, num_cols: int, occupancy_grid: List[List[int]]) -> Tuple[int, int]:
        """
        Determine rowspan and colspan by looking ahead for continuation markers.

        Args:
            row_idx: Current row index
            col_idx: Current column index
            rows_raw: All row strings
            num_rows: Total rows
            num_cols: Total columns
            occupancy_grid: Current occupancy state

        Returns:
            Tuple of (rowspan, colspan)
        """
        # Look right for <lcel> or <xcel> to determine colspan
        colspan = 1
        check_col = col_idx + 1
        while check_col < num_cols:
            if occupancy_grid[row_idx][check_col] != -1:
                break

            # Parse the row to check for <lcel> or <xcel> at this position
            tags_at_position = self._get_tag_at_position(rows_raw[row_idx], check_col)
            if TAG_LEFT_CELL in tags_at_position or TAG_CROSS_CELL in tags_at_position:
                colspan += 1
                check_col += 1
            else:
                break

        # Look down for <ucel> or <xcel> to determine rowspan
        rowspan = 1
        check_row = row_idx + 1
        while check_row < num_rows:
            if occupancy_grid[check_row][col_idx] != -1:
                break

            # Parse the row to check for <ucel> or <xcel> at this position
            tags_at_position = self._get_tag_at_position(rows_raw[check_row], col_idx)
            if TAG_UP_CELL in tags_at_position or TAG_CROSS_CELL in tags_at_position:
                rowspan += 1
                check_row += 1
            else:
                break

        return rowspan, colspan

    def _get_tag_at_position(self, row_str: str, col_idx: int) -> List[str]:
        """Get tag type at specific column position in row."""
        tags_and_content = self._parse_row_tags(row_str)
        if col_idx < len(tags_and_content):
            return [tags_and_content[col_idx][0]]
        return []

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
