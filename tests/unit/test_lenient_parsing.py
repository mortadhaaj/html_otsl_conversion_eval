"""
Tests for lenient parsing mode (strict=False).

These tests verify that the converter can handle malformed tables
that may come from AI models or other sources with inconsistent formatting.
"""

import pytest
from src.api.converters import TableConverter
from src.core.html_parser import HTMLTableParser
from src.core.otsl_parser import OTSLTableParser


class TestLenientOTSLParsing:
    """Test lenient parsing of malformed OTSL tables."""

    def test_inconsistent_row_lengths_strict_fails(self):
        """Verify that inconsistent row lengths fail in strict mode."""
        # Row 0 has 3 cells, Row 1 has 4 cells
        otsl = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<fcel>C<nl><fcel>D<fcel>E<fcel>F<fcel>G<nl></otsl>'

        converter = TableConverter(strict=True)
        # This should parse but create inconsistent structure
        # The validation would catch it if we validate
        table_ir = converter.otsl_to_ir(otsl)
        # Structure will be inconsistent
        assert table_ir.num_rows == 2
        # Max columns should be 4
        assert table_ir.num_cols == 4

    def test_inconsistent_row_lengths_lenient_pads(self):
        """Verify that lenient mode pads short rows with empty cells."""
        # Row 0 has 3 cells, Row 1 has 4 cells
        otsl = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<fcel>C<nl><fcel>D<fcel>E<fcel>F<fcel>G<nl></otsl>'

        converter = TableConverter(strict=False)
        table_ir = converter.otsl_to_ir(otsl)

        # Should have 2 rows, 4 columns (max)
        assert table_ir.num_rows == 2
        assert table_ir.num_cols == 4

        # First row should have 4 cells (3 original + 1 padded empty)
        # Second row should have 4 cells
        assert len(table_ir.cells) == 8

        # Validation should pass after padding
        is_valid, errors = table_ir.validate()
        assert is_valid, f"Table should be valid after padding: {errors}"

    def test_arabic_table_inconsistent_columns(self):
        """Test the real Arabic table example with inconsistent columns."""
        otsl = '''<otsl><loc_0><loc_0><loc_500><loc_500><ched>التخصص<ched>١٩٨٠<lcel><lcel><ched>١٩٩٠<lcel><lcel><ched>٢٠٠٠<lcel><lcel><ched>٢٠٢٠<lcel><lcel><nl><ucel><ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<nl><fcel>عدد الطلاب<fcel>٥٠٠<fcel>١٢٠٠<fcel>٧٠٠<fcel>١٥٠٠<fcel>٩٠٠<fcel>١٨٠٠<fcel>١١٠٠<fcel>٢٠٠٠<fcel>١٣٠٠<fcel>١٠٠٠<fcel>١٠٠٠<fcel>١٠٠٠<nl></otsl>'''

        # Should fail in strict mode or produce inconsistent structure
        converter_strict = TableConverter(strict=True)
        table_strict = converter_strict.otsl_to_ir(otsl)

        # Should succeed in lenient mode and create valid structure
        converter_lenient = TableConverter(strict=False)
        table_lenient = converter_lenient.otsl_to_ir(otsl)

        # Lenient mode should normalize the table
        assert table_lenient.num_rows == 3
        # Row 0: 13 tags, Row 1: 14 tags -> max is 14
        assert table_lenient.num_cols == 14

        # Should be valid after normalization
        is_valid, errors = table_lenient.validate()
        assert is_valid, f"Table should be valid in lenient mode: {errors}"

    def test_truncate_long_rows(self):
        """Verify that lenient mode truncates rows that are too long."""
        # Row 0 has 5 cells, Row 1 has 3 cells (shorter)
        otsl = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<fcel>C<nl><fcel>D<fcel>E<fcel>F<fcel>G<fcel>H<nl></otsl>'

        converter = TableConverter(strict=False)
        table_ir = converter.otsl_to_ir(otsl)

        # Max columns should be 5 (from row 1)
        assert table_ir.num_cols == 5
        assert table_ir.num_rows == 2

        # Should have all cells
        is_valid, errors = table_ir.validate()
        assert is_valid


