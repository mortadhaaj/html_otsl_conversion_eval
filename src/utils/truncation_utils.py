"""
Utilities for handling truncated HTML/OTSL output from AI models.

These utilities help detect and auto-fix truncated table output that occurs
when AI models hit maximum token limits during generation.
"""

import re
from typing import Tuple


def is_html_truncated(html_str: str) -> bool:
    """
    Detect if HTML appears to be truncated.

    Checks for:
    - Missing closing </table> tag
    - Unclosed <tr> or <td> tags
    - Incomplete tag syntax

    Args:
        html_str: HTML string to check

    Returns:
        True if HTML appears truncated

    Example:
        >>> html = "<table><tr><td>A</td></tr>"
        >>> is_html_truncated(html)
        True
    """
    html_lower = html_str.lower()

    # Check for missing </table>
    table_open = html_lower.count("<table")
    table_close = html_lower.count("</table>")
    if table_open > table_close:
        return True

    # Check for unclosed <tr> tags
    tr_open = html_lower.count("<tr")
    tr_close = html_lower.count("</tr>")
    if tr_open > tr_close:
        return True

    # Check for unclosed <td> or <th> tags
    td_open = html_lower.count("<td") + html_lower.count("<th")
    td_close = html_lower.count("</td>") + html_lower.count("</th>")
    if td_open > td_close:
        return True

    # Check if ends with incomplete tag (e.g., "<td", "<td>20")
    if re.search(r'<[a-z]+(?:\s|$)', html_str.strip()[-20:], re.IGNORECASE):
        return True

    return False


def auto_close_html(html_str: str) -> str:
    """
    Automatically add missing closing tags to truncated HTML.

    Note: This is a simple helper. For robust parsing, use the
    lenient mode (strict=False) which uses html5lib for proper
    auto-closing.

    Args:
        html_str: Potentially truncated HTML

    Returns:
        HTML with closing tags added

    Example:
        >>> html = "<table><tr><td>A</td></tr>"
        >>> auto_close_html(html)
        '<table><tr><td>A</td></tr></table>'
    """
    result = html_str

    # Count unclosed tags
    table_open = result.lower().count("<table")
    table_close = result.lower().count("</table>")

    # Add missing </table> tags
    for _ in range(table_open - table_close):
        result += "</table>"

    return result


def is_otsl_truncated(otsl_str: str) -> bool:
    """
    Detect if OTSL appears to be truncated.

    Checks for:
    - Missing closing </otsl> tag
    - Incomplete tag syntax

    Args:
        otsl_str: OTSL string to check

    Returns:
        True if OTSL appears truncated

    Example:
        >>> otsl = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<nl>"
        >>> is_otsl_truncated(otsl)
        True
    """
    stripped = otsl_str.strip()

    # Check for missing </otsl>
    if stripped.startswith("<otsl>") and not stripped.endswith("</otsl>"):
        return True

    # Check for incomplete tag at end
    if re.search(r'<[a-z_]+$', stripped, re.IGNORECASE):
        return True

    return False


def auto_close_otsl(otsl_str: str) -> str:
    """
    Automatically add missing </otsl> tag to truncated OTSL.

    Args:
        otsl_str: Potentially truncated OTSL

    Returns:
        OTSL with closing tag added

    Example:
        >>> otsl = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<nl>"
        >>> auto_close_otsl(otsl)
        '<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<nl></otsl>'
    """
    stripped = otsl_str.strip()

    if stripped.startswith("<otsl>") and not stripped.endswith("</otsl>"):
        return otsl_str + "</otsl>"

    return otsl_str


