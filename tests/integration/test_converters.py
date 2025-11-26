"""
Integration tests for table converters.
"""

import pytest
from pathlib import Path
from src.api.converters import TableConverter


class TestHTMLToOTSL:
    """Test HTML to OTSL conversion."""

    def test_simple_conversion(self, converter, simple_html):
        """Test simple HTML to OTSL conversion."""
        otsl = converter.html_to_otsl(simple_html)

        assert otsl.startswith("<otsl>")
        assert otsl.endswith("</otsl>")
        assert "<fcel>" in otsl
        assert "<nl>" in otsl

    def test_with_caption(self, converter):
        """Test HTML to OTSL with caption."""
        html = "<table><caption>Test</caption><tr><td>A</td></tr></table>"
        otsl = converter.html_to_otsl(html)

        assert "<caption>Test</caption>" in otsl

    def test_with_headers(self, converter):
        """Test HTML to OTSL with headers."""
        html = "<table><thead><tr><th>H</th></tr></thead><tbody><tr><td>D</td></tr></tbody></table>"
        otsl = converter.html_to_otsl(html)

        assert "<ched>" in otsl

    def test_with_spanning(self, converter, spanning_html):
        """Test HTML to OTSL with spanning cells."""
        otsl = converter.html_to_otsl(spanning_html)

        assert "<lcel>" in otsl or "<ucel>" in otsl


class TestOTSLToHTML:
    """Test OTSL to HTML conversion."""

    def test_simple_conversion(self, converter, simple_otsl):
        """Test simple OTSL to HTML conversion."""
        html = converter.otsl_to_html(simple_otsl)

        assert "<table" in html
        assert "</table>" in html
        assert "<td>A</td>" in html

    def test_with_caption(self, converter):
        """Test OTSL to HTML with caption."""
        otsl = "<otsl><caption>Test</caption><loc_10><loc_20><loc_100><loc_200><fcel>A<nl></otsl>"
        html = converter.otsl_to_html(otsl)

        assert "<caption>Test</caption>" in html

    def test_with_headers(self, converter):
        """Test OTSL to HTML with headers."""
        otsl = "<otsl><has_thead><has_tbody><loc_10><loc_20><loc_100><loc_200><ched>H<nl><fcel>D<nl></otsl>"
        html = converter.otsl_to_html(otsl)

        assert "<thead>" in html
        assert "<th>H</th>" in html


class TestRoundtripHTML:
    """Test HTML roundtrip conversions."""

    def test_simple_roundtrip(self, converter, simple_html):
        """Test HTML → OTSL → HTML roundtrip."""
        original_ir = converter.html_to_ir(simple_html)
        otsl = converter.html_to_otsl(simple_html)
        reconstructed_html = converter.otsl_to_html(otsl)
        reconstructed_ir = converter.html_to_ir(reconstructed_html)

        assert original_ir.num_rows == reconstructed_ir.num_rows
        assert original_ir.num_cols == reconstructed_ir.num_cols
        assert len(original_ir.cells) == len(reconstructed_ir.cells)

    def test_roundtrip_with_latex(self, converter, latex_html):
        """Test LaTeX preservation in HTML roundtrip."""
        otsl = converter.html_to_otsl(latex_html)
        reconstructed_html = converter.otsl_to_html(otsl)

        # Check that LaTeX is preserved
        assert "$x^2$" in reconstructed_html or "x^2" in reconstructed_html

    def test_roundtrip_with_spanning(self, converter, spanning_html):
        """Test spanning preservation in HTML roundtrip."""
        original_ir = converter.html_to_ir(spanning_html)
        otsl, reconstructed_html, _ = converter.roundtrip_html(spanning_html)
        reconstructed_ir = converter.html_to_ir(reconstructed_html)

        # Check structure is preserved
        assert len(original_ir.cells) == len(reconstructed_ir.cells)

        # Check first cell has rowspan=2
        original_first = original_ir.cells[0]
        reconstructed_first = reconstructed_ir.cells[0]
        assert original_first.rowspan == reconstructed_first.rowspan


class TestRoundtripOTSL:
    """Test OTSL roundtrip conversions."""

    def test_simple_roundtrip(self, converter, simple_otsl):
        """Test OTSL → HTML → OTSL roundtrip."""
        original_ir = converter.otsl_to_ir(simple_otsl)
        html = converter.otsl_to_html(simple_otsl)
        reconstructed_otsl = converter.html_to_otsl(html)
        reconstructed_ir = converter.otsl_to_ir(reconstructed_otsl)

        assert original_ir.num_rows == reconstructed_ir.num_rows
        assert original_ir.num_cols == reconstructed_ir.num_cols
        assert len(original_ir.cells) == len(reconstructed_ir.cells)


class TestValidation:
    """Test conversion validation."""

    def test_validate_matching_structures(self, converter, simple_html, simple_otsl):
        """Test validation of matching structures."""
        is_valid, message = converter.validate_conversion(simple_html, simple_otsl)

        assert is_valid
        assert "valid" in message.lower()

    def test_validate_mismatched_structures(self, converter):
        """Test validation of mismatched structures."""
        html = "<table><tr><td>A</td><td>B</td></tr></table>"
        otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>A<nl></otsl>"  # Only 1 cell

        is_valid, message = converter.validate_conversion(html, otsl)

        assert not is_valid
        assert "mismatch" in message.lower()


class TestFixtures:
    """Test conversion on all fixture files."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_all_fixtures(self, converter, fixtures_dir):
        """Test conversion on all HTML/OTSL fixture pairs."""
        html_files = sorted(fixtures_dir.glob("*.html"))

        passed = 0
        failed = []

        for html_file in html_files:
            otsl_file = html_file.with_suffix(".otsl")

            if not otsl_file.exists():
                continue

            html_content = html_file.read_text()
            otsl_content = otsl_file.read_text()

            is_valid, message = converter.validate_conversion(html_content, otsl_content)

            if is_valid:
                passed += 1
            else:
                failed.append(html_file.name)

        # Should pass all fixtures
        assert len(failed) == 0, f"Failed fixtures: {failed}"
        assert passed > 0, "No fixtures were tested"
