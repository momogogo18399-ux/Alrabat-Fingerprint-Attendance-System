#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Notifications Widget - Optimized Design with Progress Bar and Status
Fast and efficient widget for administrators to send notifications
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QComboBox, QLineEdit, QMessageBox, QScrollArea,
    QFrame, QCheckBox, QGroupBox, QSizePolicy, QProgressBar,
    QStackedWidget, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

try:
    from app.core.notifications_manager import NotificationsManager
    NOTIFICATIONS_MANAGER_AVAILABLE = True
    print("✅ NotificationsManager imported successfully")
except ImportError:
    NOTIFICATIONS_MANAGER_AVAILABLE = False
    print("⚠️ NotificationsManager not available")

class AsyncNotificationsLoader(QThread):
    """Thread for loading notifications asynchronously"""
    
    notifications_loaded = pyqtSignal(list)
    status_updated = pyqtSignal(str, str)  # message, color
    progress_updated = pyqtSignal(int)
    
    def __init__(self, supabase_url=None, supabase_key=None):
        super().__init__()
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        
    def run(self):
        """Run the async loading process"""
        try:
            self.status_updated.emit("🔍 Initializing notifications system...", "#0078d4")
            self.progress_updated.emit(10)
            
            # Simulate initialization delay
            self.msleep(100)
            self.progress_updated.emit(30)
            
            if NOTIFICATIONS_MANAGER_AVAILABLE:
                self.status_updated.emit("🚀 Setting up Supabase connection...", "#0078d4")
                self.progress_updated.emit(50)
                
                try:
                    # Initialize notifications manager
                    if not self.supabase_url:
                        self.supabase_url = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
                    if not self.supabase_key:
                        self.supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
                    
                    if (self.supabase_url and self.supabase_key and 
                        not self.supabase_url.startswith('https://your-project') and
                        not self.supabase_url.startswith('https://example') and
                        len(self.supabase_key) > 50):
                        
                        self.status_updated.emit("🔗 Connecting to Supabase...", "#0078d4")
                        self.progress_updated.emit(70)
                        
                        # Initialize manager
                        notifications_manager = NotificationsManager(self.supabase_url, self.supabase_key)
                        
                        # Test connection
                        status = notifications_manager.get_status()
                        if status['mode'] == 'Supabase':
                            self.status_updated.emit("✅ Supabase connection successful!", "#28a745")
                            self.progress_updated.emit(90)
                            
                            # Load notifications
                            notifications = notifications_manager.get_notifications()
                            self.progress_updated.emit(100)
                            self.notifications_loaded.emit(notifications or [])
                        else:
                            self.status_updated.emit("⚠️ Supabase connection failed, using local mode", "#ffc107")
                            self.progress_updated.emit(100)
                            self.notifications_loaded.emit([])
                    else:
                        self.status_updated.emit("⚠️ Supabase credentials not configured", "#ffc107")
                        self.progress_updated.emit(100)
                        self.notifications_loaded.emit([])
                        
                except Exception as e:
                    self.status_updated.emit(f"❌ Supabase error: {str(e)[:50]}...", "#dc3545")
                    self.progress_updated.emit(100)
                    self.notifications_loaded.emit([])
            else:
                self.status_updated.emit("⚠️ NotificationsManager not available", "#ffc107")
                self.progress_updated.emit(100)
                self.notifications_loaded.emit([])
                
        except Exception as e:
            self.status_updated.emit(f"❌ Error: {str(e)[:50]}...", "#dc3545")
            self.progress_updated.emit(100)
            self.notifications_loaded.emit([])

