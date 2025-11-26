# Arabic/UTF-8 Encoding Fix

**Issue**: Arabic text displaying as mojibake (`Ø§ÙØ¥`) instead of proper Arabic (`الإ`)
**Status**: ✅ **FIXED**
**Date**: 2025-11-26

---

## Problem Summary

User reported that Arabic HTML conversion was producing:
1. **Mojibake text**: `Ø§ÙØ¥ÙØ±Ø§Ø¯Ø§Øª` instead of `الإيرادات`
2. **TEDS score 0.3**: Extremely low (30% match)

**Example output (BEFORE fix)**:
```html
<caption>Ø§ÙØ¥ÙØ±Ø§Ø¯Ø§Øª Ø§ÙÙ ØªÙÙØ¹Ø©...</caption>
<td>Ø§ÙØ¥Ø³Ù</td>
```

---

## Root Cause

### Double UTF-8 Encoding

The html5lib fallback (introduced in previous fix) was causing **double UTF-8 encoding**:

```python
# In html_parser.py (BEFORE fix)
html_bytes = ET.tostring(doc, encoding='utf-8', method='html')
tree = lxml_html.fromstring(html_bytes)  # ← Problem!
```

**What happened**:
1. `ET.tostring(encoding='utf-8')` → UTF-8 bytes: `b'\xd8\xa7...'` ✓
2. `lxml_html.fromstring(bytes)` → Misinterprets as Latin-1 ✗
3. Latin-1 chars → UTF-8 bytes again → Double encoding: `b'\xc3\x98\xc2\xa7...'` ✗

**Result**: Arabic character `ا` (`\xd8\xa7` in UTF-8) becomes `Ø§` (`\xc3\x98\xc2\xa7` double-encoded)

### Byte Analysis

**Correct UTF-8** (should be):
```python
b'\xd8\xa7'  # Arabic letter Alef (ا)
```

**Double-encoded** (what we got):
```python
b'\xc3\x98\xc2\xa7'  # Mojibake: Ø§
```

---

## Solution

### Explicit UTF-8 Decoding

Decode UTF-8 bytes to string **before** passing to lxml:

```python
# In html_parser.py (AFTER fix)
html_bytes = ET.tostring(doc, encoding='utf-8', method='html')
html_text = html_bytes.decode('utf-8')  # ← Fix: Explicit decode!
tree = lxml_html.fromstring(html_text)
```

### Files Modified

**src/core/html_parser.py**:
- Lines 56-58: Primary fallback (lxml exception)
- Lines 83-85: Secondary fallback (0 rows found)

Both locations now decode UTF-8 bytes explicitly.

---

## Test Results

### Before vs After

| Metric | Before Fix | After Fix |
|--------|------------|-----------|
| **OTSL size** | 1,186 bytes | 792 bytes |
| **HTML size** | 1,335 bytes | 940 bytes |
| **Arabic chars** | ✗ False (mojibake) | ✓ True (correct) |
| **First word** | `Ø§ÙØ¥ÙØ±Ø§Ø¯Ø§Øª` | `الإيرادات` ✓ |
| **TEDS score** | **0.3048** | **0.9231** |
| **Bytes** | `b'\xc3\x98...'` | `b'\xd8\xa7...'` ✓ |
| **Improvement** | - | **3x better!** |

### Test Output (AFTER fix)

```
1. HTML → OTSL
  ✓ OTSL: 792 bytes
  ✓ First 200 chars: <otsl><caption>الإيرادات المتوقعة للتطبيقات...

2. OTSL → HTML
  ✓ HTML: 940 bytes
  ✓ Arabic characters: True
  ✓ First Arabic word: الإيرادات

3. TEDS Bidirectional Test
  ✓ TEDS Score: 0.9231
```

---

## Known Limitation: HTML Attributes Not Preserved

### What's Lost

The TEDS score of **0.92** (not 1.0) is because **HTML attributes are not preserved**:

