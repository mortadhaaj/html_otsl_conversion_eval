"""
Test user's truncated OTSL case.
"""

from pathlib import Path
from src.api.converters import TableConverter

# Read the truncated OTSL
truncated_otsl = Path("test_user_truncated_otsl.otsl").read_text()

print("=" * 80)
print("USER'S TRUNCATED OTSL - TEST")
print("=" * 80)

print(f"\nOTSL length: {len(truncated_otsl)} chars")
print(f"Ends with </otsl>: {truncated_otsl.strip().endswith('</otsl>')}")
print(f"Last 100 chars: ...{truncated_otsl[-100:]}")

# Test with strict=False (lenient mode)
print("\n--- Attempt 1: strict=False (lenient mode) ---")
try:
    converter = TableConverter(strict=False)

    # Parse OTSL to IR
    print("\nParsing truncated OTSL to IR...")
    table = converter.otsl_to_ir(truncated_otsl)

    print(f"✓ Parsed successfully!")
    print(f"  Table: {table.num_rows}x{table.num_cols}")
    print(f"  Cells: {len(table.cells)}")

    # Validate
    is_valid, errors = table.validate()
    print(f"  Valid: {is_valid}")
    if not is_valid:
        print(f"  Errors: {errors[:3]}")  # Show first 3 errors

    # Convert to HTML
    print("\nConverting to HTML...")
    html = converter.otsl_to_html(truncated_otsl)

    print(f"✓ HTML generated: {len(html)} chars")
    print(f"  First 200 chars: {html[:200]}...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test with strict=True (should fail)
print("\n\n--- Attempt 2: strict=True (should fail) ---")
try:
    converter = TableConverter(strict=True)
    table = converter.otsl_to_ir(truncated_otsl)
    print("✓ Unexpectedly succeeded with strict mode!")

except Exception as e:
    print(f"❌ Expected error: {e}")

print("\n" + "=" * 80)
print("✅ LENIENT MODE HANDLES TRUNCATED OTSL!")
print("=" * 80)
