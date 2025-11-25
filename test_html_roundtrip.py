"""
Quick test of HTML → IR → HTML roundtrip.
"""

from src.core.html_parser import HTMLTableParser
from src.core.html_builder import HTMLTableBuilder

def test_simple_table():
    """Test simple 2x2 table."""
    print("\n=== Testing Simple 2x2 Table ===")

    html_input = """<table border="1">
  <tr>
    <td>A</td>
    <td>B</td>
  </tr>
  <tr>
    <td>C</td>
    <td>D</td>
  </tr>
</table>"""

    # Parse
    parser = HTMLTableParser()
    table_ir = parser.parse(html_input)

    print(f"Parsed: {table_ir}")
    print(f"Cells: {len(table_ir.cells)}")
    for cell in table_ir.cells:
        print(f"  Cell ({cell.row_idx}, {cell.col_idx}): '{cell.content.text}'")

    # Build
    builder = HTMLTableBuilder()
    html_output = builder.build(table_ir)

    print(f"\nOutput HTML:\n{html_output}")

    # Validate structure
    is_valid, errors = table_ir.validate()
    print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    return table_ir, html_output

def test_vaccination_table():
    """Test vaccination phases table."""
    print("\n=== Testing Vaccination Phases Table ===")

    html_input = """<table border="1">
  <thead>
    <tr>
      <th>Phase</th>
      <th>Groups recommended for vaccination</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1a</td>
      <td>Health care personnel Long-term care facility residents Frontline essential workers</td>
    </tr>
    <tr>
      <td>1b</td>
      <td>Persons age 65 years and older</td>
    </tr>
    <tr>
      <td>1c</td>
      <td>Persons aged 16-64 years with high-risk conditions Essential workers not recommended in Phase 1b</td>
    </tr>
    <tr>
      <td>2</td>
      <td>All people aged 16 years and older not in Phase 1, who are recommended for vaccination</td>
    </tr>
  </tbody>
</table>"""

    # Parse
    parser = HTMLTableParser()
    table_ir = parser.parse(html_input)

    print(f"Parsed: {table_ir}")
    print(f"Column headers: {table_ir.column_headers}")
    print(f"Cells: {len(table_ir.cells)}")

    # Build
    builder = HTMLTableBuilder()
    html_output = builder.build(table_ir)

    print(f"\nOutput HTML:\n{html_output}")

    # Validate
    is_valid, errors = table_ir.validate()
    print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    return table_ir, html_output

def test_latex_table():
    """Test table with LaTeX formulas."""
    print("\n=== Testing LaTeX Formula Table ===")

    html_input = """<table border="1">
  <thead>
    <tr>
      <th>Formula</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>$x^2 + y^2 = z^2$</td>
      <td>Pythagorean theorem</td>
    </tr>
    <tr>
      <td>$E = mc^2$</td>
      <td>Einstein's mass-energy equivalence</td>
    </tr>
  </tbody>
</table>"""

    # Parse
    parser = HTMLTableParser(preserve_latex=True)
    table_ir = parser.parse(html_input)

    print(f"Parsed: {table_ir}")

    # Check LaTeX detection
    for cell in table_ir.cells:
        if cell.content and cell.content.latex_formulas:
            print(f"Cell ({cell.row_idx}, {cell.col_idx}) has {len(cell.content.latex_formulas)} formula(s):")
            for formula in cell.content.latex_formulas:
                print(f"  - {formula.original_text} (type: {formula.formula_type})")

    # Build
    builder = HTMLTableBuilder(preserve_latex_as_text=True)
    html_output = builder.build(table_ir)

    print(f"\nOutput HTML:\n{html_output}")

    # Validate
    is_valid, errors = table_ir.validate()
    print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")

    return table_ir, html_output

if __name__ == '__main__':
    try:
        test_simple_table()
        test_vaccination_table()
        test_latex_table()
        print("\n✓ All tests completed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
