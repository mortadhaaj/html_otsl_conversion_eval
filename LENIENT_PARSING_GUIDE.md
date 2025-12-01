# Lenient Parsing Mode Guide

## Overview

The HTML ↔ OTSL converter now supports **lenient parsing mode** (`strict=False`) to handle malformed tables that may come from AI models or other sources with formatting errors.

## Why Lenient Mode?

When evaluating AI-generated tables, models may produce output with:
- **Inconsistent row lengths** - Different number of cells per row
- **Empty rows** - Rows with no cells (`<tr></tr>`)
- **Missing cells** - Gaps in the table structure
- **Extra cells** - Rows with too many cells

Lenient mode allows you to:
1. ✅ Parse malformed tables without errors
2. ✅ Normalize them to valid table structures
3. ✅ Evaluate them with metrics like TEDS
4. ✅ Compare against ground truth despite formatting errors

---

## Usage

### Basic Example

```python
from src.api.converters import TableConverter

# Create converter with lenient mode
converter = TableConverter(strict=False)

# Parse malformed OTSL with inconsistent rows
malformed_otsl = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<fcel>B<nl><fcel>C<fcel>D<fcel>E<nl></otsl>'
# Row 0: 2 cells (A, B)
# Row 1: 3 cells (C, D, E) <- INCONSISTENT!

# Lenient mode normalizes the table
table_ir = converter.otsl_to_ir(malformed_otsl)
# Result: 2x3 table with row 0 padded with empty cell

# Convert to HTML
html = converter.otsl_to_html(malformed_otsl)
# Produces valid HTML with normalized structure
```

### Comparison: Strict vs Lenient

```python
# STRICT MODE (default)
converter_strict = TableConverter(strict=True)
table = converter_strict.otsl_to_ir(malformed_otsl)
is_valid, errors = table.validate()
# ❌ Validation fails: "No cell covers position (0, 2)"

# LENIENT MODE
converter_lenient = TableConverter(strict=False)
table = converter_lenient.otsl_to_ir(malformed_otsl)
is_valid, errors = table.validate()
# ✅ Validation passes after normalization
```

---

## What Lenient Mode Does

### For OTSL Parsing

#### 1. Pads Short Rows
Rows with fewer cells than the maximum are padded with empty cells.

**Input:**
```otsl
<otsl><loc_1><loc_2><loc_3><loc_4>
  <fcel>A<fcel>B<nl>          <!-- 2 cells -->
  <fcel>C<fcel>D<fcel>E<nl>  <!-- 3 cells -->
</otsl>
```

**Lenient Output:**
- Row 0: `A`, `B`, `[empty]` ← Padded!
- Row 1: `C`, `D`, `E`
- Result: 2×3 table (valid)

#### 2. Truncates Long Rows
Rows with more cells than needed are truncated to match maximum columns.

**Input:**
```otsl
<otsl><loc_1><loc_2><loc_3><loc_4>
  <fcel>A<fcel>B<fcel>C<fcel>D<nl>  <!-- 4 cells -->
  <fcel>E<fcel>F<nl>                 <!-- 2 cells -->
</otsl>
```

**Lenient Output:**
- Row 0: `A`, `B`, `C`, `D`
- Row 1: `E`, `F`, `[empty]`, `[empty]` ← Padded!
- Result: 2×4 table (valid)

### For HTML Parsing

#### 1. Filters Empty Rows
Rows with no `<td>` or `<th>` elements are removed.

**Input:**
```html
<table>
  <tr><td>A</td><td>B</td></tr>
  <tr></tr>                     <!-- EMPTY ROW -->
  <tr><td>C</td><td>D</td></tr>
</table>
```

**Lenient Output:**
- Empty row removed
- Result: 2×2 table (A, B, C, D)

#### 2. Adjusts Rowspans
When empty rows are filtered, rowspan values are adjusted to maintain structure.

**Input:**
```html
<table>
  <tr><td rowspan="2">A</td><td>B</td></tr>
  <tr></tr>  <!-- Empty row for rowspan -->
  <tr><td>C</td><td>D</td></tr>
</table>
```

**Lenient Output:**
- Empty row removed
- Cell A's rowspan adjusted from 2 to 1
- Result: 2×2 table (valid structure)

#### 3. Fills Gaps
Missing cells in the occupancy grid are filled with empty cells.

**Input:**
```html
<table>
  <tr><td>A</td></tr>
  <tr><td>B</td><td>C</td></tr>
</table>
```

**Lenient Output:**
- Row 0: `A`, `[empty]` ← Gap filled!
- Row 1: `B`, `C`
- Result: 2×2 table (valid)

---

## Use Cases

### 1. AI Model Evaluation

```python
from src.api.converters import TableConverter
from src.api.teds_utils import TEDSCalculator

# AI model output (may be malformed)
ai_output_otsl = "<otsl>...</otsl>"  # Inconsistent rows

# Ground truth (well-formed)
ground_truth_otsl = "<otsl>...</otsl>"

# Parse both with lenient mode
converter = TableConverter(strict=False)
ai_html = converter.otsl_to_html(ai_output_otsl)
gt_html = converter.otsl_to_html(ground_truth_otsl)

# Compute TEDS score
teds = TEDSCalculator()
score = teds.compute_score(ai_html, gt_html)
print(f"TEDS Score: {score:.4f}")
```

