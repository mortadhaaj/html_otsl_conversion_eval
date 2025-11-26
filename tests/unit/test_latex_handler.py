"""
Unit tests for LaTeX formula handling.
"""

import pytest
from src.core.latex_handler import LaTeXHandler, LaTeXFormula


class TestLaTeXDetection:
    """Test LaTeX formula detection."""

    def test_detect_inline_formula(self):
        """Test detection of inline LaTeX formulas."""
        handler = LaTeXHandler()
        text = "The formula $x^2 + y^2 = z^2$ is famous."
        formulas = handler.extract_formulas(text)

        assert len(formulas) == 1
        assert formulas[0].original_text == "$x^2 + y^2 = z^2$"
        assert formulas[0].formula_type == "inline"

    def test_detect_display_formula(self):
        """Test detection of display LaTeX formulas."""
        handler = LaTeXHandler()
        text = "The integral: $$\\int_0^\\infty e^{-x^2} dx$$"
        formulas = handler.extract_formulas(text)

        assert len(formulas) == 1
        assert formulas[0].formula_type == "display"

    def test_detect_multiple_formulas(self):
        """Test detection of multiple formulas in text."""
        handler = LaTeXHandler()
        text = "Inline $a + b$ and display $$c = d$$ formulas."
        formulas = handler.extract_formulas(text)

        assert len(formulas) == 2
        assert formulas[0].formula_type == "inline"
        assert formulas[1].formula_type == "display"

    def test_no_false_positives(self):
        """Test that dollar signs in text don't create false positives."""
        handler = LaTeXHandler()
        text = "The price is $5 or $10."
        formulas = handler.extract_formulas(text)

        # Should not detect these as formulas
        assert len(formulas) == 0

    def test_complex_latex(self):
        """Test complex LaTeX with nested braces."""
        handler = LaTeXHandler()
        text = r"$$\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$"
        formulas = handler.extract_formulas(text)

        assert len(formulas) == 1
        assert "frac" in formulas[0].original_text
        assert "sqrt" in formulas[0].original_text


class TestLaTeXConversion:
    """Test LaTeX to HTML conversion."""

    def test_inline_to_html(self):
        """Test converting inline LaTeX to HTML."""
        handler = LaTeXHandler()
        formula = LaTeXFormula(original_text="$x^2$", formula_type="inline", start_pos=0, end_pos=5)
        html = handler.latex_to_html(formula)

        assert html == "$x^2$"

    def test_display_to_html(self):
        """Test converting display LaTeX to HTML."""
        handler = LaTeXHandler()
        formula = LaTeXFormula(original_text="$$E = mc^2$$", formula_type="display", start_pos=0, end_pos=13)
        html = handler.latex_to_html(formula)

        assert html == "$$E = mc^2$$"

    def test_html_to_latex(self):
        """Test extracting LaTeX from HTML."""
        handler = LaTeXHandler()
        text = "Formula: $x^2$ and $$y^2$$"
        formulas = handler.extract_formulas(text)

        assert len(formulas) == 2
        assert "$x^2$" in formulas[0].original_text
        assert "$$y^2$$" in formulas[1].original_text


class TestEdgeCases:
    """Test edge cases in LaTeX handling."""

    def test_empty_string(self):
        """Test handling of empty string."""
        handler = LaTeXHandler()
        formulas = handler.extract_formulas("")

        assert formulas == []

    def test_only_dollar_signs(self):
        """Test string with only dollar signs."""
        handler = LaTeXHandler()
        formulas = handler.extract_formulas("$$")

        # Empty formula - should not be detected
        assert len(formulas) == 0

    def test_unclosed_formula(self):
        """Test handling of unclosed formula."""
        handler = LaTeXHandler()
        text = "Incomplete $x^2"
        formulas = handler.extract_formulas(text)

        # Should not detect incomplete formulas
        assert len(formulas) == 0

    def test_nested_dollar_signs(self):
        """Test handling of nested dollar signs."""
        handler = LaTeXHandler()
        text = "$a + $b$ + c$"
        formulas = handler.extract_formulas(text)

        # Should handle nested $ signs gracefully
        assert len(formulas) >= 1

    def test_unicode_in_formula(self):
        """Test LaTeX with unicode characters."""
        handler = LaTeXHandler()
        text = "$\\alpha + \\beta = \\gamma$"
        formulas = handler.extract_formulas(text)

        assert len(formulas) == 1
        assert "alpha" in formulas[0].original_text
        assert "beta" in formulas[0].original_text
