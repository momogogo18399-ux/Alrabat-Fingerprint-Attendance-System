#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Notifications Manager
Manages notifications using Supabase database for real-time communication
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import logging

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QApplication

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not available, using local storage")

class NotificationsManager(QObject):
    """
    Advanced Notifications Manager using Supabase database
    Provides real-time notification system for all users
    """
    
    # Signals for real-time updates
    notification_received = pyqtSignal(dict)  # New notification received
    notification_updated = pyqtSignal(dict)   # Notification status updated
    notification_deleted = pyqtSignal(int)    # Notification deleted
    unread_count_changed = pyqtSignal(int)   # Unread count changed
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Supabase client
        self.supabase: Optional[Client] = None
        self.supabase_available = False
        
        # Local storage fallback
        self.local_notifications = []
        self.local_unread_count = 0
        
        # Real-time subscription
        self.realtime_subscription = None
        self.is_subscribed = False
        
        # Initialize Supabase connection
        if SUPABASE_AVAILABLE and supabase_url and supabase_key:
            self._init_supabase(supabase_url, supabase_key)
        else:
            self.logger.warning("Supabase not available, using local storage mode")
            
        # Start real-time monitoring
        self._start_realtime_monitoring()
        
    def _init_supabase(self, supabase_url: str, supabase_key: str):
        """Initialize Supabase connection"""
        try:
            self.supabase = create_client(supabase_url, supabase_key)
            
            # Test connection
            response = self.supabase.table('notifications').select('id').limit(1).execute()
            if response.data is not None:
                self.supabase_available = True
                self.logger.info("✅ Supabase connection established successfully")
                
                # Load existing notifications
                self._load_notifications_from_supabase()
            else:
                self.logger.error("❌ Failed to connect to Supabase")
                
        except Exception as e:
            self.logger.error(f"❌ Error initializing Supabase: {e}")
            self.supabase_available = False
            
    def _load_notifications_from_supabase(self):
        """Load notifications from Supabase"""
        try:
            if not self.supabase_available:
                return
                
            response = self.supabase.table('notifications')\
                .select('*')\
                .eq('status', 'active')\
                .order('created_at', desc=True)\
                .execute()
                
            if response.data:
                self.local_notifications = response.data
                self._update_unread_count()
                self.logger.info(f"✅ Loaded {len(response.data)} notifications from Supabase")
            else:
                self.logger.info("ℹ️ No notifications found in Supabase")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading notifications from Supabase: {e}")
            
    def _start_realtime_monitoring(self):
        """Start real-time monitoring for notifications"""
        if not self.supabase_available:
            # Fallback to polling for local mode
            self._start_polling_timer()
            return
            
        try:
            # Subscribe to real-time changes
            self.realtime_subscription = self.supabase\
                .table('notifications')\
                .on('INSERT', callback=self._on_notification_inserted)\
                .on('UPDATE', callback=self._on_notification_updated)\
                .on('DELETE', callback=self._on_notification_deleted)\
                .subscribe()
                
            self.is_subscribed = True
            self.logger.info("✅ Real-time notifications subscription started")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting real-time subscription: {e}")
            # Fallback to polling
            self._start_polling_timer()
            
    def _start_polling_timer(self):
        """Start polling timer for local mode or fallback"""
        self.polling_timer = QTimer()
        self.polling_timer.timeout.connect(self._poll_for_updates)
        self.polling_timer.start(10000)  # Poll every 10 seconds
        self.logger.info("🔄 Started polling timer for notifications")
        
    def _poll_for_updates(self):
        """Poll for updates when real-time is not available"""
        if self.supabase_available:
            self._load_notifications_from_supabase()
        else:
            # In local mode, just emit current state
            self._update_unread_count()
            
    def _on_notification_inserted(self, payload):
        """Handle new notification inserted"""
        try:
            notification = payload['record']
            self.local_notifications.insert(0, notification)
            self._update_unread_count()
            
            # Emit signal
            self.notification_received.emit(notification)
            self.logger.info(f"🔔 New notification received: {notification['title']}")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling notification insert: {e}")
            
    def _on_notification_updated(self, payload):
        """Handle notification update"""
        try:
            updated_notification = payload['record']
            notification_id = updated_notification['id']
            
            # Update local notification
            for i, notification in enumerate(self.local_notifications):
                if notification['id'] == notification_id:
                    self.local_notifications[i] = updated_notification
                    break
                    
            self._update_unread_count()
            
            # Emit signal
            self.notification_updated.emit(updated_notification)
            self.logger.info(f"🔄 Notification updated: {updated_notification['title']}")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling notification update: {e}")
            
    def _on_notification_deleted(self, payload):
        """Handle notification deletion"""
        try:
            deleted_notification = payload['old_record']
            notification_id = deleted_notification['id']
            
            # Remove from local list
            self.local_notifications = [
                n for n in self.local_notifications 
                if n['id'] != notification_id
            ]
            
            self._update_unread_count()
            
            # Emit signal
            self.notification_deleted.emit(notification_id)
            self.logger.info(f"🗑️ Notification deleted: {deleted_notification['title']}")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling notification deletion: {e}")
            
    def _update_unread_count(self):
        """Update unread count and emit signal"""
        try:
            if self.supabase_available:
                # Get unread count from database
                unread_count = self._get_unread_count_from_supabase()
            else:
                # Calculate from local data
                unread_count = sum(1 for n in self.local_notifications if not n.get('is_read', False))
                
            if unread_count != self.local_unread_count:
                self.local_unread_count = unread_count
                self.unread_count_changed.emit(unread_count)
                
        except Exception as e:
            self.logger.error(f"❌ Error updating unread count: {e}")
            
    def _get_unread_count_from_supabase(self) -> int:
        """Get unread count from Supabase"""
        try:
            if not self.supabase_available:
                return 0
                
            # Instead of calling a non-existent RPC function, count from the notifications table
            try:
                response = self.supabase.table('notifications')\
                    .select('id')\
                    .eq('is_read', False)\
                    .execute()
                
                if response.data is not None:
                    return len(response.data)
                else:
                    return 0
                    
            except Exception as table_error:
                self.logger.warning(f"⚠️ Error counting from notifications table: {table_error}")
                # Fallback: return local count
                return sum(1 for n in self.local_notifications if not n.get('is_read', False))
            
        except Exception as e:
            self.logger.error(f"❌ Error getting unread count from Supabase: {e}")
            # Fallback: return local count
            return sum(1 for n in self.local_notifications if not n.get('is_read', False))
            
    def send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send a new notification"""
        try:
            # Add metadata
            notification_data['created_at'] = datetime.now().isoformat()
            notification_data['updated_at'] = datetime.now().isoformat()
            notification_data['status'] = 'active'
            notification_data['is_read'] = False
            notification_data['read_by_users'] = []
            
            # Process links if present - make it more robust
            if 'links' in notification_data and notification_data['links']:
                try:
                    # Validate and categorize links
                    valid_links = self._validate_links(notification_data['links'])
                    if valid_links:
                        notification_data['links'] = valid_links
                        # Add link metadata if not already present
                        if 'metadata' not in notification_data:
                            notification_data['metadata'] = {}
                        notification_data['metadata']['has_links'] = True
                        notification_data['metadata']['link_count'] = len(valid_links)
                        notification_data['metadata']['link_types'] = self._categorize_links(valid_links)
                    else:
                        # Remove invalid links
                        notification_data.pop('links', None)
                        if 'metadata' in notification_data:
                            notification_data['metadata']['has_links'] = False
                except Exception as link_error:
                    self.logger.warning(f"⚠️ Link processing error, continuing without links: {link_error}")
                    notification_data.pop('links', None)
            
            if self.supabase_available:
                # Send to Supabase
                try:
                    # Clean the data to ensure it's JSON serializable
                    clean_data = {}
                    for key, value in notification_data.items():
                        if value is not None:
                            if isinstance(value, (list, dict)):
                                # Ensure lists and dicts are clean
                                clean_data[key] = value
                            else:
                                # Convert other types to string if needed
                                clean_data[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value
                    
                    self.logger.info(f"📤 Sending to Supabase: {clean_data}")
                    response = self.supabase.table('notifications')\
                        .insert(clean_data)\
                        .execute()
                        
                    if response.data:
                        self.logger.info(f"✅ Notification sent to Supabase: {notification_data['title']}")
                        # Add to local cache for immediate access
                        if response.data[0]:
                            notification_data['id'] = response.data[0].get('id')
                            self.local_notifications.insert(0, notification_data)
                            self._update_unread_count()
                            # Emit signal for real-time update
                            self.notification_received.emit(notification_data)
                        return True
                    else:
                        self.logger.error("❌ Failed to send notification to Supabase - no data returned")
                        return False
                        
                except Exception as supabase_error:
                    self.logger.error(f"❌ Supabase insert error: {supabase_error}")
                    return False
            else:
                # Store locally
                notification_data['id'] = len(self.local_notifications) + 1
                self.local_notifications.insert(0, notification_data)
                self._update_unread_count()
                
                # Emit signal for local mode
                self.notification_received.emit(notification_data)
                
                self.logger.info(f"✅ Notification stored locally: {notification_data['title']}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error sending notification: {e}")
            return False
    
    def _validate_links(self, links: List[str]) -> List[str]:
        """Validate and clean links"""
        valid_links = []
        for link in links:
            if link and isinstance(link, str):
                link = link.strip()
                if link:
                    # Try to fix common URL issues
                    if not link.startswith(('http://', 'https://', 'ftp://')):
                        link = 'https://' + link
                    valid_links.append(link)
        return valid_links
    
    def _categorize_links(self, links: List[str]) -> Dict[str, List[str]]:
        """Categorize links by type"""
        categories = {
            "documents": [],
            "downloads": [],
            "videos": [],
            "images": [],
            "websites": []
        }
        
        for link in links:
            link_lower = link.lower()
            if any(ext in link_lower for ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']):
                categories["documents"].append(link)
            elif any(ext in link_lower for ext in ['.zip', '.rar', '.exe', '.msi', '.dmg']):
                categories["downloads"].append(link)
            elif any(ext in link_lower for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv']):
                categories["videos"].append(link)
            elif any(ext in link_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                categories["images"].append(link)
            else:
                categories["websites"].append(link)
        
        return categories
            
    def get_notifications(self, user_id: str = None, user_role: str = None, 
                         limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            if self.supabase_available:
                # Get from Supabase with filtering
                query = self.supabase.table('notifications')\
                    .select('*')\
                    .eq('status', 'active')\
                    .order('created_at', desc=True)\
                    .range(offset, offset + limit - 1)
                    
                # Apply user filtering
                if user_role and user_role != 'Admin':
                    query = query.or_(f"target_users.eq.all,target_users.eq.{user_role}")
                    
                response = query.execute()
                return response.data or []
            else:
                # Return from local storage
                notifications = self.local_notifications.copy()
                
                # Apply user filtering
                if user_role and user_role != 'Admin':
                    notifications = [
                        n for n in notifications
                        if n.get('target_users') in ['all', user_role]
                    ]
                    
                return notifications[offset:offset + limit]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting notifications: {e}")
            return []
            
    def mark_as_read(self, notification_id: int, user_id: str) -> bool:
        """Mark a notification as read by a user"""
        try:
            if self.supabase_available:
                # Update in Supabase
                response = self.supabase.rpc('mark_notification_read', {
                    'notification_id': notification_id,
                    'user_id': user_id
                }).execute()
                
                if response.data:
                    self.logger.info(f"✅ Marked notification {notification_id} as read")
                    return True
                else:
                    self.logger.error(f"❌ Failed to mark notification {notification_id} as read")
                    return False
            else:
                # Update locally
                for notification in self.local_notifications:
                    if notification['id'] == notification_id:
                        if 'read_by_users' not in notification:
                            notification['read_by_users'] = []
                        if user_id not in notification['read_by_users']:
                            notification['read_by_users'].append(user_id)
                        notification['is_read'] = True
                        break
                        
                self._update_unread_count()
                self.logger.info(f"✅ Marked notification {notification_id} as read locally")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error marking notification as read: {e}")
            return False
            
    def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification (admin only)"""
        try:
            if self.supabase_available:
                # Delete from Supabase
                response = self.supabase.table('notifications')\
                    .delete()\
                    .eq('id', notification_id)\
                    .execute()
                    
                if response.data:
                    self.logger.info(f"✅ Deleted notification {notification_id} from Supabase")
                    return True
                else:
                    self.logger.error(f"❌ Failed to delete notification {notification_id}")
                    return False
            else:
                # Remove from local storage
                self.local_notifications = [
                    n for n in self.local_notifications 
                    if n['id'] != notification_id
                ]
                
                self._update_unread_count()
                self.logger.info(f"✅ Deleted notification {notification_id} locally")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error deleting notification: {e}")
            return False
            
    def get_unread_count(self, user_id: str = None, user_role: str = None) -> int:
        """Get unread notifications count for a user"""
        try:
            if self.supabase_available:
                return self._get_unread_count_from_supabase()
            else:
                return self.local_unread_count
                
        except Exception as e:
            self.logger.error(f"❌ Error getting unread count: {e}")
            return 0
            
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.is_subscribed and self.realtime_subscription:
                self.supabase.remove_channel(self.realtime_subscription)
                self.is_subscribed = False
                self.logger.info("✅ Real-time subscription cleaned up")
                
            if hasattr(self, 'polling_timer'):
                self.polling_timer.stop()
                self.logger.info("✅ Polling timer stopped")
                
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get manager status information"""
        return {
            'supabase_available': self.supabase_available,
            'is_subscribed': self.is_subscribed,
            'total_notifications': len(self.local_notifications),
            'unread_count': self.local_unread_count,
            'mode': 'Supabase' if self.supabase_available else 'Local'
        }
