"""
Analyze the malformed OTSL example to understand the inconsistency.
"""

# The OTSL example provided
otsl_example = """<otsl><loc_0><loc_0><loc_500><loc_500><ched>التخصص<ched>١٩٨٠<lcel><lcel><ched>١٩٩٠<lcel><lcel><ched>٢٠٠٠<lcel><lcel><ched>٢٠٢٠<lcel><lcel><nl><ucel><ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الجامعات)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<ched>عدد الطلاب (الكليات التقنية)<nl><fcel>عدد الطلاب<fcel>٥٠٠<fcel>١٢٠٠<fcel>٧٠٠<fcel>١٥٠٠<fcel>٩٠٠<fcel>١٨٠٠<fcel>١١٠٠<fcel>٢٠٠٠<fcel>١٣٠٠<fcel>١٠٠٠<fcel>١٠٠٠<fcel>١٠٠٠<nl><fcel>نسبة النجاح<fcel>٨٠<fcel>٧٥٠<fcel>٨٢<fcel>٧٧٠<fcel>٨٥٠<fcel>٨٠<fcel>٨٨٠<fcel>٨٣٠<fcel>٩٠٠<fcel>٨٥٠<fcel>٨٥٠<fcel>٨٥٠<nl><fcel>عدد الطلاب<fcel>٦٠٠<fcel>٣٠٠<fcel>٨٠٠<fcel>٤٥٠<fcel>١٠٠٠<fcel>٦٥٠<fcel>١٢٠٠<fcel>٨٠٠<fcel>١٥٠٠<fcel>٨٠٠<fcel>١٥٠٠<fcel>٨٠٠<nl><fcel>نسبة النجاح<fcel>٧٨<fcel>٧٢٠<fcel>٨٣٠<fcel>٧٥٠<fcel>٨٧٠<fcel>٧٨٠<fcel>٨٩٠<fcel>٨٨٠<fcel>٩٢٠<fcel>٨٤٠<fcel>٨٤٠<fcel>٨٤٠<nl><fcel>عدد الطلاب<fcel>٨٠٠<fcel>-<fcel>٩٠٠<fcel>-<fcel>١٠٥٠<fcel>-<fcel>١٢٥٠<fcel>-<fcel>١٤٠٠<fcel>-<fcel>١٤٠٠<fcel>١٤٠٠<nl><fcel>نسبة النجاح<fcel>٨٥<fcel>-<fcel>٨٨٠<fcel>-<fcel>٩٠٠<fcel>-<fcel>٩٢٠<fcel>-<fcel>٩٥٠<fcel>-<fcel>٩٥٠<fcel>٩٥٠<nl><fcel>عدد الطلاب<fcel>٣٠٠<fcel>٢٠٠<fcel>٤٠٠<fcel>٣٥٠<fcel>٥٥٠<fcel>٥٠٠<fcel>٧٠٠<fcel>٦٥٠<fcel>٨٥٠<fcel>٨٥٠<fcel>٨٠٠<fcel>٨٥٠<nl><fcel>نسبة النجاح<fcel>٨٢<fcel>٧٠٠<fcel>٨٥٠<fcel>٧٣٠<fcel>٨٧٠<fcel>٧٦٠<fcel>٨٩٠<fcel>٧٩٩<fcel>٦٧٠<fcel>٨٩٠<fcel>٨٥٠<fcel>٨٥٠<nl></otsl>"""

# Parse manually to analyze structure
import re

# Remove wrapper and location tags
content = otsl_example.strip()[6:-7]  # Remove <otsl> and </otsl>
content = re.sub(r'<loc_\d+>', '', content).strip()

# Split by rows
rows_raw = content.split('<nl>')
rows_raw = [r for r in rows_raw if r.strip()]

print(f"Total rows: {len(rows_raw)}")
print("\nAnalyzing each row:\n")

for i, row in enumerate(rows_raw):
    # Count tags in row
    tags = re.findall(r'<(ched|rhed|fcel|ecel|lcel|ucel|xcel)>', row)
    print(f"Row {i}: {len(tags)} tags")
    print(f"  Tags: {tags}")

# Expected structure
print("\n=== ANALYSIS ===")
print("Row 0: 13 tags (1 ched + 4 ched groups with lcel,lcel)")
print("  التخصص, ١٩٨٠[lcel,lcel], ١٩٩٠[lcel,lcel], ٢٠٠٠[lcel,lcel], ٢٠٢٠[lcel,lcel]")
print("  This means: 1 + (4 * 3) = 13 columns")
print("")
print("Row 1: Should have 13 tags but has MORE (1 ucel + 13 ched)")
print("  This is INCONSISTENT - row 1 has 14 tags instead of 13!")
print("")
print("Rows 2-9: Each should have 13 tags")
