"""
TEDS (Tree-Edit-Distance-based Similarity) metric utilities.

TEDS compares table structures by computing tree edit distance on HTML trees.
This module provides utilities for computing TEDS scores and normalizing HTML
for fair comparison.

Installation:
    pip install table-recognition-metric

Note: table-recognition-metric requires Python <3.12. If you're using Python 3.12+,
you may need to use a virtual environment with Python 3.11 or earlier.

Reference:
    https://github.com/ibm-aur-nlp/PubTabNet
    Paper: "Image-based table recognition: data, model, and evaluation"
"""

from typing import Tuple, Optional
import warnings


class TEDSCalculator:
    """Calculator for TEDS metric on HTML tables."""

    def __init__(self, structure_only: bool = False, ignore_nodes: Optional[set] = None):
        """
        Initialize TEDS calculator.

        Args:
            structure_only: If True, only compare table structure (ignore text content)
            ignore_nodes: Set of HTML node names to ignore in comparison

        Raises:
            ImportError: If table-recognition-metric package is not installed
        """
        self.structure_only = structure_only
        self.ignore_nodes = ignore_nodes or set()

        try:
            from table_recognition_metric import TEDS as _TEDS
            self._teds = _TEDS(structure_only=structure_only, ignore_nodes=ignore_nodes)
            self._available = True
        except ImportError:
            warnings.warn(
                "table-recognition-metric package not installed. "
                "TEDS scores will not be computed. "
                "Install with: pip install table-recognition-metric "
                "(requires Python <3.12)"
            )
            self._teds = None
            self._available = False

    def is_available(self) -> bool:
        """Check if TEDS calculator is available."""
        return self._available

    def compute_score(self, pred_html: str, gt_html: str) -> float:
        """
        Compute TEDS score between predicted and ground truth HTML tables.

        Args:
            pred_html: Predicted HTML table string
            gt_html: Ground truth HTML table string

        Returns:
            TEDS score between 0 and 1 (1 = perfect match)

        Raises:
            RuntimeError: If TEDS package is not available
        """
        if not self._available:
            raise RuntimeError(
                "TEDS calculator not available. Install table-recognition-metric package."
            )

        return self._teds.evaluate(pred_html, gt_html)

    def compute_batch_scores(self, pred_htmls: list, gt_htmls: list) -> list:
        """
        Compute TEDS scores for a batch of HTML table pairs.

        Args:
            pred_htmls: List of predicted HTML table strings
            gt_htmls: List of ground truth HTML table strings

        Returns:
            List of TEDS scores

        Raises:
            RuntimeError: If TEDS package is not available
        """
        if not self._available:
            raise RuntimeError(
                "TEDS calculator not available. Install table-recognition-metric package."
            )

        return [self._teds.evaluate(pred, gt) for pred, gt in zip(pred_htmls, gt_htmls)]


def normalize_html_for_teds(html_str: str, ensure_thead: bool = True) -> str:
    """
    Normalize HTML table for TEDS comparison.

    TEDS is sensitive to HTML tree structure. Missing <thead> can change
    the tree depth and affect scores. This function normalizes HTML to
    ensure consistent structure.

    Args:
        html_str: HTML table string
        ensure_thead: If True, ensure table has <thead> section

    Returns:
        Normalized HTML string
    """
    from lxml import html as lxml_html
    from lxml import etree

    try:
        # Parse HTML
        tree = lxml_html.fromstring(html_str)
        table = tree if tree.tag == 'table' else tree.find('.//table')

        if table is None:
            return html_str

        if ensure_thead:
            # Check if thead exists
            thead = table.find('.//thead')

            if thead is None:
                # Create thead from first tr if it contains th elements
                tbody = table.find('.//tbody')
                if tbody is None:
                    # Get all tr elements directly under table
                    rows = table.findall('./tr')
                    if rows:
                        first_row = rows[0]
                        # Check if first row has th elements
                        if first_row.findall('.//th'):
                            # Create thead and move first row into it
                            thead = etree.Element('thead')
                            table.insert(0, thead)
                            table.remove(first_row)
                            thead.append(first_row)

                            # Create tbody for remaining rows
                            if len(rows) > 1:
                                tbody = etree.Element('tbody')
                                table.append(tbody)
                                for row in rows[1:]:
                                    table.remove(row)
                                    tbody.append(row)
                else:
                    # Check if first row in tbody has th elements
                    rows = tbody.findall('./tr')
                    if rows:
                        first_row = rows[0]
                        if first_row.findall('.//th'):
                            # Create thead and move first row from tbody
                            thead = etree.Element('thead')
                            table.insert(0, thead)
                            tbody.remove(first_row)
                            thead.append(first_row)

        # Convert back to string
        return lxml_html.tostring(table, encoding='unicode')

    except Exception as e:
        warnings.warn(f"Failed to normalize HTML: {e}. Returning original HTML.")
        return html_str


def compare_with_teds(html1: str, html2: str,
                      structure_only: bool = False,
                      normalize: bool = True) -> Tuple[float, str]:
    """
    Compare two HTML tables using TEDS metric.

    Args:
        html1: First HTML table string
        html2: Second HTML table string
        structure_only: If True, only compare structure (ignore content)
        normalize: If True, normalize HTML before comparison

    Returns:
        Tuple of (teds_score, message)
        - teds_score: TEDS score between 0 and 1
        - message: Description of the result
    """
    calculator = TEDSCalculator(structure_only=structure_only)

    if not calculator.is_available():
        return (
            -1.0,
            "TEDS calculator not available. Install table-recognition-metric package."
        )

    try:
        if normalize:
            html1 = normalize_html_for_teds(html1)
            html2 = normalize_html_for_teds(html2)

        score = calculator.compute_score(html1, html2)

        if score >= 0.99:
            message = f"Perfect match (TEDS = {score:.4f})"
        elif score >= 0.90:
            message = f"Very good match (TEDS = {score:.4f})"
        elif score >= 0.75:
            message = f"Good match (TEDS = {score:.4f})"
        elif score >= 0.50:
            message = f"Moderate match (TEDS = {score:.4f})"
        else:
            message = f"Poor match (TEDS = {score:.4f})"

        return score, message

    except Exception as e:
        return -1.0, f"Error computing TEDS: {e}"


# Example usage
if __name__ == "__main__":
    html1 = """
    <table>
        <thead><tr><th>A</th><th>B</th></tr></thead>
        <tbody><tr><td>1</td><td>2</td></tr></tbody>
    </table>
    """

    html2 = """
    <table>
        <tr><th>A</th><th>B</th></tr>
        <tr><td>1</td><td>2</td></tr>
    </table>
    """

    # Without normalization, these may have different TEDS scores
    # due to thead vs no thead difference
    score, message = compare_with_teds(html1, html2, normalize=False)
    print(f"Without normalization: {message}")

    # With normalization, they should match better
    score, message = compare_with_teds(html1, html2, normalize=True)
    print(f"With normalization: {message}")
