# 🚀 نظام الحضور والانصراف المتطور - Employee Attendance System

## 📋 جدول المحتويات
- [🌟 نظرة عامة](#-نظرة-عامة)
- [✨ المميزات](#-المميزات)
- [💻 التقنيات المستخدمة](#-التقنيات-المستخدمة)
- [🚀 البدء السريع](#-البدء-السريع)
- [📚 الوثائق](#-الوثائق)
- [🔧 الإعدادات](#-الإعدادات)
- [🌐 النشر](#-النشر)
- [🤝 المساهمة](#-المساهمة)

---

## 🌟 نظرة عامة

نظام شامل ومتطور لإدارة الحضور والانصراف يجمع بين:
- **🌐 واجهة ويب** للموظفين (Flask)
- **💻 تطبيق سطح مكتب** للمديرين (PyQt6)
- **🗄️ قاعدة بيانات هجينة** (SQLite + Supabase)
- **🤖 ذكاء اصطناعي** للتحليل والتقارير

بدلاً من الاعتماد على أجهزة البصمة الفيزيائية، يستخدم النظام "بصمة الجهاز" لربط الموظف بأجهزته المحمولة بشكل آمن.

---

## ✨ المميزات

### 🌐 واجهة الويب للموظفين
- ✅ تسجيل الحضور والانصراف عبر الهاتف
- ✅ تتبع الموقع GPS مع إحداثيات دقيقة
- ✅ بصمة الجهاز الآمنة لمنع التسجيل بالنيابة
- ✅ دعم متعدد اللغات (عربي/إنجليزي)

### 💻 لوحة تحكم المدير
- ✅ عرض الحضور في الوقت الفعلي
- ✅ حساب التأخير تلقائياً
- ✅ إدارة الموظفين والمواقع
- ✅ تقارير مفصلة وتصدير Excel
- ✅ دعم السمات (فاتح/داكن)

### 🔄 نظام المزامنة المتقدم
- ✅ مزامنة فورية كل 2-3 ثوانِ
- ✅ دعم الاتصال المتقطع
- ✅ قاعدة بيانات محلية + سحابية
- ✅ إعادة المحاولة التلقائية

---

## 💻 التقنيات المستخدمة

- **Backend**: Python 3.8+, Flask
- **Desktop GUI**: PyQt6 (محدث ومحسن)
- **Database**: SQLite (محلي) + PostgreSQL (Supabase)
- **AI & Analytics**: Google Generative AI, LangChain, Pandas
- **Reports**: openpyxl, matplotlib, plotly
- **Security**: bcrypt, JWT
- **Project Status**: ✅ نظيف ومنظم

---

## 🚀 البدء السريع

### المتطلبات
- Python 3.8 أو أحدث
- pip (مثبت حزم Python)

### التثبيت
```bash
# 1. استنساخ المشروع
git clone <repository-url>
cd Fingerprint-Attendance-System

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. نسخ ملف الإعدادات
cp env.example .env
# تعديل .env بإعداداتك
```

### التشغيل
```bash
# Terminal 1: تشغيل خادم الويب
python web_app.py

# Terminal 2: تشغيل تطبيق المدير
python start_app.py
```

### بيانات الدخول
- **اسم المستخدم**: `admin`
- **كلمة المرور**: `admin`

---

## 📚 الوثائق

جميع الوثائق التفصيلية موجودة في مجلد `docs/`:

- 📖 [دليل الإعداد الكامل](docs/COMPLETE_SETUP_GUIDE.md)
- 🚀 [دليل النشر](docs/DEPLOYMENT.md)
- ⚡ [دليل تحسين الأداء](docs/PERFORMANCE_SOLUTIONS_GUIDE.md)
- 🔧 [دليل النظام الهجين](docs/SIMPLE_HYBRID_SYSTEM_README.md)
- 📊 [تقرير التحكم الكامل](docs/COMPLETE_CONTROL_SYSTEM_REPORT.md)
- 🎯 [حالة المشروع](docs/PROJECT_STATUS.md)

---

## 🔧 الإعدادات

### المتغيرات البيئية الأساسية
```bash
# قاعدة البيانات
SQLITE_FILE=attendance.db
DATABASE_URL=postgresql://...

# Supabase (للمزامنة)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# التحديثات
GITHUB_OWNER=your-username
GITHUB_REPO=your-repo-name
```

### النظام الهجين
```bash
# تفعيل المزامنة مع Supabase
HYBRID_MODE=true
NEXT_PUBLIC_SUPABASE_URL=https://...
```

---

## 🌐 النشر

### النشر على VPS
```bash
# سكريبت التثبيت التلقائي
curl -fsSL https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/deploy/install_vps.sh | bash -s -- \
  --repo-url https://github.com/YOUR_USER/YOUR_REPO.git \
  --domain your-domain.com \
  --db-url "postgresql://attendance:strongpass@127.0.0.1:5432/attendance"
```

### إعداد SSL
```bash
sudo certbot --nginx -d your-domain.com --non-interactive --agree-tos --email your-email@example.com
```

---

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:
1. Fork المشروع
2. إنشاء branch للميزة الجديدة
3. Commit التغييرات
4. Push إلى Branch
5. فتح Pull Request

---

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT.

---

## 📞 الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- افتح issue على GitHub repository
- راجع الوثائق في مجلد `docs/`
- تحقق من السجلات للتشخيص

---

## 🎉 المشروع جاهز للاستخدام!

**تاريخ الإكمال**: 23 أغسطس 2025  
**تاريخ التنظيف**: 23 أغسطس 2025  
**حالة المشروع**: ✅ مكتمل ومحسن ونظيف ومنظم  
**الأداء**: ⚡ محسن بشكل كبير  
**الحالة**: 🚀 جاهز للإنتاج  
**الملفات المحذوفة**: 70+ ملف مكرر واختبار قديم  
**المساحة المحررة**: ~3-4 MB