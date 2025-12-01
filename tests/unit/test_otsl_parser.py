"""
Unit tests for OTSL table parser.
"""

import pytest
from src.core.otsl_parser import OTSLTableParser


class TestBasicParsing:
    """Test basic OTSL parsing."""

    def test_parse_simple_table(self, simple_otsl):
        """Test parsing a simple OTSL table."""
        parser = OTSLTableParser()
        table = parser.parse(simple_otsl)

        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4

    def test_parse_with_caption(self):
        """Test parsing OTSL with caption."""
        otsl = "<otsl><caption>Test</caption><loc_10><loc_20><loc_100><loc_200><fcel>A<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        assert table.caption is not None
        assert table.caption.text == "Test"

    def test_parse_with_headers(self):
        """Test parsing OTSL with column headers."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><ched>H1<ched>H2<nl><fcel>A<fcel>B<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        assert len(table.cells) == 4
        assert table.cells[0].is_header
        assert table.cells[0].header_type == "column"
        assert not table.cells[2].is_header


class TestSpanningCells:
    """Test parsing OTSL cells with spans."""

    def test_parse_colspan(self):
        """Test parsing cell with colspan markers."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>Merged<lcel><nl><fcel>A<fcel>B<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        # First cell should have colspan=2
        assert table.cells[0].colspan == 2
        assert table.cells[0].content.text == "Merged"

    def test_parse_rowspan(self):
        """Test parsing cell with rowspan markers."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>Merged<fcel>A<nl><ucel><fcel>B<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        # First cell should have rowspan=2
        assert table.cells[0].rowspan == 2
        assert table.cells[0].content.text == "Merged"

    def test_parse_both_spans(self):
        """Test parsing cell with both rowspan and colspan."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>Big<lcel><nl><ucel><xcel><nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        # First cell should have both spans
        assert table.cells[0].rowspan == 2
        assert table.cells[0].colspan == 2


class TestEmptyCells:
    """Test parsing empty cells."""

    def test_parse_empty_cell(self):
        """Test parsing OTSL with empty cell markers."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>A<ecel><nl><fcel>C<fcel>D<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        assert len(table.cells) == 4
        # Second cell should be empty
        assert table.cells[1].content.text == ""

    def test_multiple_empty_cells(self):
        """Test parsing table with multiple empty cells."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><ecel><ecel><nl><ecel><ecel><nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        assert len(table.cells) == 4
        for cell in table.cells:
            assert cell.content.text == ""

    def test_empty_cell_with_rowspan(self):
        """Test empty cell that spans multiple rows (regression test for issue)."""
        # OTSL with empty cell at (0,1) that spans 2 rows
        # Row 0: [Cell A] [Empty spanning 2 rows]
        # Row 1: [Cell B] [continued from above]
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>A<ecel><nl><fcel>B<ucel><nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 3  # Only 3 cells created

        # Find the empty cell
        empty_cell = next((c for c in table.cells if c.content.text == ""), None)
        assert empty_cell is not None
        assert empty_cell.row_idx == 0
        assert empty_cell.col_idx == 1
        assert empty_cell.rowspan == 2  # Should span 2 rows!
        assert empty_cell.colspan == 1

    def test_empty_cell_with_colspan_and_rowspan(self):
        """Test empty cell with both colspan and rowspan."""
        # OTSL with empty cell at (0,1) that spans 2 rows and 2 columns
        # Row 0: [Cell A] [Empty spanning 2x2]
        # Row 1: [Cell B] [continued from above]
        otsl = "<otsl><loc_10><loc_20><loc_30><loc_100><loc_200><loc_300><fcel>A<ecel><lcel><nl><fcel>B<ucel><xcel><nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        assert table.num_rows == 2
        assert table.num_cols == 3
        assert len(table.cells) == 3

        # Find the empty cell
        empty_cell = next((c for c in table.cells if c.content.text == ""), None)
        assert empty_cell is not None
        assert empty_cell.row_idx == 0
        assert empty_cell.col_idx == 1
        assert empty_cell.rowspan == 2
        assert empty_cell.colspan == 2


class TestLaTeXParsing:
    """Test parsing OTSL with LaTeX formulas."""

    def test_parse_latex_formula(self):
        """Test parsing OTSL with LaTeX formulas."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>$x^2$<fcel>Formula<nl></otsl>"
        parser = OTSLTableParser(preserve_latex=True)
        table = parser.parse(otsl)

        # First cell should have LaTeX formula
        first_cell = table.cells[0]
        assert len(first_cell.content.latex_formulas) > 0
        assert "$x^2$" in first_cell.content.text

    def test_parse_without_latex_preservation(self):
        """Test parsing without LaTeX preservation."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>$x^2$<nl></otsl>"
        parser = OTSLTableParser(preserve_latex=False)
        table = parser.parse(otsl)

        # LaTeX formulas should not be extracted
        assert len(table.cells[0].content.latex_formulas) == 0


class TestRowHeaders:
    """Test parsing row headers."""

    def test_parse_row_header(self):
        """Test parsing OTSL with row headers."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><rhed>Row1<fcel>Data<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        # First cell should be a row header
        assert table.cells[0].is_header
        assert table.cells[0].header_type == "row"


class TestEdgeCases:
    """Test edge cases in OTSL parsing."""

    def test_invalid_format_no_otsl_tag(self):
        """Test parsing string without OTSL tags."""
        parser = OTSLTableParser()

        with pytest.raises(ValueError):
            parser.parse("<table>Not OTSL</table>")

    def test_invalid_format_no_closing_tag(self):
        """Test parsing OTSL without closing tag."""
        parser = OTSLTableParser()

        with pytest.raises(ValueError):
            parser.parse("<otsl><loc_10><loc_20><loc_100><loc_200><fcel>A")

    def test_location_coordinates(self):
        """Test that location coordinates are parsed correctly."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>A<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        # Location coordinates are removed during parsing
        assert table is not None
        assert len(table.cells) == 1

    def test_multiple_location_tags(self):
        """Test parsing with multiple location tags."""
        otsl = "<otsl><loc_10><loc_20><loc_30><loc_40><fcel>A<nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        assert table is not None

    def test_whitespace_in_content(self):
        """Test handling of whitespace in cell content."""
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>  Spaces  <nl></otsl>"
        parser = OTSLTableParser()
        table = parser.parse(otsl)

        # Whitespace should be preserved or normalized
        content = table.cells[0].content.text
        assert "Spaces" in content
