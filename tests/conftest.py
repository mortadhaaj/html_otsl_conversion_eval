"""
Shared pytest fixtures for table conversion tests.
"""

import pytest
from pathlib import Path
from src.core.table_structure import TableStructure, Cell, CellContent
from src.api.converters import TableConverter


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def converter():
    """Return a TableConverter instance."""
    return TableConverter()


@pytest.fixture
def simple_cell():
    """Return a simple Cell object."""
    content = CellContent(text="Test", latex_formulas=[], has_math_tags=False)
    return Cell(
        row_idx=0,
        col_idx=0,
        rowspan=1,
        colspan=1,
        content=content,
        is_header=False,
        header_type=None
    )


@pytest.fixture
def simple_table():
    """Return a simple 2x2 TableStructure."""
    cells = []
    for row in range(2):
        for col in range(2):
            content = CellContent(
                text=f"Cell_{row}_{col}",
                latex_formulas=[],
                has_math_tags=False
            )
            cell = Cell(
                row_idx=row,
                col_idx=col,
                rowspan=1,
                colspan=1,
                content=content,
                is_header=False,
                header_type=None
            )
            cells.append(cell)

    return TableStructure(
        num_rows=2,
        num_cols=2,
        cells=cells,
        caption=None,
        has_border=True,
        column_headers=[],
        row_headers=[]
    )


@pytest.fixture
def simple_html():
    """Return simple HTML table string."""
    return """
    <table border="1">
        <tr>
            <td>A</td>
            <td>B</td>
        </tr>
        <tr>
            <td>C</td>
            <td>D</td>
        </tr>
    </table>
    """


@pytest.fixture
def simple_otsl():
    """Return simple OTSL table string."""
    return "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>A<fcel>B<nl><fcel>C<fcel>D<nl></otsl>"


@pytest.fixture
def latex_html():
    """Return HTML with LaTeX formulas."""
    return """
    <table border="1">
        <tr>
            <td>$x^2$</td>
            <td>Formula 1</td>
        </tr>
        <tr>
            <td>$$E = mc^2$$</td>
            <td>Formula 2</td>
        </tr>
    </table>
    """


@pytest.fixture
def spanning_html():
    """Return HTML with rowspan and colspan."""
    return """
    <table border="1">
        <tr>
            <td rowspan="2">A</td>
            <td colspan="2">B</td>
        </tr>
        <tr>
            <td>C</td>
            <td>D</td>
        </tr>
    </table>
    """
