# Malformed HTML Edge Case - Fixed

**Issue**: HTML tables with unclosed/malformed tags causing "Table has no rows" error
**Status**: ✅ **FIXED**
**Date**: 2025-11-26

---

## Problem Reported

User provided HTML with Arabic (RTL) text that was failing with error:
```
ValueError: Table has no rows
```

**Problematic HTML**:
```html
<table>
  <caption><div class="caption" dir="rtl">الإيرادات...</caption>  <!-- Missing </div> -->
  <tbody>
    <tr><td dir="rtl">الإسم</td>...</tr>
    ...
  </tbody>
</table>
```

**Issue**: The `<caption>` opens with `<div class="caption" dir="rtl">` but closes with `</caption>` instead of `</div></caption>`.

---

## Root Cause Analysis

### Investigation Results

**lxml parsing** (primary parser):
```
✓ Parsed successfully (no exception)
✗ Tbody elements: 0
✗ TR in tbody: 0
✗ TR direct: 0
```

lxml didn't fail with an exception, but it **misinterpreted the structure** due to the unclosed `<div>`. It treated everything after the malformed caption as part of the caption itself, finding 0 rows.

**html5lib parsing** (fallback parser):
```
✓ Parsed successfully
✓ Tbody elements: 1
✓ TR in tbody: 6  ← Correctly found all rows!
✓ TR direct: 0
```

html5lib successfully parsed the malformed HTML and found all rows.

### Why Fallback Wasn't Working

**Original logic**:
```python
try:
    tree = lxml_html.fromstring(html_str)  # Succeeds but misparses
except Exception as e:
    # Fallback to html5lib
    # ← Never reaches here because lxml didn't raise exception!
```

The html5lib fallback only triggered when lxml raised an **exception**. But in this case, lxml parsed successfully - it just produced an incorrect structure.

---

## Solution Implemented

### Enhanced Fallback Logic

**New approach**: Trigger html5lib fallback in two scenarios:
1. When lxml raises an exception (original behavior)
2. **NEW**: When lxml successfully parses but finds 0 rows (likely misparsed)

```python
# Parse with lxml first
try:
    tree = lxml_html.fromstring(html_str)
except Exception as e:
    # Fallback #1: lxml failed with exception
    tree = parse_with_html5lib_and_convert_to_lxml(html_str)
    used_fallback = True

# Extract rows
all_rows, row_sections = self._extract_rows(table_elem)

# Fallback #2: lxml found no rows (likely misparse)
if not all_rows and not used_fallback:
    try:
        tree = parse_with_html5lib_and_convert_to_lxml(html_str)
        # Re-extract with corrected tree
        table_elem = self._find_table(tree)
        all_rows, row_sections = self._extract_rows(table_elem)
    except Exception:
        pass  # Fallback failed, use original results
```

### html5lib → lxml Conversion Fix

**Problem**: html5lib returns `xml.etree.ElementTree.Element` objects, which don't support XPath. Our code uses XPath extensively, so we need lxml elements.

**Solution**: Serialize html5lib's output and re-parse with lxml:

```python
import xml.etree.ElementTree as ET

# Parse with html5lib
doc = html5lib.parse(html_str, namespaceHTMLElements=False)

# Convert to lxml: serialize then re-parse
html_bytes = ET.tostring(doc, encoding='utf-8', method='html')
tree = lxml_html.fromstring(html_bytes)
```

**Critical**: Must use `xml.etree.ElementTree.tostring()`, NOT `lxml.etree.tostring()`, because lxml's tostring() can't serialize standard library ElementTree elements.

---

## Files Modified

### 1. `src/core/html_parser.py`

**Changes**:
- Import `xml.etree.ElementTree` for proper serialization
- Enhanced fallback logic to trigger on 0 rows found
- Fixed html5lib → lxml conversion using proper serializer

**Key sections**:

```python
# Lines 50-59: Primary fallback (lxml exception)
try:
    tree = lxml_html.fromstring(html_str)
except Exception as e:
    try:
        doc = html5lib.parse(html_str, namespaceHTMLElements=False)
        import xml.etree.ElementTree as ET
        html_bytes = ET.tostring(doc, encoding='utf-8', method='html')
        tree = lxml_html.fromstring(html_bytes)
        used_fallback = True
    except Exception as e2:
        raise ValueError(f"Failed to parse HTML: {e}, fallback also failed: {e2}")

# Lines 75-88: Secondary fallback (0 rows found)
if not all_rows and not used_fallback:
    try:
        doc = html5lib.parse(html_str, namespaceHTMLElements=False)
        import xml.etree.ElementTree as ET
        html_bytes = ET.tostring(doc, encoding='utf-8', method='html')
        tree = lxml_html.fromstring(html_bytes)
        table_elem = self._find_table(tree)
        if table_elem is not None:
            caption_content = self._extract_caption(table_elem)
            has_border = self._has_border(table_elem)
            all_rows, row_sections = self._extract_rows(table_elem)
    except Exception:
        pass
```

