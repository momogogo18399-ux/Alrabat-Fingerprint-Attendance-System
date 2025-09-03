#!/usr/bin/env python3
"""
Gentle Notification Window - Gentle Notification Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer


class GentleNotification(QWidget):
    """
    نافذة إشعار لطيفة تظهر من الأسفل بدون إزعاج
    """
    
    def __init__(self, parent=None, title="", message="", notification_type="info"):
        super().__init__(parent)
        
        self.title = title
        self.message = message
        self.notification_type = notification_type
        
        # إعدادات النافذة
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # بدون إطار
            Qt.WindowType.Tool |                 # نافذة أداة
            Qt.WindowType.WindowStaysOnTopHint  # تبقى في الأعلى
        )
        
        # إعدادات الشكل
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 80)
        
        # إعداد الواجهة
        self.setup_ui()
        self.setup_animations()
        self.setup_styles()
        
        # مؤقت الإخفاء التلقائي
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.timeout.connect(self.hide)
        
        # مؤقت التلاشي التدريجي
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.fade_out)
        
    def setup_ui(self):
        """إعداد عناصر الواجهة"""
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # الإطار الرئيسي
        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")
        
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(8)
        
        # صف العنوان والرسالة
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # أيقونة النوع
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.set_icon()
        content_layout.addWidget(self.icon_label)
        
        # عمود النص
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        # العنوان
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        text_layout.addWidget(self.title_label)
        
        # الرسالة
        self.message_label = QLabel(self.message)
        self.message_label.setObjectName("messageLabel")
        self.message_label.setFont(QFont("Arial", 9))
        self.message_label.setWordWrap(True)
        text_layout.addWidget(self.message_label)
        
        content_layout.addLayout(text_layout)
        
        # زر الClose
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.hide)
        content_layout.addWidget(self.close_button)
        
        frame_layout.addLayout(content_layout)
        
        # Add الإطار إلى التخطيط الرئيسي
        main_layout.addWidget(self.main_frame)
        
        # Add تأثير الظل
        self.add_shadow_effect()
        
    def setup_animations(self):
        """إعداد الحركات"""
        # حركة الظهور
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(300)
        self.show_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # حركة الإخفاء
        self.hide_animation = QPropertyAnimation(self, b"geometry")
        self.hide_animation.setDuration(300)
        self.hide_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.hide_animation.finished.connect(self.deleteLater)
        
    def setup_styles(self):
        """إعداد الأنماط"""
        # تحديد النوع
        if self.notification_type == "info":
            self.set_info_style()
        elif self.notification_type == "warning":
            self.set_warning_style()
        elif self.notification_type == "success":
            self.set_success_style()
        elif self.notification_type == "error":
            self.set_error_style()
        else:
            self.set_info_style()
    
    def set_info_style(self):
        """نمط الInformation"""
        self.main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 10px;
                color: #1565c0;
            }
        """)
        
        self.title_label.setStyleSheet("color: #1565c0;")
        self.message_label.setStyleSheet("color: #1976d2;")
        self.close_button.setStyleSheet("""
            QPushButton#closeButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#closeButton:hover {
                background-color: #1976d2;
            }
            QPushButton#closeButton:pressed {
                background-color: #1565c0;
            }
        """)
    
    def set_warning_style(self):
        """نمط الWarning"""
        self.main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 10px;
                color: #e65100;
            }
        """)
        
        self.title_label.setStyleSheet("color: #e65100;")
        self.message_label.setStyleSheet("color: #f57c00;")
        self.close_button.setStyleSheet("""
            QPushButton#closeButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#closeButton:hover {
                background-color: #f57c00;
            }
            QPushButton#closeButton:pressed {
                background-color: #e65100;
            }
        """)
    
    def set_success_style(self):
        """نمط النجاح"""
        self.main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
                border-radius: 10px;
                color: #2e7d32;
            }
        """)
        
        self.title_label.setStyleSheet("color: #2e7d32;")
        self.message_label.setStyleSheet("color: #388e3c;")
        self.close_button.setStyleSheet("""
            QPushButton#closeButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#closeButton:hover {
                background-color: #388e3c;
            }
            QPushButton#closeButton:pressed {
                background-color: #2e7d32;
            }
        """)
    
    def set_error_style(self):
        """نمط الError"""
        self.main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: #ffebee;
                border: 2px solid #f44336;
                border-radius: 10px;
                color: #c62828;
            }
        """)
        
        self.title_label.setStyleSheet("color: #c62828;")
        self.message_label.setStyleSheet("color: #d32f2f;")
        self.close_button.setStyleSheet("""
            QPushButton#closeButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#closeButton:hover {
                background-color: #d32f2f;
            }
            QPushButton#closeButton:pressed {
                background-color: #c62828;
            }
        """)
    
    def set_icon(self):
        """تعيين الأيقونة حسب النوع"""
        if self.notification_type == "info":
            self.icon_label.setText("ℹ️")
        elif self.notification_type == "warning":
            self.icon_label.setText("⚠️")
        elif self.notification_type == "success":
            self.icon_label.setText("✅")
        elif self.notification_type == "error":
            self.icon_label.setText("❌")
        else:
            self.icon_label.setText("ℹ️")
    
    def add_shadow_effect(self):
        """Add تأثير الظل"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.main_frame.setGraphicsEffect(shadow)
    
    def showEvent(self, event):
        """عند ظهور النافذة"""
        super().showEvent(event)
        
        # بدء حركة الظهور
        self.animate_show()
        
        # بدء مؤقت الإخفاء التلقائي
        self.auto_hide_timer.start(5000)  # 5 ثوانٍ
    
    def animate_show(self):
        """حركة الظهور"""
        # حساب الموقع النهائي
        final_rect = self.geometry()
        
        # الموقع الأولي (أسفل النافذة)
        start_rect = QRect(
            final_rect.x(),
            final_rect.y() + 100,  # 100 بكسل أسفل
            final_rect.width(),
            final_rect.height()
        )
        
        # تعيين الموقع الأولي
        self.setGeometry(start_rect)
        
        # بدء الحركة
        self.show_animation.setStartValue(start_rect)
        self.show_animation.setEndValue(final_rect)
        self.show_animation.start()
    
    def hideEvent(self, event):
        """عند إخفاء النافذة"""
        # إيقاف المؤقتات
        self.auto_hide_timer.stop()
        self.fade_timer.stop()
        
        super().hideEvent(event)
    
    def fade_out(self):
        """تلاشي تدريجي"""
        current_opacity = self.windowOpacity()
        if current_opacity > 0:
            self.setWindowOpacity(current_opacity - 0.1)
        else:
            self.hide()
    
    def mousePressEvent(self, event):
        """معالجة النقر"""
        if event.button() == Qt.MouseButton.LeftButton:
            # عند النقر، إخفاء الإشعار
            self.hide()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """عند دخول الماوس"""
        # إيقاف الإخفاء التلقائي عند دخول الماوس
        self.auto_hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """عند خروج الماوس"""
        # إعادة بدء الإخفاء التلقائي عند خروج الماوس
        self.auto_hide_timer.start(3000)  # 3 ثوانٍ إضافية
        super().leaveEvent(event)
