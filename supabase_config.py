#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Configuration Helper
ملف مساعد لتكوين Supabase
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseConfig:
    """Supabase Configuration Helper"""
    
    @staticmethod
    def get_config():
        """Get Supabase configuration"""
        config = {
            'url': os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
            'key': os.getenv('SUPABASE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY'),
            'service_key': os.getenv('SUPABASE_SERVICE_KEY')
        }
        return config
    
    @staticmethod
    def is_configured():
        """Check if Supabase is properly configured"""
        config = SupabaseConfig.get_config()
        return bool(config['url'] and config['key'])
    
    @staticmethod
    def print_config():
        """Print current configuration"""
        config = SupabaseConfig.get_config()
        print("🔧 Supabase Configuration:")
        print(f"URL: {config['url']}")
        print(f"Key: {config['key'][:20] if config['key'] else 'None'}...")
        print(f"Service Key: {config['service_key'][:20] if config['service_key'] else 'None'}...")
        print(f"Configured: {SupabaseConfig.is_configured()}")
    
    @staticmethod
    def create_env_template():
        """Create .env template"""
        template = """# Supabase Configuration (مطلوب للمزامنة)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here

# Alternative variable names for compatibility
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Hybrid Database System Settings
HYBRID_MODE=true
SYNC_INTERVAL=300
AUTO_SYNC=true
INSTANT_SYNC=true
SUPABASE_FIRST=true

# Database Settings
SQLITE_FILE=attendance.db

# Flask Settings
FLASK_DEBUG=0
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
"""
        return template

def main():
    """Main function"""
    print("🚀 Supabase Configuration Helper")
    print("=" * 50)
    
    # Print current configuration
    SupabaseConfig.print_config()
    
    if not SupabaseConfig.is_configured():
        print("\n❌ Supabase غير مُكوّن")
        print("📝 قم بإنشاء ملف .env بالمحتوى التالي:")
        print("\n" + SupabaseConfig.create_env_template())
        
        print("\n🔗 للحصول على بيانات Supabase:")
        print("1. اذهب إلى https://supabase.com")
        print("2. أنشئ مشروع جديد")
        print("3. اذهب إلى Settings > API")
        print("4. انسخ URL و anon key")
        print("5. ضعهما في ملف .env")
    else:
        print("\n✅ Supabase مُكوّن بشكل صحيح")
        print("🔄 يمكنك الآن استخدام المزامنة")

if __name__ == "__main__":
    main()
