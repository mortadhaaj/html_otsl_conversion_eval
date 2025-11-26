"""Tests for malformed HTML parsing."""

import pytest
from src.core.html_parser import HTMLTableParser


class TestMalformedHTML:
    """Test parsing of malformed HTML tables."""

    def test_unclosed_tag_in_caption(self):
        """Test parsing HTML with unclosed tag in caption.

        This is a real-world edge case where HTML has:
        <caption><div class="caption">...</caption>
        instead of:
        <caption><div class="caption">...</div></caption>

        The unclosed <div> causes lxml to misparse, but html5lib
        should handle it correctly via fallback.
        """
        # Malformed HTML: <div> opened but not closed in caption
        html = """
        <table>
            <caption><div class="caption" dir="rtl">Table Caption</caption>
            <tbody>
                <tr><td>A</td><td>B</td></tr>
                <tr><td>C</td><td>D</td></tr>
            </tbody>
        </table>
        """

        parser = HTMLTableParser()
        table = parser.parse(html)

        # Should successfully parse despite malformed caption
        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4

        # Caption should be extracted (text from div)
        assert table.caption is not None
        assert "Table Caption" in table.caption.text

    def test_arabic_text_with_malformed_caption(self):
        """Test parsing Arabic text in malformed HTML.

        This is the actual user-reported issue with RTL text
        and unclosed tags.
        """
        html = """
        <table>
            <caption><div class="caption" dir="rtl">الإيرادات المتوقعة</caption>
            <tbody>
                <tr>
                    <td dir="rtl">الإسم</td>
                    <td dir="rtl">الفئة</td>
                </tr>
                <tr>
                    <td>App Name</td>
                    <td dir="rtl">تطبيقات</td>
                </tr>
            </tbody>
        </table>
        """

        parser = HTMLTableParser()
        table = parser.parse(html)

        # Should successfully parse
        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4

        # Arabic text should be preserved (check for any non-empty text)
        first_cell = table.cells[0]
        assert first_cell.content.text  # Text exists
        assert len(first_cell.content.text) > 0  # Not empty

    def test_multiple_unclosed_tags(self):
        """Test HTML with multiple malformed tags."""
        html = """
        <table>
            <caption><div><span>Caption</caption>
            <tr><td><b>Bold</td><td><i>Italic</td></tr>
        </table>
        """

        parser = HTMLTableParser()
        table = parser.parse(html)

        # Should parse successfully via html5lib fallback
        assert table.num_rows == 1
        assert table.num_cols == 2

    def test_malformed_vs_wellformed_produces_same_result(self):
        """Test that malformed and well-formed HTML produce same IR."""
        # Well-formed HTML
        html_good = """
        <table>
            <caption><div class="caption">Test Table</div></caption>
            <tbody>
                <tr><td>A</td><td>B</td></tr>
                <tr><td>C</td><td>D</td></tr>
            </tbody>
        </table>
        """

        # Malformed HTML (missing </div>)
        html_bad = """
        <table>
            <caption><div class="caption">Test Table</caption>
            <tbody>
                <tr><td>A</td><td>B</td></tr>
                <tr><td>C</td><td>D</td></tr>
            </tbody>
        </table>
        """

        parser = HTMLTableParser()
        table_good = parser.parse(html_good)
        table_bad = parser.parse(html_bad)

        # Both should produce same structure
        assert table_good.num_rows == table_bad.num_rows
        assert table_good.num_cols == table_bad.num_cols
        assert len(table_good.cells) == len(table_bad.cells)

        # Caption text should match
        assert table_good.caption.text == table_bad.caption.text

    def test_empty_table_with_malformed_caption(self):
        """Test that empty table with malformed caption still raises error."""
        html = """
        <table>
            <caption><div>Caption</caption>
        </table>
        """

        parser = HTMLTableParser()

        # Should still raise "no rows" error even with fallback
        with pytest.raises(ValueError, match="Table has no rows"):
            parser.parse(html)
