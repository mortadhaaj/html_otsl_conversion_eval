"""
Tests for truncated HTML handling.

These tests verify that the converter can handle HTML that's been truncated
due to maximum token limits in AI model generation.
"""

import pytest
from src.api.converters import TableConverter
from pathlib import Path


class TestTruncatedHTML:
    """Test handling of truncated HTML (common in AI-generated output)."""

    def test_missing_closing_table_tag(self):
        """Test HTML missing the closing </table> tag."""
        html = """<table>
  <tr>
    <td>A</td>
    <td>B</td>
  </tr>
  <tr>
    <td>C</td>
    <td>D</td>
  </tr>
"""  # Missing </table>

        # Should work in lenient mode (html5lib auto-closes)
        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4

        # Should validate successfully
        is_valid, errors = table.validate()
        assert is_valid

    def test_truncated_mid_cell_opening(self):
        """Test HTML truncated in the middle of opening a cell tag."""
        html = """<table>
  <tr>
    <td>A</td>
    <td>B</td>
  </tr>
  <tr>
    <td>C</td>
    <td"""  # Truncated mid-tag

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should parse available cells
        assert table.num_rows >= 1
        assert table.num_cols == 2

    def test_truncated_mid_cell_content(self):
        """Test HTML truncated in the middle of cell content."""
        html = """<table>
  <tr>
    <td>Complete content</td>
    <td>Truncated con"""  # Truncated mid-content

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should parse with partial content
        assert table.num_rows == 1
        assert table.num_cols == 2

        # Check that partial content is preserved
        cells = sorted(table.cells, key=lambda c: c.col_idx)
        assert cells[0].content.text == "Complete content"
        assert cells[1].content.text == "Truncated con"

    def test_truncated_mid_row(self):
        """Test HTML truncated in the middle of a row."""
        html = """<table>
  <tr>
    <td>A</td>
    <td>B</td>
  </tr>
  <tr>
    <td>C</td>"""  # Missing second cell and closing tags

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should have 2 rows (html5lib closes the partial row)
        assert table.num_rows == 2
        assert table.num_cols == 2

        # Lenient mode should fill the gap
        is_valid, errors = table.validate()
        assert is_valid

    def test_missing_closing_tr_td_and_table(self):
        """Test HTML missing all closing tags."""
        html = """<table>
  <tr>
    <td>A
    <td>B
  <tr>
    <td>C
    <td>D"""  # Missing all closing tags

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # html5lib should auto-close everything
        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4

    def test_real_truncated_example_1(self):
        """Test real truncated example (missing </table>)."""
        fixture = Path("tests/fixtures/malformed_truncated.html")
        if not fixture.exists():
            pytest.skip("Fixture not found")

        html = fixture.read_text()
        assert "</table>" not in html  # Verify it's actually truncated

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should parse successfully
        assert table.num_rows > 0
        assert table.num_cols > 0

        # Should be able to convert to OTSL
        otsl = converter.html_to_otsl(html)
        assert "<otsl>" in otsl
        assert "</otsl>" in otsl

        # Should validate
        is_valid, errors = table.validate()
        assert is_valid, f"Validation failed: {errors}"

    def test_real_truncated_example_2(self):
        """Test real truncated example (truncated mid-cell)."""
        fixture = Path("tests/fixtures/malformed_truncated_midcell.html")
        if not fixture.exists():
            pytest.skip("Fixture not found")

        html = fixture.read_text()
        assert html.strip().endswith("<td>20")  # Verify truncation

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should parse successfully
        assert table.num_rows > 0
        assert table.num_cols > 0

        # Should handle partial content
        last_row_cells = [c for c in table.cells if c.row_idx == table.num_rows - 1]
        assert len(last_row_cells) == table.num_cols

        # One cell should have partial content
        contents = [c.content.text for c in sorted(last_row_cells, key=lambda x: x.col_idx)]
        assert any("20" in c for c in contents)

        # Should validate
        is_valid, errors = table.validate()
        assert is_valid

    def test_truncated_with_unclosed_tags_in_content(self):
        """Test truncated HTML with unclosed tags within cell content."""
        html = """<table>
  <tr>
    <td>Text with <b>bold</td>
    <td>Another <i>italic text"""  # Unclosed <i> and truncated

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # html5lib should handle this gracefully
        assert table.num_rows == 1
        assert table.num_cols == 2

    def test_roundtrip_truncated_html(self):
        """Test roundtrip conversion of truncated HTML."""
        html = """<table>
  <tr><td>A</td><td>B</td></tr>
  <tr><td>C</td><td>D"""  # Truncated

        converter = TableConverter(strict=False)

        # Convert to OTSL
        otsl = converter.html_to_otsl(html)

        # Convert back to HTML
        html_reconstructed = converter.otsl_to_html(otsl)

        # Should have valid table
        assert "<table" in html_reconstructed
        assert "</table>" in html_reconstructed

        # Should have all cells
        table = converter.html_to_ir(html_reconstructed)
        assert len(table.cells) == 4


