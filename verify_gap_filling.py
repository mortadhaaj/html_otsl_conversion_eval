"""
Verify that gap-filling logic is working in lenient mode.
"""

from pathlib import Path
from src.api.converters import TableConverter

html_path = Path("test_user_malformed_table.html")
html = html_path.read_text()

print("=" * 80)
print("VERIFYING GAP-FILLING IN LENIENT MODE")
print("=" * 80)

# Test with lenient mode
converter = TableConverter(strict=False)

# Parse to IR
table = converter.html_to_ir(html)

print(f"\nTable: {table.num_rows}x{table.num_cols}")
print(f"Total cells: {len(table.cells)}")

# Check column 4 specifically
print("\nColumn 4 occupancy:")
col4_cells = [c for c in table.cells if c.col_idx == 4]
print(f"Cells in column 4: {len(col4_cells)}")

for row_idx in range(table.num_rows):
    row_col4_cells = [c for c in col4_cells if c.row_idx == row_idx]
    if row_col4_cells:
        cell = row_col4_cells[0]
        content = cell.content.text if cell.content.text else "(empty)"
        span_info = f"rs={cell.rowspan}" if cell.rowspan > 1 else ""
        print(f"  Row {row_idx}: {content[:20]} {span_info}")
    else:
        print(f"  Row {row_idx}: NO CELL!")

# Validate
print("\nValidation:")
is_valid, errors = table.validate()
print(f"Valid: {is_valid}")
if not is_valid:
    print(f"Errors: {errors}")

# Try OTSL conversion
print("\nOTSL Conversion:")
try:
    otsl = converter.html_to_otsl(html)
    print(f"✓ Success! ({len(otsl)} chars)")
except Exception as e:
    print(f"❌ Failed: {e}")
