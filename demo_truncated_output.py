"""
Demonstration of handling truncated AI output.

Shows how to parse, fix, and evaluate truncated HTML/OTSL
that occurs when AI models hit maximum token limits.
"""

from src.api.converters import TableConverter
from src.utils.truncation_utils import (
    detect_truncation,
    fix_truncated_output,
    auto_close_html,
    auto_close_otsl
)


def demo_missing_closing_tag():
    """Demo: HTML missing </table> tag."""
    print("=" * 60)
    print("DEMO 1: Missing Closing </table> Tag")
    print("=" * 60)

    truncated_html = """<table>
  <tr>
    <td>Department</td>
    <td>Value</td>
  </tr>
  <tr>
    <td>Engineering</td>
    <td>100</td>
  </tr>
  <tr>
    <td>Sales</td>
    <td>150</td>
  </tr>
"""  # Missing </table>

    print("\nTruncated HTML (no </table> tag):")
    print(truncated_html)

    # Detect truncation
    is_trunc, ctype, reason = detect_truncation(truncated_html)
    print(f"\n✓ Detected: {reason}")

    # Parse with lenient mode (html5lib auto-closes)
    print("\n--- Parsing with lenient mode ---")
    converter = TableConverter(strict=False)
    table = converter.html_to_ir(truncated_html)

    print(f"✓ Parsed successfully: {table.num_rows}x{table.num_cols}")
    print(f"  Cells: {len(table.cells)}")

    # Validate
    is_valid, errors = table.validate()
    print(f"  Valid: {is_valid}")

    # Convert to OTSL
    otsl = converter.html_to_otsl(truncated_html)
    print(f"\n✓ Converted to OTSL ({len(otsl)} chars)")
    print(otsl[:100] + "...")


def demo_truncated_mid_cell():
    """Demo: HTML truncated in the middle of a cell."""
    print("\n" + "=" * 60)
    print("DEMO 2: Truncated Mid-Cell Content")
    print("=" * 60)

    truncated_html = """<table>
  <tr>
    <td>Product</td>
    <td>Price</td>
  </tr>
  <tr>
    <td>Laptop</td>
    <td>$1,2"""  # Truncated mid-price

    print("\nTruncated HTML (mid-cell):")
    print(truncated_html)
    print("\n❌ Truncated at: '$1,2' (incomplete)")

    # Detect
    is_trunc, ctype, reason = detect_truncation(truncated_html)
    print(f"\n✓ Detected: {reason}")

    # Parse
    converter = TableConverter(strict=False)
    table = converter.html_to_ir(truncated_html)

    print(f"\n✓ Parsed: {table.num_rows}x{table.num_cols}")

    # Check last cell
    last_row_cells = [c for c in table.cells if c.row_idx == table.num_rows - 1]
    contents = [c.content.text for c in sorted(last_row_cells, key=lambda x: x.col_idx)]
    print(f"  Row 2 cells: {contents}")
    print(f"  Note: Partial content preserved: '{contents[-1]}'")


def demo_otsl_truncation():
    """Demo: OTSL missing closing tag."""
    print("\n" + "=" * 60)
    print("DEMO 3: OTSL Truncation")
    print("=" * 60)

    truncated_otsl = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<nl><fcel>C<fcel>D<nl>"

    print("\nTruncated OTSL (no </otsl> tag):")
    print(truncated_otsl)

    # Detect
    is_trunc, ctype, reason = detect_truncation(truncated_otsl)
    print(f"\n✓ Detected: {reason}")

    # Auto-fix
    fixed_otsl = auto_close_otsl(truncated_otsl)
    print(f"\n✓ Auto-fixed: Added </otsl> tag")
    print(f"  Result: ...{fixed_otsl[-50:]}")

    # Parse
    converter = TableConverter(strict=False)
    table = converter.otsl_to_ir(fixed_otsl)

    print(f"\n✓ Parsed: {table.num_rows}x{table.num_cols}")

    # Convert to HTML
    html = converter.otsl_to_html(fixed_otsl)
    print(f"✓ Converted to HTML:")
    print(html)


