#!/usr/bin/env python3
"""Test the complex OTSL case with lenient mode."""

from src.api.converters import TableConverter

# User's complex OTSL example
otsl_example = """<otsl><has_tbody><loc_0><loc_0><loc_500><loc_500><fcel>جدول1:مؤشرات إحصاءات الطاقة المتجددة (2019-2020)<lcel><lcel><lcel><lcel><lcel><lcel><nl><fcel>المؤشرات<fcel>الوحدة<fcel>الوصف<fcel>المسئول<lcel><lcel><lcel><nl><ucel><ucel><ucel><fcel>GHI(م)<fcel>2019<fcel>2020<ucel><nl><fcel>المؤشرات البيومي للإشعاع الأفقي الكاني (<ecel><ecel><ecel><ecel><ecel><ecel><nl><fcel>مستوى المملكة<fcel>5,916<fcel>5,523<fcel>المنطقة الوسطى<ecel><ecel><ecel><nl><fcel>المنطقة الشرفية<fcel>5,066<fcel>6,066<fcel>واط. ساعة/م2<fcel>5,583<fcel>5,085<fcel>5,582<nl><fcel>المنطقة الجنوبية<fcel>/يوم<fcel>5,935<fcel>5,970<fcel>5,658<fcel>5,654<fcel>5,658<nl><fcel>المنطقة الغربية<fcel>5,954<ucel><ucel><ucel><ucel><ucel><nl><fcel>المنطقة الشمالية<fcel>6,043<fcel>5,138<fcel>المنطقة الشمالية<ecel><ecel><ecel><nl><fcel>المتوسط البيومي للإشعاع العميودي المباشر(DNI)<lcel><lcel><lcel><lcel><lcel><lcel><nl><fcel>مستوى المملكة<fcel>5,559<fcel>5,727<fcel>المنطقة الوسطى<ecel><ecel><ecel><nl><fcel>المنطقة الشرفية<fcel>5,555<fcel>5,863<fcel>واط. ساعة/م2<fcel>5,004<fcel>5,059<fcel>5,059<nl><fcel>المنطقة الجنوبية<fcel>/يوم<fcel>5,032<fcel>5,773<fcel>5,804<fcel>5,543<fcel>5,804<nl><fcel>المنطقة الغربية<fcel>5,543<ucel><ucel><ucel><ucel><ucel><nl><fcel>المنطقة الشمالية<fcel>6,659<fcel>6,136<ucel><ucel><ucel><ucel><nl><fcel>المتوسط البيومي للإشعاع الأفقي المنتشر(DHI)<lcel><lcel><lcel><lcel><lcel><lcel><nl><fcel>مستوى المملكة<fcel>2,153<fcel>1,914<fcel>المنطقة الوسطى<ecel><ecel><ecel><nl><fcel>المنطقة الشرفية<fcel>2,285<fcel>2,086<fcel>واط. ساعة/م2<fcel>2,170<fcel>1,910<fcel>2,170<nl><fcel>المنطقة الجنوبية<fcel>/يوم<fcel>2,410<fcel>2,123<ucel><ucel><ucel><nl><fcel>المنطقة الغربية<fcel>2,162<ucel><ucel><ucel><ucel><ucel><nl><fcel>المنطقة الشمالية<fcel>1,737<fcel>1,546<ucel><ucel><ucel><ucel><nl></otsl>"""

print("Testing OTSL to HTML conversion with lenient mode...")

# Test with strict=False (lenient mode)
print("\n1. Testing with strict=False (lenient mode):")
try:
    converter = TableConverter(strict=False)
    html = converter.otsl_to_html(otsl_example)
    print("✅ SUCCESS! Conversion completed in lenient mode")
    print(f"Generated HTML length: {len(html)} characters")
    print("\nFirst 500 characters of HTML:")
    print(html[:500])
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test with strict=True to see the error
print("\n2. Testing with strict=True (should fail with validation error):")
try:
    converter_strict = TableConverter(strict=True)
    html_strict = converter_strict.otsl_to_html(otsl_example)
    print("⚠️  Unexpectedly succeeded with strict mode")
except ValueError as e:
    print(f"✅ Expected validation error: {str(e)[:200]}...")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n✅ Test completed!")