class TestTruncatedHTMLStrictMode:
    """Test that truncated HTML may fail in strict mode."""

    def test_truncated_strict_mode_may_succeed(self):
        """Note: html5lib fallback may still work even in strict mode."""
        html = """<table>
  <tr><td>A</td><td>B</td></tr>
"""  # Missing </table>

        # Even in strict mode, html5lib may auto-close
        converter = TableConverter(strict=True)
        table = converter.html_to_ir(html)

        # May succeed due to html5lib
        assert table.num_rows >= 1


class TestTruncatedOTSL:
    """Test handling of truncated OTSL."""

    def test_truncated_otsl_mid_tag(self):
        """Test OTSL truncated in the middle of a tag."""
        otsl = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<nl><fcel>C<fc"

        converter = TableConverter(strict=False)

        # This may fail as OTSL parsing is regex-based
        try:
            table = converter.otsl_to_ir(otsl)
            # If it parses, should have partial data
            assert table.num_rows >= 1
        except ValueError:
            # Expected - OTSL requires proper structure
            pass

    def test_truncated_otsl_missing_closing(self):
        """Test OTSL missing closing </otsl> tag - lenient mode auto-closes it."""
        otsl = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<nl><fcel>C<fcel>D<nl>"

        # Lenient mode should auto-close the tag
        converter = TableConverter(strict=False)
        table = converter.otsl_to_ir(otsl)

        # Should parse successfully after auto-closing
        assert table.num_rows == 2
        assert table.num_cols == 2

        # Strict mode should still fail
        converter_strict = TableConverter(strict=True)
        with pytest.raises(ValueError, match="must end with </otsl>"):
            converter_strict.otsl_to_ir(otsl)

    def test_otsl_auto_close_with_wrapper(self):
        """Test adding missing </otsl> tag programmatically."""
        otsl_truncated = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<nl>"

        # Auto-close if needed
        if not otsl_truncated.strip().endswith("</otsl>"):
            otsl_fixed = otsl_truncated + "</otsl>"
        else:
            otsl_fixed = otsl_truncated

        converter = TableConverter(strict=False)
        table = converter.otsl_to_ir(otsl_fixed)

        assert table.num_rows == 1
        assert table.num_cols == 2


class TestTruncationUtils:
    """Test utilities for handling truncated output."""

    def test_detect_truncated_html(self):
        """Test detection of truncated HTML."""
        from lxml import html as lxml_html

        html_complete = "<table><tr><td>A</td></tr></table>"
        html_truncated = "<table><tr><td>A</td></tr>"

        # Simple detection: count opening vs closing tags
        def is_likely_truncated(html_str: str) -> bool:
            table_open = html_str.count("<table")
            table_close = html_str.count("</table>")
            return table_open > table_close

        assert not is_likely_truncated(html_complete)
        assert is_likely_truncated(html_truncated)

    def test_auto_close_html_wrapper(self):
        """Test utility to auto-close HTML tags."""

        def auto_close_html(html_str: str) -> str:
            """Add missing closing tags if needed."""
            if "<table" in html_str and "</table>" not in html_str:
                return html_str + "</table>"
            return html_str

        html_truncated = "<table><tr><td>A</td></tr>"
        html_fixed = auto_close_html(html_truncated)

        assert "</table>" in html_fixed

        # Should parse successfully now
        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html_fixed)
        assert table.num_rows == 1

    def test_auto_close_otsl_wrapper(self):
        """Test utility to auto-close OTSL tags."""

        def auto_close_otsl(otsl_str: str) -> str:
            """Add missing </otsl> tag if needed."""
            if otsl_str.strip().startswith("<otsl>") and not otsl_str.strip().endswith("</otsl>"):
                return otsl_str + "</otsl>"
            return otsl_str

        otsl_truncated = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<nl>"
        otsl_fixed = auto_close_otsl(otsl_truncated)

        assert "</otsl>" in otsl_fixed

        # Should parse successfully now
        converter = TableConverter(strict=False)
        table = converter.otsl_to_ir(otsl_fixed)
        assert table.num_rows == 1
