# دليل استكشاف أخطاء المزامنة

## 🚨 المشاكل الشائعة وحلولها

### 1. خطأ: UNIQUE constraint failed: holidays.date

**السبب**: محاولة إضافة إجازة بتاريخ موجود بالفعل

**الحل**: تم إضافة فحص التكرار في دالة `add_holiday`

```python
# فحص وجود إجازة بنفس التاريخ
cursor.execute('SELECT id FROM holidays WHERE date = ?', (date_str,))
existing_holiday = cursor.fetchone()

if existing_holiday:
    logger.warning(f"⚠️ إجازة بتاريخ {date_str} موجودة بالفعل")
    return existing_holiday[0]  # إرجاع ID الإجازة الموجودة
```

### 2. خطأ: database is locked

**السبب**: قاعدة البيانات مقفلة بسبب عمليات متعددة

**الحل**: تم تحسين إدارة الاتصالات

```python
# استخدام timeout أطول لتجنب القفل
conn = sqlite3.connect(self.local_db_path, timeout=20.0)
```

### 3. خطأ: المزامنة لا تعمل مع الإجازات والمواقع

**السبب**: عدم وجود دوال المزامنة المطلوبة

**الحل**: تم إضافة جميع الدوال المطلوبة

## 🔧 الإصلاحات المطبقة

### ✅ إضافة دوال الإجازات والمواقع في `supabase_manager.py`
- `add_location()`, `update_location()`, `delete_location()`
- `add_holiday()`, `update_holiday()`, `delete_holiday()`
- `get_all_locations()`, `get_all_holidays()`

### ✅ إضافة دوال المزامنة في `simple_hybrid_manager.py`
- `_sync_locations_from_supabase()`
- `_sync_holidays_from_supabase()`
- دوال المساعدة للفحص والتحديث

### ✅ تحسين إدارة قاعدة البيانات
- فحص التكرار قبل الإضافة
- timeout أطول لتجنب القفل
- معالجة أفضل للأخطاء

## 🧪 اختبار الإصلاحات

### الاختبار البسيط
```bash
python test_sync_fix.py
```

### الاختبار المتقدم
```bash
python test_sync_advanced.py
```

## 📋 خطوات التأكد من عمل المزامنة

### 1. فحص ملف `.env`
تأكد من وجود متغيرات Supabase:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
```

### 2. فحص الاتصال بالإنترنت
- تأكد من وجود اتصال إنترنت مستقر
- تأكد من الوصول إلى Supabase

### 3. فحص قاعدة البيانات المحلية
```bash
# فحص وجود الجداول
sqlite3 attendance.db ".tables"

# فحص محتوى الجداول
sqlite3 attendance.db "SELECT * FROM holidays LIMIT 5;"
sqlite3 attendance.db "SELECT * FROM locations LIMIT 5;"
```

## 🔍 تشخيص المشاكل

### فحص السجلات
```bash
# عرض سجلات النظام
tail -f logs/app.log

# البحث عن أخطاء المزامنة
grep -i "sync\|mزامنة" logs/app.log
```

### فحص حالة المزامنة
```python
from app.database.simple_hybrid_manager import SimpleHybridManager

manager = SimpleHybridManager()

# فحص الإحصائيات
print(manager.detailed_stats)

# فحص حالة المزامنة
print(manager.control_settings)
```

## 🚀 حل المشاكل الشائعة

### المشكلة: المزامنة بطيئة
**الحل**: تقليل فترات المزامنة
```python
self.sync_interval = 1  # مزامنة كل ثانية
self.supabase_sync_interval = 2  # مزامنة من Supabase كل ثانيتين
```

### المشكلة: فشل في المزامنة
**الحل**: زيادة عدد المحاولات
```python
'max_retry_count': 5,  # زيادة عدد المحاولات
```

### المشكلة: قاعدة البيانات مقفلة
**الحل**: إعادة تشغيل التطبيق أو زيادة timeout
```python
conn = sqlite3.connect(self.local_db_path, timeout=30.0)
```

## 📞 الدعم الإضافي

إذا استمرت المشاكل:

1. **راجع السجلات**: `logs/app.log`
2. **تحقق من Supabase**: تأكد من صحة البيانات
3. **أعد تشغيل التطبيق**: لإعادة تهيئة المزامنة
4. **تحقق من الصلاحيات**: تأكد من صلاحيات الكتابة

## 🎯 النتيجة المتوقعة

بعد تطبيق الإصلاحات:
- ✅ المزامنة تعمل مع الإجازات
- ✅ المزامنة تعمل مع المواقع
- ✅ مزامنة ثنائية الاتجاه
- ✅ تحديث تلقائي كل 3 ثوان
- ✅ معالجة الأخطاء والتكرار