def detect_truncation(content: str) -> Tuple[bool, str, str]:
    """
    Detect if content is HTML or OTSL and whether it's truncated.

    Args:
        content: String content to analyze

    Returns:
        Tuple of (is_truncated, content_type, reason)
        - is_truncated: True if truncated
        - content_type: 'html', 'otsl', or 'unknown'
        - reason: Description of why it's considered truncated

    Example:
        >>> content = "<table><tr><td>A"
        >>> is_trunc, ctype, reason = detect_truncation(content)
        >>> print(f"{ctype}: {is_trunc} - {reason}")
        html: True - Missing closing </table> tag
    """
    content_lower = content.lower().strip()

    # Determine content type
    if content_lower.startswith("<otsl>"):
        content_type = "otsl"
    elif "<table" in content_lower:
        content_type = "html"
    else:
        return False, "unknown", "Not HTML or OTSL"

    # Check for truncation
    if content_type == "html":
        if is_html_truncated(content):
            # Determine specific reason
            if "</table>" not in content_lower:
                return True, "html", "Missing closing </table> tag"
            elif content_lower.count("<tr") > content_lower.count("</tr>"):
                return True, "html", "Unclosed <tr> tags"
            elif (content_lower.count("<td") + content_lower.count("<th")) > \
                 (content_lower.count("</td>") + content_lower.count("</th>")):
                return True, "html", "Unclosed <td>/<th> tags"
            else:
                return True, "html", "Incomplete tag syntax"
        return False, "html", "Complete HTML"

    elif content_type == "otsl":
        if is_otsl_truncated(content):
            if "</otsl>" not in content:
                return True, "otsl", "Missing closing </otsl> tag"
            else:
                return True, "otsl", "Incomplete tag syntax"
        return False, "otsl", "Complete OTSL"

    return False, "unknown", "Could not determine"


def fix_truncated_output(content: str, auto_fix: bool = True) -> Tuple[str, bool, str]:
    """
    Detect and optionally fix truncated output.

    Args:
        content: HTML or OTSL content
        auto_fix: If True, attempt to auto-close tags

    Returns:
        Tuple of (fixed_content, was_truncated, message)

    Example:
        >>> html = "<table><tr><td>A</td></tr>"
        >>> fixed, truncated, msg = fix_truncated_output(html)
        >>> print(msg)
        Fixed: Added missing </table> tag
    """
    is_truncated, content_type, reason = detect_truncation(content)

    if not is_truncated:
        return content, False, f"No truncation detected ({content_type})"

    if not auto_fix:
        return content, True, f"Truncated: {reason} (not fixed)"

    # Apply auto-fix
    if content_type == "html":
        fixed = auto_close_html(content)
        return fixed, True, f"Fixed: Added missing closing tag(s)"
    elif content_type == "otsl":
        fixed = auto_close_otsl(content)
        return fixed, True, f"Fixed: Added missing </otsl> tag"
    else:
        return content, True, f"Truncated but cannot fix: {reason}"


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Truncation Detection Examples")
    print("=" * 60)

    # Example 1: Truncated HTML
    html1 = "<table><tr><td>A</td><td>B</td></tr>"
    is_trunc, ctype, reason = detect_truncation(html1)
    print(f"\n1. HTML (truncated): {is_trunc}")
    print(f"   Reason: {reason}")

    fixed, was_trunc, msg = fix_truncated_output(html1)
    print(f"   Fix: {msg}")
    print(f"   Result: {fixed}")

    # Example 2: Complete HTML
    html2 = "<table><tr><td>A</td></tr></table>"
    is_trunc, ctype, reason = detect_truncation(html2)
    print(f"\n2. HTML (complete): {is_trunc}")
    print(f"   Reason: {reason}")

    # Example 3: Truncated OTSL
    otsl1 = "<otsl><loc_1><loc_2><loc_3><loc_4><fcel>A<nl>"
    is_trunc, ctype, reason = detect_truncation(otsl1)
    print(f"\n3. OTSL (truncated): {is_trunc}")
    print(f"   Reason: {reason}")

    fixed, was_trunc, msg = fix_truncated_output(otsl1)
    print(f"   Fix: {msg}")
    print(f"   Result: {fixed}")

    print("\n" + "=" * 60)