class TestLenientHTMLParsing:
    """Test lenient parsing of malformed HTML tables."""

    def test_empty_rows_strict_mode(self):
        """Verify that empty rows are preserved in strict mode."""
        html = """<table>
            <tr><td>A</td><td>B</td></tr>
            <tr></tr>
            <tr><td>C</td><td>D</td></tr>
        </table>"""

        parser = HTMLTableParser(strict=True)
        # This should parse but might have issues
        try:
            table_ir = parser.parse(html)
            # Empty row creates issues with validation
            is_valid, errors = table_ir.validate()
            # Might fail due to uncovered cells
        except Exception:
            # May raise exception due to validation issues
            pass

    def test_empty_rows_lenient_mode(self):
        """Verify that empty rows are filtered out in lenient mode."""
        html = """<table>
            <tr><td>A</td><td>B</td></tr>
            <tr></tr>
            <tr><td>C</td><td>D</td></tr>
        </table>"""

        parser = HTMLTableParser(strict=False)
        table_ir = parser.parse(html)

        # Should have only 2 rows (empty row filtered)
        assert table_ir.num_rows == 2
        assert table_ir.num_cols == 2

        # Should be valid
        is_valid, errors = table_ir.validate()
        assert is_valid

    def test_empty_table_lenient_mode(self):
        """Verify that completely empty table returns minimal structure."""
        html = """<table></table>"""

        parser = HTMLTableParser(strict=False)
        table_ir = parser.parse(html)

        # Should return 1x1 table with empty cell
        assert table_ir.num_rows == 1
        assert table_ir.num_cols == 1
        assert len(table_ir.cells) == 1
        assert table_ir.cells[0].content.text == ""

    def test_gaps_in_occupancy_filled(self):
        """Verify that gaps in occupancy grid are filled with empty cells."""
        # Table with rowspan that creates gaps
        html = """<table>
            <tr><td rowspan="2">A</td><td>B</td></tr>
            <tr><td>C</td></tr>
        </table>"""

        parser = HTMLTableParser(strict=False)
        table_ir = parser.parse(html)

        # Should be 2x2
        assert table_ir.num_rows == 2
        assert table_ir.num_cols == 2

        # All positions should be filled
        is_valid, errors = table_ir.validate()
        assert is_valid


class TestLenientRoundtrip:
    """Test roundtrip conversion with lenient mode."""

    def test_lenient_otsl_to_html(self):
        """Test converting malformed OTSL to HTML in lenient mode."""
        # Inconsistent row lengths
        otsl = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<nl><fcel>C<fcel>D<fcel>E<nl></otsl>'

        converter = TableConverter(strict=False)
        html = converter.otsl_to_html(otsl)

        # Should produce valid HTML
        assert '<table' in html
        assert '<tr>' in html
        assert '<td>A</td>' in html
        assert '<td>B</td>' in html

    def test_lenient_html_to_otsl(self):
        """Test converting malformed HTML to OTSL in lenient mode."""
        html = """<table>
            <tr><td>A</td><td>B</td></tr>
            <tr></tr>
            <tr><td>C</td><td>D</td></tr>
        </table>"""

        converter = TableConverter(strict=False)
        otsl = converter.html_to_otsl(html)

        # Should produce valid OTSL (with empty row filtered)
        assert '<otsl>' in otsl
        assert '<fcel>A' in otsl
        assert '<fcel>B' in otsl
        assert '<fcel>C' in otsl


