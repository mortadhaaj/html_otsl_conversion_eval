"""
OTSL table builder.

Converts intermediate representation (IR) to OTSL format.
"""

import random
from typing import List, Optional
from src.core.table_structure import TableStructure, Cell
from src.utils.constants import (
    TAG_FILLED_CELL, TAG_EMPTY_CELL, TAG_LEFT_CELL, TAG_UP_CELL, TAG_CROSS_CELL,
    TAG_COL_HEADER, TAG_ROW_HEADER, TAG_NEWLINE
)


class OTSLTableBuilder:
    """Converts intermediate representation to OTSL format."""

    def __init__(self, include_location: bool = True):
        """
        Initialize OTSL builder.

        Args:
            include_location: If True, include random location coordinates
        """
        self.include_location = include_location

    def build(self, table: TableStructure) -> str:
        """
        Build OTSL from intermediate representation.

        Args:
            table: TableStructure to convert

        Returns:
            OTSL string

        Raises:
            ValueError: If table structure is invalid
        """
        # Validate table
        is_valid, errors = table.validate()
        if not is_valid:
            raise ValueError(f"Invalid table structure: {'; '.join(errors)}")

        # Build OTSL parts
        parts = ['<otsl>']

        # Add caption if present
        if table.caption:
            parts.append(f'<caption>{table.caption.text}</caption>')

        # Add structure metadata (preserve thead/tbody/tfoot information)
        if table.has_explicit_thead:
            parts.append('<has_thead>')
        if table.has_explicit_tbody:
            parts.append('<has_tbody>')
        if table.has_explicit_tfoot:
            parts.append('<has_tfoot>')
            # Add tfoot row indices
            if table.tfoot_rows:
                tfoot_indices = ','.join(str(r) for r in sorted(table.tfoot_rows))
                parts.append(f'<tfoot_rows>{tfoot_indices}</tfoot_rows>')

        # Add location tags (random coordinates)
        if self.include_location:
            loc_tags = self._generate_location_tags()
            parts.append(loc_tags)

        # Build table content
        content = self._build_table_content(table)
        parts.append(content)

        parts.append('</otsl>')

        return ''.join(parts)

    def _generate_location_tags(self) -> str:
        """Generate random location tags."""
        # Generate 4 random coordinates for bounding box
        x = random.randint(30, 200)
        y = random.randint(80, 300)
        w = random.randint(300, 800)
        h = random.randint(200, 600)

        return f'<loc_{x}><loc_{y}><loc_{w}><loc_{h}>'

    def _build_table_content(self, table: TableStructure) -> str:
        """Build table content with interleaved tags and text."""
        # Create occupancy grid
        occupancy_grid = table.get_occupancy_grid()

        rows_content = []

        for row_idx in range(table.num_rows):
            row_parts = []

            for col_idx in range(table.num_cols):
                cell_idx = occupancy_grid[row_idx, col_idx]

                if cell_idx == -1:
                    # No cell at this position - shouldn't happen in valid table
                    row_parts.append(f'<{TAG_EMPTY_CELL}>')
                    continue

                cell = table.cells[cell_idx]

                # Check if this is the origin of the cell
                if cell.row_idx == row_idx and cell.col_idx == col_idx:
                    # Cell originates here
                    tag, content = self._format_cell(cell, table)
                    row_parts.append(f'<{tag}>{content}')
                else:
                    # Cell occupies this position due to spanning
                    span_type = table.get_cell_span_type(row_idx, col_idx)

                    if span_type == 'colspan':
                        row_parts.append(f'<{TAG_LEFT_CELL}>')
                    elif span_type == 'rowspan':
                        row_parts.append(f'<{TAG_UP_CELL}>')
                    elif span_type == 'both':
                        row_parts.append(f'<{TAG_CROSS_CELL}>')

            # Add newline at end of row
            row_content = ''.join(row_parts)
            rows_content.append(row_content + f'<{TAG_NEWLINE}>')

        return ''.join(rows_content)

    def _format_cell(self, cell: Cell, table: TableStructure) -> tuple[str, str]:
        """
        Format a cell into (tag, content) tuple.

        Args:
            cell: Cell to format
            table: TableStructure for context

        Returns:
            Tuple of (tag_type, content_text)
        """
        # Determine tag type
        if cell.header_type == 'column' or (cell.is_header and cell.row_idx in table.column_headers):
            tag = TAG_COL_HEADER
        elif cell.header_type == 'row' or (cell.is_header and cell.col_idx in table.row_headers):
            tag = TAG_ROW_HEADER
        elif cell.content and not cell.content.is_empty():
            tag = TAG_FILLED_CELL
        else:
            tag = TAG_EMPTY_CELL

        # Get content text
        content = cell.content.text if cell.content else ""

        # For empty cells, no content
        if tag == TAG_EMPTY_CELL:
            content = ""

        return tag, content
