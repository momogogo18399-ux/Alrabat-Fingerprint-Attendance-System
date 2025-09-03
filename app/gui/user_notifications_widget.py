#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Notifications Widget
Widget for users to view notifications sent by admins using advanced database system
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QScrollArea, QFrame, QGroupBox, QCheckBox,
    QMessageBox, QSplitter, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap

try:
    from app.core.notifications_manager import NotificationsManager
    NOTIFICATIONS_MANAGER_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_MANAGER_AVAILABLE = False
    print("⚠️ NotificationsManager not available")

class UserNotificationsWidget(QWidget):
    """Widget for users to view admin notifications using advanced database system"""
    
    notification_read = pyqtSignal(str)  # notification_id
    
    def __init__(self, db_manager=None, user_id=None, user_role=None, main_window=None, 
                 supabase_url=None, supabase_key=None):
        super().__init__()
        self.db_manager = db_manager
        self.user_id = user_id
        self.user_role = user_role
        self.main_window = main_window
        self.notifications = []
        self.unread_count = 0
        
        # Initialize notifications manager
        self.notifications_manager = None
        self._init_notifications_manager(supabase_url, supabase_key)
        
        self.setup_ui()
        self.load_notifications()
        
        # Connect to notifications manager signals
        if self.notifications_manager:
            self._connect_notifications_manager()
        
        # Start auto-refresh timer
        self._start_auto_refresh_timer()
        
    def _init_notifications_manager(self, supabase_url, supabase_key):
        """Initialize the notifications manager"""
        try:
            if NOTIFICATIONS_MANAGER_AVAILABLE:
                # Try to get Supabase credentials from environment or config
                if not supabase_url:
                    supabase_url = os.getenv('SUPABASE_URL')
                if not supabase_key:
                    supabase_key = os.getenv('SUPABASE_ANON_KEY')
                
                self.notifications_manager = NotificationsManager(supabase_url, supabase_key)
                print(f"✅ Notifications Manager initialized: {self.notifications_manager.get_status()['mode']}")
            else:
                print("⚠️ NotificationsManager not available, using local mode")
                
        except Exception as e:
            print(f"❌ Error initializing NotificationsManager: {e}")
            self.notifications_manager = None
            
    def _connect_notifications_manager(self):
        """Connect to notifications manager signals"""
        try:
            if self.notifications_manager:
                self.notifications_manager.notification_received.connect(self._on_notification_received)
                self.notifications_manager.notification_updated.connect(self._on_notification_updated)
                self.notifications_manager.notification_deleted.connect(self._on_notification_deleted)
                self.notifications_manager.unread_count_changed.connect(self._on_unread_count_changed)
                print("✅ Connected to NotificationsManager signals")
                
        except Exception as e:
            print(f"❌ Error connecting to NotificationsManager: {e}")
            
    def _on_notification_received(self, notification):
        """Handle new notification received"""
        try:
            # Check if notification is targeted to this user
            if self._is_notification_targeted(notification):
                # Add to local list
                self.notifications.insert(0, notification)
                
                # Refresh display
                self.apply_filters()
                self.update_unread_count()
                
                print(f"🔔 New notification received: {notification['title']}")
                
        except Exception as e:
            print(f"❌ Error handling notification received: {e}")
            
    def _on_notification_updated(self, notification):
        """Handle notification updated"""
        try:
            # Update in local list
            for i, n in enumerate(self.notifications):
                if n['id'] == notification['id']:
                    self.notifications[i] = notification
                    break
                    
            # Refresh display
            self.apply_filters()
            self.update_unread_count()
            
            print(f"🔄 Notification updated: {notification['title']}")
            
        except Exception as e:
            print(f"❌ Error handling notification updated: {e}")
            
    def _on_notification_deleted(self, notification_id):
        """Handle notification deleted"""
        try:
            # Remove from local list
            self.notifications = [n for n in self.notifications if n['id'] != notification_id]
            
            # Refresh display
            self.apply_filters()
            self.update_unread_count()
            
            print(f"🗑️ Notification deleted: {notification_id}")
            
        except Exception as e:
            print(f"❌ Error handling notification deleted: {e}")
            
    def _on_unread_count_changed(self, count):
        """Handle unread count changed"""
        try:
            self.unread_count = count
            self.update_unread_count()
            print(f"📊 Unread count changed: {count}")
            
        except Exception as e:
            print(f"❌ Error handling unread count changed: {e}")
            
    def _is_notification_targeted(self, notification):
        """Check if notification is targeted to this user"""
        try:
            target_users = notification.get('target_users', 'all')
            
            # If targeting all users
            if target_users == 'all':
                return True
                
            # If targeting specific role
            if target_users == self.user_role:
                return True
                
            # If targeting specific user IDs
            target_user_ids = notification.get('target_user_ids', [])
            if target_user_ids and str(self.user_id) in target_user_ids:
                return True
                
            return False
            
        except Exception as e:
            print(f"❌ Error checking notification target: {e}")
            return False
            
    def _start_auto_refresh_timer(self):
        """Start auto-refresh timer for notifications"""
        try:
            self.auto_refresh_timer = QTimer(self)
            self.auto_refresh_timer.timeout.connect(self.auto_refresh_notifications)
            self.auto_refresh_timer.start(10000)  # Refresh every 10 seconds
            print("✅ Started auto-refresh timer for notifications")
            
        except Exception as e:
            print(f"❌ Error starting auto-refresh timer: {e}")
        
    def auto_refresh_notifications(self):
        """Auto-refresh notifications from manager"""
        try:
            if self.notifications_manager:
                # Get fresh notifications from manager
                fresh_notifications = self.notifications_manager.get_notifications(
                    user_id=self.user_id,
                    user_role=self.user_role,
                    limit=100
                )
                
                # Update local list
                self.notifications = fresh_notifications
                
                # Refresh display
                self.apply_filters()
                self.update_unread_count()
                
                print(f"🔄 Auto-refresh completed: {len(fresh_notifications)} notifications")
                
        except Exception as e:
            # Don't print errors in auto-refresh to avoid spam
            pass
        
    def setup_ui(self):
        """Setup user interface with modern, beautiful design"""
        # Main layout with improved spacing
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Enhanced header with modern design
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Beautiful title with gradient-like effect
        title_label = QLabel("📋 Notification Center")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 15px 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-radius: 12px;
                border: 2px solid #2980b9;
                border: 2px solid #2980b9;
            }
        """)
        
        # Enhanced status indicator with better styling
        self.status_label = QLabel("🔄 Initializing...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 13px;
                padding: 10px 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-weight: 500;
            }
        """)
        
        # Beautiful unread badge with animation-like design
        self.unread_badge = QLabel("0")
        self.unread_badge.setStyleSheet("""
            QLabel {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, 
                    fx:0.3, fy:0.3, stop:0 #ff6b6b, stop:1 #ee5a52);
                color: white;
                border-radius: 15px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 13px;
                min-width: 25px;
                text-align: center;
                border: 2px solid #ff4757;
                box-shadow: 0 2px 6px rgba(255, 107, 107, 0.4);
            }
        """)
        self.unread_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.unread_badge)
        
        main_layout.addLayout(header_layout)
        
        # Enhanced main scroll area with better styling
        self.main_scroll_area = QScrollArea()
        self.main_scroll_area.setWidgetResizable(True)
        self.main_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.main_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.main_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 15px;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 16px;
                border-radius: 8px;
                margin: 2px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #6c757d, stop:1 #495057);
                border-radius: 8px;
                min-height: 40px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #495057, stop:1 #343a40);
            }
            QScrollBar:horizontal {
                background-color: #e9ecef;
                height: 16px;
                border-radius: 8px;
                margin: 2px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #6c757d, stop:1 #495057);
                border-radius: 8px;
                min-width: 40px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #495057, stop:1 #343a40);
            }
        """)
        
        # Enhanced main content widget
        main_content_widget = QWidget()
        main_content_layout = QVBoxLayout()
        main_content_layout.setSpacing(25)
        main_content_layout.setContentsMargins(25, 25, 25, 25)
        
        # Enhanced splitter with better proportions
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #dee2e6, stop:1 #adb5bd);
                border: 1px solid #adb5bd;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #adb5bd, stop:1 #6c757d);
            }
        """)
        
        # Enhanced left panel with beautiful design
        left_panel = self.create_filters_panel()
        self.left_scroll_area = QScrollArea()
        self.left_scroll_area.setWidget(left_panel)
        self.left_scroll_area.setWidgetResizable(True)
        self.left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.left_scroll_area.setMinimumWidth(350)
        self.left_scroll_area.setMaximumWidth(400)
        self.left_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 3px solid #e9ecef;
                border-radius: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
        """)
        self.splitter.addWidget(self.left_scroll_area)
        
        # Enhanced right panel with beautiful design
        right_panel = self.create_notifications_panel()
        self.right_scroll_area = QScrollArea()
        self.right_scroll_area.setWidget(right_panel)
        self.right_scroll_area.setWidgetResizable(True)
        self.right_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.right_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.right_scroll_area.setMinimumWidth(650)
        self.right_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 3px solid #e9ecef;
                border-radius: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
        """)
        self.splitter.addWidget(self.right_scroll_area)
        
        # Set enhanced splitter proportions
        self.splitter.setSizes([375, 675])
        self.splitter.splitterMoved.connect(self.on_splitter_moved)
        
        main_content_layout.addWidget(self.splitter)
        main_content_widget.setLayout(main_content_layout)
        
        # Set the main content widget to the scroll area
        self.main_scroll_area.setWidget(main_content_widget)
        main_layout.addWidget(self.main_scroll_area)
        
        self.setLayout(main_layout)
        
        # Initialize notifications_layout reference after it's created
        if hasattr(self, 'notifications_layout'):
            print("✅ UserNotificationsWidget UI setup completed successfully")
        else:
            print("⚠️ Warning: notifications_layout not found after UI setup")
            
        # Update status
        self._update_status()
        
    def on_splitter_moved(self, pos, index):
        """Handle splitter movement to maintain proper proportions"""
        try:
            # Ensure minimum widths are maintained
            left_width = self.findChild(QScrollArea).width()
            if left_width < 320:
                self.findChild(QScrollArea).setMinimumWidth(320)
            if left_width > 380:
                self.findChild(QScrollArea).setMaximumWidth(380)
        except Exception as e:
            print(f"❌ Error handling splitter movement: {e}")
        
    def _update_status(self):
        """Update status indicator"""
        try:
            if self.notifications_manager:
                status = self.notifications_manager.get_status()
                mode = status['mode']
                total = status['total_notifications']
                
                if mode == 'Supabase':
                    self.status_label.setText(f"✅ {mode} - {total} notifications")
                    self.status_label.setStyleSheet("""
                        QLabel {
                            color: #28a745;
                            font-size: 12px;
                            padding: 5px;
                            background-color: #d4edda;
                            border-radius: 5px;
                        }
                    """)
                else:
                    self.status_label.setText(f"🔄 {mode} - {total} notifications")
                    self.status_label.setStyleSheet("""
                        QLabel {
                            color: #ffc107;
                            font-size: 12px;
                            padding: 5px;
                            background-color: #fff3cd;
                            border-radius: 5px;
                        }
                    """)
            else:
                self.status_label.setText("❌ Not Available")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #dc3545;
                        font-size: 12px;
                        padding: 5px;
                        background-color: #f8d7da;
                        border-radius: 5px;
                    }
                """)
                
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            self.status_label.setText("❌ Error")
        
    def create_filters_panel(self):
        """Create the left panel with beautiful notification filters"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 3px solid #e9ecef;
                border-radius: 15px;
                padding: 25px;
            }
        """)
        
        # Create main layout with enhanced spacing
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Beautiful filter title with modern design
        filter_title = QLabel("🔍 Smart Filters")
        filter_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        filter_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filter_title.setStyleSheet("""
            QLabel {
                margin-bottom: 20px;
                padding: 15px 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 12px;
                border: 2px solid #5a6fd8;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
        """)
        main_layout.addWidget(filter_title)
        
        # Enhanced scroll area for filters content
        self.filters_scroll_area = QScrollArea()
        self.filters_scroll_area.setWidgetResizable(True)
        self.filters_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.filters_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.filters_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #6c757d, stop:1 #495057);
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #495057, stop:1 #343a40);
            }
        """)
        
        # Create filters content widget with enhanced styling
        filters_widget = QWidget()
        filters_layout = QVBoxLayout()
        filters_layout.setSpacing(30)
        filters_layout.setContentsMargins(20, 20, 20, 20)
        
        # Enhanced status filters with beautiful design
        status_group = QGroupBox("📊 Message Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding: 20px;
                border: 3px solid #e9ecef;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                margin-top: 15px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #495057;
            }
        """)
        status_layout = QVBoxLayout()
        status_layout.setSpacing(15)
        
        self.show_unread = QCheckBox("🔴 Unread Messages")
        self.show_read = QCheckBox("🟢 Read Messages")
        
        # Set both as default
        self.show_unread.setChecked(True)
        self.show_read.setChecked(True)
        
        # Enhanced status checkbox styling
        status_checkbox_style = """
            QCheckBox {
                font-size: 14px;
                padding: 12px;
                spacing: 15px;
                color: #495057;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border: 2px solid #28a745;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #adb5bd;
            }
        """
        self.show_unread.setStyleSheet(status_checkbox_style)
        self.show_read.setStyleSheet(status_checkbox_style)
        
        self.show_unread.toggled.connect(self.apply_filters)
        self.show_read.toggled.connect(self.apply_filters)
        
        status_layout.addWidget(self.show_unread)
        status_layout.addWidget(self.show_read)
        status_group.setLayout(status_layout)
        filters_layout.addWidget(status_group)
        
        # Enhanced priority filters with beautiful design
        priority_group = QGroupBox("⚡ Priority Level")
        priority_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding: 20px;
                border: 3px solid #e9ecef;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                margin-top: 15px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #495057;
            }
        """)
        priority_layout = QVBoxLayout()
        priority_layout.setSpacing(15)
        
        self.priority_urgent = QCheckBox("🔴 Urgent")
        self.priority_high = QCheckBox("🟠 High Priority")
        self.priority_medium = QCheckBox("🟡 Medium Priority")
        self.priority_low = QCheckBox("🟢 Low Priority")
        
        # Set all as default
        self.priority_urgent.setChecked(True)
        self.priority_high.setChecked(True)
        self.priority_medium.setChecked(True)
        self.priority_low.setChecked(True)
        
        # Enhanced priority checkbox styling
        priority_checkbox_style = """
            QCheckBox {
                font-size: 14px;
                padding: 12px;
                spacing: 15px;
                color: #495057;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border: 2px solid #28a745;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #adb5bd;
            }
        """
        self.priority_urgent.setStyleSheet(priority_checkbox_style)
        self.priority_high.setStyleSheet(priority_checkbox_style)
        self.priority_medium.setStyleSheet(priority_checkbox_style)
        self.priority_low.setStyleSheet(priority_checkbox_style)
        
        # Connect priority filters
        self.priority_urgent.toggled.connect(self.apply_filters)
        self.priority_high.toggled.connect(self.apply_filters)
        self.priority_medium.toggled.connect(self.apply_filters)
        self.priority_low.toggled.connect(self.apply_filters)
        
        priority_layout.addWidget(self.priority_urgent)
        priority_layout.addWidget(self.priority_high)
        priority_layout.addWidget(self.priority_medium)
        priority_layout.addWidget(self.priority_low)
        priority_group.setLayout(priority_layout)
        filters_layout.addWidget(priority_group)
        
        # Type filters
        type_group = QGroupBox("📋 Type")
        type_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                padding: 15px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        type_layout = QVBoxLayout()
        type_layout.setSpacing(8)  # Increased spacing
        
        self.type_general = QCheckBox("📢 General")
        self.type_update = QCheckBox("🔄 Update")
        self.type_important = QCheckBox("⚠️ Important")
        self.type_event = QCheckBox("🎉 Event")
        self.type_maintenance = QCheckBox("🔧 Maintenance")
        self.type_training = QCheckBox("📚 Training")
        self.type_policy = QCheckBox("💼 Policy")
        self.type_emergency = QCheckBox("🚨 Emergency")
        self.type_document = QCheckBox("🔗 Document")
        self.type_download = QCheckBox("📥 Download")
        self.type_website = QCheckBox("🌐 Website")
        
        # Style type checkboxes
        type_checkbox_style = """
            QCheckBox {
                font-size: 13px;
                padding: 6px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """
        self.type_general.setStyleSheet(type_checkbox_style)
        self.type_update.setStyleSheet(type_checkbox_style)
        self.type_important.setStyleSheet(type_checkbox_style)
        self.type_event.setStyleSheet(type_checkbox_style)
        self.type_maintenance.setStyleSheet(type_checkbox_style)
        self.type_training.setStyleSheet(type_checkbox_style)
        self.type_policy.setStyleSheet(type_checkbox_style)
        self.type_emergency.setStyleSheet(type_checkbox_style)
        self.type_document.setStyleSheet(type_checkbox_style)
        self.type_download.setStyleSheet(type_checkbox_style)
        self.type_website.setStyleSheet(type_checkbox_style)
        
        # Set all as default
        for checkbox in [self.type_general, self.type_update, self.type_important, 
                        self.type_event, self.type_maintenance, self.type_training, 
                        self.type_policy, self.type_emergency, self.type_document,
                        self.type_download, self.type_website]:
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.apply_filters)
        
        type_layout.addWidget(self.type_general)
        type_layout.addWidget(self.type_update)
        type_layout.addWidget(self.type_important)
        type_layout.addWidget(self.type_event)
        type_layout.addWidget(self.type_maintenance)
        type_layout.addWidget(self.type_training)
        type_layout.addWidget(self.type_policy)
        type_layout.addWidget(self.type_emergency)
        type_layout.addWidget(self.type_document)
        type_layout.addWidget(self.type_download)
        type_layout.addWidget(self.type_website)
        type_group.setLayout(type_layout)
        filters_layout.addWidget(type_group)
        
        # Enhanced action buttons with beautiful design
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding: 20px;
                border: 3px solid #e9ecef;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                margin-top: 15px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #495057;
            }
        """)
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(20)
        
        # Enhanced mark all as read button
        self.mark_all_read_button = QPushButton("✅ Mark All as Read")
        self.mark_all_read_button.setMinimumHeight(50)
        self.mark_all_read_button.clicked.connect(self.mark_all_as_read)
        self.mark_all_read_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #17a2b8, stop:1 #138496);
                color: white;
                border: none;
                padding: 15px 20px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                min-height: 50px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #138496, stop:1 #117a8b);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #117a8b, stop:1 #0f6674);
            }
        """)
        
        # Enhanced refresh button
        self.refresh_button = QPushButton("🔄 Refresh Notifications")
        self.refresh_button.setMinimumHeight(50)
        self.refresh_button.clicked.connect(self.refresh_notifications)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #6f42c1, stop:1 #5a32a3);
                color: white;
                border: none;
                padding: 15px 20px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                min-height: 50px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5a32a3, stop:1 #4c2889);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4c2889, stop:1 #3d1f6b);
            }
        """)
        
        actions_layout.addWidget(self.mark_all_read_button)
        actions_layout.addWidget(self.refresh_button)
        actions_group.setLayout(actions_layout)
        filters_layout.addWidget(actions_group)
        
        # Add stretch at the end to push content to top
        filters_layout.addStretch()
        
        # Set the filters layout to the filters widget
        filters_widget.setLayout(filters_layout)
        
        # Set the filters widget to the scroll area
        self.filters_scroll_area.setWidget(filters_widget)
        
        # Add the scroll area to the main layout
        main_layout.addWidget(self.filters_scroll_area)
        
        panel.setLayout(main_layout)
        return panel
        
    def create_notifications_panel(self):
        """Create the right panel with beautiful notifications list"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 3px solid #e9ecef;
                border-radius: 15px;
                padding: 25px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Beautiful notifications title with modern design
        notifications_title = QLabel("📋 Message Center")
        notifications_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        notifications_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notifications_title.setStyleSheet("""
            margin-bottom: 20px;
            padding: 15px 25px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #fd79a8, stop:1 #fdcb6e);
            color: white;
            border-radius: 12px;
            border: 2px solid #e84393;
            box-shadow: 0 4px 12px rgba(253, 121, 168, 0.3);
        """)
        layout.addWidget(notifications_title)
        
        # Enhanced empty state message with beautiful design
        self.empty_state = QLabel("✨ Your inbox is clean and organized!")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setStyleSheet("""
            color: #6c757d;
            font-size: 18px;
            font-weight: 500;
            padding: 60px 40px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #f8f9fa, stop:1 #e9ecef);
            border: 3px dashed #dee2e6;
            border-radius: 15px;
            margin: 30px;
            font-family: 'Segoe UI';
        """)
        self.empty_state.setVisible(False)
        layout.addWidget(self.empty_state)
        
        # Enhanced scrollable notifications area
        self.notifications_widget = QWidget()
        self.notifications_layout = QVBoxLayout()
        self.notifications_layout.setSpacing(20)
        self.notifications_layout.setContentsMargins(15, 15, 15, 15)
        self.notifications_widget.setLayout(self.notifications_layout)
        
        # Enhanced scroll area with beautiful styling
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.notifications_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 16px;
                border-radius: 8px;
                margin: 2px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #6c757d, stop:1 #495057);
                border-radius: 8px;
                min-height: 40px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #495057, stop:1 #343a40);
            }
        """)
        layout.addWidget(scroll_area)
        
        panel.setLayout(layout)
        return panel
        
    def refresh_notifications(self):
        """تحديث التنبيهات من النظام المشترك"""
        try:
            if self.notifications_manager:
                # Get fresh notifications from manager
                fresh_notifications = self.notifications_manager.get_notifications(
                    user_id=self.user_id,
                    user_role=self.user_role,
                    limit=100
                )
                
                if fresh_notifications:
                    self.notifications = fresh_notifications
                    print(f"✅ تم تحديث التنبيهات: {len(fresh_notifications)} تنبيه")
                else:
                    print("ℹ️ لا توجد تنبيهات جديدة")
            else:
                print("⚠️ لا يمكن الوصول للنظام المشترك")
                
            self.apply_filters()
            self.update_unread_count()
            self._update_status()
            
        except Exception as e:
            print(f"❌ Failed في تحديث التنبيهات: {e}")
            import traceback
            traceback.print_exc()

    def load_notifications(self):
        """Load notifications from database or local storage"""
        # Safety check: ensure notifications_layout is properly initialized
        if not hasattr(self, 'notifications_layout') or self.notifications_layout is None:
            print("Warning: notifications_layout not initialized, skipping load_notifications")
            return
            
        try:
            if self.notifications_manager:
                # Get notifications from manager
                self.notifications = self.notifications_manager.get_notifications(
                    user_id=self.user_id,
                    user_role=self.user_role,
                    limit=100
                )
                print(f"✅ تم تحميل {len(self.notifications)} تنبيه من النظام المتقدم")
            else:
                # Fallback to sample data
                if not self.notifications:
                    self.add_sample_notifications()
                    print("ℹ️ تم استخدام البيانات المحلية (لا يوجد مدير تنبيهات)")
                    
            self.apply_filters()
            self.update_unread_count()
            
        except Exception as e:
            print(f"❌ Error loading notifications: {e}")
            # Fallback to sample data
            if not self.notifications:
                self.add_sample_notifications()
        
    def add_sample_notifications(self):
        """Add sample notifications for testing"""
        sample_notifications = [
            {
                "id": "1",
                "notification_type": "📢 General Announcement",
                "priority": "medium",
                "title": "Welcome to the New System",
                "message": "We are excited to announce the launch of our new attendance management system. Please take some time to explore the new features and let us know if you have any questions.",
                "created_at": datetime.now().isoformat(),
                "admin_id": "admin1",
                "admin_name": "System Administrator",
                "status": "active",
                "is_read": False,
                "target_users": "all"
            },
            {
                "id": "2",
                "notification_type": "🔄 System Update",
                "priority": "high",
                "title": "System Maintenance Tonight",
                "message": "The system will be under maintenance from 10 PM to 2 AM tonight. Please save your work and expect some downtime during this period.",
                "created_at": datetime.now().isoformat(),
                "admin_id": "admin1",
                "admin_name": "System Administrator",
                "status": "active",
                "is_read": False,
                "target_users": "all"
            },
            {
                "id": "3",
                "notification_type": "⚠️ Important Notice",
                "priority": "urgent",
                "title": "Monthly Review Meeting",
                "message": "All employees are required to attend the monthly review meeting tomorrow at 9 AM in the main conference room. Please prepare your reports.",
                "created_at": datetime.now().isoformat(),
                "admin_id": "admin1",
                "admin_name": "System Administrator",
                "status": "active",
                "is_read": True,
                "target_users": "all"
            }
        ]
        
        self.notifications.extend(sample_notifications)
        
    def apply_filters(self):
        """Apply selected filters to notifications"""
        # Safety check: ensure notifications_layout is properly initialized
        if not hasattr(self, 'notifications_layout') or self.notifications_layout is None:
            print("Warning: notifications_layout not initialized, skipping apply_filters")
            return
            
        # Clear existing notifications
        for i in reversed(range(self.notifications_layout.count())):
            widget = self.notifications_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
            
        # Get filter states
        show_unread = self.show_unread.isChecked()
        show_read = self.show_read.isChecked()
        
        # Get priority filters
        priority_filters = []
        if self.priority_urgent.isChecked():
            priority_filters.append("urgent")
        if self.priority_high.isChecked():
            priority_filters.append("high")
        if self.priority_medium.isChecked():
            priority_filters.append("medium")
        if self.priority_low.isChecked():
            priority_filters.append("low")
            
        # Get type filters
        type_filters = []
        if self.type_general.isChecked():
            type_filters.append("General Announcement")
        if self.type_update.isChecked():
            type_filters.append("System Update")
        if self.type_important.isChecked():
            type_filters.append("Important Notice")
        if self.type_event.isChecked():
            type_filters.append("Celebration/Event")
        if self.type_maintenance.isChecked():
            type_filters.append("Maintenance Notice")
        if self.type_training.isChecked():
            type_filters.append("Training/Workshop")
        if self.type_policy.isChecked():
            type_filters.append("Policy Change")
        if self.type_emergency.isChecked():
            type_filters.append("Emergency Alert")
        if self.type_document.isChecked():
            type_filters.append("Document/Resource")
        if self.type_download.isChecked():
            type_filters.append("Download Link")
        if self.type_website.isChecked():
            type_filters.append("Website Link")
            
        # Filter notifications
        filtered_notifications = []
        for notification in self.notifications:
            # Check status filter
            is_read = notification.get("is_read", False)
            if is_read and not show_read:
                continue
            if not is_read and not show_unread:
                continue
                
            # Check priority filter
            priority = notification.get("priority", "medium")
            if priority not in priority_filters:
                continue
                
            # Check type filter
            notification_type = notification.get("notification_type", "")
            if not any(type_filter in notification_type for type_filter in type_filters):
                continue
                
            filtered_notifications.append(notification)
            
        # Display filtered notifications
        if filtered_notifications:
            self.empty_state.setVisible(False)
            for notification in filtered_notifications:
                notification_widget = self.create_notification_widget(notification)
                if notification_widget is not None:
                    self.notifications_layout.addWidget(notification_widget)
        else:
            self.empty_state.setVisible(True)
            
        # Add stretch to push notifications to top
        self.notifications_layout.addStretch()
        
    def create_notification_widget(self, notification: Dict[str, Any]):
        """Create a beautiful, clear, and easy-to-read notification widget"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Enhanced styling with better contrast and readability
        is_read = notification.get("is_read", False)
        if not is_read:
            widget.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffffff, stop:1 #f0f8ff);
                    border: 3px solid #1e88e5;
                    border-radius: 20px;
                    padding: 25px;
                    margin: 15px;
                }
                QFrame:hover {
                    border-color: #1565c0;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #f0f8ff, stop:1 #e3f2fd);
                }
            """)
        else:
            widget.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffffff, stop:1 #fafafa);
                    border: 2px solid #e0e0e0;
                    border-radius: 20px;
                    padding: 25px;
                    margin: 15px;
                }
                QFrame:hover {
                    border-color: #1e88e5;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #fafafa, stop:1 #f0f8ff);
                }
            """)
        
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Enhanced header with clear visual hierarchy
        header_layout = QHBoxLayout()
        header_layout.setSpacing(25)
        
        # Notification type with clear icon and styling
        notification_type = notification.get("notification_type", "Notification")
        type_label = QLabel(f"📢 {notification_type}")
        type_label.setStyleSheet("""
            font-weight: 700; 
            color: #ffffff; 
            font-size: 16px;
            padding: 12px 20px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #3f51b5, stop:1 #5c6bc0);
            border-radius: 12px;
            border: 2px solid #303f9f;
        """)
        
        # Priority with clear color coding
        priority = notification.get("priority", "medium")
        priority_label = QLabel(f"⚡ {priority.upper()}")
        priority_colors = {
            "urgent": {"bg": "#f44336", "border": "#d32f2f", "text": "white"},
            "high": {"bg": "#ff9800", "border": "#f57c00", "text": "white"},
            "medium": {"bg": "#ffc107", "border": "#ffa000", "text": "#212121"},
            "low": {"bg": "#4caf50", "border": "#388e3c", "text": "white"}
        }
        priority_style = priority_colors.get(priority, {"bg": "#9e9e9e", "border": "#757575", "text": "white"})
        priority_label.setStyleSheet(f"""
            color: {priority_style['text']}; 
            font-weight: 700; 
            font-size: 14px; 
            padding: 10px 16px; 
            background-color: {priority_style['bg']}; 
            border: 2px solid {priority_style['border']};
            border-radius: 10px;
        """)
        
        # Clear timestamp display
        timestamp = notification.get("created_at") or notification.get("timestamp")
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = str(timestamp)
        else:
            time_str = "Unknown"
            
        time_label = QLabel(f"🕒 {time_str}")
        time_label.setStyleSheet("""
            color: #424242; 
            font-size: 13px; 
            padding: 10px 16px; 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #f5f5f5, stop:1 #eeeeee);
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            font-weight: 600;
        """)
        
        header_layout.addWidget(type_label)
        header_layout.addStretch()
        header_layout.addWidget(priority_label)
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Enhanced title with clear typography and emphasis
        title_label = QLabel(notification.get("title", "No Title"))
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: 700; 
            color: #212121; 
            margin: 20px 0; 
            padding: 15px 20px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #f8f9fa, stop:1 #e9ecef);
            border-radius: 12px;
            border-left: 6px solid #1e88e5;
            line-height: 1.4;
        """)
        layout.addWidget(title_label)
        
        # Enhanced message with excellent readability
        message_label = QLabel(notification.get("message", "No Message"))
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            color: #424242; 
            margin: 20px 0; 
            font-size: 16px; 
            line-height: 1.7; 
            padding: 20px;
            background-color: #ffffff;
            border-radius: 12px;
            border: 2px solid #e8eaf6;
            font-weight: 500;
            text-align: justify;
        """)
        # Ensure message is fully visible
        message_label.setMinimumHeight(80)
        message_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(message_label)
        
        # Enhanced spacing before links
        layout.addSpacing(20)
        
        # Enhanced links section with clear visual separation
        links = notification.get("links", [])
        if links:
            links_group = QGroupBox("🔗 Links & Resources")
            links_group.setStyleSheet("""
                QGroupBox {
                    font-weight: 700;
                    font-size: 16px;
                    padding: 20px;
                    border: 3px solid #e3f2fd;
                    border-radius: 15px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffffff, stop:1 #f3f8ff);
                    margin-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 20px;
                    padding: 0 15px 0 15px;
                    color: #1976d2;
                    background-color: #ffffff;
                }
            """)
            links_layout = QVBoxLayout()
            links_layout.setSpacing(15)
            
            for i, link in enumerate(links):
                link_layout = QHBoxLayout()
                link_layout.setSpacing(20)
                
                # Enhanced link icon based on type
                link_type = self._get_link_type(link)
                icon_map = {
                    "document": "📄",
                    "download": "📥",
                    "video": "🎥",
                    "image": "🖼️",
                    "website": "🌐"
                }
                icon = icon_map.get(link_type, "🔗")
                
                # Enhanced link label with better styling and readability
                link_label = QLabel(f"{icon} {link}")
                link_label.setStyleSheet("""
                    font-size: 14px;
                    color: #1976d2;
                    padding: 12px 16px;
                    background-color: #f8f9fa;
                    border: 2px solid #e3f2fd;
                    border-radius: 8px;
                    font-weight: 600;
                    line-height: 1.4;
                """)
                link_label.setWordWrap(True)
                link_label.mousePressEvent = lambda e, url=link: self._open_link(url)
                link_label.setCursor(Qt.CursorShape.PointingHandCursor)
                
                # Enhanced copy button with clear design
                copy_button = QPushButton("📋 Copy")
                copy_button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #4caf50, stop:1 #66bb6a);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 8px;
                        font-weight: 700;
                        font-size: 13px;
                        min-width: 90px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #66bb6a, stop:1 #81c784);
                    }
                    QPushButton:pressed {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #388e3c, stop:1 #4caf50);
                    }
                """)
                copy_button.clicked.connect(lambda checked, url=link: self._copy_link(url))
                
                link_layout.addWidget(link_label)
                link_layout.addWidget(copy_button)
                links_layout.addLayout(link_layout)
            
            links_group.setLayout(links_layout)
            layout.addWidget(links_group)
        
        # Enhanced footer with clear action buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(25)
        
        if not is_read:
            mark_read_button = QPushButton("✅ Mark as Read")
            mark_read_button.setMinimumHeight(50)
            mark_read_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #4caf50, stop:1 #66bb6a);
                    color: white;
                    border: none;
                    padding: 15px 25px;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: 700;
                    min-height: 50px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #66bb6a, stop:1 #81c784);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #388e3c, stop:1 #4caf50);
                }
            """)
            mark_read_button.clicked.connect(lambda: self.mark_as_read(notification["id"]))
            footer_layout.addWidget(mark_read_button)
        
        footer_layout.addStretch()
        
        # Enhanced status indicator with clear visual feedback
        status_text = "📖 Read" if is_read else "📖 Unread"
        status_label = QLabel(status_text)
        status_style = {
            "read": {"color": "#2e7d32", "bg": "#e8f5e8", "border": "#c8e6cb"},
            "unread": {"color": "#d32f2f", "bg": "#ffebee", "border": "#ffcdd2"}
        }
        status_style_data = status_style["read" if is_read else "unread"]
        status_label.setStyleSheet(f"""
            color: {status_style_data['color']}; 
            font-size: 15px; 
            font-weight: 700;
            padding: 12px 20px; 
            background-color: {status_style_data['bg']};
            border-radius: 10px; 
            border: 2px solid {status_style_data['border']};
        """)
        footer_layout.addWidget(status_label)
        
        layout.addLayout(footer_layout)
        
        widget.setLayout(layout)
        return widget
    
    def _get_link_type(self, link):
        """Determine the type of link"""
        link_lower = link.lower()
        if any(ext in link_lower for ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']):
            return "document"
        elif any(ext in link_lower for ext in ['.zip', '.rar', '.exe', '.msi', '.dmg']):
            return "download"
        elif any(ext in link_lower for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv']):
            return "video"
        elif any(ext in link_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
            return "image"
        else:
            return "website"
    
    def _open_link(self, url):
        """Open link in default browser"""
        try:
            import webbrowser
            webbrowser.open(url)
            print(f"✅ Opened link: {url}")
        except Exception as e:
            print(f"❌ Failed to open link: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open link:\n{url}")
    
    def _copy_link(self, url):
        """Copy link to clipboard"""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(url)
            print(f"✅ Copied link to clipboard: {url}")
            
            # Show temporary success message
            QMessageBox.information(self, "Success", "Link copied to clipboard!")
        except Exception as e:
            print(f"❌ Failed to copy link: {e}")
            QMessageBox.warning(self, "Error", "Failed to copy link to clipboard")
        
    def mark_as_read(self, notification_id: str):
        """Mark a notification as read"""
        try:
            if self.notifications_manager:
                # Mark as read in database
                success = self.notifications_manager.mark_as_read(int(notification_id), str(self.user_id))
                if success:
                    print(f"✅ Marked notification {notification_id} as read in database")
                else:
                    print(f"❌ Failed to mark notification {notification_id} as read in database")
            
            # Update local notification
            for notification in self.notifications:
                if str(notification["id"]) == str(notification_id):
                    notification["is_read"] = True
                    break
                    
            self.apply_filters()
            self.update_unread_count()
            
        except Exception as e:
            print(f"❌ Error marking notification as read: {e}")
            
    def mark_all_as_read(self):
        """Mark all notifications as read"""
        reply = QMessageBox.question(
            self, 
            "Confirm Action", 
            "Are you sure you want to mark all notifications as read?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.notifications_manager:
                    # Mark all as read in database
                    for notification in self.notifications:
                        if not notification.get("is_read", False):
                            self.notifications_manager.mark_as_read(
                                int(notification["id"]), 
                                str(self.user_id)
                            )
                
                # Update local notifications
                for notification in self.notifications:
                    notification["is_read"] = True
                    
                self.apply_filters()
                self.update_unread_count()
                
                print("✅ Marked all notifications as read")
                
            except Exception as e:
                print(f"❌ Error marking all notifications as read: {e}")
                
    def update_unread_count(self):
        """Update the unread count badge"""
        try:
            if self.notifications_manager:
                # Get unread count from manager
                unread_count = self.notifications_manager.get_unread_count(
                    user_id=self.user_id,
                    user_role=self.user_role
                )
            else:
                # Calculate from local data
                unread_count = sum(1 for n in self.notifications if not n.get("is_read", False))
                
            self.unread_count = unread_count
            self.unread_badge.setText(str(unread_count))
            
            # Hide badge if no unread notifications
            if unread_count == 0:
                self.unread_badge.setVisible(False)
            else:
                self.unread_badge.setVisible(True)
                
        except Exception as e:
            print(f"❌ Error updating unread count: {e}")
            
    def add_notification(self, notification: Dict[str, Any]):
        """Add a new notification to the list"""
        try:
            # Check if notification is targeted to this user
            if not self._is_notification_targeted(notification):
                return
                
            # Add ID if not present
            if "id" not in notification:
                notification["id"] = str(len(self.notifications) + 1)
                
            # Set status as unread
            notification["is_read"] = False
            notification["status"] = "active"
            
            # Add timestamp if not present
            if "created_at" not in notification and "timestamp" not in notification:
                notification["created_at"] = datetime.now().isoformat()
                
            # Add to list
            self.notifications.insert(0, notification)
            
            # Refresh display
            self.apply_filters()
            self.update_unread_count()
            
            print(f"✅ Added new notification: {notification.get('title', 'No Title')}")
            
        except Exception as e:
            print(f"❌ Error adding notification: {e}")
            
    def closeEvent(self, event):
        """Cleanup when widget is closed"""
        try:
            if hasattr(self, 'auto_refresh_timer'):
                self.auto_refresh_timer.stop()
                
            if self.notifications_manager:
                self.notifications_manager.cleanup()
                
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
        event.accept()
