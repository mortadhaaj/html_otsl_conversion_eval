"""
Debug script for malformed HTML table with conflicting rowspans.
"""

from pathlib import Path
from src.api.converters import TableConverter

# Read the malformed HTML
html_path = Path("test_user_malformed_table.html")
html = html_path.read_text()

print("=" * 80)
print("DEBUGGING MALFORMED HTML TABLE")
print("=" * 80)

# Try with strict=False (lenient mode)
print("\n--- Attempt 1: strict=False (lenient mode) ---")
try:
    converter = TableConverter(strict=False)

    # Parse to IR
    print("\nParsing HTML to IR...")
    table = converter.html_to_ir(html)

    print(f"✓ Parsed to IR: {table.num_rows}x{table.num_cols}")
    print(f"  Total cells: {len(table.cells)}")

    # Show cell structure
    print("\nCell structure (showing rowspans):")
    for row_idx in range(min(table.num_rows, 16)):  # Show first 16 rows
        row_cells = [c for c in table.cells if c.row_idx == row_idx]
        row_cells.sort(key=lambda c: c.col_idx)

        cell_info = []
        for cell in row_cells:
            span_info = ""
            if cell.rowspan > 1 or cell.colspan > 1:
                span_info = f" (rs={cell.rowspan}, cs={cell.colspan})"
            content_preview = cell.content.text[:15] if cell.content.text else "(empty)"
            cell_info.append(f"[{cell.col_idx}]{span_info}: {content_preview}")

        print(f"  Row {row_idx}: {len(row_cells)} cells -> {', '.join(cell_info)}")

    # Check for cells extending beyond table
    print("\nChecking for cells extending beyond table...")
    for i, cell in enumerate(table.cells):
        end_row = cell.row_idx + cell.rowspan - 1
        end_col = cell.col_idx + cell.colspan - 1

        if end_row >= table.num_rows:
            print(f"  ❌ Cell {i} at ({cell.row_idx},{cell.col_idx}) with rowspan={cell.rowspan} extends to row {end_row} (table has {table.num_rows} rows)")

        if end_col >= table.num_cols:
            print(f"  ❌ Cell {i} at ({cell.row_idx},{cell.col_idx}) with colspan={cell.colspan} extends to col {end_col} (table has {table.num_cols} cols)")

    # Try to convert to OTSL
    print("\nConverting to OTSL...")
    otsl = converter.html_to_otsl(html)

    print(f"✓ Conversion successful! ({len(otsl)} chars)")
    print(f"\nFirst 300 chars of OTSL:")
    print(otsl[:300])

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

# Try with strict=True
print("\n\n--- Attempt 2: strict=True (strict mode) ---")
try:
    converter = TableConverter(strict=True)
    otsl = converter.html_to_otsl(html)
    print("✓ Conversion successful with strict mode!")

except Exception as e:
    print(f"❌ Error: {e}")
