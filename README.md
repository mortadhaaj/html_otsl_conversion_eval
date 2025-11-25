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
│   │   ├── html_parser.py        # HTML → IR
│   │   ├── html_builder.py       # IR → HTML
│   │   ├── otsl_parser.py        # OTSL → IR (TODO)
│   │   ├── otsl_builder.py       # IR → OTSL (TODO)
│   │   └── latex_handler.py      # LaTeX detection & preservation
│   ├── utils/
│   │   ├── html_normalizer.py    # TEDS normalization (TODO)
│   │   ├── validation.py         # Structure validation (TODO)
│   │   └── constants.py          # OTSL tokens, patterns
│   └── api/
│       ├── converters.py         # High-level API (TODO)
│       └── teds_utils.py         # TEDS comparison (TODO)
├── tests/
│   ├── fixtures/                 # 14 test cases (HTML + OTSL)
│   ├── unit/                     # Component tests (TODO)
│   └── integration/              # Roundtrip & TEDS tests (TODO)
├── examples/                     # Usage examples (TODO)
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

## Current Status

### ✅ Completed (Iteration 1)
- [x] Project structure
- [x] Intermediate Representation (IR) classes
- [x] LaTeX handler with detection & preservation
- [x] HTML parser with thead/tbody/caption support
- [x] HTML builder with proper structure generation
- [x] 14 comprehensive test cases (HTML + OTSL)
- [x] HTML → IR → HTML roundtrip verified

### 🚧 In Progress (Iteration 2)
- [ ] OTSL parser using docling_core utilities
- [ ] OTSL builder with token generation
- [ ] High-level API for bidirectional conversion
- [ ] Full bidirectional tests (HTML ↔ OTSL)

### 📋 Planned (Iteration 3)
- [ ] TEDS normalization validation
- [ ] HTML normalizer (flatten_table, etc.)
- [ ] TEDS comparison utilities
- [ ] Unit tests for all components

## Installation

```bash
pip install -r requirements.txt
```

## Quick Test

```bash
python test_html_roundtrip.py
```

Expected output:
```
=== Testing Simple 2x2 Table ===
Parsed: TableStructure(2x2, 4 cells)
✓ All tests completed successfully!
```

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
