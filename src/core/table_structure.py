"""
Intermediate Representation (IR) for table structures.

Provides format-agnostic representation bridging HTML and OTSL formats.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class LaTeXFormula:
    """Represents a LaTeX formula within cell content."""
    original_text: str  # Original LaTeX string
    start_pos: int  # Start position in content
    end_pos: int  # End position in content
    formula_type: str  # 'inline' ($...$), 'display' ($$...$$), 'tag' (<math>...)


@dataclass
class CellContent:
    """Represents the content of a single table cell."""
    text: str
    latex_formulas: List[LaTeXFormula] = field(default_factory=list)
    has_math_tags: bool = False  # Whether HTML had <math>, <sup>, <sub> tags

    def __str__(self) -> str:
        return self.text

    def is_empty(self) -> bool:
        """Check if cell content is empty (ignoring whitespace)."""
        return not self.text.strip()


@dataclass
class Cell:
    """Represents a table cell with position and spanning."""
    row_idx: int
    col_idx: int
    rowspan: int = 1
    colspan: int = 1
    content: Optional[CellContent] = None
    is_header: bool = False
    header_type: Optional[str] = None  # 'column', 'row', or None

    def occupies_position(self, row: int, col: int) -> bool:
        """Check if this cell occupies the given grid position."""
        return (
            self.row_idx <= row < self.row_idx + self.rowspan and
            self.col_idx <= col < self.col_idx + self.colspan
        )

    def get_occupied_positions(self) -> List[Tuple[int, int]]:
        """Get all grid positions occupied by this cell."""
        positions = []
        for r in range(self.row_idx, self.row_idx + self.rowspan):
            for c in range(self.col_idx, self.col_idx + self.colspan):
                positions.append((r, c))
        return positions


@dataclass
class TableStructure:
    """Intermediate representation of a table."""
    num_rows: int
    num_cols: int
    cells: List[Cell]
    caption: Optional[CellContent] = None
    has_border: bool = True
    column_headers: List[int] = field(default_factory=list)  # Row indices with column headers
    row_headers: List[int] = field(default_factory=list)  # Column indices with row headers

    def get_cell_at(self, row: int, col: int) -> Optional[Cell]:
        """
        Get cell that occupies the specific grid position.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Cell that occupies this position, or None if position is invalid
        """
        if row < 0 or row >= self.num_rows or col < 0 or col >= self.num_cols:
            return None

        for cell in self.cells:
            if cell.occupies_position(row, col):
                return cell
        return None

    def get_cell_origin_at(self, row: int, col: int) -> Optional[Cell]:
        """
        Get cell that originates at the specific position (not spanning cells).

        Args:
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Cell originating at this position, or None if no cell starts here
        """
        for cell in self.cells:
            if cell.row_idx == row and cell.col_idx == col:
                return cell
        return None

    def get_occupancy_grid(self) -> np.ndarray:
        """
        Return grid showing which cell occupies each position.

        Returns:
            2D array where grid[r, c] contains the index of the cell occupying position (r, c),
            or -1 if no cell occupies that position.
        """
        grid = np.full((self.num_rows, self.num_cols), -1, dtype=int)

        for idx, cell in enumerate(self.cells):
            for r in range(cell.row_idx, cell.row_idx + cell.rowspan):
                for c in range(cell.col_idx, cell.col_idx + cell.colspan):
                    if 0 <= r < self.num_rows and 0 <= c < self.num_cols:
                        grid[r, c] = idx

        return grid

    def get_cell_span_type(self, row: int, col: int) -> str:
        """
        Determine the span type for a grid position.

        Args:
            row: Row index
            col: Column index

        Returns:
            'origin' if cell starts here
            'colspan' if occupied by colspan from left
            'rowspan' if occupied by rowspan from above
            'both' if occupied by both colspan and rowspan
            'empty' if no cell occupies this position
        """
        cell = self.get_cell_at(row, col)
        if cell is None:
            return 'empty'

        if cell.row_idx == row and cell.col_idx == col:
            return 'origin'

        is_colspan = col > cell.col_idx
        is_rowspan = row > cell.row_idx

        if is_colspan and is_rowspan:
            return 'both'
        elif is_colspan:
            return 'colspan'
        elif is_rowspan:
            return 'rowspan'
        else:
            return 'origin'

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate table structure integrity.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check dimensions
        if self.num_rows <= 0:
            errors.append("Table must have at least one row")
        if self.num_cols <= 0:
            errors.append("Table must have at least one column")

        # Check cells
        if not self.cells:
            errors.append("Table must have at least one cell")

        # Check cell positions
        for i, cell in enumerate(self.cells):
            if cell.row_idx < 0 or cell.row_idx >= self.num_rows:
                errors.append(f"Cell {i} has invalid row_idx: {cell.row_idx}")
            if cell.col_idx < 0 or cell.col_idx >= self.num_cols:
                errors.append(f"Cell {i} has invalid col_idx: {cell.col_idx}")
            if cell.rowspan < 1:
                errors.append(f"Cell {i} has invalid rowspan: {cell.rowspan}")
            if cell.colspan < 1:
                errors.append(f"Cell {i} has invalid colspan: {cell.colspan}")

            # Check if cell extends beyond table bounds
            if cell.row_idx + cell.rowspan > self.num_rows:
                errors.append(f"Cell {i} extends beyond table rows")
            if cell.col_idx + cell.colspan > self.num_cols:
                errors.append(f"Cell {i} extends beyond table columns")

        # Check for overlapping cells
        grid = self.get_occupancy_grid()
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                if grid[r, c] == -1:
                    errors.append(f"No cell covers position ({r}, {c})")

        # Check header indices
        for row_idx in self.column_headers:
            if row_idx < 0 or row_idx >= self.num_rows:
                errors.append(f"Invalid column header row index: {row_idx}")

        for col_idx in self.row_headers:
            if col_idx < 0 or col_idx >= self.num_cols:
                errors.append(f"Invalid row header column index: {col_idx}")

        return len(errors) == 0, errors

    def __str__(self) -> str:
        """String representation of table structure."""
        return f"TableStructure({self.num_rows}x{self.num_cols}, {len(self.cells)} cells)"
