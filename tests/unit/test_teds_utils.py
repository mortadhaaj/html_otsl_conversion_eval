"""
Unit tests for TEDS utilities.

These tests will be skipped if table-recognition-metric is not installed.
"""

import pytest
from src.api.teds_utils import (
    TEDSCalculator,
    normalize_html_for_teds,
    compare_with_teds
)


# Skip all tests if TEDS package is not available
calculator = TEDSCalculator()
pytestmark = pytest.mark.skipif(
    not calculator.is_available(),
    reason="table-recognition-metric package not installed"
)


class TestTEDSCalculator:
    """Test TEDS calculator."""

    def test_calculator_initialization(self):
        """Test TEDS calculator can be initialized."""
        calc = TEDSCalculator()
        assert calc.is_available()

    def test_identical_tables(self):
        """Test TEDS score for identical tables."""
        html = "<table><tr><td>A</td></tr></table>"
        calc = TEDSCalculator()
        score = calc.compute_score(html, html)

        # Identical tables should have score of 1.0
        assert score == pytest.approx(1.0)

    def test_different_tables(self):
        """Test TEDS score for different tables."""
        html1 = "<table><tr><td>A</td></tr></table>"
        html2 = "<table><tr><td>B</td></tr></table>"

        calc = TEDSCalculator()
        score = calc.compute_score(html1, html2)

        # Different content should have score < 1.0
        assert 0.0 <= score < 1.0

    def test_structure_only_mode(self):
        """Test TEDS in structure-only mode."""
        html1 = "<table><tr><td>A</td></tr></table>"
        html2 = "<table><tr><td>B</td></tr></table>"

        calc = TEDSCalculator(structure_only=True)
        score = calc.compute_score(html1, html2)

        # Same structure, different content should score 1.0 in structure-only mode
        assert score == pytest.approx(1.0)


class TestHTMLNormalization:
    """Test HTML normalization for TEDS."""

    def test_normalize_simple_table(self):
        """Test normalizing a simple table."""
        html = "<table><tr><td>A</td></tr></table>"
        normalized = normalize_html_for_teds(html)

        assert "<table" in normalized
        assert "</table>" in normalized

    def test_ensure_thead(self):
        """Test ensuring thead exists."""
        html = """
        <table>
            <tr><th>Header</th></tr>
            <tr><td>Data</td></tr>
        </table>
        """
        normalized = normalize_html_for_teds(html, ensure_thead=True)

        # Should have thead for header row
        assert "<thead>" in normalized or "<THEAD>" in normalized.upper()

    def test_preserve_existing_thead(self):
        """Test that existing thead is preserved."""
        html = """
        <table>
            <thead><tr><th>Header</th></tr></thead>
            <tbody><tr><td>Data</td></tr></tbody>
        </table>
        """
        normalized = normalize_html_for_teds(html, ensure_thead=True)

        # Should still have thead
        assert "<thead>" in normalized or "<THEAD>" in normalized.upper()


class TestCompareWithTEDS:
    """Test high-level TEDS comparison function."""

    def test_compare_identical_tables(self):
        """Test comparing identical tables."""
        html = "<table><tr><td>A</td></tr></table>"
        score, message = compare_with_teds(html, html)

        assert score == pytest.approx(1.0)
        assert "perfect" in message.lower() or "1.0" in message

    def test_compare_with_normalization(self):
        """Test comparing tables with normalization."""
        html1 = """
        <table>
            <thead><tr><th>A</th></tr></thead>
            <tbody><tr><td>1</td></tr></tbody>
        </table>
        """

        html2 = """
        <table>
            <tr><th>A</th></tr>
            <tr><td>1</td></tr>
        </table>
        """

        score_without, _ = compare_with_teds(html1, html2, normalize=False)
        score_with, _ = compare_with_teds(html1, html2, normalize=True)

        # Normalization should improve or maintain score
        assert score_with >= score_without

    def test_compare_structure_only(self):
        """Test comparing tables in structure-only mode."""
        html1 = "<table><tr><td>A</td><td>B</td></tr></table>"
        html2 = "<table><tr><td>X</td><td>Y</td></tr></table>"

        score, message = compare_with_teds(
            html1, html2,
            structure_only=True,
            normalize=False
        )

        # Same structure should score highly
        assert score >= 0.99


class TestEdgeCases:
    """Test edge cases in TEDS utilities."""

    def test_empty_table(self):
        """Test handling of empty table."""
        html = "<table></table>"
        normalized = normalize_html_for_teds(html)

        assert normalized is not None

    def test_malformed_html(self):
        """Test handling of malformed HTML."""
        html = "<table><tr><td>Unclosed"
        normalized = normalize_html_for_teds(html)

        # Should return something (original or normalized)
        assert normalized is not None

    def test_nested_tables(self):
        """Test handling of nested tables."""
        html = """
        <table>
            <tr>
                <td>
                    <table><tr><td>Nested</td></tr></table>
                </td>
            </tr>
        </table>
        """
        normalized = normalize_html_for_teds(html)

        assert normalized is not None
