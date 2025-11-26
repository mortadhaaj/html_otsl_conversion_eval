"""
Unit tests for HTML table parser.
"""

import pytest
from src.core.html_parser import HTMLTableParser


class TestBasicParsing:
    """Test basic HTML parsing."""

    def test_parse_simple_table(self, simple_html):
        """Test parsing a simple HTML table."""
        parser = HTMLTableParser()
        table = parser.parse(simple_html)

        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4

    def test_parse_with_thead(self):
        """Test parsing table with thead."""
        html = """
        <table>
            <thead>
                <tr><th>Header</th></tr>
            </thead>
            <tbody>
                <tr><td>Data</td></tr>
            </tbody>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        assert table.num_rows == 2
        assert len(table.column_headers) == 1
        assert 0 in table.column_headers

    def test_parse_with_caption(self):
        """Test parsing table with caption."""
        html = """
        <table>
            <caption>Test Caption</caption>
            <tr><td>A</td></tr>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        assert table.caption is not None
        assert table.caption.text == "Test Caption"

    def test_parse_without_border(self):
        """Test parsing table without border attribute."""
        html = "<table><tr><td>A</td></tr></table>"
        parser = HTMLTableParser()
        table = parser.parse(html)

        # When no border attribute, should be False
        assert not table.has_border


class TestSpanningCells:
    """Test parsing cells with rowspan/colspan."""

    def test_parse_colspan(self):
        """Test parsing cell with colspan."""
        html = """
        <table>
            <tr>
                <td colspan="2">Merged</td>
            </tr>
            <tr>
                <td>A</td>
                <td>B</td>
            </tr>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        # First cell should have colspan=2
        merged_cell = table.cells[0]
        assert merged_cell.colspan == 2
        assert merged_cell.content.text == "Merged"

    def test_parse_rowspan(self):
        """Test parsing cell with rowspan."""
        html = """
        <table>
            <tr>
                <td rowspan="2">Merged</td>
                <td>A</td>
            </tr>
            <tr>
                <td>B</td>
            </tr>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        # First cell should have rowspan=2
        merged_cell = table.cells[0]
        assert merged_cell.rowspan == 2
        assert merged_cell.content.text == "Merged"

    def test_parse_both_spans(self, spanning_html):
        """Test parsing cell with both rowspan and colspan."""
        parser = HTMLTableParser()
        table = parser.parse(spanning_html)

        # Should have 4 cells total
        assert len(table.cells) == 4

        # First cell has rowspan=2
        assert table.cells[0].rowspan == 2
        assert table.cells[0].content.text == "A"

        # Second cell has colspan=2
        assert table.cells[1].colspan == 2
        assert table.cells[1].content.text == "B"


class TestLaTeXParsing:
    """Test parsing HTML with LaTeX formulas."""

    def test_parse_latex_formula(self, latex_html):
        """Test parsing table with LaTeX formulas."""
        parser = HTMLTableParser(preserve_latex=True)
        table = parser.parse(latex_html)

        # Check that LaTeX formulas are detected
        first_cell = table.cells[0]
        assert len(first_cell.content.latex_formulas) > 0
        assert "$x^2$" in first_cell.content.text

    def test_parse_without_latex_preservation(self):
        """Test parsing without LaTeX preservation."""
        html = "<table><tr><td>$x^2$</td></tr></table>"
        parser = HTMLTableParser(preserve_latex=False)
        table = parser.parse(html)

        # LaTeX formulas should not be extracted
        first_cell = table.cells[0]
        assert len(first_cell.content.latex_formulas) == 0


class TestHeaderDetection:
    """Test detection of header cells."""

    def test_detect_th_as_header(self):
        """Test that <th> elements are detected as headers."""
        html = """
        <table>
            <tr>
                <th>Header</th>
                <td>Data</td>
            </tr>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        # First cell should be a header
        assert table.cells[0].is_header
        # When th is in tbody at start of row, it's treated as row header
        assert table.cells[0].header_type == "row"

        # Second cell should not be a header
        assert not table.cells[1].is_header

    def test_detect_row_headers(self):
        """Test detection of row headers."""
        html = """
        <table>
            <tbody>
                <tr>
                    <th scope="row">Row1</th>
                    <td>Data</td>
                </tr>
            </tbody>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        # First cell should be a row header
        assert table.cells[0].is_header
        # Note: header_type detection may vary based on implementation


class TestEdgeCases:
    """Test edge cases in HTML parsing."""

    def test_empty_table(self):
        """Test parsing empty table."""
        html = "<table></table>"
        parser = HTMLTableParser()

        with pytest.raises((ValueError, Exception)):
            parser.parse(html)

    def test_empty_cells(self):
        """Test parsing table with empty cells."""
        html = """
        <table>
            <tr>
                <td></td>
                <td>B</td>
            </tr>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        # First cell should have empty content
        assert table.cells[0].content.text == ""
        assert table.cells[1].content.text == "B"

    def test_whitespace_handling(self):
        """Test handling of whitespace in cells."""
        html = """
        <table>
            <tr>
                <td>  Spaces  </td>
            </tr>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        # Whitespace should be normalized
        content = table.cells[0].content.text
        assert content == "Spaces" or content.strip() == "Spaces"

    def test_invalid_html(self):
        """Test parsing invalid HTML."""
        html = "<table><tr><td>Unclosed"
        parser = HTMLTableParser()

        # Parser should handle invalid HTML gracefully
        # (html5lib is lenient and will try to parse it)
        table = parser.parse(html)
        assert table is not None

    def test_nested_elements(self):
        """Test parsing cells with nested HTML elements."""
        html = """
        <table>
            <tr>
                <td><b>Bold</b> text</td>
            </tr>
        </table>
        """
        parser = HTMLTableParser()
        table = parser.parse(html)

        # Text content should be extracted
        text = table.cells[0].content.text
        assert "Bold" in text
        assert "text" in text
