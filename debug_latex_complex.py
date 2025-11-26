"""Debug script for edge_case_latex_complex.html conversion."""

from src.api.converters import TableConverter
from src.api.teds_utils import TEDSCalculator
from pathlib import Path

# Read the original HTML
html_file = Path('tests/fixtures/edge_case_latex_complex.html')
original_html = html_file.read_text()

print("=== Original HTML ===")
print(original_html)
print()

# Convert HTML → OTSL
converter = TableConverter()
otsl_result = converter.html_to_otsl(original_html)

print("=== OTSL (intermediate) ===")
print(otsl_result)
print()

# Convert OTSL → HTML
reconstructed_html = converter.otsl_to_html(otsl_result)

print("=== Reconstructed HTML ===")
print(reconstructed_html)
print()

# Compare specific cell content
print("=== Checking specific content ===")
if '<sup>' in original_html:
    print("✓ Original HTML contains <sup> tags")
else:
    print("✗ Original HTML missing <sup> tags")

if '<sup>' in otsl_result:
    print("✓ OTSL contains <sup> tags")
else:
    print("✗ OTSL missing <sup> tags")

if '<sup>' in reconstructed_html:
    print("✓ Reconstructed HTML contains <sup> tags")
else:
    print("✗ Reconstructed HTML missing <sup> tags")

# Extract the specific line with superscripts
import re
original_match = re.search(r'E = mc.*?</td>', original_html, re.DOTALL)
recon_match = re.search(r'E = mc.*?</td>', reconstructed_html, re.DOTALL)

if original_match:
    print(f"\nOriginal line: {original_match.group()}")
if recon_match:
    print(f"Reconstructed line: {recon_match.group()}")

# TEDS comparison
teds_calc = TEDSCalculator()
if teds_calc.is_available():
    score = teds_calc.compute_score(reconstructed_html, original_html)
    print(f"\n=== TEDS Score: {score:.4f} ===")
    if score >= 0.99:
        print("✓ PERFECT TEDS score (≥ 0.99)!")
    else:
        print(f"✗ TEDS score below threshold: {score:.4f} < 0.99")
else:
    print("\n✗ TEDS not available")