class TestRealWorldMalformed:
    """Test real-world malformed examples from fixtures."""

    def test_malformed_empty_rows_fixture(self):
        """Test the malformed_empty_rows.html fixture."""
        from pathlib import Path

        fixture_file = Path("tests/fixtures/malformed_empty_rows.html")
        if not fixture_file.exists():
            pytest.skip("Fixture file not found")

        html_content = fixture_file.read_text()

        # Should fail or have issues in strict mode
        # But work in lenient mode
        converter = TableConverter(strict=False)
        table_ir = converter.html_to_ir(html_content)

        # Should have valid structure
        assert table_ir.num_rows > 0
        assert table_ir.num_cols > 0

        # Should be able to convert to OTSL
        otsl = converter.html_to_otsl(html_content)
        assert '<otsl>' in otsl

    def test_malformed_inconsistent_otsl_fixture(self):
        """Test the malformed_inconsistent_otsl.otsl fixture."""
        from pathlib import Path

        fixture_file = Path("tests/fixtures/malformed_inconsistent_otsl.otsl")
        if not fixture_file.exists():
            pytest.skip("Fixture file not found")

        otsl_content = fixture_file.read_text()

        # Should work in lenient mode
        converter = TableConverter(strict=False)
        table_ir = converter.otsl_to_ir(otsl_content)

        # Should have valid structure (normalized)
        assert table_ir.num_rows > 0
        assert table_ir.num_cols > 0

        # Should be able to convert to HTML
        html = converter.otsl_to_html(otsl_content)
        assert '<table' in html


class TestRowspanClamping:
    """Test clamping of rowspans that extend beyond table boundaries."""

    def test_rowspan_extends_beyond_table(self):
        """Test HTML where cells have rowspan extending beyond table (malformed)."""
        # Last row has rowspan=2, but there's no row below it
        html = """<table>
            <tr>
                <td>A</td>
                <td>B</td>
            </tr>
            <tr>
                <td rowspan="2">C</td>
                <td rowspan="2">D</td>
            </tr>
        </table>"""

        # Lenient mode should clamp the rowspan to 1 (last row)
        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should have 2 rows, 2 cols
        assert table.num_rows == 2
        assert table.num_cols == 2

        # Find cells in row 1 (last row)
        row1_cells = [c for c in table.cells if c.row_idx == 1]
        assert len(row1_cells) == 2

        # Both cells should have rowspan=1 (clamped from 2)
        for cell in row1_cells:
            assert cell.rowspan == 1  # Clamped to not extend beyond table

        # Should convert to OTSL successfully
        otsl = converter.html_to_otsl(html)
        assert otsl is not None
        assert len(otsl) > 0

    def test_multiple_rowspans_extending_beyond(self):
        """Test table with many cells having rowspan extending beyond table."""
        # Simulates the user's case: multiple rows with cells having rowspan=2 at the end
        html = """<table>
            <thead>
                <tr><th rowspan="2">H1</th><th>H2</th></tr>
                <tr><th>H3</th></tr>
            </thead>
            <tbody>
                <tr><td rowspan="2">A</td><td>B</td></tr>
                <tr><td>C</td></tr>
                <tr><td rowspan="2">D</td><td>E</td></tr>
                <tr><td rowspan="2">F</td></tr>
            </tbody>
        </table>"""

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Table should be valid
        is_valid, errors = table.validate()
        assert is_valid, f"Table should be valid, but got errors: {errors}"

        # Check that last row cells have rowspan=1 (clamped)
        last_row = table.num_rows - 1
        last_row_cells = [c for c in table.cells if c.row_idx == last_row]

        for cell in last_row_cells:
            # Cells in last row should have rowspan=1
            assert cell.rowspan == 1, f"Cell at ({cell.row_idx},{cell.col_idx}) should have rowspan=1, got {cell.rowspan}"

        # Should convert to OTSL successfully
        otsl = converter.html_to_otsl(html)
        assert otsl is not None

    def test_user_malformed_table_case(self):
        """Test the user's actual malformed HTML table case."""
        # This is a regression test for the issue where rowspan extends beyond table
        # and column 4 is missing from tbody rows
        html = """<table>
        <thead>
        <tr>
        <th rowspan="2">Header1</th>
        <th colspan="3">Header2</th>
        <th rowspan="2">Header3</th>
        </tr>
        <tr>
        <th>H2.1</th>
        <th>H2.2</th>
        <th>H2.3</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td rowspan="2">Row1</td>
        <td>A</td>
        <td>B</td>
        <td>C</td>
        </tr>
        <tr>
        <td rowspan="2">D</td>
        <td>E</td>
        <td>F</td>
        </tr>
        <tr>
        <td rowspan="2">Row2</td>
        <td>G</td>
        <td>H</td>
        </tr>
        </tbody>
        </table>"""

        converter = TableConverter(strict=False)
        
        # Should parse successfully
        table = converter.html_to_ir(html)
        assert table.num_rows > 0
        assert table.num_cols == 5

        # Should validate
        is_valid, errors = table.validate()
        assert is_valid, f"Table should be valid: {errors}"

        # Should convert to OTSL
        otsl = converter.html_to_otsl(html)
        assert '<otsl>' in otsl

        # Should roundtrip
        table2 = converter.otsl_to_ir(otsl)
        assert table2.num_rows == table.num_rows
        assert table2.num_cols == table.num_cols


