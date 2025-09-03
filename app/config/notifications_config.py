#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notifications System Configuration
Configuration file for the advanced notifications system
"""

import os
from typing import Dict, Any

class NotificationsConfig:
    """Configuration class for notifications system"""
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    
    # Database Configuration
    DATABASE_TABLE = 'notifications'
    
    # Real-time Configuration
    REALTIME_ENABLED = True
    REALTIME_POLLING_INTERVAL = 10000  # 10 seconds in milliseconds
    
    # Notification Types
    NOTIFICATION_TYPES = [
        "📢 General Announcement",
        "🔄 System Update", 
        "⚠️ Important Notice",
        "🎉 Celebration/Event",
        "🔧 Maintenance Notice",
        "📚 Training/Workshop",
        "💼 Policy Change",
        "🚨 Emergency Alert"
    ]
    
    # Priority Levels
    PRIORITY_LEVELS = [
        "low",
        "medium", 
        "high",
        "urgent"
    ]
    
    # Target User Groups
    TARGET_USER_GROUPS = [
        "all",
        "employees",
        "managers",
        "admins"
    ]
    
    # Notification Status
    NOTIFICATION_STATUSES = [
        "active",
        "inactive",
        "expired",
        "deleted"
    ]
    
    # UI Configuration
    UI_REFRESH_INTERVAL = 5000  # 5 seconds in milliseconds
    MAX_NOTIFICATIONS_DISPLAY = 100
    NOTIFICATION_EXPIRY_DAYS = 30
    
    # Styling Configuration
    STYLES = {
        'urgent': {
            'color': '#dc3545',
            'background': '#f8d7da',
            'border': '#dc3545'
        },
        'high': {
            'color': '#fd7e14',
            'background': '#fff3cd',
            'border': '#fd7e14'
        },
        'medium': {
            'color': '#ffc107',
            'background': '#fff3cd',
            'border': '#ffc107'
        },
        'low': {
            'color': '#28a745',
            'background': '#d4edda',
            'border': '#28a745'
        }
    }
    
    @classmethod
    def get_supabase_config(cls) -> Dict[str, str]:
        """Get Supabase configuration"""
        return {
            'url': cls.SUPABASE_URL,
            'key': cls.SUPABASE_ANON_KEY
        }
    
    @classmethod
    def is_supabase_configured(cls) -> bool:
        """Check if Supabase is properly configured"""
        return bool(cls.SUPABASE_URL and cls.SUPABASE_ANON_KEY)
    
    @classmethod
    def get_ui_config(cls) -> Dict[str, Any]:
        """Get UI configuration"""
        return {
            'refresh_interval': cls.UI_REFRESH_INTERVAL,
            'max_display': cls.MAX_NOTIFICATIONS_DISPLAY,
            'expiry_days': cls.NOTIFICATION_EXPIRY_DAYS
        }
    
    @classmethod
    def get_realtime_config(cls) -> Dict[str, Any]:
        """Get real-time configuration"""
        return {
            'enabled': cls.REALTIME_ENABLED,
            'polling_interval': cls.REALTIME_POLLING_INTERVAL
        }
    
    @classmethod
    def get_style_for_priority(cls, priority: str) -> Dict[str, str]:
        """Get styling for a specific priority level"""
        return cls.STYLES.get(priority, cls.STYLES['medium'])
    
    @classmethod
    def validate_notification_data(cls, data: Dict[str, Any]) -> bool:
        """Validate notification data"""
        required_fields = ['title', 'message', 'notification_type', 'priority', 'target_users']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        if data['notification_type'] not in cls.NOTIFICATION_TYPES:
            return False
            
        if data['priority'] not in cls.PRIORITY_LEVELS:
            return False
            
        if data['target_users'] not in cls.TARGET_USER_GROUPS:
            return False
            
        return True
