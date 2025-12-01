"""
Test to reproduce the escaped quotes error.
"""

from pathlib import Path
from src.api.converters import TableConverter

html = Path("test_escaped_quotes.html").read_text()

print("HTML snippet:")
print(html[:100])
print()

print("Testing with strict=False:")
try:
    converter = TableConverter(strict=False)
    otsl = converter.html_to_otsl(html)
    print(f"✓ Success: {len(otsl)} chars")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
