# OTSL Format Specification

## Overview

OTSL (Optimized Table Structure Language) is a minimized table structure language that represents table structure with only 5 cell type tokens, reducing sequence length by ~50% compared to HTML.

## Basic Structure

```
<otsl>[<caption>text</caption>]<loc_X><loc_Y><loc_W><loc_H>CONTENT<nl>...</otsl>
```

- `<otsl>` and `</otsl>`: Wrapper tags
- `<caption>text</caption>`: Optional caption (must appear before locations)
- `<loc_N>`: 4 location coordinates for bounding box (x, y, width, height)
- Content: Interleaved tags and cell text
- `<nl>`: Newline marker at end of each row

## Cell Tags

Tags appear **BEFORE** content (not wrapping it). Standalone tags have no content after them.

| Tag | Type | Usage | Example |
|-----|------|-------|---------|
| `<ched>` | Column Header | Before each column header text | `<ched>Name<ched>Age` |
| `<rhed>` | Row Header | Before each row header text | `<rhed>Total` |
| `<fcel>` | Filled Cell | Before each filled cell text | `<fcel>John` |
| `<ecel>` | Empty Cell | Standalone - empty cell | `<ecel>` |
| `<lcel>` | Left Cell | Standalone - colspan continuation | `<lcel>` |
| `<ucel>` | Up Cell | Standalone - rowspan continuation | `<ucel>` |
| `<xcel>` | Cross Cell | Standalone - both spans | `<xcel>` |
| `<nl>` | Newline | End of row marker | `...content<nl>` |

## Examples

### Simple Table (2×2)

**HTML:**
```html
<table>
  <tr><td>A</td><td>B</td></tr>
  <tr><td>C</td><td>D</td></tr>
</table>
```

**OTSL:**
```xml
<otsl><loc_150><loc_280><loc_320><loc_360><fcel>A<fcel>B<nl><fcel>C<fcel>D<nl></otsl>
```

### Table with Headers

**HTML:**
```html
<table>
  <thead>
    <tr><th>Name</th><th>Age</th></tr>
  </thead>
  <tbody>
    <tr><td>John</td><td>25</td></tr>
  </tbody>
</table>
```

**OTSL:**
```xml
<otsl><loc_X><loc_Y><loc_W><loc_H><ched>Name<ched>Age<nl><fcel>John<fcel>25<nl></otsl>
```

### Table with Caption

**HTML:**
```html
<table>
  <caption>Employee Data</caption>
  <tr><td>A</td><td>B</td></tr>
</table>
```

**OTSL:**
```xml
<otsl><caption>Employee Data</caption><loc_X><loc_Y><loc_W><loc_H><fcel>A<fcel>B<nl></otsl>
```

### Colspan Example

**HTML:**
```html
<tr>
  <td colspan="2">Wide Cell</td>
  <td>Normal</td>
</tr>
```

**OTSL:**
```xml
<fcel>Wide Cell<lcel><fcel>Normal<nl>
```

The `<lcel>` tag marks the second column as occupied by the colspan from the left.

### Rowspan Example

**HTML:**
```html
<tr>
  <td rowspan="2">Tall</td>
  <td>A</td>
</tr>
<tr>
  <td>B</td>
</tr>
```

**OTSL:**
```xml
<fcel>Tall<fcel>A<nl>
<ucel><fcel>B<nl>
```

The `<ucel>` tag marks the first column of row 2 as occupied by rowspan from above.

### Complex Spanning (Row+Col)

**HTML:**
```html
<tr>
  <td rowspan="2" colspan="2">Large</td>
  <td>A</td>
</tr>
<tr>
  <td>B</td>
</tr>
```

**OTSL:**
```xml
<fcel>Large<lcel><fcel>A<nl>
<ucel><xcel><fcel>B<nl>
```

- Position (0,0): `<fcel>Large` - cell originates here
- Position (0,1): `<lcel>` - occupied by colspan from left
- Position (1,0): `<ucel>` - occupied by rowspan from above
- Position (1,1): `<xcel>` - occupied by BOTH rowspan and colspan

### Empty Cells

**HTML:**
```html
<tr>
  <td>A</td>
  <td></td>
  <td>C</td>
</tr>
```

**OTSL:**
```xml
<fcel>A<ecel><fcel>C<nl>
```

### Mixed Row Headers

**HTML:**
```html
<thead>
  <tr><th>Category</th><th>Value</th></tr>
</thead>
<tbody>
  <tr><th>Revenue</th><td>$100k</td></tr>
</tbody>
```

**OTSL:**
```xml
<ched>Category<ched>Value<nl>
<rhed>Revenue<fcel>$100k<nl>
```

## Key Rules

1. **Tags precede content**: `<ched>Text` not `<ched>Text</ched>`
2. **No closing tags for cells**: Only `</otsl>` and `</caption>` close
3. **Spanning cells**: Use standalone tags (`<lcel>`, `<ucel>`, `<xcel>`) at occupied positions
4. **Row termination**: Every row ends with `<nl>`
5. **Caption placement**: Must appear before location tags if present
6. **Location tags**: Always 4 coordinates after opening `<otsl>` tag

## References

- [OTSL Paper (arXiv:2305.03393)](https://arxiv.org/abs/2305.03393)
- [SmolDocling Paper (arXiv:2503.11576)](https://arxiv.org/abs/2503.11576)
- [Docling Documentation](https://docling-project.github.io/docling/)
