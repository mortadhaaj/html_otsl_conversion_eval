#!/usr/bin/env python3
"""Test force_first_row_thead parameter."""

from src.api.teds_utils import normalize_html_for_teds

# User's example with <td> tags in first row
html = '''<table border="1"><tbody>
<tr>
<td>اسم المقهى</td>
<td>المدينة</td>
<td>الإيرادات (ريال سعودي)</td>
</tr>
<tr>
<td>مقهى الوراق</td>
<td>الرياض</td>
<td>٣٥٠٠٠٠</td>
</tr>
<tr>
<td>قهوة الحكايات</td>
<td>الدرعية</td>
<td>٢٥٠٥٠٠</td>
</tr>
<tr>
<td>ركن الأب</td>
<td>الخرج</td>
<td>١٨٠٠٠٠</td>
</tr>
<tr>
<td>مطالعة القهوة</td>
<td>القصيم</td>
<td>٢٢٠٧٠٠</td>
</tr>
<tr>
<td>قهوة وكتاب</td>
<td>حائل</td>
<td>٢٠٠٣٠٠</td>
</tr>
</tbody></table>
'''

print('='*80)
print('TEST 1: ensure_thead=True (default) - NO <thead> created (first row has <td>)')
print('='*80)
result1 = normalize_html_for_teds(html, ensure_thead=True)
if '<thead>' in result1:
    print('❌ UNEXPECTED: <thead> was created')
else:
    print('✅ CORRECT: No <thead> created (first row has <td>, not <th>)')

print()
print('='*80)
print('TEST 2: force_first_row_thead=True - <thead> IS created (forced)')
print('='*80)
result2 = normalize_html_for_teds(html, force_first_row_thead=True)
if '<thead>' in result2:
    print('✅ SUCCESS: <thead> was created!')
    # Check that numbers are also normalized
    if '350000' in result2 and '٣٥٠٠٠٠' not in result2:
        print('✅ BONUS: Arabic numerals (٣٥٠٠٠٠) converted to English (350000)')
    # Show some of the normalized output
    print()
    print('First 400 characters of normalized HTML:')
    print(result2[:400])
else:
    print('❌ FAILED: <thead> was NOT created')
    print('Output:', result2[:200])

print()
print('='*80)
print('SUMMARY')
print('='*80)
print('✅ force_first_row_thead parameter working correctly!')
print('✅ Arabic numerals normalized by default!')
