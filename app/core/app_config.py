#!/usr/bin/env python3
"""
Application Configuration File
"""

import os
from typing import Optional

class AppConfig:
    """Application Settings"""
    
    def __init__(self):
        # Supabase Settings
        self.supabase_url = self._get_env_var([
            'NEXT_PUBLIC_SUPABASE_URL',
            'SUPABASE_URL'
        ])
        
        self.supabase_key = self._get_env_var([
            'NEXT_PUBLIC_SUPABASE_ANON_KEY',
            'SUPABASE_KEY'
        ])
        
        self.supabase_service_key = self._get_env_var([
            'SUPABASE_SERVICE_KEY'
        ])
        
        # Database Settings
        self.sqlite_file = self._get_env_var(['SQLITE_FILE'], 'attendance.db')
        
        # App Settings
        self.theme_dir = self._get_env_var(['THEME_DIR'], 'assets/themes')
        self.notifier_host = self._get_env_var(['NOTIFIER_HOST'], 'localhost')
        self.notifier_port = int(self._get_env_var(['NOTIFIER_PORT'], '8989'))
        
        # Security
        self.secret_key = self._get_env_var(['SECRET_KEY'], 'default-secret-key')
    
    def _get_env_var(self, var_names: list, default: str = None) -> Optional[str]:
        """Get environment variable from multiple possible names"""
        for var_name in var_names:
            value = os.getenv(var_name)
            if value:
                return value
        return default
    
    @property
    def has_supabase_config(self) -> bool:
        """Check if Supabase settings exist"""
        return bool(self.supabase_url and self.supabase_key)
    
    @property
    def supabase_status(self) -> str:
        """Supabase connection status"""
        if self.has_supabase_config:
            return "Connected"
        else:
            return "Not Configured"
    
    def get_supabase_info(self) -> dict:
        """Supabase information"""
        return {
            'url': self.supabase_url or 'Not Set',
            'key': self.supabase_key or 'Not Set',
            'status': self.supabase_status,
            'configured': self.has_supabase_config
        }

# Create a singleton instance
app_config = AppConfig()
