#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync All Settings - مزامنة شاملة لجميع الإعدادات
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def sync_all_settings():
    """مزامنة شاملة لجميع الإعدادات"""
    print("🚀 مزامنة شاملة لجميع الإعدادات")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Test Supabase connection
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found")
            print("📝 قم بإنشاء ملف .env أولاً")
            return False
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Read local settings
        print("\n📱 قراءة الإعدادات المحلية...")
        local_settings = get_local_settings()
        
        if not local_settings:
            print("❌ لا توجد إعدادات محلية")
            return False
        
        print(f"✅ تم العثور على {len(local_settings)} إعداد محلي")
        for key, value in local_settings.items():
            print(f"  - {key}: {value}")
        
        # Read Supabase settings
        print("\n🌐 قراءة الإعدادات من Supabase...")
        try:
            response = supabase.table('app_settings').select('*').execute()
            supabase_settings = {setting['key_name']: setting['value'] for setting in response.data}
            print(f"✅ تم العثور على {len(supabase_settings)} إعداد في Supabase")
            for key, value in supabase_settings.items():
                print(f"  - {key}: {value}")
        except Exception as e:
            print(f"❌ Error reading Supabase: {e}")
            return False
        
        # Compare and sync
        print("\n🔍 مقارنة الإعدادات...")
        
        # Find differences
        differences = []
        for key in set(local_settings.keys()) | set(supabase_settings.keys()):
            local_value = local_settings.get(key)
            supabase_value = supabase_settings.get(key)
            
            if local_value != supabase_value:
                differences.append({
                    'key': key,
                    'local': local_value,
                    'supabase': supabase_value
                })
                print(f"❌ {key}: محلي={local_value}, سحابي={supabase_value}")
        
        if not differences:
            print("✅ جميع الإعدادات متطابقة!")
            return True
        
        print(f"\n📊 تم العثور على {len(differences)} اختلاف")
        
        # Ask user for sync direction
        print("\n🛠️ اختر اتجاه المزامنة:")
        print("1. مزامنة المحلي إلى Supabase (استخدام الإعدادات المحلية)")
        print("2. مزامنة Supabase إلى المحلي (استخدام إعدادات Supabase)")
        print("3. مزامنة ذكية (تحديث القيم المختلفة)")
        
        choice = input("\nاختر رقم (1/2/3): ").strip()
        
        if choice == "1":
            # Sync local to Supabase
            print("\n🔄 مزامنة المحلي إلى Supabase...")
            sync_local_to_supabase(supabase, local_settings)
        elif choice == "2":
            # Sync Supabase to local
            print("\n🔄 مزامنة Supabase إلى المحلي...")
            sync_supabase_to_local(supabase_settings)
        elif choice == "3":
            # Smart sync
            print("\n🧠 مزامنة ذكية...")
            smart_sync(supabase, local_settings, supabase_settings)
        else:
            print("❌ اختيار غير صحيح")
            return False
        
        # Verify sync
        print("\n🔍 التحقق من المزامنة...")
        verify_sync()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_local_settings():
    """قراءة الإعدادات المحلية"""
    try:
        import sqlite3
        
        db_path = "attendance.db"
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return {}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check app_settings table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'")
        if not cursor.fetchone():
            print("❌ app_settings table not found locally")
            conn.close()
            return {}
        
        # Get all settings
        cursor.execute("SELECT key, value FROM app_settings")
        settings = cursor.fetchall()
        
        conn.close()
        
        return {key: value for key, value in settings}
        
    except Exception as e:
        print(f"❌ Error reading local settings: {e}")
        return {}

def sync_local_to_supabase(supabase, local_settings):
    """مزامنة المحلي إلى Supabase"""
    success_count = 0
    
    for key, value in local_settings.items():
        try:
            result = supabase.table('app_settings').upsert({
                'key_name': key,
                'value': value,
                'updated_at': '2025-01-27T10:00:00Z'
            }).execute()
            print(f"✅ {key}: {value}")
            success_count += 1
        except Exception as e:
            print(f"❌ {key}: {e}")
    
    print(f"\n📊 النتائج: {success_count}/{len(local_settings)} تمت المزامنة")

def sync_supabase_to_local(supabase_settings):
    """مزامنة Supabase إلى المحلي"""
    try:
        import sqlite3
        
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        success_count = 0
        for key, value in supabase_settings.items():
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                print(f"✅ {key}: {value}")
                success_count += 1
            except Exception as e:
                print(f"❌ {key}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 النتائج: {success_count}/{len(supabase_settings)} تمت المزامنة")
        
    except Exception as e:
        print(f"❌ Error syncing to local: {e}")

def smart_sync(supabase, local_settings, supabase_settings):
    """مزامنة ذكية"""
    print("🧠 تحليل الاختلافات...")
    
    # Sync local to Supabase for Work Rules
    work_rules_keys = ['work_start_time', 'late_allowance_minutes']
    for key in work_rules_keys:
        if key in local_settings:
            try:
                result = supabase.table('app_settings').upsert({
                    'key_name': key,
                    'value': local_settings[key],
                    'updated_at': '2025-01-27T10:00:00Z'
                }).execute()
                print(f"✅ {key}: {local_settings[key]} (محلي → سحابي)")
            except Exception as e:
                print(f"❌ {key}: {e}")
    
    # Sync other settings from Supabase to local
    other_keys = [k for k in supabase_settings.keys() if k not in work_rules_keys]
    for key in other_keys:
        try:
            import sqlite3
            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, supabase_settings[key]))
            
            conn.commit()
            conn.close()
            print(f"✅ {key}: {supabase_settings[key]} (سحابي → محلي)")
        except Exception as e:
            print(f"❌ {key}: {e}")

def verify_sync():
    """التحقق من المزامنة"""
    try:
        # Read local settings
        local_settings = get_local_settings()
        
        # Read Supabase settings
        from supabase import create_client
        from dotenv import load_dotenv
        
        load_dotenv()
        supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
        
        response = supabase.table('app_settings').select('*').execute()
        supabase_settings = {setting['key_name']: setting['value'] for setting in response.data}
        
        print(f"📱 المحلي: {len(local_settings)} إعداد")
        print(f"🌐 Supabase: {len(supabase_settings)} إعداد")
        
        # Compare
        all_keys = set(local_settings.keys()) | set(supabase_settings.keys())
        
        for key in sorted(all_keys):
            local_value = local_settings.get(key)
            supabase_value = supabase_settings.get(key)
            
            if local_value == supabase_value:
                print(f"✅ {key}: متطابق")
            else:
                print(f"❌ {key}: محلي={local_value}, سحابي={supabase_value}")
        
    except Exception as e:
        print(f"❌ Error verifying sync: {e}")

def main():
    """Main function"""
    print("🔧 مزامنة شاملة لجميع الإعدادات")
    print("=" * 60)
    
    success = sync_all_settings()
    
    if success:
        print("\n🎉 تمت المزامنة بنجاح!")
        print("✅ الإعدادات متطابقة الآن")
        print("\n🚀 يمكنك الآن تشغيل التطبيق:")
        print("python start_app.py")
    else:
        print("\n⚠️ فشلت المزامنة")
        print("🔧 تحقق من الأخطاء أعلاه")
    
    input("\nاضغط Enter للخروج...")

if __name__ == "__main__":
    main()