class NotificationCard(QWidget):
    """Simple notification card"""
    
    def __init__(self, notification_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.notification_data = notification_data
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the modern notification card UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        
        # Main card container with modern design
        card_container = QFrame()
        card_container.setFrameStyle(QFrame.Shape.NoFrame)
        card_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin: 4px;
            }
            QFrame:hover {
                border: 2px solid #0078d4;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f8ff, stop:1 #e6f3ff);
            }
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header section with priority indicator and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Priority indicator with color coding
        priority = self.notification_data.get('priority', 'medium').lower()
        priority_colors = {
            'low': '#28a745',
            'medium': '#ffc107', 
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        priority_color = priority_colors.get(priority, '#6c757d')
        
        priority_indicator = QFrame()
        priority_indicator.setFixedSize(8, 8)
        priority_indicator.setStyleSheet(f"""
            QFrame {{
                background-color: {priority_color};
                border-radius: 4px;
                margin: 2px;
            }}
        """)
        
        # Title with improved typography
        title_label = QLabel(self.notification_data.get('title', 'No Title'))
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            QLabel {
                color: #1a1a1a;
                line-height: 1.3;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        header_layout.addWidget(priority_indicator)
        header_layout.addWidget(title_label, 1)
        
        # Type badge with modern pill design
        type_text = self.notification_data.get('notification_type', 'Unknown')
        type_badge = QLabel(type_text)
        type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_badge.setStyleSheet(f"""
            QLabel {{
                color: #495057;
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 16px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
                min-width: 80px;
            }}
        """)
        
        header_layout.addWidget(type_badge)
        
        # Message section with enhanced styling and proper text wrapping
        message_container = QFrame()
        message_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #f1f3f4;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        message_layout = QVBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(8)
        
        # Message with proper text wrapping using QTextEdit for better control
        message_text = self.notification_data.get('message', 'No message')
        
        message_label = QTextEdit()
        message_label.setPlainText(message_text)
        message_label.setReadOnly(True)
        message_label.setMaximumHeight(80)
        message_label.setMaximumWidth(400)
        message_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        message_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        message_label.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        message_label.setStyleSheet("""
            QTextEdit {
                color: #2c3e50;
                line-height: 1.5;
                font-size: 11px;
                margin: 0px;
                padding: 8px;
                background-color: transparent;
                border: none;
                outline: none;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QTextEdit QScrollBar:vertical {
                width: 8px;
                background: #f0f0f0;
                border-radius: 4px;
            }
            QTextEdit QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        message_layout.addWidget(message_label)
        
        # Display links if available with better visibility
        links = self.notification_data.get('links', [])
        if links:
            links_container = QFrame()
            links_container.setStyleSheet("""
                QFrame {
                    background-color: #f8f9ff;
                    border: 1px solid #e3e6ff;
                    border-radius: 6px;
                    padding: 8px;
                    margin-top: 8px;
                }
            """)
            
            links_layout = QVBoxLayout()
            links_layout.setContentsMargins(0, 0, 0, 0)
            links_layout.setSpacing(4)
            
            links_header = QLabel("🔗 الروابط المرفقة:")
            links_header.setStyleSheet("""
                QLabel {
                    color: #0078d4;
                    font-size: 10px;
                    font-weight: bold;
                    margin-bottom: 4px;
                }
            """)
            links_layout.addWidget(links_header)
            
            for link in links:
                link_label = QLabel(f"• {link.strip()}")
                link_label.setStyleSheet("""
                    QLabel {
                        color: #0056b3;
                        font-size: 10px;
                        font-style: italic;
                        margin-left: 8px;
                    }
                """)
                link_label.setWordWrap(True)
                links_layout.addWidget(link_label)
            
            links_container.setLayout(links_layout)
            message_layout.addWidget(links_container)
        
        message_container.setLayout(message_layout)
        
        # Footer section with metadata and actions
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        
        # Date and time with icon
        created_at = self.notification_data.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = dt.strftime("%b %d, %Y at %H:%M")
            except:
                date_str = created_at
        else:
            date_str = "Unknown"
            
        date_label = QLabel(f"📅 {date_str}")
        date_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 10px;
                font-style: italic;
            }
        """)
        
        # Target users with icon
        target_users = self.notification_data.get('target_users', 'All Users')
        target_label = QLabel(f"👥 {target_users}")
        target_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 10px;
                font-style: italic;
            }
        """)
        
        footer_layout.addWidget(date_label)
        footer_layout.addWidget(target_label)
        footer_layout.addStretch()
        
        # Action buttons with modern design
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)
        
        # Read status indicator
        is_read = self.notification_data.get('is_read', False)
        status_icon = "✅" if is_read else "🔴"
        status_label = QLabel(status_icon)
        status_label.setToolTip("Read" if is_read else "Unread")
        status_label.setStyleSheet("font-size: 12px;")
        
        # Delete button with improved styling
        delete_button = QPushButton("🗑️")
        delete_button.setToolTip("Delete Notification")
        delete_button.setFixedSize(32, 32)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 16px;
                color: #6c757d;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc3545;
                border-color: #dc3545;
                color: white;
            }
            QPushButton:pressed {
                background-color: #c82333;
                border-color: #c82333;
            }
        """)
        delete_button.clicked.connect(self.delete_notification)
        
        actions_layout.addWidget(status_label)
        actions_layout.addWidget(delete_button)
        
        footer_layout.addLayout(actions_layout)
        
        # Assemble the card
        card_layout.addLayout(header_layout)
        card_layout.addWidget(message_container)
        card_layout.addLayout(footer_layout)
        
        card_container.setLayout(card_layout)
        layout.addWidget(card_container)
        self.setLayout(layout)
        
        # Set flexible height based on content
        self.setMinimumHeight(160)
        self.setMaximumHeight(300)
        
    def delete_notification(self):
        """Delete this notification"""
        reply = QMessageBox.question(
            self, 
            "Delete Notification", 
            "Are you sure you want to delete this notification?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Find the parent widget that has delete_notification method
            parent = self.parent()
            while parent and not hasattr(parent, 'delete_notification'):
                parent = parent.parent()
            
            if parent and hasattr(parent, 'delete_notification'):
                parent.delete_notification(self.notification_data['id'])
            else:
                print("❌ Could not find parent with delete_notification method")

class AdminNotificationsWidget(QWidget):
    """Admin Notifications Tab - Optimized Design with Progress Bar and Status"""
    
    notification_sent = pyqtSignal(str, str)  # type, message
    notification_added = pyqtSignal(dict)  # notification_data
    
    def __init__(self, db_manager=None, supabase_url=None, supabase_key=None):
        super().__init__()
        self.db_manager = db_manager
        self.notifications = []
        self.notifications_manager = None
        
        # Initialize async loader
        self.async_loader = AsyncNotificationsLoader(supabase_url, supabase_key)
        self.async_loader.notifications_loaded.connect(self._on_notifications_loaded)
        self.async_loader.status_updated.connect(self._on_status_updated)
        self.async_loader.progress_updated.connect(self._on_progress_updated)
        
        # Add sample notifications for immediate display
        self._add_sample_notifications()
        
        self.setup_ui()
        
        # Start async loading
        QTimer.singleShot(100, self._start_async_loading)
        
    def _start_async_loading(self):
        """Start the async loading process"""
        self.async_loader.start()
        
    def _on_notifications_loaded(self, notifications):
        """Handle notifications loaded from async loader"""
        if notifications:
            self.notifications = notifications
            print(f"✅ Loaded {len(self.notifications)} notifications from async loader")
        else:
            print("ℹ️ No notifications loaded from async loader, using sample data")
        
        # Update display
        self.display_notifications()
        
        # Try to get notifications manager from async loader
        try:
            if hasattr(self.async_loader, 'notifications_manager'):
                self.notifications_manager = self.async_loader.notifications_manager
        except:
            pass
        
        # Show final status
        QTimer.singleShot(500, self._show_final_status)
        
    def _on_status_updated(self, message, color):
        """Handle status updates from async loader"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
        """)
        
    def _on_progress_updated(self, value):
        """Handle progress updates from async loader"""
        self.progress_bar.setValue(value)
        if value >= 100:
            QTimer.singleShot(500, self._hide_progress)
            
    def _hide_progress(self):
        """Hide progress bar when loading is complete"""
        self.progress_container.hide()
        self.status_label.show()
        
    def _show_final_status(self):
        """Show final connection status"""
        try:
            if self.notifications_manager:
                status = self.notifications_manager.get_status()
                if status['mode'] == 'Supabase':
                    self.status_label.setText("🟢 Connected to Supabase - Real-time enabled")
                    self.status_label.setStyleSheet("""
                        background-color: #28a745;
                        color: white;
                        padding: 8px;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: bold;
                    """)
                else:
                    self.status_label.setText("🟡 Local Mode - No Supabase connection")
                    self.status_label.setStyleSheet("""
                        background-color: #ffc107;
                        color: #212529;
                        padding: 8px;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: bold;
                    """)
            else:
                self.status_label.setText("🔴 No Notifications Manager Available")
                self.status_label.setStyleSheet("""
                    background-color: #dc3545;
                    color: white;
                    padding: 8px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                """)
        except Exception as e:
            print(f"❌ Error showing final status: {e}")
            self.status_label.setText("❌ Connection Status Error")
            self.status_label.setStyleSheet("""
                background-color: #dc3545;
                color: white;
                padding: 8px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            """)
    
    def _add_sample_notifications(self):
        """Add sample notifications for immediate display"""
        sample_notifications = [
            {
                "id": 1,
                "notification_type": "System Update",
                "priority": "high",
                "target_users": "All Users",
                "title": "System Update Available",
                "message": "A new system update is available. Please restart the application to apply the updates. This update includes important security patches and performance improvements.",
                "admin_id": "admin",
                "admin_name": "System Administrator",
                "created_at": datetime.now().isoformat(),
                "is_read": False,
                "links": ["https://example.com/update", "https://example.com/changelog"],
                "tags": [],
                "status": "active"
            },
            {
                "id": 2,
                "notification_type": "Maintenance",
                "priority": "medium",
                "target_users": "Employees",
                "title": "Scheduled Maintenance Notice",
                "message": "The system will be under maintenance from 2:00 AM to 4:00 AM tomorrow. During this time, some features may be temporarily unavailable. We apologize for any inconvenience.",
                "admin_id": "admin",
                "admin_name": "System Administrator",
                "created_at": datetime.now().isoformat(),
                "is_read": False,
                "links": ["https://example.com/maintenance", "https://example.com/status"],
                "tags": [],
                "status": "active"
            },
            {
                "id": 3,
                "notification_type": "General Announcement",
                "priority": "medium",
                "target_users": "All Users",
                "title": "اختبار الرسالة الطويلة جداً",
                "message": "gggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg",
                "admin_id": "admin",
                "admin_name": "System Administrator",
                "created_at": datetime.now().isoformat(),
                "is_read": False,
                "links": ["https://example.com/test-long-message", "https://example.com/another-test-link", "https://example.com/third-test-link"],
                "tags": [],
                "status": "active"
            }
        ]
        
        self.notifications.extend(sample_notifications)
    
    def setup_ui(self):
        """Setup the main UI with progress bar and status"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Admin Notifications")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress container (shown during loading)
        self.progress_container = QFrame()
        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        
        progress_label = QLabel("Loading notifications system...")
        progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_label.setStyleSheet("font-size: 12px; color: #0078d4; font-weight: bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 6px;
            }
        """)
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        self.progress_container.setLayout(progress_layout)
        
        # Status label (shown after loading)
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            background-color: #0078d4;
            color: white;
            padding: 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
        """)
        self.status_label.hide()  # Initially hidden
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left panel - Create notification
        left_panel = self._create_left_panel()
        content_layout.addWidget(left_panel)
        
        # Right panel - Notifications history
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel)
        
        # Add all elements to main layout
        main_layout.addWidget(header_label)
        main_layout.addWidget(self.progress_container)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        
    def _create_left_panel(self):
        """Create the left panel for creating notifications"""
        panel = QGroupBox("Create New Notification")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "General Announcement",
            "System Update",
            "Maintenance",
            "Emergency",
            "Policy Update"
        ])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        
        # Priority selection
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Priority:")
        self.priority_checkboxes = {}
        
        for priority in ["Low", "Medium", "High", "Urgent"]:
            checkbox = QCheckBox(priority)
            if priority == "Medium":
                checkbox.setChecked(True)
            self.priority_checkboxes[priority.lower()] = checkbox
            priority_layout.addWidget(checkbox)
        
        # Target users selection
        target_layout = QHBoxLayout()
        target_label = QLabel("Target:")
        self.target_checkboxes = {}
        
        for target in ["All Users", "Employees", "Managers"]:
            checkbox = QCheckBox(target)
            if target == "All Users":
                checkbox.setChecked(True)
            self.target_checkboxes[target.lower().replace(" ", "_")] = checkbox
            target_layout.addWidget(checkbox)
        
        # Title input
        title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter notification title...")
        
        # Message input
        message_label = QLabel("Message:")
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter notification message...")
        self.message_input.setMaximumHeight(80)
        
        # Links input
        links_label = QLabel("Links (Optional):")
        self.links_input = QLineEdit()
        self.links_input.setPlaceholderText("Enter links separated by commas...")
        
        # Send button
        send_button = QPushButton("Send Notification")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        send_button.clicked.connect(self.send_notification)
        
        # Add all elements to left panel
        layout.addLayout(type_layout)
        layout.addLayout(priority_layout)
        layout.addLayout(target_layout)
        layout.addWidget(title_label)
        layout.addWidget(self.title_input)
        layout.addWidget(message_label)
        layout.addWidget(self.message_input)
        layout.addWidget(links_label)
        layout.addWidget(self.links_input)
        layout.addWidget(send_button)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _create_right_panel(self):
        """Create the right panel for notifications history"""
        panel = QGroupBox("Notifications History")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Search and filter
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notifications...")
        self.search_input.textChanged.connect(self.filter_notifications)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Types", "General Announcement", "System Update", "Maintenance", "Emergency", "Policy Update"])
        self.filter_combo.currentTextChanged.connect(self.filter_notifications)
        
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.filter_combo)
        
        # Notifications area
        self.notifications_layout = QVBoxLayout()
        self.notifications_layout.setSpacing(8)
        
        # Scroll area for notifications
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.notifications_layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        refresh_button.clicked.connect(self.load_notifications)
        
        clear_button = QPushButton("Clear All")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        clear_button.clicked.connect(self.clear_all_notifications)
        
        actions_layout.addWidget(refresh_button)
        actions_layout.addWidget(clear_button)
        actions_layout.addStretch()
        
        # Add all elements to right panel
        layout.addLayout(filter_layout)
        layout.addWidget(scroll_area)
        layout.addLayout(actions_layout)
        
        panel.setLayout(layout)
        return panel
    
    def load_notifications(self):
        """Load notifications from storage"""
        try:
            if self.notifications_manager and hasattr(self.notifications_manager, 'get_notifications'):
                # Load from Supabase
                supabase_notifications = self.notifications_manager.get_notifications()
                if supabase_notifications:
                    self.notifications = supabase_notifications
                    print(f"✅ Loaded {len(self.notifications)} notifications from Supabase")
                else:
                    print("ℹ️ No notifications found in Supabase")
            else:
                print("ℹ️ Using local notifications")
            
            self.display_notifications()
            
        except Exception as e:
            print(f"❌ Error loading notifications: {e}")
            # Fallback to local notifications
            self.display_notifications()
    
    def display_notifications(self):
        """Display notifications in the UI with improved spacing"""
        # Clear existing notifications
        for i in range(self.notifications_layout.count()):
            item = self.notifications_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Add notifications with better spacing
        for i, notification in enumerate(self.notifications):
            # Add spacing between cards
            if i > 0:
                spacer = QFrame()
                spacer.setFixedHeight(16)
                spacer.setStyleSheet("background-color: transparent;")
                self.notifications_layout.addWidget(spacer)
            
            card = NotificationCard(notification, self)
            self.notifications_layout.addWidget(card)
        
        # Add stretch at the end
        self.notifications_layout.addStretch()
        
    def send_notification(self):
        """Send new notification to Supabase and local storage"""
        title = self.title_input.text().strip()
        message = self.message_input.toPlainText().strip()
        
        if not title or not message:
            QMessageBox.warning(self, "Warning", "Please enter title and message")
            return
        
        # Determine priority
        priority = "medium"  # default
        for key, checkbox in self.priority_checkboxes.items():
            if checkbox.isChecked():
                priority = key
                break
        
        # Determine targets
        target = "all"  # default
        for key, checkbox in self.target_checkboxes.items():
            if checkbox.isChecked():
                target = key
                break
        
        # Process links
        links = []
        links_text = self.links_input.text().strip()
        if links_text:
            links = [link.strip() for link in links_text.split(',') if link.strip()]
        
        # Create new notification
        new_notification = {
            "id": len(self.notifications) + 1,
            "notification_type": self.type_combo.currentText(),
            "priority": priority,
            "target_users": target,
            "title": title,
            "message": message,
            "admin_id": "admin",
            "admin_name": "Current Administrator",
            "created_at": datetime.now().isoformat(),
            "is_read": False,
            "links": links,
            "tags": [],
            "status": "active"
        }
        
        # Try to send to Supabase first
        if self.notifications_manager and hasattr(self.notifications_manager, 'send_notification'):
            try:
                print("🚀 Attempting to send notification to Supabase...")
                # Send to Supabase
                result = self.notifications_manager.send_notification(new_notification)
                if result:
                    print("✅ Notification sent to Supabase successfully!")
                    QMessageBox.information(self, "Success", "Notification sent to Supabase and all users!")
                else:
                    print("⚠️ Failed to send to Supabase, using local storage")
                    # Fallback to local storage
                    self._add_local_notification(new_notification)
                    QMessageBox.information(self, "Success", "Notification sent to local storage!")
            except Exception as e:
                print(f"⚠️ Supabase error: {e}, using local storage")
                # Fallback to local storage
                self._add_local_notification(new_notification)
                QMessageBox.information(self, "Success", "Notification sent to local storage!")
        else:
            # No Supabase manager, use local storage
            print("⚠️ No NotificationsManager available, using local storage")
            self._add_local_notification(new_notification)
            QMessageBox.information(self, "Success", "Notification sent to local storage!")
        
        # Clear fields
        self.title_input.clear()
        self.message_input.clear()
        self.links_input.clear()
        
    def _add_local_notification(self, notification):
        """Add notification to local storage"""
        # Add notification to list
        self.notifications.insert(0, notification)
        
        # Update display
        self.display_notifications()
        
        # Emit signal for other parts of the system
        self.notification_added.emit(notification)
        
    def filter_notifications(self):
        """Filter notifications by search and type"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        
        # Hide all notifications
        for i in range(self.notifications_layout.count()):
            item = self.notifications_layout.itemAt(i)
            if item.widget():
                item.widget().hide()
        
        # Show matching notifications
        for i in range(self.notifications_layout.count()):
            item = self.notifications_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'notification_data'):
                notification = item.widget().notification_data
                
                # Check search text
                title_match = search_text in notification.get('title', '').lower()
                message_match = search_text in notification.get('message', '').lower()
                search_match = title_match or message_match
                
                # Check type filter
                type_match = filter_type == "All Types" or filter_type == notification.get('notification_type', '')
                
                if search_match and type_match:
                    item.widget().show()
    
    def delete_notification(self, notification_id):
        """Delete a notification"""
        try:
            if self.notifications_manager and hasattr(self.notifications_manager, 'delete_notification'):
                # Delete from Supabase
                result = self.notifications_manager.delete_notification(notification_id)
                if result:
                    print(f"✅ Notification {notification_id} deleted from Supabase")
                else:
                    print(f"⚠️ Failed to delete notification {notification_id} from Supabase")
            
            # Remove from local list
            self.notifications = [n for n in self.notifications if n['id'] != notification_id]
            
            # Update display
            self.display_notifications()
            
        except Exception as e:
            print(f"❌ Error deleting notification: {e}")
    
    def clear_all_notifications(self):
        """Clear all notifications"""
        reply = QMessageBox.question(
            self, 
            "Clear All Notifications", 
            "Are you sure you want to delete all notifications? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.notifications_manager and hasattr(self.notifications_manager, 'clear_all_notifications'):
                    # Clear from Supabase
                    result = self.notifications_manager.clear_all_notifications()
                    if result:
                        print("✅ All notifications cleared from Supabase")
                    else:
                        print("⚠️ Failed to clear notifications from Supabase")
                
                # Clear local list
                self.notifications.clear()
                
                # Update display
                self.display_notifications()
                
            except Exception as e:
                print(f"❌ Error clearing notifications: {e}")
    
    def closeEvent(self, event):
        """Clean up when widget is closed"""
        if hasattr(self, 'async_loader') and self.async_loader.isRunning():
            self.async_loader.quit()
            self.async_loader.wait()
        event.accept()
