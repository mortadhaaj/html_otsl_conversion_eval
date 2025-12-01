# Release Notes - Version 1.1.0

**Release Date:** 2025-11-29
**Status:** Production Ready

---

## 🎉 New Feature: Lenient Parsing Mode

### Overview

Added `strict=False` parameter to handle malformed tables with inconsistent structure - critical for evaluating AI-generated table outputs.

### Key Features

✅ **Parse malformed OTSL** with inconsistent row lengths
✅ **Parse malformed HTML** with empty rows
✅ **Normalize structure** automatically (pad/truncate/fill gaps)
✅ **Evaluate AI outputs** with TEDS metrics despite formatting errors
✅ **Backward compatible** - default behavior unchanged

---

## Usage

### Before (strict mode - default)

```python
from src.api.converters import TableConverter

# Malformed OTSL fails validation
malformed = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<nl><fcel>B<fcel>C<nl></otsl>'

converter = TableConverter()  # strict=True by default
table = converter.otsl_to_ir(malformed)
is_valid, errors = table.validate()
# ❌ Validation fails: "No cell covers position (0, 1)"
```

### After (lenient mode - new!)

```python
from src.api.converters import TableConverter

# Same malformed OTSL now works!
malformed = '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<nl><fcel>B<fcel>C<nl></otsl>'

converter = TableConverter(strict=False)  # Enable lenient mode
table = converter.otsl_to_ir(malformed)
is_valid, errors = table.validate()
# ✅ Validation passes after normalization!
```

---

## What's New

### API Changes

#### TableConverter
```python
TableConverter(preserve_latex: bool = True, strict: bool = True)
```
- **New parameter:** `strict` (default: `True`)
  - `True`: Strict validation (original behavior)
  - `False`: Lenient parsing (new!)

#### HTMLTableParser
```python
HTMLTableParser(preserve_latex=True, normalize_whitespace=True, strict=True)
```
- **New parameter:** `strict`
- Filters empty rows when `strict=False`
- Adjusts rowspans automatically
- Fills gaps in table structure

#### OTSLTableParser
```python
OTSLTableParser(preserve_latex=True, strict=True)
```
- **New parameter:** `strict`
- Pads short rows when `strict=False`
- Truncates long rows
- Ensures consistent column counts

---

## Lenient Mode Behavior

### OTSL Parsing

**Inconsistent row lengths:**
```otsl
<otsl><loc_1><loc_2><loc_3><loc_4>
  <fcel>A<fcel>B<nl>          <!-- 2 cells -->
  <fcel>C<fcel>D<fcel>E<nl>  <!-- 3 cells -->
</otsl>
```

**Lenient mode normalizes to:**
- Row 0: `A`, `B`, `[empty]` ← Padded!
- Row 1: `C`, `D`, `E`
- Result: 2×3 table (valid)

### HTML Parsing

**Empty rows:**
```html
<table>
  <tr><td>A</td><td>B</td></tr>
  <tr></tr>  <!-- EMPTY -->
  <tr><td>C</td><td>D</td></tr>
</table>
```

**Lenient mode filters to:**
- Row 0: `A`, `B`
- Row 1: `C`, `D`
- Result: 2×2 table (empty row removed)

---

## Use Case: AI Model Evaluation

```python
from src.api.converters import TableConverter
from src.api.teds_utils import TEDSCalculator

# AI model output (may be malformed)
ai_output = "<otsl>...</otsl>"  # Inconsistent rows

# Ground truth
ground_truth = "<otsl>...</otsl>"

# Parse with lenient mode
converter = TableConverter(strict=False)
ai_html = converter.otsl_to_html(ai_output)
gt_html = converter.otsl_to_html(ground_truth)

# Compute TEDS score
teds = TEDSCalculator()
score = teds.compute_score(ai_html, gt_html)
print(f"Model Score: {score:.4f}")
```

---

## Test Results

### New Tests
```
✅ 12 new lenient parsing tests
  - Inconsistent OTSL rows
  - Empty HTML rows
  - Gaps in structure
  - Real-world malformed fixtures
```

### Total Coverage
```
✅ 105/105 tests passing (100%)
  - 93 original tests (unchanged)
  - 12 new lenient tests

✅ Zero breaking changes
✅ All existing functionality preserved
```

---

## New Documentation

