"""
Comprehensive test of bidirectional HTML ↔ OTSL conversion.
"""

import os
from pathlib import Path
from src.api.converters import TableConverter


def test_simple_otsl_parsing():
    """Test parsing simple OTSL."""
    print("\n=== Test 1: Simple OTSL Parsing ===")

    otsl_input = '<otsl><loc_150><loc_280><loc_320><loc_360><fcel>A<fcel>B<nl><fcel>C<fcel>D<nl></otsl>'

    converter = TableConverter()
    table_ir = converter.otsl_to_ir(otsl_input)

    print(f"Parsed: {table_ir}")
    print(f"Dimensions: {table_ir.num_rows}x{table_ir.num_cols}")
    print(f"Cells: {len(table_ir.cells)}")

    for cell in table_ir.cells:
        print(f"  Cell ({cell.row_idx}, {cell.col_idx}): '{cell.content.text}'")

    # Validate
    is_valid, errors = table_ir.validate()
    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    return table_ir


def test_otsl_to_html():
    """Test OTSL → HTML conversion."""
    print("\n=== Test 2: OTSL → HTML ===")

    otsl_input = '<otsl><loc_70><loc_180><loc_560><loc_390><ched>Formula<ched>Description<nl><fcel>$x^2 + y^2 = z^2$<fcel>Pythagorean theorem<nl></otsl>'

    converter = TableConverter()
    html_output = converter.otsl_to_html(otsl_input)

    print(f"Input OTSL:\n{otsl_input}")
    print(f"\nOutput HTML:\n{html_output}")

    return html_output


def test_html_to_otsl():
    """Test HTML → OTSL conversion."""
    print("\n=== Test 3: HTML → OTSL ===")

    html_input = """<table border="1">
  <thead>
    <tr>
      <th>Name</th>
      <th>Age</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>John</td>
      <td>25</td>
    </tr>
  </tbody>
</table>"""

    converter = TableConverter()
    otsl_output = converter.html_to_otsl(html_input)

    print(f"Input HTML:\n{html_input}")
    print(f"\nOutput OTSL:\n{otsl_output}")

    return otsl_output


def test_roundtrip_html():
    """Test HTML → OTSL → HTML roundtrip."""
    print("\n=== Test 4: HTML Roundtrip ===")

    html_input = """<table border="1">
  <caption>Test Table</caption>
  <tr>
    <td>A</td>
    <td>B</td>
  </tr>
  <tr>
    <td>C</td>
    <td>D</td>
  </tr>
</table>"""

    converter = TableConverter()
    otsl, html_output, summary = converter.roundtrip_html(html_input)

    print(f"Original HTML:\n{html_input}")
    print(f"\nIntermediate OTSL:\n{otsl}")
    print(f"\nReconstructed HTML:\n{html_output}")
    print(f"\nSummary: {summary}")

    return html_output


def test_roundtrip_otsl():
    """Test OTSL → HTML → OTSL roundtrip."""
    print("\n=== Test 5: OTSL Roundtrip ===")

    otsl_input = '<otsl><caption>Sample</caption><loc_100><loc_200><loc_400><loc_300><ched>X<ched>Y<nl><fcel>1<fcel>2<nl></otsl>'

    converter = TableConverter()
    html, otsl_output, summary = converter.roundtrip_otsl(otsl_input)

    print(f"Original OTSL:\n{otsl_input}")
    print(f"\nIntermediate HTML:\n{html}")
    print(f"\nReconstructed OTSL:\n{otsl_output}")
    print(f"\nSummary: {summary}")

    return otsl_output