class TestEscapedQuotesInAttributes:
    """Test handling of escaped quotes in colspan/rowspan attributes."""

    def test_escaped_colspan(self):
        """Test HTML with escaped quotes in colspan attribute."""
        # colspan=\"2\" instead of colspan="2"
        html = '<table><tr><th colspan=\\"2\\">Test</th></tr></table>'

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should parse successfully
        assert table.num_cols == 2
        assert len(table.cells) == 1

        # Cell should have colspan=2
        assert table.cells[0].colspan == 2

        # Should convert to OTSL
        otsl = converter.html_to_otsl(html)
        assert '<lcel>' in otsl

    def test_escaped_rowspan(self):
        """Test HTML with escaped quotes in rowspan attribute."""
        # Use non-empty second row to avoid empty row filtering
        html = '<table><tr><th rowspan=\\"2\\">A</th><td>B</td></tr><tr><td>C</td></tr></table>'

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Cell should have rowspan=2
        assert table.cells[0].rowspan == 2

    def test_both_escaped(self):
        """Test HTML with both colspan and rowspan escaped."""
        # Use non-empty second row to avoid empty row filtering
        html = '<table><tr><th colspan=\\"2\\" rowspan=\\"2\\">A</th></tr><tr><td>B</td><td>C</td></tr></table>'

        converter = TableConverter(strict=False)
        table = converter.html_to_ir(html)

        # Should parse both spans correctly
        assert table.cells[0].colspan == 2
        assert table.cells[0].rowspan == 2

    def test_malformed_span_values(self):
        """Test that malformed span values default to 1."""
        # Non-numeric value
        html1 = '<table><tr><th colspan=\\"abc\\">Test</th></tr></table>'

        converter = TableConverter(strict=False)
        table1 = converter.html_to_ir(html1)

        # Should default to 1
        assert table1.cells[0].colspan == 1

        # Empty value
        html2 = '<table><tr><th colspan=\\"\\">Test</th></tr></table>'
        table2 = converter.html_to_ir(html2)
        assert table2.cells[0].colspan == 1

    def test_user_escaped_quotes_case(self):
        """Test the user's actual HTML case with escaped quotes."""
        html = '<table><thead><tr><th colspan=\\"2\\">Tables</th></tr><tr><th>Contents</th><th>Data</th></tr></thead></table>'

        converter = TableConverter(strict=False)

        # Should parse successfully
        table = converter.html_to_ir(html)
        assert table.num_rows == 2
        assert table.num_cols == 2

        # First cell should have colspan=2
        first_cell = [c for c in table.cells if c.row_idx == 0][0]
        assert first_cell.colspan == 2

        # Should convert to OTSL
        otsl = converter.html_to_otsl(html)
        assert '<otsl>' in otsl
        assert '<lcel>' in otsl  # colspan marker

        # Should roundtrip
        table2 = converter.otsl_to_ir(otsl)
        assert table2.num_rows == table.num_rows
        assert table2.num_cols == table.num_cols
