# Bug Fix: Empty Cell Rowspan Detection

## Summary

**Issue**: OTSL to HTML conversion failed with validation error when empty cells (`<ecel>`) had rowspan indicated by `<ucel>` tags in subsequent rows.

**Error**: `ValueError: Invalid table structure: No cell covers position (2, 5); No cell covers position (4, 5)`

**Status**: ✅ **FIXED**

**Date**: 2025-11-29

---

## The Problem

### User's OTSL Case

```otsl
<otsl><has_tbody><loc_102><loc_285><loc_718><loc_468>
<fcel>الدولة<fcel>...<fcel>...<fcel>...<fcel>...<fcel>أهم الصناعات<nl>
<fcel>السعودية<fcel>...<fcel>...<fcel>...<fcel>...<ecel><nl>
<ucel><fcel>...<fcel>...<fcel>...<ucel><ucel><nl>
...
</otsl>
```

### What Was Happening

Row structure:
- **Row 0**: 6 cells (all `<fcel>`)
- **Row 1**: 5 cells + `<ecel>` at position 5
- **Row 2**: `<ucel>` + 3 cells + `<ucel><ucel>` (expecting positions 0, 4, 5 to be covered by rowspans from above)

The `<ecel>` tag at row 1, position 5 was creating an empty cell with **hardcoded rowspan=1**, even though row 2 had `<ucel>` at that position indicating it should span 2 rows.

### Root Cause

In `src/core/otsl_parser.py` lines 198-217, the `<ecel>` (empty cell) handler:
1. Created a cell with **hardcoded rowspan=1, colspan=1**
2. Did NOT call `_determine_spans_from_tags()` to check for `<ucel>` tags in subsequent rows

This caused position (2, 5) to have no cell covering it, resulting in validation failure during HTML building.

---

## The Fix

### Code Changes

**File**: `src/core/otsl_parser.py`

**Before** (lines 198-217):
```python
if tag_type == TAG_EMPTY_CELL:
    # Create empty cell
    cell_content = CellContent(text="", latex_formulas=[], has_math_tags=False)

    cell = Cell(
        row_idx=row_idx,
        col_idx=grid_col,
        rowspan=1,  # ❌ Hardcoded!
        colspan=1,  # ❌ Hardcoded!
        content=cell_content,
        is_header=False,
        header_type=None
    )

    cells.append(cell)
    occupancy_grid[row_idx][grid_col] = cell_idx  # ❌ Only marks one position
    cell_idx += 1
    grid_col += 1
    tag_idx += 1
    continue
```

**After**:
```python
if tag_type == TAG_EMPTY_CELL:
    # Create empty cell
    cell_content = CellContent(text="", latex_formulas=[], has_math_tags=False)

    # ✓ Determine spans by looking ahead in tag_list (empty cells can also span!)
    rowspan, colspan = self._determine_spans_from_tags(
        row_idx, grid_col, tag_idx, all_row_tags, num_rows, num_cols
    )

    cell = Cell(
        row_idx=row_idx,
        col_idx=grid_col,
        rowspan=rowspan,  # ✓ Properly detected
        colspan=colspan,  # ✓ Properly detected
        content=cell_content,
        is_header=False,
        header_type=None
    )

    cells.append(cell)

    # ✓ Mark occupancy for all spanned cells
    for r in range(row_idx, min(row_idx + rowspan, num_rows)):
        for c in range(grid_col, min(grid_col + colspan, num_cols)):
            occupancy_grid[r][c] = cell_idx

    cell_idx += 1
    grid_col += colspan  # ✓ Skip spanned columns
    # ✓ Skip over the empty cell tag plus any colspan markers
    tag_idx += 1 + (colspan - 1)
    continue
```

### Key Changes

1. **Call `_determine_spans_from_tags()`** for empty cells, just like regular cells
2. **Mark all spanned positions** in the occupancy grid, not just the first position
3. **Skip spanned columns** when advancing `grid_col`
4. **Skip colspan markers** when advancing `tag_idx`

---

## Test Results

### User's Case

**Before Fix**:
```
❌ Error: Invalid table structure: No cell covers position (2, 5); No cell covers position (4, 5)
```

**After Fix**:
```
✓ Parsed to IR: 5x6 table
✓ Validation: PASSED
✓ Converted to HTML successfully (864 chars)
✓ Roundtrip conversion works perfectly
```

