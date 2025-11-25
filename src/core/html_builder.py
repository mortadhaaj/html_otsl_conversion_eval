"""
HTML table builder.

Converts intermediate representation (IR) to HTML tables.
"""

from typing import List, Optional, Set
from lxml import etree
from lxml.html import builder as E
from src.core.table_structure import TableStructure, Cell, CellContent
from src.core.latex_handler import LaTeXHandler


class HTMLTableBuilder:
    """Converts intermediate representation to HTML."""

    def __init__(self, include_borders: bool = True,
                 normalize_for_teds: bool = False,
                 preserve_latex_as_text: bool = True):
        """
        Initialize HTML builder.

        Args:
            include_borders: If True, add border attribute to table
            normalize_for_teds: If True, ensure consistent thead/tbody structure for TEDS
            preserve_latex_as_text: If True, keep LaTeX as plain text (e.g., "$x^2$")
        """
        self.include_borders = include_borders
        self.normalize_for_teds = normalize_for_teds
        self.preserve_latex_as_text = preserve_latex_as_text
        self.latex_handler = LaTeXHandler()

    def build(self, table: TableStructure) -> str:
        """
        Build HTML from intermediate representation.

        Args:
            table: TableStructure to convert

        Returns:
            HTML string

        Raises:
            ValueError: If table structure is invalid
        """
        # Validate table
        is_valid, errors = table.validate()
        if not is_valid:
            raise ValueError(f"Invalid table structure: {'; '.join(errors)}")

        # Build table element
        table_attribs = {}
        if self.include_borders and table.has_border:
            table_attribs['border'] = '1'

        table_elem = etree.Element('table', **table_attribs)

        # Add caption if present
        if table.caption:
            caption_elem = etree.SubElement(table_elem, 'caption')
            caption_elem.text = table.caption.text

        # Organize rows into sections
        thead_rows, tbody_rows = self._organize_rows(table)

        # Build thead if needed
        if thead_rows or self.normalize_for_teds:
            thead_elem = etree.SubElement(table_elem, 'thead')
            rows_to_include = thead_rows if thead_rows else [0]  # Use first row if normalizing
            for row_idx in rows_to_include:
                self._build_row(thead_elem, table, row_idx)

        # Build tbody
        tbody_elem = etree.SubElement(table_elem, 'tbody')
        tbody_start = max(thead_rows) + 1 if thead_rows else (1 if self.normalize_for_teds else 0)
        for row_idx in tbody_rows:
            if row_idx >= tbody_start:  # Skip rows already in thead
                self._build_row(tbody_elem, table, row_idx)

        # Convert to HTML string
        html_str = etree.tostring(table_elem, encoding='unicode', method='html', pretty_print=True)

        return html_str

    def _organize_rows(self, table: TableStructure) -> tuple[List[int], List[int]]:
        """
        Organize rows into thead and tbody sections.

        Returns:
            Tuple of (thead_row_indices, tbody_row_indices)
        """
        thead_rows = sorted(table.column_headers) if table.column_headers else []
        all_rows = list(range(table.num_rows))
        tbody_rows = [r for r in all_rows if r not in thead_rows]

        return thead_rows, tbody_rows

    def _build_row(self, parent_elem, table: TableStructure, row_idx: int):
        """
        Build a table row.

        Args:
            parent_elem: Parent element (thead or tbody)
            table: TableStructure
            row_idx: Row index to build
        """
        tr_elem = etree.SubElement(parent_elem, 'tr')

        # Get cells that originate in this row
        row_cells = [c for c in table.cells if c.row_idx == row_idx]
        row_cells.sort(key=lambda c: c.col_idx)

        # Track which columns have been added
        added_cols: Set[int] = set()

        for cell in row_cells:
            # Skip if this cell's column was already added (shouldn't happen with proper IR)
            if cell.col_idx in added_cols:
                continue

            # Determine cell tag (th or td)
            cell_tag = 'th' if cell.is_header else 'td'

            # Build attributes
            attribs = {}
            if cell.rowspan > 1:
                attribs['rowspan'] = str(cell.rowspan)
            if cell.colspan > 1:
                attribs['colspan'] = str(cell.colspan)

            # Create cell element
            cell_elem = etree.SubElement(tr_elem, cell_tag, **attribs)

            # Set cell content
            if cell.content:
                content_text = self._render_cell_content(cell.content)
                cell_elem.text = content_text

            # Mark columns as added
            for c in range(cell.col_idx, cell.col_idx + cell.colspan):
                added_cols.add(c)

    def _render_cell_content(self, content: CellContent) -> str:
        """
        Render cell content to text.

        Args:
            content: CellContent to render

        Returns:
            Rendered text
        """
        if self.preserve_latex_as_text:
            # Keep LaTeX as plain text
            return content.text
        else:
            # Convert LaTeX to HTML tags
            text = content.text
            for formula in content.latex_formulas:
                html_repr = self.latex_handler.latex_to_html(formula, preserve_as_text=False)
                text = text.replace(formula.original_text, html_repr, 1)
            return text
