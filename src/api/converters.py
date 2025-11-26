"""
High-level API for table conversions.

Provides simple interface for bidirectional HTML ↔ OTSL conversion.
"""

from typing import Tuple, Optional
from src.core.html_parser import HTMLTableParser
from src.core.html_builder import HTMLTableBuilder
from src.core.otsl_parser import OTSLTableParser
from src.core.otsl_builder import OTSLTableBuilder
from src.core.table_structure import TableStructure


class TableConverter:
    """High-level API for table conversions."""

    def __init__(self, preserve_latex: bool = True):
        """
        Initialize table converter.

        Args:
            preserve_latex: If True, detect and preserve LaTeX formulas
        """
        self.preserve_latex = preserve_latex

    def html_to_otsl(self, html: str, include_location: bool = True) -> str:
        """
        Convert HTML table to OTSL format.

        Args:
            html: HTML string containing a table
            include_location: If True, include random location coordinates in OTSL

        Returns:
            OTSL string

        Example:
            >>> converter = TableConverter()
            >>> html = '<table><tr><td>A</td><td>B</td></tr></table>'
            >>> otsl = converter.html_to_otsl(html)
        """
        parser = HTMLTableParser(preserve_latex=self.preserve_latex)
        table_ir = parser.parse(html)

        builder = OTSLTableBuilder(include_location=include_location)
        otsl = builder.build(table_ir)

        return otsl

    def otsl_to_html(self, otsl: str, include_borders: bool = True,
                    normalize_for_teds: bool = False) -> str:
        """
        Convert OTSL table to HTML format.

        Args:
            otsl: OTSL string
            include_borders: If True, add border="1" to table
            normalize_for_teds: If True, ensure consistent thead/tbody structure

        Returns:
            HTML string

        Example:
            >>> converter = TableConverter()
            >>> otsl = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<nl></otsl>'
            >>> html = converter.otsl_to_html(otsl)
        """
        parser = OTSLTableParser(preserve_latex=self.preserve_latex)
        table_ir = parser.parse(otsl)

        builder = HTMLTableBuilder(
            include_borders=include_borders,
            normalize_for_teds=normalize_for_teds
        )
        html = builder.build(table_ir)

        return html

    def html_to_ir(self, html: str) -> TableStructure:
        """
        Convert HTML table to intermediate representation.

        Args:
            html: HTML string containing a table

        Returns:
            TableStructure object

        Example:
            >>> converter = TableConverter()
            >>> table_ir = converter.html_to_ir('<table>...</table>')
            >>> print(f"Table: {table_ir.num_rows}x{table_ir.num_cols}")
        """
        parser = HTMLTableParser(preserve_latex=self.preserve_latex)
        return parser.parse(html)

    def otsl_to_ir(self, otsl: str) -> TableStructure:
        """
        Convert OTSL table to intermediate representation.

        Args:
            otsl: OTSL string

        Returns:
            TableStructure object

        Example:
            >>> converter = TableConverter()
            >>> table_ir = converter.otsl_to_ir('<otsl>...</otsl>')
        """
        parser = OTSLTableParser(preserve_latex=self.preserve_latex)
        return parser.parse(otsl)

    def ir_to_html(self, table_ir: TableStructure, include_borders: bool = True,
                   normalize_for_teds: bool = False) -> str:
        """
        Convert intermediate representation to HTML.

        Args:
            table_ir: TableStructure object
            include_borders: If True, add border="1" to table
            normalize_for_teds: If True, ensure consistent thead/tbody structure

        Returns:
            HTML string
        """
        builder = HTMLTableBuilder(
            include_borders=include_borders,
            normalize_for_teds=normalize_for_teds
        )
        return builder.build(table_ir)

    def ir_to_otsl(self, table_ir: TableStructure, include_location: bool = True) -> str:
        """
        Convert intermediate representation to OTSL.

        Args:
            table_ir: TableStructure object
            include_location: If True, include random location coordinates

        Returns:
            OTSL string
        """
        builder = OTSLTableBuilder(include_location=include_location)
        return builder.build(table_ir)

    def roundtrip_html(self, html: str) -> Tuple[str, str, str]:
        """
        HTML → OTSL → HTML roundtrip.

        Args:
            html: Original HTML string

        Returns:
            Tuple of (otsl, reconstructed_html, intermediate_ir_summary)

        Example:
            >>> converter = TableConverter()
            >>> otsl, html_out, summary = converter.roundtrip_html(html_in)
            >>> print(f"Roundtrip: {summary}")
        """
        # Parse HTML to IR
        table_ir = self.html_to_ir(html)

        # Convert IR to OTSL
        otsl = self.ir_to_otsl(table_ir)

        # Convert OTSL back to HTML
        html_reconstructed = self.otsl_to_html(otsl)

        # Create summary
        summary = f"TableStructure({table_ir.num_rows}x{table_ir.num_cols}, {len(table_ir.cells)} cells)"

        return otsl, html_reconstructed, summary

    def roundtrip_otsl(self, otsl: str) -> Tuple[str, str, str]:
        """
        OTSL → HTML → OTSL roundtrip.

        Args:
            otsl: Original OTSL string

        Returns:
            Tuple of (html, reconstructed_otsl, intermediate_ir_summary)

        Example:
            >>> converter = TableConverter()
            >>> html, otsl_out, summary = converter.roundtrip_otsl(otsl_in)
        """
        # Parse OTSL to IR
        table_ir = self.otsl_to_ir(otsl)

        # Convert IR to HTML
        html = self.ir_to_html(table_ir)

        # Convert HTML back to OTSL
        otsl_reconstructed = self.html_to_otsl(html)

        # Create summary
        summary = f"TableStructure({table_ir.num_rows}x{table_ir.num_cols}, {len(table_ir.cells)} cells)"

        return html, otsl_reconstructed, summary

    def validate_conversion(self, html: str, otsl: str) -> Tuple[bool, str]:
        """
        Validate that HTML and OTSL represent the same table structure.

        Args:
            html: HTML string
            otsl: OTSL string

        Returns:
            Tuple of (is_valid, message)

        Example:
            >>> converter = TableConverter()
            >>> is_valid, msg = converter.validate_conversion(html, otsl)
            >>> if is_valid:
            >>>     print("Conversion is valid!")
        """
        try:
            # Parse both to IR
            html_ir = self.html_to_ir(html)
            otsl_ir = self.otsl_to_ir(otsl)

            # Compare structures
            if html_ir.num_rows != otsl_ir.num_rows:
                return False, f"Row count mismatch: HTML={html_ir.num_rows}, OTSL={otsl_ir.num_rows}"

            if html_ir.num_cols != otsl_ir.num_cols:
                return False, f"Column count mismatch: HTML={html_ir.num_cols}, OTSL={otsl_ir.num_cols}"

            if len(html_ir.cells) != len(otsl_ir.cells):
                return False, f"Cell count mismatch: HTML={len(html_ir.cells)}, OTSL={len(otsl_ir.cells)}"

            # Compare cell contents
            for html_cell, otsl_cell in zip(html_ir.cells, otsl_ir.cells):
                if html_cell.row_idx != otsl_cell.row_idx or html_cell.col_idx != otsl_cell.col_idx:
                    return False, f"Cell position mismatch at ({html_cell.row_idx}, {html_cell.col_idx})"

                if html_cell.rowspan != otsl_cell.rowspan or html_cell.colspan != otsl_cell.colspan:
                    return False, f"Cell span mismatch at ({html_cell.row_idx}, {html_cell.col_idx})"

                # Compare content (allowing for whitespace differences)
                html_text = html_cell.content.text.strip() if html_cell.content else ""
                otsl_text = otsl_cell.content.text.strip() if otsl_cell.content else ""
                if html_text != otsl_text:
                    return False, f"Content mismatch at ({html_cell.row_idx}, {html_cell.col_idx}): '{html_text}' != '{otsl_text}'"

            return True, "Conversion is valid - structures match"

        except Exception as e:
            return False, f"Validation error: {str(e)}"
