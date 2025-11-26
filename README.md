# HTML ↔ OTSL Table Conversion System

Bidirectional table conversion system between HTML and Docling OTSL formats with LaTeX preservation and TEDS compatibility.

## Features

- **Bidirectional Conversion**: HTML ↔ OTSL with format-agnostic intermediate representation
- **LaTeX Preservation**: Detects and preserves LaTeX formulas ($x^2$, $$...$$, HTML math tags)
- **Complex Table Support**: Handles rowspan, colspan, thead, tbody, tfoot, captions
- **TEDS Compatible**: Normalization options for fair TEDS comparison
- **Comprehensive Testing**: 14+ test cases covering edge cases and complex scenarios

## Project Structure

```
/tmp/table_conversions/
├── src/
│   ├── core/
│   │   ├── table_structure.py    # IR: TableStructure, Cell, CellContent
│   │   ├── html_parser.py        # HTML → IR ✓
│   │   ├── html_builder.py       # IR → HTML ✓
│   │   ├── otsl_parser.py        # OTSL → IR ✓
│   │   ├── otsl_builder.py       # IR → OTSL ✓
│   │   └── latex_handler.py      # LaTeX detection & preservation ✓
│   ├── utils/
│   │   └── constants.py          # OTSL tokens, patterns ✓
│   └── api/
│       ├── converters.py         # High-level API ✓
│       └── teds_utils.py         # TEDS comparison & normalization ✓
├── tests/
│   ├── fixtures/                 # 14 test cases (HTML + OTSL pairs) ✓
│   ├── unit/                     # 6 unit test modules ✓
│   │   ├── test_latex_handler.py
│   │   ├── test_table_structure.py
│   │   ├── test_html_parser.py
│   │   ├── test_otsl_parser.py
│   │   └── test_teds_utils.py
│   ├── integration/              # Integration tests ✓
│   │   └── test_converters.py
│   └── conftest.py               # Pytest fixtures ✓
├── test_bidirectional.py         # Full test suite ✓
├── test_html_roundtrip.py        # HTML roundtrip tests ✓
├── debug_failures.py             # Debugging utility ✓
└── requirements.txt
```

## Test Cases

### Basic Cases
1. **simple_2x2.html** - Simple 2×2 table
2. **vaccination_phases.html** - User-provided example with thead
3. **latex_example.html** - LaTeX formulas

### Advanced Cases
4. **multi_row_thead.html** - Multiple rows in thead with spanning
5. **caption_bottom.html** - Caption positioning with tfoot
6. **complex_merging_tbody.html** - Complex rowspan/colspan in tbody
7. **complex_merging_thead.html** - 3-level thead hierarchy

### Edge Cases
8. **edge_case_empty_cells.html** - Many empty cells
9. **edge_case_single_cell.html** - Single cell table
10. **edge_case_all_headers.html** - Only headers, no data
11. **edge_case_large_spans.html** - Large rowspan (4) and colspan (3)
12. **edge_case_no_thead.html** - Table without thead
13. **edge_case_mixed_headers.html** - th elements in tbody (row headers)
14. **edge_case_latex_complex.html** - Complex LaTeX with superscripts

### Advanced Edge Cases
15. **edge_case_asymmetric.html** - Asymmetric structure with mixed spans (5x4, 11 cells)
16. **edge_case_long_content.html** - Very long text content (research abstracts)
17. **edge_case_max_spanning.html** - Maximum spanning complexity (7x5, 20 cells)
18. **edge_case_large_table.html** - Large table (13x13, 169 cells - multiplication table)

## Current Status

### ✅ Completed
- [x] Project structure
- [x] Intermediate Representation (IR) classes
- [x] LaTeX handler with detection & preservation
- [x] HTML parser with thead/tbody/caption support
- [x] HTML builder with proper structure generation
- [x] OTSL parser with complex spanning support
- [x] OTSL builder with token generation
- [x] High-level API for bidirectional conversion
- [x] 18 comprehensive test cases (HTML + OTSL pairs)
- [x] Full bidirectional conversion (HTML ↔ OTSL) - **18/18 tests passing**
- [x] Pytest unit test suite (65/75 tests passing - 87%)
- [x] TEDS integration with normalization utilities
- [x] Advanced edge cases: asymmetric tables, long content, max spanning, large tables

### 📋 Future Enhancements
- [ ] Fix remaining pytest test failures (attribute naming)
- [ ] Add TEDS validation examples with Python <3.12
- [ ] Performance optimization for large tables
- [ ] Support for nested tables
- [ ] Additional edge case fixtures

## Installation

```bash
pip install -r requirements.txt
```

## Quick Test

### Run bidirectional conversion tests (all formats)
```bash
python test_bidirectional.py
```

Expected output: `✓ ALL TESTS COMPLETED! 14/14 passing`

### Run pytest suite
```bash
pytest tests/ -v
```

Expected output: `65 passed, 10 failed` (87% pass rate)

### TEDS Integration

The system includes TEDS (Tree-Edit-Distance-based Similarity) utilities for comparing table structures:

```python
from src.api.teds_utils import compare_with_teds, normalize_html_for_teds

# Compare two HTML tables
html1 = "<table>...</table>"
html2 = "<table>...</table>"

# With normalization (recommended)
score, message = compare_with_teds(html1, html2, normalize=True)
print(f"TEDS Score: {score:.4f} - {message}")

# Normalize HTML for consistent structure
normalized_html = normalize_html_for_teds(html, ensure_thead=True)
```

**Note**: TEDS requires `table-recognition-metric` package, which only supports Python <3.12. The utilities will work without it installed, but will return informative warnings.

## Key Design Decisions

### Library-First Approach
- Uses docling_core for OTSL parsing (tested, maintained)
- Uses lxml/html5lib for HTML parsing (robust, standards-compliant)
- Extends with custom logic only where needed

### Intermediate Representation
- Format-agnostic bridge between HTML and OTSL
- Enables independent testing of each direction
- Centralized validation and structure checks

### TEDS Normalization
- Default: preserve structure (normalize_for_teds=False)
- Optional: flatten_table() for consistent comparison
- Based on KITAB-Bench approach

## References

- [OTSL Paper (arXiv)](https://arxiv.org/abs/2305.03393)
- [SmolDocling Paper](https://arxiv.org/abs/2503.11576)
- [Docling GitHub](https://github.com/docling-project/docling)
- [table-recognition-metric](https://github.com/SWHL/TableRecognitionMetric)
- [KITAB-Bench](https://github.com/mbzuai-oryx/KITAB-Bench)

## Contributors

- Mortadha AJ (mortadha@gmail.com)
- Implementation based on research from IBM, MBZUAI, and community

## License

TBD
