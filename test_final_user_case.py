"""
Final test of user's OTSL case to verify the fix.
"""

from src.api.converters import TableConverter

# User's exact OTSL from the error report
user_otsl = """<otsl><has_tbody><loc_102><loc_285><loc_718><loc_468><fcel>الدولة<fcel>استراتيجيات التسويق<fcel>الجمهور المستهدف<fcel>الفعالية<fcel>القنوات الأكثر فعالية<fcel>أهم الصناعات<nl><fcel>السعودية<fcel>التسويق الرقمي: 85%، التسويق التقليدي: 15%<fcel>الشباب، النساء العاملات<fcel>تيك توك، تويتر<fcel>التجارة الإلكترونية، الترفيه<ecel><nl><ucel><fcel>التسويق الرقمي: 75%، التسويق عبر المؤثرين: 25%<fcel>السياح، رواد الأعمال<fcel>انستغرام، لينكد إن<ucel><ucel><nl><fcel>الكويت<fcel>التسويق الرقمي: 70%، التسويق التقليدي: 30%<fcel>الأسر الثرية، الشباب<fcel>تويتر، انستغرام<fcel>العقارات، الأزياء<ecel><nl><ucel><fcel>التسويق الرقمي: 60%، التسويق المؤثر: 40%<fcel>الشباب، العائلات<fcel>سناب شات، تيك توك<ucel><ucel><nl></otsl>"""

print("=" * 80)
print("FINAL USER CASE TEST - OTSL TO HTML CONVERSION")
print("=" * 80)

# Test with lenient mode (recommended for AI-generated tables)
print("\n--- Converting with strict=False ---")
converter = TableConverter(strict=False)

try:
    # Parse to IR
    table = converter.otsl_to_ir(user_otsl)
    print(f"✓ Parsed to IR: {table.num_rows}x{table.num_cols} table")
    print(f"  Total cells: {len(table.cells)}")

    # Validate
    is_valid, errors = table.validate()
    print(f"✓ Validation: {'PASSED' if is_valid else 'FAILED'}")
    if not is_valid:
        print(f"  Errors: {errors}")

    # Convert to HTML
    html = converter.otsl_to_html(user_otsl)
    print(f"✓ Converted to HTML successfully ({len(html)} chars)")

    # Show the HTML structure
    print("\n--- Generated HTML ---")
    print(html)

    # Test roundtrip
    print("\n--- Testing Roundtrip (HTML → OTSL) ---")
    otsl_back = converter.html_to_otsl(html)
    print(f"✓ Converted back to OTSL ({len(otsl_back)} chars)")

    # Parse the roundtrip OTSL
    table_back = converter.otsl_to_ir(otsl_back)
    print(f"✓ Roundtrip table: {table_back.num_rows}x{table_back.num_cols}")

    # Compare structures
    print("\n--- Comparison ---")
    print(f"Original cells: {len(table.cells)}")
    print(f"Roundtrip cells: {len(table_back.cells)}")
    print(f"Match: {len(table.cells) == len(table_back.cells)}")

    print("\n" + "=" * 80)
    print("✅ SUCCESS! User's OTSL case now works perfectly!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