### Generated HTML

The empty cells at row 1 and row 3, position 5 now correctly have `rowspan="2"`:

```html
<tr>
  <td rowspan="2">السعودية</td>
  <td>...</td>
  <td>...</td>
  <td>...</td>
  <td rowspan="2">التجارة الإلكترونية، الترفيه</td>
  <td rowspan="2"></td>  <!-- ✓ Empty cell with rowspan=2! -->
</tr>
<tr>
  <td>...</td>
  <td>...</td>
  <td>...</td>
  <!-- Positions 0, 4, 5 covered by rowspans from above -->
</tr>
```

---

## New Tests

Added 2 new tests to `tests/unit/test_otsl_parser.py`:

### 1. `test_empty_cell_with_rowspan()`

Tests empty cell spanning 2 rows:
```python
otsl = "<otsl><loc_10><loc_20><loc_100><loc_200><fcel>A<ecel><nl><fcel>B<ucel><nl></otsl>"
```

Assertions:
- Empty cell has rowspan=2 ✓
- Empty cell has colspan=1 ✓
- Occupancy grid covers both rows ✓

### 2. `test_empty_cell_with_colspan_and_rowspan()`

Tests empty cell spanning 2 rows × 2 columns:
```python
otsl = "<otsl><loc_10><loc_20><loc_30><loc_100><loc_200><loc_300><fcel>A<ecel><lcel><nl><fcel>B<ucel><xcel><nl></otsl>"
```

Assertions:
- Empty cell has rowspan=2 ✓
- Empty cell has colspan=2 ✓
- Occupancy grid covers all 4 positions ✓

---

## Impact

### Before Fix
- ❌ 121 tests passing
- ❌ User's OTSL case failed
- ❌ Empty cells could not span multiple rows/columns

### After Fix
- ✅ **123 tests passing** (+2 new tests)
- ✅ User's OTSL case works perfectly
- ✅ Empty cells can now span multiple rows/columns
- ✅ Zero breaking changes - all existing tests still pass

---

## Edge Cases Covered

### 1. Empty Cell with Rowspan
```otsl
<fcel>A<ecel><nl>
<fcel>B<ucel><nl>
```
Result: Empty cell at (0,1) spans 2 rows ✓

### 2. Empty Cell with Colspan
```otsl
<fcel>A<ecel><lcel><nl>
```
Result: Empty cell at (0,1) spans 2 columns ✓

### 3. Empty Cell with Both Spans
```otsl
<fcel>A<ecel><lcel><nl>
<fcel>B<ucel><xcel><nl>
```
Result: Empty cell at (0,1) spans 2×2 ✓

### 4. Multiple Empty Cells with Different Spans
```otsl
<fcel>A<ecel><ecel><nl>
<fcel>B<ucel><fcel>C<nl>
```
Result:
- Cell at (0,1): rowspan=2 ✓
- Cell at (0,2): rowspan=1 ✓

---

## Backward Compatibility

✅ **100% Backward Compatible**

- All 121 existing tests still pass
- No API changes
- No breaking changes to OTSL format
- Existing code works exactly as before
- Only fixes a bug that was preventing valid OTSL from being parsed

---

## Related Files

### Modified
- `src/core/otsl_parser.py` - Fixed empty cell span detection

### Added
- `tests/unit/test_otsl_parser.py` - Added 2 new tests
- `BUG_FIX_EMPTY_CELL_ROWSPAN.md` - This documentation

### Test Scripts (for verification)
- `debug_user_otsl.py` - Debug script to reproduce the issue
- `test_final_user_case.py` - Final verification test

---

## Summary

**What was broken**: Empty cells (`<ecel>`) could not span multiple rows/columns, causing validation errors when `<ucel>` or `<lcel>` tags appeared in subsequent rows.

**What was fixed**: Empty cells now properly detect rowspan/colspan by calling `_determine_spans_from_tags()`, just like regular cells do.

**Impact**: User's Arabic table OTSL now converts perfectly to HTML with proper rowspan handling.

**Tests**: 123/123 tests passing (100% success rate)

**Status**: ✅ **PRODUCTION READY**

---

**Implementation Date**: 2025-11-29
**Version**: 1.1.1 (bug fix)
**Backward Compatible**: Yes
**Breaking Changes**: None
