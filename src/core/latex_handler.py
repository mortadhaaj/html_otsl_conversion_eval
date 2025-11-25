"""
LaTeX formula detection and preservation handler.

Handles detection, extraction, and reconstruction of LaTeX formulas
in table cell content, supporting both LaTeX delimiters and HTML math tags.
"""

import re
from typing import List, Tuple, Optional
from src.core.table_structure import LaTeXFormula


class LaTeXHandler:
    """Handles detection and preservation of LaTeX formulas."""

    # Regex patterns for LaTeX detection
    DISPLAY_PATTERN = r'\$\$([^\$]+)\$\$'  # $$formula$$
    INLINE_PATTERN = r'\$([^\$]+)\$'  # $formula$
    LATEX_COMMAND_PATTERN = r'\\[a-zA-Z]+(?:\{[^}]*\}|\[[^\]]*\])*'  # \command{...} or \command[...]

    # HTML math tag patterns
    MATH_TAG_PATTERN = r'<(math|formula|equation)>(.*?)</\1>'
    SUP_SUB_PATTERN = r'<(sup|sub)>(.*?)</\1>'

    def __init__(self):
        """Initialize LaTeX handler with compiled patterns."""
        self.display_regex = re.compile(self.DISPLAY_PATTERN)
        self.inline_regex = re.compile(self.INLINE_PATTERN)
        self.latex_command_regex = re.compile(self.LATEX_COMMAND_PATTERN)
        self.math_tag_regex = re.compile(self.MATH_TAG_PATTERN, re.IGNORECASE)
        self.sup_sub_regex = re.compile(self.SUP_SUB_PATTERN, re.IGNORECASE)

    def extract_formulas(self, text: str) -> List[LaTeXFormula]:
        """
        Extract all LaTeX formulas from text.

        Detection order (to avoid conflicts):
        1. Display math: $$...$$
        2. Inline math: $...$
        3. HTML math tags: <math>, <formula>, <equation>
        4. Superscript/subscript: <sup>, <sub>

        Args:
            text: Text content to search

        Returns:
            List of LaTeXFormula objects with positions
        """
        formulas = []

        # 1. Extract display math ($$...$$) first to avoid conflicts with inline
        for match in self.display_regex.finditer(text):
            formula_content = match.group(1)
            # Validate it contains LaTeX commands
            if self._looks_like_latex(formula_content):
                formulas.append(LaTeXFormula(
                    original_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    formula_type='display'
                ))

        # 2. Extract inline math ($...$)
        for match in self.inline_regex.finditer(text):
            # Skip if already part of display math
            if any(f.start_pos <= match.start() < f.end_pos for f in formulas):
                continue

            formula_content = match.group(1)
            # Validate it looks like LaTeX (not just "$5" or "$10,000")
            if self._looks_like_latex(formula_content):
                formulas.append(LaTeXFormula(
                    original_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    formula_type='inline'
                ))

        # 3. Extract HTML math tags
        for match in self.math_tag_regex.finditer(text):
            # Skip if overlaps with existing formulas
            if any(f.start_pos <= match.start() < f.end_pos for f in formulas):
                continue

            formulas.append(LaTeXFormula(
                original_text=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                formula_type='tag'
            ))

        # 4. Extract sup/sub tags (convert to LaTeX)
        for match in self.sup_sub_regex.finditer(text):
            # Skip if overlaps with existing formulas
            if any(f.start_pos <= match.start() < f.end_pos for f in formulas):
                continue

            tag_type = match.group(1).lower()
            content = match.group(2)
            # Convert to LaTeX notation
            latex_repr = f"^{{{content}}}" if tag_type == 'sup' else f"_{{{content}}}"

            formulas.append(LaTeXFormula(
                original_text=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                formula_type=f'tag_{tag_type}'
            ))

        # Sort by position
        formulas.sort(key=lambda f: f.start_pos)

        return formulas

    def _looks_like_latex(self, text: str) -> bool:
        """
        Check if text looks like LaTeX formula (not just numbers/currency).

        Args:
            text: Text to check

        Returns:
            True if likely LaTeX, False if likely false positive
        """
        # Check for LaTeX commands
        if self.latex_command_regex.search(text):
            return True

        # Check for common LaTeX symbols
        latex_symbols = ['^', '_', '{', '}', '\\', '=', '+', '-', '*', '/', '(', ')']
        has_symbols = any(sym in text for sym in latex_symbols[:-4])  # Exclude parentheses

        # Check if it's likely currency (just numbers, commas, dots)
        is_currency = re.match(r'^[\d,.\s]+$', text.strip())

        return has_symbols and not is_currency

    def html_to_latex(self, html_text: str) -> str:
        """
        Convert HTML math tags to LaTeX representation.

        Conversions:
        - <sup>2</sup> → ^{2}
        - <sub>i</sub> → _{i}
        - <math>...</math> → Keep content as is

        Args:
            html_text: HTML text with math tags

        Returns:
            Text with HTML tags converted to LaTeX
        """
        result = html_text

        # Convert <sup> tags
        result = re.sub(
            r'<sup>(.*?)</sup>',
            lambda m: f'^{{{m.group(1)}}}',
            result,
            flags=re.IGNORECASE
        )

        # Convert <sub> tags
        result = re.sub(
            r'<sub>(.*?)</sub>',
            lambda m: f'_{{{m.group(1)}}}',
            result,
            flags=re.IGNORECASE
        )

        # For <math> tags, extract content (assume it's already LaTeX)
        result = re.sub(
            r'<(math|formula|equation)>(.*?)</\1>',
            lambda m: f'${m.group(2)}$',
            result,
            flags=re.IGNORECASE
        )

        return result

    def latex_to_html(self, formula: LaTeXFormula, preserve_as_text: bool = True) -> str:
        """
        Convert LaTeX formula to HTML representation.

        Args:
            formula: LaTeX formula to convert
            preserve_as_text: If True, keep as plain text (e.g., "$x^2$")
                             If False, convert to HTML tags

        Returns:
            HTML representation of formula
        """
        if preserve_as_text:
            # Keep as plain text
            return formula.original_text

        # Convert to HTML tags
        if formula.formula_type.startswith('tag'):
            # Already HTML, return as is
            return formula.original_text

        # For LaTeX formulas, convert basic patterns to HTML
        text = formula.original_text

        # Remove $ delimiters
        if text.startswith('$$'):
            text = text[2:-2]
        elif text.startswith('$'):
            text = text[1:-1]

        # Convert ^{...} to <sup>...</sup>
        text = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', text)
        text = re.sub(r'\^(.)', r'<sup>\1</sup>', text)  # ^x format

        # Convert _{...} to <sub>...</sub>
        text = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', text)
        text = re.sub(r'_(.)', r'<sub>\1</sub>', text)  # _x format

        return text

    def validate_latex(self, formula_str: str) -> Tuple[bool, Optional[str]]:
        """
        Basic validation of LaTeX syntax.

        Args:
            formula_str: LaTeX formula string

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for balanced braces
        brace_count = 0
        for char in formula_str:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            if brace_count < 0:
                return False, "Unbalanced braces: too many closing braces"

        if brace_count > 0:
            return False, "Unbalanced braces: too many opening braces"

        # Check for balanced dollar signs (if not already stripped)
        if formula_str.count('$') % 2 != 0:
            return False, "Unbalanced dollar signs"

        return True, None

    def preserve_formulas_in_text(self, text: str) -> Tuple[str, List[LaTeXFormula]]:
        """
        Extract formulas and return text with placeholders.

        Useful for processing text while preserving formula positions.

        Args:
            text: Text with LaTeX formulas

        Returns:
            Tuple of (text_with_placeholders, formulas)
        """
        formulas = self.extract_formulas(text)

        if not formulas:
            return text, []

        # Replace formulas with placeholders
        result = text
        offset = 0

        for i, formula in enumerate(formulas):
            placeholder = f"__LATEX_{i}__"
            start = formula.start_pos + offset
            end = formula.end_pos + offset
            result = result[:start] + placeholder + result[end:]
            offset += len(placeholder) - (end - start)

        return result, formulas

    def restore_formulas_in_text(self, text_with_placeholders: str,
                                 formulas: List[LaTeXFormula]) -> str:
        """
        Restore formulas from placeholders.

        Args:
            text_with_placeholders: Text with __LATEX_N__ placeholders
            formulas: List of formulas to restore

        Returns:
            Text with formulas restored
        """
        result = text_with_placeholders

        for i, formula in enumerate(formulas):
            placeholder = f"__LATEX_{i}__"
            result = result.replace(placeholder, formula.original_text, 1)

        return result
