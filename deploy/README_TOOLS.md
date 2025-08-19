# أدوات النشر والبناء - دليل الاستخدام

## 🔧 `build_all.py` - أداة البناء والنشر

### الوظائف الرئيسية:
- بناء المثبتات باستخدام PyInstaller و Inno Setup
- رفع المثبتات إلى GitHub Releases
- إنشاء ملفات .env.example
- إدارة GitHub tokens

### الاستخدام:

#### 1. إنشاء ملف .env.example:
```bash
python deploy/build_all.py --create-env
```

#### 2. بناء المثبتات فقط:
```bash
python deploy/build_all.py --skip-upload
```

#### 3. رفع المثبتات إلى GitHub:
```bash
# باستخدام token من متغير البيئة
export GITHUB_TOKEN="your-token-here"
python deploy/build_all.py --github-repo YOUR_USER/YOUR_REPO

# أو باستخدام token من المعاملات
python deploy/build_all.py --github-repo YOUR_USER/YOUR_REPO --token your-token-here
```

#### 4. البناء والرفع الكامل:
```bash
python deploy/build_all.py --github-repo YOUR_USER/YOUR_REPO --token your-token-here
```

### المتطلبات:
- Python 3.8+
- Inno Setup 6 (لـ Windows)
- PyInstaller
- GitHub token مع صلاحيات `repo`

### تثبيت التبعيات:
```bash
# تثبيت التبعيات المطلوبة لأدوات النشر
python deploy/install_dependencies.py

# أو تثبيت يدوي
pip install requests psycopg2-binary python-dotenv psutil
```

### استكشاف الأخطاء:

#### مشكلة: ISCC.exe not found
```bash
# تثبيت Inno Setup 6
# Windows: تحميل من https://jrsoftware.org/isdl.php
# أو استخدام Chocolatey:
choco install innosetup
```

#### مشكلة: PyInstaller not installed
```bash
pip install pyinstaller==6.15.0
```

#### مشكلة: GitHub authentication failed
```bash
# التحقق من صحة الـ token
# التأكد من الصلاحيات المطلوبة (repo)
# التحقق من SSO authorization إذا كان مطلوباً
```

---

## 🛡️ `security_check.py` - أداة فحص الأمان

### الوظائف الرئيسية:
- فحص صلاحيات الملفات
- التحقق من شهادات SSL
- مراقبة حالة الخدمات
- فحص قاعدة البيانات
- مراقبة موارد النظام
- فحص السجلات
- التحقق من النسخ الاحتياطية

### المتطلبات:
- Python 3.8+
- `requests` module (for SSL and API checks)
- `psycopg2-binary` (for PostgreSQL connection checks)
- `python-dotenv` (for environment variable checks)
- `psutil` module (for Windows system resource checks)

### تثبيت التبعيات:
```bash
# تثبيت التبعيات المطلوبة
python deploy/install_dependencies.py

# أو تثبيت يدوي
pip install requests psycopg2-binary python-dotenv psutil
```

### الاستخدام:

#### Windows:
```bash
# تشغيل كمسؤول (مستحسن)
python deploy/security_check.py

# أو تشغيل عادي
python deploy/security_check.py your-domain.com
```

#### Linux/Unix:
```bash
# فحص أساسي
sudo python3 deploy/security_check.py

# فحص مع نطاق محدد
sudo python3 deploy/security_check.py your-domain.com

# تشغيل بدون صلاحيات root (محدود)
python3 deploy/security_check.py
```

### دعم الأنظمة المتعددة:
- **Windows:** فحص Windows Firewall، Event Logs، Windows Services
- **Linux/Unix:** فحص UFW، systemd services، journalctl logs
- **Cross-platform:** فحص قاعدة البيانات، SSL، API، موارد النظام

### الفحوصات المدرجة:

#### ✅ فحوصات الأمان:
- **صلاحيات الملفات:** التحقق من صلاحيات الملفات الحساسة
- **شهادة SSL:** التحقق من صحة شهادة SSL
- **جدار الحماية:** فحص إعدادات UFW
- **Headers الأمان:** التحقق من headers الأمان في API

#### ✅ فحوصات النظام:
- **حالة الخدمات:** attendance, nginx, postgresql
- **اتصال قاعدة البيانات:** SQLite/PostgreSQL
- **موارد النظام:** الذاكرة والقرص
- **السجلات:** البحث عن أخطاء وتحذيرات

#### ✅ فحوصات إضافية:
- **API التحديثات:** اختبار API التحديثات
- **متغيرات البيئة:** التحقق من الإعدادات المطلوبة
- **النسخ الاحتياطية:** فحص حالة النسخ الاحتياطية

### تفسير النتائج:

#### 🟢 SUCCESS (أخضر):
- كل شيء يعمل بشكل صحيح
- لا توجد مشاكل

#### 🟡 WARNING (أصفر):
- مشاكل طفيفة تحتاج مراجعة
- لا تؤثر على التشغيل الأساسي

#### 🔴 ERROR (أحمر):
- مشاكل خطيرة تحتاج إصلاح فوري
- قد تؤثر على تشغيل النظام

### نصائح للاستخدام:

#### 1. تشغيل دوري:
```bash
# إضافة إلى crontab للتشغيل اليومي
0 2 * * * /usr/bin/python3 /opt/attendance/deploy/security_check.py your-domain.com >> /var/log/security_check.log 2>&1
```

#### 2. مراقبة النتائج:
```bash
# مراجعة السجلات
tail -f /var/log/security_check.log

# تشغيل تفاعلي
sudo python3 deploy/security_check.py your-domain.com
```

#### 3. إصلاح المشاكل الشائعة:

##### مشكلة صلاحيات الملفات:
```bash
sudo chmod 600 /opt/attendance/.env
sudo chmod 600 /opt/attendance/github_token.txt
sudo chown attendance:attendance /opt/attendance/.env
```

##### مشكلة جدار الحماية:
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
```

##### مشكلة الخدمات:
```bash
sudo systemctl restart attendance
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

---

## 📋 قائمة التحقق السريعة

### قبل النشر:
- [ ] إنشاء GitHub repository
- [ ] إنشاء GitHub token
- [ ] تثبيت Inno Setup 6
- [ ] تثبيت PyInstaller

### بعد النشر:
- [ ] تشغيل `security_check.py`
- [ ] إصلاح أي أخطاء أو تحذيرات
- [ ] بناء ونشر المثبتات
- [ ] اختبار التحديثات التلقائية

### الصيانة الدورية:
- [ ] تشغيل فحص الأمان أسبوعياً
- [ ] مراجعة السجلات
- [ ] تحديث النظام
- [ ] إنشاء نسخ احتياطية

---

## 📞 الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- راجع السجلات: `sudo journalctl -u attendance -f`
- تحقق من حالة الخدمة: `sudo systemctl status attendance`
- راجع ملف `DEPLOYMENT.md` للنشر
- استخدم `security_check.py` للتشخيص
