#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إنشاء جدول app_settings في Supabase تلقائياً
"""

import os
import sys
from dotenv import load_dotenv

def create_table_directly():
    """إنشاء الجدول مباشرة باستخدام Supabase Python client"""
    try:
        from supabase import create_client, Client
        print("✅ تم استيراد Supabase client بنجاح")
        
        # تحميل متغيرات البيئة
        load_dotenv()
        
        # التحقق من وجود متغيرات Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ متغيرات Supabase غير موجودة في ملف .env")
            print("يرجى إنشاء ملف .env مع المتغيرات التالية:")
            print("SUPABASE_URL=your_supabase_url")
            print("SUPABASE_KEY=your_supabase_anon_key")
            return False
        
        # إنشاء عميل Supabase
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ تم الاتصال بـ Supabase بنجاح")
        
        # إنشاء جدول app_settings
        print("🔨 إنشاء جدول app_settings...")
        
        # محاولة قراءة من الجدول (للتأكد من وجوده)
        try:
            result = supabase.table('app_settings').select('*').limit(1).execute()
            print("✅ جدول app_settings موجود بالفعل")
        except Exception as e:
            print(f"⚠️ الجدول غير موجود، محاولة إنشاؤه: {e}")
            print("📝 يرجى إنشاء الجدول يدوياً في Supabase Dashboard")
            print("استخدم محتوى ملف create_app_settings_table.sql")
            return False
        
        # إدخال الإعدادات الافتراضية
        default_settings = [
            {'key_name': 'work_start_time', 'value': '09:00'},
            {'key_name': 'late_allowance_minutes', 'value': '15'},
            {'key_name': 'theme', 'value': 'light'},
            {'key_name': 'language', 'value': 'ar'},
            {'key_name': 'auto_sync', 'value': 'true'},
            {'key_name': 'sync_interval', 'value': '300'}
        ]
        
        print("📝 إدخال الإعدادات الافتراضية...")
        for setting in default_settings:
            try:
                # استخدام upsert لإدخال أو تحديث الإعداد
                supabase.table('app_settings').upsert(
                    setting,
                    on_conflict='key_name'
                ).execute()
                print(f"✅ تم إدخال/تحديث: {setting['key_name']} = {setting['value']}")
            except Exception as e:
                print(f"⚠️ خطأ في إدخال {setting['key_name']}: {e}")
        
        # عرض الإعدادات المُنشأة
        print("\n📋 الإعدادات الموجودة في Supabase:")
        try:
            result = supabase.table('app_settings').select('*').execute()
            for row in result.data:
                print(f"  {row['key_name']}: {row['value']}")
        except Exception as e:
            print(f"⚠️ خطأ في قراءة الإعدادات: {e}")
        
        print("\n🎉 تم إنشاء جدول app_settings بنجاح!")
        return True
        
    except ImportError as e:
        print(f"❌ مكتبة Supabase غير مثبتة: {e}")
        print("🔧 قم بتثبيت المكتبة:")
        print("pip install supabase python-dotenv")
        return False
    except Exception as e:
        print(f"❌ خطأ في إنشاء الجدول: {e}")
        return False

def create_app_settings_table():
    """إنشاء جدول app_settings في Supabase"""
    
    # تحميل متغيرات البيئة
    load_dotenv()
    
    # التحقق من وجود متغيرات Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ متغيرات Supabase غير موجودة في ملف .env")
        print("يرجى إنشاء ملف .env مع المتغيرات التالية:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_KEY=your_supabase_anon_key")
        return False
    
    try:
        # محاولة استيراد SupabaseManager
        try:
            # إضافة مسار التطبيق
            current_dir = os.path.dirname(os.path.abspath(__file__))
            app_dir = os.path.join(current_dir, 'app')
            sys.path.insert(0, app_dir)
            
            from database.supabase_manager import SupabaseManager
            print("✅ تم استيراد SupabaseManager بنجاح")
            
            # إنشاء مدير Supabase
            supabase_manager = SupabaseManager()
            print("✅ تم الاتصال بـ Supabase بنجاح")
            
            # إنشاء جدول app_settings
            print("🔨 إنشاء جدول app_settings...")
            
            # محاولة قراءة من الجدول (للتأكد من وجوده)
            try:
                result = supabase_manager.supabase.table('app_settings').select('*').limit(1).execute()
                print("✅ جدول app_settings موجود بالفعل")
            except Exception as e:
                print(f"⚠️ الجدول غير موجود، محاولة إنشاؤه: {e}")
                print("📝 يرجى إنشاء الجدول يدوياً في Supabase Dashboard")
                print("استخدم محتوى ملف create_app_settings_table.sql")
                return False
            
            # إدخال الإعدادات الافتراضية
            default_settings = [
                {'key_name': 'work_start_time', 'value': '09:00'},
                {'key_name': 'late_allowance_minutes', 'value': '15'},
                {'key_name': 'theme', 'value': 'light'},
                {'key_name': 'language', 'value': 'ar'},
                {'key_name': 'auto_sync', 'value': 'true'},
                {'key_name': 'sync_interval', 'value': '300'}
            ]
            
            print("📝 إدخال الإعدادات الافتراضية...")
            for setting in default_settings:
                try:
                    # استخدام upsert لإدخال أو تحديث الإعداد
                    supabase_manager.supabase.table('app_settings').upsert(
                        setting,
                        on_conflict='key_name'
                    ).execute()
                    print(f"✅ تم إدخال/تحديث: {setting['key_name']} = {setting['value']}")
                except Exception as e:
                    print(f"⚠️ خطأ في إدخال {setting['key_name']}: {e}")
            
            # عرض الإعدادات المُنشأة
            print("\n📋 الإعدادات الموجودة في Supabase:")
            try:
                settings = supabase_manager.get_all_settings()
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            except Exception as e:
                print(f"⚠️ خطأ في قراءة الإعدادات: {e}")
            
            print("\n🎉 تم إنشاء جدول app_settings بنجاح!")
            return True
            
        except ImportError as e:
            print(f"❌ خطأ في استيراد SupabaseManager: {e}")
            print("🔧 محاولة إنشاء الجدول مباشرة...")
            return create_table_directly()
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الجدول: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء إنشاء جدول app_settings في Supabase...")
    print("=" * 50)
    
    success = create_app_settings_table()
    
    if success:
        print("\n✅ تم إنشاء الجدول بنجاح!")
        print("يمكنك الآن تشغيل التطبيق الرئيسي:")
        print("python start_app.py")
    else:
        print("\n❌ فشل في إنشاء الجدول")
        print("يرجى التحقق من:")
        print("1. ملف .env يحتوي على بيانات Supabase الصحيحة")
        print("2. مشروع Supabase نشط")
        print("3. المفاتيح صحيحة")

if __name__ == "__main__":
    main()