def test_fixture_files():
    """Test all fixture files."""
    print("\n=== Test 6: Fixture Files ===")

    fixtures_dir = Path("tests/fixtures")
    html_files = sorted(fixtures_dir.glob("*.html"))

    converter = TableConverter()
    results = []

    for html_file in html_files:
        otsl_file = html_file.with_suffix('.otsl')

        if not otsl_file.exists():
            print(f"⚠ Skipping {html_file.name} - no matching OTSL file")
            continue

        print(f"\nTesting: {html_file.name}")

        # Read files
        html_content = html_file.read_text()
        otsl_content = otsl_file.read_text()

        try:
            # Parse both
            html_ir = converter.html_to_ir(html_content)
            otsl_ir = converter.otsl_to_ir(otsl_content)

            print(f"  HTML IR: {html_ir}")
            print(f"  OTSL IR: {otsl_ir}")

            # Validate conversion
            is_valid, msg = converter.validate_conversion(html_content, otsl_content)
            status = "✓ PASS" if is_valid else "✗ FAIL"
            print(f"  {status}: {msg}")

            results.append({
                'file': html_file.name,
                'valid': is_valid,
                'message': msg
            })

        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            results.append({
                'file': html_file.name,
                'valid': False,
                'message': f"Error: {str(e)}"
            })

    # Summary
    print(f"\n=== Fixture Test Summary ===")
    passed = sum(1 for r in results if r['valid'])
    total = len(results)
    print(f"Passed: {passed}/{total}")

    for result in results:
        status = "✓" if result['valid'] else "✗"
        print(f"  {status} {result['file']}")

    return results


def test_latex_preservation():
    """Test LaTeX formula preservation."""
    print("\n=== Test 7: LaTeX Preservation ===")

    html_input = """<table border="1">
  <tr>
    <td>$E = mc^2$</td>
    <td>Einstein's equation</td>
  </tr>
  <tr>
    <td>$$\\int_0^\\infty e^{-x^2} dx$$</td>
    <td>Gaussian integral</td>
  </tr>
</table>"""

    converter = TableConverter()

    # HTML → IR
    table_ir = converter.html_to_ir(html_input)

    print("LaTeX formulas detected:")
    for cell in table_ir.cells:
        if cell.content and cell.content.latex_formulas:
            print(f"  Cell ({cell.row_idx}, {cell.col_idx}):")
            for formula in cell.content.latex_formulas:
                print(f"    - {formula.original_text} (type: {formula.formula_type})")

    # Full roundtrip
    otsl, html_output, summary = converter.roundtrip_html(html_input)

    print(f"\nOTSL:\n{otsl}")
    print(f"\nReconstructed HTML:\n{html_output}")

    # Check if LaTeX is preserved
    if '$E = mc^2$' in html_output and '\\int_0^\\infty' in html_output:
        print("\n✓ LaTeX formulas preserved in roundtrip!")
    else:
        print("\n✗ LaTeX formulas NOT preserved!")

    return html_output


def test_complex_spanning():
    """Test complex table with rowspan and colspan."""
    print("\n=== Test 8: Complex Spanning ===")

    # Read complex spanning fixture
    html_file = Path("tests/fixtures/complex_merging_thead.html")
    otsl_file = Path("tests/fixtures/complex_merging_thead.otsl")

    if not html_file.exists() or not otsl_file.exists():
        print("Fixture files not found, skipping test")
        return

    html_content = html_file.read_text()
    otsl_content = otsl_file.read_text()

    converter = TableConverter()

    # Parse HTML
    html_ir = converter.html_to_ir(html_content)
    print(f"HTML IR: {html_ir}")
    print(f"Column headers: {html_ir.column_headers}")

    # Check spanning cells
    for cell in html_ir.cells:
        if cell.rowspan > 1 or cell.colspan > 1:
            print(f"  Spanning cell at ({cell.row_idx}, {cell.col_idx}): rowspan={cell.rowspan}, colspan={cell.colspan}")

    # Parse OTSL
    otsl_ir = converter.otsl_to_ir(otsl_content)
    print(f"\nOTSL IR: {otsl_ir}")

    # Validate
    is_valid, msg = converter.validate_conversion(html_content, otsl_content)
    print(f"\nValidation: {'✓ PASS' if is_valid else '✗ FAIL'} - {msg}")

    return is_valid


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("BIDIRECTIONAL HTML ↔ OTSL CONVERSION TESTS")
        print("=" * 60)

        test_simple_otsl_parsing()
        test_otsl_to_html()
        test_html_to_otsl()
        test_roundtrip_html()
        test_roundtrip_otsl()
        test_latex_preservation()
        test_complex_spanning()
        test_fixture_files()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS COMPLETED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