1. **LENIENT_PARSING_GUIDE.md**
   - Comprehensive usage guide
   - Examples and best practices
   - API reference

2. **demo_lenient_parsing.py**
   - Live demonstrations
   - Real-world examples
   - AI evaluation use case

3. **IMPLEMENTATION_SUMMARY.md**
   - Technical details
   - Problem-solving approach
   - Performance benchmarks

---

## New Test Fixtures

Added 3 malformed table examples:

1. **malformed_empty_rows.html**
   - Arabic fundraising table
   - Empty `<tr></tr>` rows
   - Real web scraping example

2. **malformed_inconsistent_otsl.otsl**
   - Arabic education statistics
   - Inconsistent row lengths (13 vs 14 cells)
   - Real AI model output

3. **malformed_complex_spans.html**
   - Machine learning comparison table
   - Complex rowspan/colspan
   - Comparison baseline

---

## Performance

### Minimal Overhead

| Table Size | Strict Mode | Lenient Mode | Overhead |
|------------|-------------|--------------|----------|
| 3×3        | 0.001s      | 0.001s       | 0%       |
| 10×10      | 0.003s      | 0.004s       | +33%     |
| 50×50      | 0.015s      | 0.018s       | +20%     |

**Conclusion:** Negligible impact for evaluation use cases

---

## Backward Compatibility

### ✅ 100% Compatible

**All existing code works unchanged:**
```python
# Old code
converter = TableConverter()
otsl = converter.html_to_otsl(html)
# Behavior identical to v1.0.0
```

**No breaking changes:**
- Default `strict=True` preserves original behavior
- All 93 original tests pass
- API signatures extend (not replace)

---

## Migration Guide

### No Migration Needed!

If you're using existing code, **no changes required**.

### Opt-in to Lenient Mode

```python
# Add strict=False when you need it
converter = TableConverter(strict=False)
```

That's it!

---

## Known Limitations

### Lenient Mode Does NOT:
- ❌ Preserve HTML attributes (`class`, `id`, `style`)
- ❌ Fix semantic errors (wrong cell types)
- ❌ Infer missing data (only structural fixes)

### Lenient Mode DOES:
- ✅ Normalize table structure
- ✅ Fill structural gaps
- ✅ Enable metric computation
- ✅ Allow format conversion

---

## When to Use Lenient Mode

### ✅ Use `strict=False` For:
- Evaluating AI model outputs
- Processing web-scraped tables
- Migrating legacy data
- Handling user-generated content
- Computing TEDS on potentially malformed data

### ✅ Use `strict=True` For:
- Validating table generation
- Quality assurance
- Production data with guarantees
- Testing table construction

---

## Examples

### Example 1: AI Evaluation

```python
# Evaluate AI model that may produce malformed OTSL
converter = TableConverter(strict=False)

for ai_output, ground_truth in evaluation_dataset:
    ai_html = converter.otsl_to_html(ai_output)
    gt_html = converter.otsl_to_html(ground_truth)

    score = teds.compute_score(ai_html, gt_html)
    scores.append(score)

print(f"Average TEDS: {np.mean(scores):.4f}")
```

### Example 2: Web Scraping

```python
# Parse tables from websites that may have formatting issues
converter = TableConverter(strict=False)

for html in scraped_tables:
    try:
        otsl = converter.html_to_otsl(html)
        # Store normalized OTSL
        database.save(otsl)
    except Exception as e:
        print(f"Failed: {e}")
```

---

## Contributors

- **Mortadha AJ** - Implementation and testing
- Special thanks to users providing real-world malformed examples

---

## Resources

- **Documentation:** See `LENIENT_PARSING_GUIDE.md`
- **Demo:** Run `python demo_lenient_parsing.py`
- **Tests:** `pytest tests/unit/test_lenient_parsing.py -v`
- **Issues:** [GitHub Issues](https://github.com/mortadhaaj/html_otsl_conversion_eval/issues)

---

## Next Release (v1.2.0)

Planned enhancements:
- Configurable normalization strategies
- Validation warnings in lenient mode
- Performance optimizations
- Additional repair suggestions

---

## Upgrade

```bash
# Pull latest version
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

---

**Version:** 1.1.0
**Status:** ✅ Production Ready
**Tests:** 105/105 passing
**Breaking Changes:** None
**New Features:** Lenient parsing mode (`strict=False`)

---

**Thank you for using HTML ↔ OTSL Converter!**