### 2. `tests/unit/test_malformed_html.py` (NEW)

**5 new test cases**:

1. **test_unclosed_tag_in_caption**: Tests `<caption><div>...</caption>` (missing `</div>`)
2. **test_arabic_text_with_malformed_caption**: Tests user's exact scenario with RTL text
3. **test_multiple_unclosed_tags**: Tests multiple malformed tags
4. **test_malformed_vs_wellformed_produces_same_result**: Verifies both produce identical IR
5. **test_empty_table_with_malformed_caption**: Ensures empty table still raises error

All tests passing ✓

---

## Test Results

### Unit Tests
```
===== 93 passed in 0.15s =====
- 88 original tests: ✓ All passing
- 5 new malformed HTML tests: ✓ All passing
```

### User's HTML Conversion
```
Step 1: HTML → OTSL conversion
✓ SUCCESS!
  6 rows × 5 columns extracted
  Arabic text preserved

Step 2: OTSL → HTML roundtrip
✓ SUCCESS!
  HTML reconstructed correctly

Step 3: Validation
✓ VALIDATION PASSED!
  Conversion is valid - structures match
```

**Full user HTML**:
```html
<html><body><table>
  <caption><div class="caption" dir="rtl">الإيرادات المتوقعة للتطبيقات الجديدة المُطورة باستخدام دارت في السوق المحلي</caption>
  <tbody>
    <tr><td dir="rtl">الإسم</td><td dir="rtl">الفئة</td>...</tr>
    <tr><td>ChatApp Messenger</td><td dir="rtl">تطبيقات المراسلة</td>...</tr>
    <tr><td>HealthTracker Plus</td>...</tr>
    <tr><td>EduLearn Hub</td>...</tr>
    <tr><td>ShopEase</td>...</tr>
    <tr><td>TravelBuddy</td>...</tr>
  </tbody>
</table></body></html>
```

**Result**:
- ✅ Converts successfully to OTSL
- ✅ 6 rows × 5 columns preserved
- ✅ Arabic/RTL text preserved
- ✅ `dir` attributes handled correctly
- ✅ Roundtrip HTML ↔ OTSL ↔ HTML works perfectly

---

## Edge Cases Covered

The fix now handles:

1. **Unclosed tags in captions**: `<caption><div>text</caption>`
2. **Unclosed tags in cells**: `<td><b>text</td>`
3. **Multiple unclosed tags**: `<caption><div><span>text</caption>`
4. **Arabic/RTL text with malformed HTML**
5. **Mixed well-formed and malformed tags**

All of these scenarios now work via html5lib fallback.

---

## Impact

### What Was Fixed
- ✅ Malformed HTML with unclosed tags now parses correctly
- ✅ Arabic/RTL content with `dir` attributes works
- ✅ html5lib fallback actually works (was broken before)
- ✅ Zero-row misparsing automatically triggers fallback

### What Wasn't Changed
- ✅ No breaking changes to existing functionality
- ✅ All 88 original tests still passing
- ✅ Well-formed HTML continues to use fast lxml parser
- ✅ Only malformed HTML uses html5lib fallback

### Performance
- Well-formed HTML: **No performance impact** (still uses lxml)
- Malformed HTML: Slightly slower (html5lib + serialize + re-parse), but now **works** instead of failing

---

## Git Commits

```
56e57ff Fix: Handle malformed HTML with html5lib fallback
3c816a3 Fix: Update tests for inline HTML tag preservation
fe7a7e7 Fix: Preserve inline HTML tags in bidirectional conversion
```

---

## Summary

✅ **User's reported issue is FIXED**
✅ **HTML with unclosed tags now works**
✅ **Arabic/RTL text fully supported**
✅ **93/93 tests passing (100%)**
✅ **No breaking changes**

The HTML parser is now more robust and handles real-world malformed HTML gracefully.

---

**Test Command**:
```bash
conda activate py311_teds
pytest tests/unit/test_malformed_html.py -v  # New malformed HTML tests
pytest tests/ -q                              # All tests
```

**Example Usage**:
```python
from src.api.converters import TableConverter

# Works even with malformed HTML!
html = '<table><caption><div>Caption</caption><tr><td>A</td></tr></table>'

converter = TableConverter()
otsl = converter.html_to_otsl(html)  # ✓ Now succeeds!
```

**Generated**: 2025-11-26
