from src.api.converters import TableConverter

for filename in ['multi_row_thead', 'complex_merging_tbody', 'complex_merging_thead', 'edge_case_large_spans']:
    html = open(f'tests/fixtures/{filename}.html').read()
    otsl = open(f'tests/fixtures/{filename}.otsl').read()

    converter = TableConverter()
    html_ir = converter.html_to_ir(html)
    otsl_ir = converter.otsl_to_ir(otsl)

    print(f'\n{filename}:')
    print(f'  HTML: {html_ir.num_rows}x{html_ir.num_cols}, {len(html_ir.cells)} cells')
    print(f'  OTSL: {otsl_ir.num_rows}x{otsl_ir.num_cols}, {len(otsl_ir.cells)} cells')

    if len(html_ir.cells) != len(otsl_ir.cells):
        print(f'  ✗ Cell count mismatch!')
        # Show all cells from each
        print(f'  HTML cells:')
        for i, cell in enumerate(html_ir.cells):
            print(f'    {i}: ({cell.row_idx},{cell.col_idx}) span({cell.rowspan},{cell.colspan}) "{cell.content.text[:20] if cell.content else ""}"')
        print(f'  OTSL cells:')
        for i, cell in enumerate(otsl_ir.cells):
            print(f'    {i}: ({cell.row_idx},{cell.col_idx}) span({cell.rowspan},{cell.colspan}) "{cell.content.text[:20] if cell.content else ""}"')
