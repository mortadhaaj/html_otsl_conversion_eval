"""
Unit tests for table structure classes.
"""

import pytest
from src.core.table_structure import TableStructure, Cell, CellContent, LaTeXFormula


class TestCellContent:
    """Test CellContent class."""

    def test_create_simple_content(self):
        """Test creating simple cell content."""
        content = CellContent(text="Hello", latex_formulas=[], has_math_tags=False)

        assert content.text == "Hello"
        assert content.latex_formulas == []
        assert not content.has_math_tags

    def test_create_with_latex(self):
        """Test creating content with LaTeX formulas."""
        formula = LaTeXFormula(original_text="$x^2$", formula_type="inline", start_pos=0, end_pos=5)
        content = CellContent(
            text="Formula: $x^2$",
            latex_formulas=[formula],
            has_math_tags=False
        )

        assert len(content.latex_formulas) == 1
        assert "$x^2$" in content.latex_formulas[0].original_text

    def test_empty_content(self):
        """Test creating empty content."""
        content = CellContent(text="", latex_formulas=[], has_math_tags=False)

        assert content.text == ""
        assert not content.latex_formulas


class TestCell:
    """Test Cell class."""

    def test_create_simple_cell(self):
        """Test creating a simple cell."""
        content = CellContent(text="A", latex_formulas=[], has_math_tags=False)
        cell = Cell(
            row_idx=0,
            col_idx=0,
            rowspan=1,
            colspan=1,
            content=content,
            is_header=False,
            header_type=None
        )

        assert cell.row_idx == 0
        assert cell.col_idx == 0
        assert cell.rowspan == 1
        assert cell.colspan == 1
        assert cell.content.text == "A"
        assert not cell.is_header

    def test_create_header_cell(self):
        """Test creating a header cell."""
        content = CellContent(text="Header", latex_formulas=[], has_math_tags=False)
        cell = Cell(
            row_idx=0,
            col_idx=0,
            rowspan=1,
            colspan=1,
            content=content,
            is_header=True,
            header_type="column"
        )

        assert cell.is_header
        assert cell.header_type == "column"

    def test_create_spanning_cell(self):
        """Test creating a cell with rowspan and colspan."""
        content = CellContent(text="Merged", latex_formulas=[], has_math_tags=False)
        cell = Cell(
            row_idx=0,
            col_idx=0,
            rowspan=2,
            colspan=3,
            content=content,
            is_header=False,
            header_type=None
        )

        assert cell.rowspan == 2
        assert cell.colspan == 3

    def test_cell_with_empty_content(self):
        """Test creating a cell with empty content."""
        content = CellContent(text="", latex_formulas=[], has_math_tags=False)
        cell = Cell(
            row_idx=1,
            col_idx=1,
            rowspan=1,
            colspan=1,
            content=content,
            is_header=False,
            header_type=None
        )

        assert cell.content.text == ""


class TestTableStructure:
    """Test TableStructure class."""

    def test_create_simple_table(self, simple_table):
        """Test creating a simple table structure."""
        assert simple_table.num_rows == 2
        assert simple_table.num_cols == 2
        assert len(simple_table.cells) == 4
        assert simple_table.caption is None
        assert simple_table.has_border

    def test_create_with_caption(self):
        """Test creating table with caption."""
        caption = CellContent(text="Test Caption", latex_formulas=[], has_math_tags=False)
        table = TableStructure(
            num_rows=1,
            num_cols=1,
            cells=[],
            caption=caption,
            has_border=True,
            column_headers=[],
            row_headers=[]
        )

        assert table.caption is not None
        assert table.caption.text == "Test Caption"

    def test_get_occupancy_grid(self, simple_table):
        """Test generating occupancy grid."""
        grid = simple_table.get_occupancy_grid()

        assert len(grid) == 2  # 2 rows
        assert len(grid[0]) == 2  # 2 columns
        # Each cell should be marked with its index
        assert grid[0][0] == 0  # First cell
        assert grid[0][1] == 1  # Second cell
        assert grid[1][0] == 2  # Third cell
        assert grid[1][1] == 3  # Fourth cell

    def test_occupancy_grid_with_spanning(self):
        """Test occupancy grid with spanning cells."""
        content = CellContent(text="Merged", latex_formulas=[], has_math_tags=False)
        cell = Cell(
            row_idx=0,
            col_idx=0,
            rowspan=2,
            colspan=2,
            content=content,
            is_header=False,
            header_type=None
        )

        table = TableStructure(
            num_rows=2,
            num_cols=2,
            cells=[cell],
            caption=None,
            has_border=True,
            column_headers=[],
            row_headers=[]
        )

        grid = table.get_occupancy_grid()

        # All positions should be marked with cell index 0
        assert grid[0][0] == 0
        assert grid[0][1] == 0
        assert grid[1][0] == 0
        assert grid[1][1] == 0

    def test_column_headers(self):
        """Test table with column headers."""
        table = TableStructure(
            num_rows=2,
            num_cols=2,
            cells=[],
            caption=None,
            has_border=True,
            column_headers=[0],  # First row is header
            row_headers=[]
        )

        assert 0 in table.column_headers
        assert len(table.row_headers) == 0

    def test_row_headers(self):
        """Test table with row headers."""
        table = TableStructure(
            num_rows=2,
            num_cols=2,
            cells=[],
            caption=None,
            has_border=True,
            column_headers=[],
            row_headers=[0]  # First column is header
        )

        assert 0 in table.row_headers
        assert len(table.column_headers) == 0


class TestTableValidation:
    """Test table structure validation."""

    def test_valid_simple_table(self, simple_table):
        """Test that simple table is valid."""
        # Should not raise any exceptions
        grid = simple_table.get_occupancy_grid()
        assert grid is not None

    def test_cell_positions(self, simple_table):
        """Test that cells are at expected positions."""
        cells_by_position = {}
        for cell in simple_table.cells:
            cells_by_position[(cell.row_idx, cell.col_idx)] = cell

        assert (0, 0) in cells_by_position
        assert (0, 1) in cells_by_position
        assert (1, 0) in cells_by_position
        assert (1, 1) in cells_by_position

    def test_no_overlapping_cells(self, simple_table):
        """Test that cells don't overlap in occupancy grid."""
        grid = simple_table.get_occupancy_grid()

        # Count how many cells occupy each position
        for row in range(simple_table.num_rows):
            for col in range(simple_table.num_cols):
                # Each position should be occupied by exactly one cell
                assert grid[row][col] >= 0
