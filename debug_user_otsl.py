"""
Debug script for user's OTSL conversion issue.
Error: No cell covers position (2, 5); No cell covers position (4, 5)
"""

from src.api.converters import TableConverter

# User's problematic OTSL (reconstructed based on pattern)
user_otsl = """<otsl><has_tbody><loc_102><loc_285><loc_718><loc_468><fcel>الدولة<fcel>استراتيجيات التسويق<fcel>الجمهور المستهدف<fcel>الفعالية<fcel>القنوات الأكثر فعالية<fcel>أهم الصناعات<nl><fcel>السعودية<fcel>التسويق الرقمي: 85%، التسويق التقليدي: 15%<fcel>الشباب، النساء العاملات<fcel>تيك توك، تويتر<fcel>التجارة الإلكترونية، الترفيه<ecel><nl><ucel><fcel>التسويق الرقمي: 75%، التسويق عبر المؤثرين: 25%<fcel>السياح، رواد الأعمال<fcel>انستغرام، لينكد إن<ucel><ucel><nl><fcel>الكويت<fcel>التسويق الرقمي: 70%، التسويق التقليدي: 30%<fcel>الأسر الثرية، الشباب<fcel>تويتر، انستغرام<fcel>العقارات، الأزياء<ecel><nl><ucel><fcel>التسويق الرقمي: 60%، التسويق المؤثر: 40%<fcel>الشباب، العائلات<fcel>سناب شات، تيك توك<ucel><ucel><nl></otsl>"""

print("=" * 80)
print("DEBUGGING USER'S OTSL CONVERSION ERROR")
print("=" * 80)

# Try with strict=False (lenient mode)
print("\n--- Attempt 1: strict=False (lenient mode) ---")
try:
    converter = TableConverter(strict=False)

    # First, parse to IR to see the structure
    print("\nParsing OTSL to IR...")
    table = converter.otsl_to_ir(user_otsl)

    print(f"✓ IR parsed: {table.num_rows}x{table.num_cols}")
    print(f"  Total cells: {len(table.cells)}")

    # Show cell structure
    print("\nCell structure:")
    for row_idx in range(table.num_rows):
        row_cells = [c for c in table.cells if c.row_idx == row_idx]
        row_cells.sort(key=lambda c: c.col_idx)

        cell_info = []
        for cell in row_cells:
            span_info = ""
            if cell.rowspan > 1 or cell.colspan > 1:
                span_info = f" (rs={cell.rowspan}, cs={cell.colspan})"
            content_preview = cell.content.text[:20] if cell.content.text else "(empty)"
            cell_info.append(f"[{cell.col_idx}]{span_info}: {content_preview}")

        print(f"  Row {row_idx}: {len(row_cells)} cells: {', '.join(cell_info)}")

    # Now try to convert to HTML
    print("\nConverting to HTML...")
    html = converter.otsl_to_html(user_otsl)

    print("✓ Conversion successful!")
    print(f"\nGenerated HTML ({len(html)} chars):")
    print(html)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

# Try with strict=True to see difference
print("\n\n--- Attempt 2: strict=True (strict mode) ---")
try:
    converter = TableConverter(strict=True)
    html = converter.otsl_to_html(user_otsl)
    print("✓ Conversion successful with strict mode!")

except Exception as e:
    print(f"❌ Error: {e}")