def demo_auto_fix_utility():
    """Demo: Using the auto-fix utility."""
    print("\n" + "=" * 60)
    print("DEMO 4: Auto-Fix Utility")
    print("=" * 60)

    truncated_html = "<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr>"

    print("\nOriginal (truncated):")
    print(truncated_html)

    # Use fix_truncated_output utility
    fixed, was_truncated, message = fix_truncated_output(truncated_html)

    print(f"\n✓ {message}")
    print(f"  Was truncated: {was_truncated}")
    print(f"\nFixed HTML:")
    print(fixed)

    # Parse and validate
    converter = TableConverter(strict=False)
    table = converter.html_to_ir(fixed)

    is_valid, errors = table.validate()
    print(f"\n✓ Validation: {'PASSED' if is_valid else 'FAILED'}")


def demo_ai_evaluation_pipeline():
    """Demo: Complete AI evaluation pipeline with truncation handling."""
    print("\n" + "=" * 60)
    print("DEMO 5: AI Evaluation Pipeline")
    print("=" * 60)

    # Simulate AI model output (truncated)
    ai_output = """<table>
  <tr>
    <td>Category</td>
    <td>Value</td>
  </tr>
  <tr>
    <td>Revenue</td>
    <td>$1.5M</td>
  </tr>
  <tr>
    <td>Expenses</td>
    <td>$800K</td>
  </tr>
"""  # Missing </table>

    # Ground truth
    ground_truth = """<table>
  <tr>
    <td>Category</td>
    <td>Value</td>
  </tr>
  <tr>
    <td>Revenue</td>
    <td>$1.5M</td>
  </tr>
  <tr>
    <td>Expenses</td>
    <td>$800K</td>
  </tr>
</table>"""

    print("AI Output (truncated):")
    print(ai_output[:100] + "...")

    # Step 1: Detect truncation
    is_trunc, ctype, reason = detect_truncation(ai_output)
    if is_trunc:
        print(f"\n⚠️  Detected: {reason}")

    # Step 2: Auto-fix
    fixed_output, _, msg = fix_truncated_output(ai_output)
    print(f"✓ {msg}")

    # Step 3: Parse with lenient mode
    converter = TableConverter(strict=False)
    ai_table = converter.html_to_ir(fixed_output)
    gt_table = converter.html_to_ir(ground_truth)

    print(f"\n✓ Parsed AI output: {ai_table.num_rows}x{ai_table.num_cols}")
    print(f"✓ Parsed ground truth: {gt_table.num_rows}x{gt_table.num_cols}")

    # Step 4: Validate
    is_valid, errors = ai_table.validate()
    print(f"✓ AI output valid: {is_valid}")

    # Step 5: Compute similarity (would use TEDS in real scenario)
    print(f"\n✓ Both tables match: {ai_table.num_rows == gt_table.num_rows and ai_table.num_cols == gt_table.num_cols}")
    print("✓ Ready for TEDS evaluation!")


def demo_real_world_example():
    """Demo: Your actual truncated example."""
    print("\n" + "=" * 60)
    print("DEMO 6: Real-World Example (Your Case)")
    print("=" * 60)

    # Your actual example
    from pathlib import Path

    fixture = Path("tests/fixtures/malformed_truncated.html")
    if not fixture.exists():
        print("Fixture not found, skipping")
        return

    html = fixture.read_text()

    print(f"File: {fixture.name}")
    print(f"Size: {len(html)} characters")
    print(f"Has </table>: {('</table>' in html)}")

    # Detect
    is_trunc, ctype, reason = detect_truncation(html)
    print(f"\n✓ Detected: {reason}")

    # Parse
    converter = TableConverter(strict=False)
    table = converter.html_to_ir(html)

    print(f"\n✓ Parsed: {table.num_rows}x{table.num_cols} table")
    print(f"  Total cells: {len(table.cells)}")

    # Convert to OTSL
    otsl = converter.html_to_otsl(html)
    print(f"\n✓ Converted to OTSL ({len(otsl)} characters)")

    # Validate
    is_valid, errors = table.validate()
    print(f"✓ Validation: {'PASSED' if is_valid else 'FAILED'}")

    if is_valid:
        print("\n✅ Successfully processed truncated AI output!")


if __name__ == "__main__":
    demo_missing_closing_tag()
    demo_truncated_mid_cell()
    demo_otsl_truncation()
    demo_auto_fix_utility()
    demo_ai_evaluation_pipeline()
    demo_real_world_example()

    print("\n" + "=" * 60)
    print("✅ All truncation handling demos completed!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Lenient mode (strict=False) handles truncated HTML automatically")
    print("2. html5lib auto-closes missing tags")
    print("3. OTSL truncation can be fixed with auto_close_otsl()")
    print("4. Truncation detection utilities available")
    print("5. Ready for AI model evaluation!")
