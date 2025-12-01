"""
Demonstration of lenient parsing mode for malformed tables.

This script shows how to use strict=False to parse tables with:
- Inconsistent row lengths (different number of cells per row)
- Empty rows in HTML
- Missing cells
"""

from src.api.converters import TableConverter


def demo_inconsistent_otsl():
    """Demo: OTSL with inconsistent row lengths."""
    print("=" * 60)
    print("DEMO 1: OTSL with Inconsistent Row Lengths")
    print("=" * 60)

    # Row 0 has 3 cells, Row 1 has 4 cells (INCONSISTENT!)
    malformed_otsl = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<fcel>C<nl><fcel>D<fcel>E<fcel>F<fcel>G<nl></otsl>'

    print("\nMalformed OTSL:")
    print(malformed_otsl)
    print("\nRow 0: 3 cells (A, B, C)")
    print("Row 1: 4 cells (D, E, F, G) <-- INCONSISTENT!")

    # Try with strict mode (default)
    print("\n--- STRICT MODE (default) ---")
    converter_strict = TableConverter(strict=True)
    table_strict = converter_strict.otsl_to_ir(malformed_otsl)
    print(f"Result: {table_strict.num_rows}x{table_strict.num_cols}")
    print(f"Cells: {len(table_strict.cells)}")

    # Validation may fail
    is_valid, errors = table_strict.validate()
    if not is_valid:
        print(f"❌ Validation failed: {errors[0]}")
    else:
        print("✓ Valid (but may have gaps)")

    # Try with lenient mode
    print("\n--- LENIENT MODE (strict=False) ---")
    converter_lenient = TableConverter(strict=False)
    table_lenient = converter_lenient.otsl_to_ir(malformed_otsl)
    print(f"Result: {table_lenient.num_rows}x{table_lenient.num_cols}")
    print(f"Cells: {len(table_lenient.cells)} (padded short rows!)")

    # Should validate successfully
    is_valid, errors = table_lenient.validate()
    if is_valid:
        print("✓ Validation passed after normalization!")
    else:
        print(f"❌ Validation failed: {errors}")

    # Convert to HTML
    html_output = converter_lenient.otsl_to_html(malformed_otsl)
    print("\nConverted to HTML:")
    print(html_output)


def demo_empty_rows_html():
    """Demo: HTML with empty rows."""
    print("\n" + "=" * 60)
    print("DEMO 2: HTML with Empty Rows")
    print("=" * 60)

    malformed_html = """<table border="1">
        <tr><td>A</td><td>B</td></tr>
        <tr></tr>
        <tr><td>C</td><td>D</td></tr>
    </table>"""

    print("\nMalformed HTML:")
    print(malformed_html)
    print("\nNote: Row 2 is EMPTY (<tr></tr>)")

    # Strict mode
    print("\n--- STRICT MODE ---")
    converter_strict = TableConverter(strict=True)
    try:
        table_strict = converter_strict.html_to_ir(malformed_html)
        print(f"Result: {table_strict.num_rows}x{table_strict.num_cols}")
        is_valid, errors = table_strict.validate()
        if not is_valid:
            print(f"❌ Validation: {errors[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Lenient mode
    print("\n--- LENIENT MODE ---")
    converter_lenient = TableConverter(strict=False)
    table_lenient = converter_lenient.html_to_ir(malformed_html)
    print(f"Result: {table_lenient.num_rows}x{table_lenient.num_cols} (empty row filtered!)")

    is_valid, errors = table_lenient.validate()
    print(f"✓ Validation: {'PASSED' if is_valid else 'FAILED'}")

    # Convert to OTSL
    otsl_output = converter_lenient.html_to_otsl(malformed_html)
    print("\nConverted to OTSL:")
    print(otsl_output)


def demo_arabic_table():
    """Demo: Real Arabic table with inconsistent columns."""
    print("\n" + "=" * 60)
    print("DEMO 3: Arabic Table with Inconsistent Columns")
    print("=" * 60)

    # Actual malformed OTSL from user
    arabic_otsl = '''<otsl><loc_0><loc_0><loc_500><loc_500><ched>التخصص<ched>١٩٨٠<lcel><lcel><ched>١٩٩٠<lcel><lcel><ched>٢٠٠٠<lcel><lcel><ched>٢٠٢٠<lcel><lcel><nl><ucel><ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<nl><fcel>عدد الطلاب<fcel>٥٠٠<fcel>١٢٠٠<fcel>٧٠٠<fcel>١٥٠٠<fcel>٩٠٠<fcel>١٨٠٠<fcel>١١٠٠<fcel>٢٠٠٠<fcel>١٣٠٠<fcel>١٠٠٠<fcel>١٠٠٠<fcel>١٠٠٠<nl></otsl>'''

    print("\nArabic OTSL (truncated for display)")
    print("Row 0: 13 tags")
    print("Row 1: 14 tags (1 ucel + 13 ched) <-- INCONSISTENT!")
    print("Row 2: 13 tags")

    # Lenient mode
    print("\n--- LENIENT MODE ---")
    converter = TableConverter(strict=False)
    table = converter.otsl_to_ir(arabic_otsl)
    print(f"Result: {table.num_rows}x{table.num_cols}")

    is_valid, errors = table.validate()
    print(f"✓ Validation: {'PASSED' if is_valid else 'FAILED'}")

    if is_valid:
        print("\n✓ Successfully parsed malformed Arabic table!")
        print("  This is useful for evaluating AI-generated tables")


def demo_use_case():
    """Demo: Use case for AI model evaluation."""
    print("\n" + "=" * 60)
    print("USE CASE: Evaluating AI-Generated Tables")
    print("=" * 60)

    print("""
When evaluating AI models that generate tables, they may produce
malformed output with:
- Inconsistent row lengths
- Missing cells
- Empty rows

Using strict=False allows you to:
1. Parse these malformed tables
2. Convert them to a normalized format
3. Evaluate them with metrics like TEDS
4. Compare against ground truth despite formatting errors

Example:
    # AI model output (may be malformed)
    ai_output = "<otsl>...</otsl>"  # Inconsistent rows

    # Ground truth (well-formed)
    ground_truth = "<otsl>...</otsl>"

    # Parse both with lenient mode
    converter = TableConverter(strict=False)
    ai_table = converter.otsl_to_html(ai_output)
    gt_table = converter.otsl_to_html(ground_truth)

    # Compute TEDS score for evaluation
    from src.api.teds_utils import TEDSCalculator
    teds = TEDSCalculator()
    score = teds.compute_score(ai_table, gt_table)
    print(f"TEDS Score: {score:.4f}")
    """)


if __name__ == "__main__":
    demo_inconsistent_otsl()
    demo_empty_rows_html()
    demo_arabic_table()
    demo_use_case()

    print("\n" + "=" * 60)
    print("✓ All demos completed successfully!")
    print("=" * 60)
