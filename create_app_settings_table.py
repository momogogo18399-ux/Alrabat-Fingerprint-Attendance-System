#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create app_settings table in Supabase
إنشاء جدول app_settings في Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

def create_app_settings_table():
    """إنشاء جدول app_settings في Supabase"""
    print("🔧 إنشاء جدول app_settings في Supabase")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found")
            print("📝 قم بإنشاء ملف .env أولاً")
            return False
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Create table using raw SQL
        print("\n📝 إنشاء جدول app_settings...")
        
        # SQL commands
        sql_commands = [
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                id SERIAL PRIMARY KEY,
                key_name VARCHAR(100) UNIQUE NOT NULL,
                value TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_app_settings_key ON app_settings(key_name);
            """,
            """
            INSERT INTO app_settings (key_name, value) VALUES
                ('work_start_time', '08:00:00'),
                ('late_allowance_minutes', '20'),
                ('theme', 'dark'),
                ('language', 'ar'),
                ('auto_sync', 'true'),
                ('sync_interval', '300'),
                ('auto_backup', 'true')
            ON CONFLICT (key_name) DO NOTHING;
            """,
            """
            ALTER TABLE app_settings DISABLE ROW LEVEL SECURITY;
            """
        ]
        
        # Execute SQL commands
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"  {i}. تنفيذ أمر SQL...")
                result = supabase.rpc('exec_sql', {'sql': sql}).execute()
                print(f"    ✅ تم تنفيذ الأمر {i}")
            except Exception as e:
                print(f"    ⚠️ ملاحظة: {e}")
                # Try alternative method
                try:
                    if 'CREATE TABLE' in sql:
                        # Try to create table using table operations
                        print("    🔄 محاولة إنشاء الجدول بطريقة بديلة...")
                        # This will fail if table exists, which is fine
                        supabase.table('app_settings').select('*').limit(1).execute()
                        print("    ✅ الجدول موجود بالفعل")
                    elif 'INSERT' in sql:
                        # Try to insert settings
                        print("    🔄 محاولة إدخال الإعدادات...")
                        settings = [
                            {'key_name': 'work_start_time', 'value': '08:00:00'},
                            {'key_name': 'late_allowance_minutes', 'value': '20'},
                            {'key_name': 'theme', 'value': 'dark'},
                            {'key_name': 'language', 'value': 'ar'},
                            {'key_name': 'auto_sync', 'value': 'true'},
                            {'key_name': 'sync_interval', 'value': '300'},
                            {'key_name': 'auto_backup', 'value': 'true'}
                        ]
                        
                        for setting in settings:
                            try:
                                supabase.table('app_settings').upsert(setting).execute()
                                print(f"      ✅ {setting['key_name']}: {setting['value']}")
                            except Exception as e2:
                                print(f"      ⚠️ {setting['key_name']}: {e2}")
                except Exception as e2:
                    print(f"    ❌ فشل في الطريقة البديلة: {e2}")
        
        # Verify table creation
        print("\n🔍 التحقق من إنشاء الجدول...")
        try:
            response = supabase.table('app_settings').select('*').execute()
            if response.data:
                print(f"✅ تم إنشاء الجدول بنجاح! ({len(response.data)} إعداد)")
                print("\n📊 الإعدادات الموجودة:")
                for setting in response.data:
                    print(f"  - {setting.get('key_name')}: {setting.get('value')}")
            else:
                print("⚠️ الجدول فارغ")
        except Exception as e:
            print(f"❌ Error في التحقق: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 إنشاء جدول app_settings في Supabase")
    print("=" * 60)
    
    success = create_app_settings_table()
    
    if success:
        print("\n🎉 تم إنشاء الجدول بنجاح!")
        print("✅ يمكنك الآن تشغيل التطبيق:")
        print("python start_app.py")
    else:
        print("\n⚠️ فشل في إنشاء الجدول")
        print("🔧 تحقق من الأخطاء أعلاه")
    
    input("\nاضغط Enter للخروج...")

if __name__ == "__main__":
    main()