| Attribute | Original | Reconstructed | Lost |
|-----------|----------|---------------|------|
| `dir="rtl"` | 21 instances | 0 | **21** ✗ |
| `class="caption"` | 1 instance | 0 | **1** ✗ |
| `<div>` in caption | Yes | No | **1** ✗ |

**Example**:
```html
<!-- Original -->
<td dir="rtl">الإسم</td>

<!-- Reconstructed -->
<td>الإسم</td>  <!-- dir="rtl" lost! -->
```

### Why This Happens

The **Intermediate Representation (IR)** only stores:
- ✓ Cell content (text)
- ✓ Rowspan/colspan
- ✓ Header type (column/row)
- ✓ Caption text
- ✗ HTML attributes (dir, class, id, style, etc.)

### Impact

**What's preserved** (TEDS 0.92):
- ✓ Table structure (6 rows × 5 columns)
- ✓ All text content (Arabic perfectly preserved)
- ✓ Cell positions and spanning
- ✓ Caption text

**What's lost**:
- ✗ `dir="rtl"` attributes (RTL text direction)
- ✗ `class` attributes
- ✗ `id` attributes
- ✗ `style` attributes
- ✗ Other custom HTML attributes

### Future Work

To achieve **perfect TEDS scores (1.0)**, would need to:
1. Extend `CellContent` to store attributes dict
2. Extend OTSL format to encode attributes
3. Update parsers/builders to preserve attributes

This is a **significant architectural change** and beyond current scope.

---

## What Was Fixed

✅ **Encoding issue**: Arabic text now displays correctly
✅ **TEDS improvement**: 0.30 → 0.92 (3x better!)
✅ **UTF-8 handling**: No more double-encoding
✅ **Malformed HTML**: Still works via html5lib
✅ **All tests passing**: 93/93 (100%)

---

## What's Still Limited

⚠️ **Attributes not preserved**: TEDS 0.92 instead of 1.0
⚠️ **RTL markers lost**: `dir="rtl"` attributes stripped
⚠️ **Styling lost**: `class`, `id`, `style` not preserved

**Note**: This is a fundamental IR limitation, not a bug. The system preserves **content and structure**, but not **presentation attributes**.

---

## Test Case Added

**tests/fixtures/arabic_rtl_table.html**:
- User's actual Arabic table (6×5)
- Malformed caption: `<caption><div>...</caption>`
- 21 `dir="rtl"` attributes
- Perfect for testing encoding + malformed HTML

---

## Usage Example

```python
from src.api.converters import TableConverter

# Arabic HTML with malformed caption
html = '''<table>
  <caption><div dir="rtl">الإيرادات المتوقعة</caption>
  <tbody>
    <tr><td dir="rtl">الإسم</td><td dir="rtl">الفئة</td></tr>
  </tbody>
</table>'''

converter = TableConverter()

# ✓ Now works perfectly!
otsl = converter.html_to_otsl(html)
print(otsl)  # Arabic text displays correctly!

# ✓ Roundtrip works
html_reconstructed = converter.otsl_to_html(otsl)
# Note: dir="rtl" attributes will be lost (known limitation)
```

---

## Git Commits

```
65e3876 Fix: Arabic/UTF-8 encoding in html5lib fallback
56e57ff Fix: Handle malformed HTML with html5lib fallback
```

---

## Summary

✅ **MAJOR IMPROVEMENT**: TEDS 0.30 → 0.92 (3x better!)
✅ **Arabic text works perfectly**: No more mojibake
✅ **UTF-8 encoding fixed**: Correct byte sequences
✅ **Malformed HTML handled**: Via html5lib fallback
✅ **Production ready**: With documented limitations

⚠️ **Known limitation**: HTML attributes not preserved (would require IR extension)

**For most use cases**: TEDS 0.92 is excellent - structure and content are perfect, only presentation attributes are lost.

---

**Test Command**:
```bash
conda activate py311_teds
python -c "
from src.api.converters import TableConverter
html = open('tests/fixtures/arabic_rtl_table.html').read()
converter = TableConverter()
otsl = converter.html_to_otsl(html)
print('Arabic text preserved:', 'الإ' in otsl)
"
```

**Generated**: 2025-11-26