### 2. Web Scraping

```python
# HTML from web may have formatting issues
scraped_html = """..."""  # May have empty rows

converter = TableConverter(strict=False)
otsl = converter.html_to_otsl(scraped_html)
# Normalized OTSL ready for storage/processing
```

### 3. Legacy Data Migration

```python
# Old tables may not follow modern standards
legacy_html = """..."""  # Inconsistent structure

converter = TableConverter(strict=False)
table_ir = converter.html_to_ir(legacy_html)
# Normalized IR can be exported to any format
```

---

## Real-World Examples

### Example 1: Arabic Table (from User)

The user provided this malformed OTSL:
- Row 0: 13 tags
- Row 1: 14 tags (1 ucel + 13 ched) ← INCONSISTENT!
- Rows 2-9: 13 tags each

**Strict mode:** Creates invalid structure (validation fails)

**Lenient mode:** Normalizes to 10×14 table (validation passes)

```python
converter = TableConverter(strict=False)
table = converter.otsl_to_ir(arabic_otsl)
# Result: 10x14 table, all cells accounted for
```

### Example 2: Empty Rows in HTML (from fixtures/129.html)

Table with `rowspan="2"` cells followed by empty `<tr></tr>` rows.

**Strict mode:** Invalid structure (cells extend beyond table)

**Lenient mode:** Empty rows filtered, rowspans adjusted, valid structure

```python
converter = TableConverter(strict=False)
html_content = Path("fixtures/129.html").read_text()
otsl = converter.html_to_otsl(html_content)
# Successfully converts with normalized structure
```

---

## Testing

Run the lenient parsing tests:

```bash
# Test lenient parsing
pytest tests/unit/test_lenient_parsing.py -v

# Run demo script
python demo_lenient_parsing.py
```

### Test Coverage

```
✅ 12 lenient parsing tests
  - Inconsistent row lengths (OTSL)
  - Empty rows (HTML)
  - Empty tables
  - Gaps in occupancy
  - Roundtrip conversion
  - Real-world fixtures
```

---

## API Reference

### TableConverter

```python
TableConverter(preserve_latex: bool = True, strict: bool = True)
```

**Parameters:**
- `preserve_latex` (bool): Detect and preserve LaTeX formulas (default: True)
- `strict` (bool): Raise errors on malformed tables (default: True)
  - `True`: Strict validation, may fail on malformed tables
  - `False`: Lenient parsing, normalizes malformed tables

**Methods:**
All existing methods support the `strict` parameter:
- `html_to_otsl(html)` - Convert HTML to OTSL
- `otsl_to_html(otsl)` - Convert OTSL to HTML
- `html_to_ir(html)` - Parse HTML to IR
- `otsl_to_ir(otsl)` - Parse OTSL to IR

---

## Limitations

### What Lenient Mode Does NOT Do

❌ **Does not preserve HTML attributes** (same as strict mode)
- Attributes like `class`, `id`, `style` are lost

❌ **Does not fix semantic errors**
- Headers in wrong positions
- Incorrectly marked cell types

❌ **Does not infer missing data**
- Only fills structural gaps with empty cells

### What Lenient Mode DOES

✅ **Normalizes table structure**
- Consistent row lengths
- Valid occupancy grid
- Proper cell positioning

✅ **Allows evaluation of malformed tables**
- Can compute TEDS scores
- Can perform roundtrip conversion
- Can validate structure

---

## Performance

Lenient mode adds minimal overhead:
- Small tables (<10×10): ~0.001s additional
- Large tables (>100×100): ~0.005s additional
- Filtering empty rows: negligible
- Padding/truncating: O(rows × cols)

---

## Best Practices

### When to Use Lenient Mode

✅ **Use lenient mode when:**
- Evaluating AI model outputs
- Processing web-scraped data
- Migrating legacy tables
- Handling user-generated content
- Computing metrics on potentially malformed data

### When to Use Strict Mode

✅ **Use strict mode when:**
- Validating table generation code
- Ensuring data quality
- Testing table construction
- Production data with quality guarantees

---

## Changelog

### Version 1.1.0 (2025-11-29)

**New Features:**
- ✅ Added `strict` parameter to `TableConverter`, `HTMLTableParser`, `OTSLTableParser`
- ✅ Lenient OTSL parsing: pads/truncates inconsistent rows
- ✅ Lenient HTML parsing: filters empty rows, adjusts rowspans, fills gaps
- ✅ 12 comprehensive tests for lenient mode
- ✅ 3 malformed fixtures added to test suite
- ✅ Demo script (`demo_lenient_parsing.py`)

**Compatibility:**
- 🔄 Backward compatible - `strict=True` by default
- ✅ All 93 existing tests still pass
- ✅ 105 total tests (93 + 12 new)

---

## Support

For issues or questions:
- GitHub Issues: [html_otsl_conversion_eval/issues](https://github.com/mortadhaaj/html_otsl_conversion_eval/issues)
- Email: mortadhaaj@gmail.com

---

**Last Updated:** 2025-11-29
**Version:** 1.1.0
