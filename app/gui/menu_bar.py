#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Menu Bar for the Attendance System
Based on existing features and functionality
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QAction, QToolBar, 
    QStatusBar, QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

class MainMenuBar(QMainWindow):
    """Main Menu Bar with all existing features"""
    
    # Signals for menu actions
    menu_action_triggered = pyqtSignal(str, str)  # menu_name, action_name
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fingerprint Attendance System - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize menu bar
        self.init_menu_bar()
        
        # Initialize tool bar
        self.init_tool_bar()
        
        # Initialize status bar
        self.init_status_bar()
        
        # Setup connections
        self.setup_connections()
        
        # Initialize sync timer
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.auto_sync)
        self.sync_timer.start(30000)  # 30 seconds
        
    def init_menu_bar(self):
        """Initialize the main menu bar"""
        menubar = self.menuBar()
        menubar.setFont(QFont("Segoe UI", 9))
        
        # File Menu
        self.create_file_menu(menubar)
        
        # QR Scanner Menu
        self.create_qr_scanner_menu(menubar)
        
        # Employees Menu
        self.create_employees_menu(menubar)
        
        # Attendance Menu
        self.create_attendance_menu(menubar)
        
        # Reports Menu
        self.create_reports_menu(menubar)
        
        # Company Menu
        self.create_company_menu(menubar)
        
        # Users Menu
        self.create_users_menu(menubar)
        
        # Settings Menu
        self.create_settings_menu(menubar)
        
        # Sync Menu
        self.create_sync_menu(menubar)
        
        # Notifications Menu
        self.create_notifications_menu(menubar)
        
        # AI Assistant Menu
        self.create_ai_assistant_menu(menubar)
        
        # Analytics Menu
        self.create_analytics_menu(menubar)
        
        # Security Menu
        self.create_security_menu(menubar)
        
        # Help Menu
        self.create_help_menu(menubar)
        
        # Create toolbar actions after all menus are created
        self.create_toolbar_actions()
    
    def create_toolbar_actions(self):
        """Create toolbar actions after menus are created"""
        if hasattr(self, 'main_toolbar'):
            # Find actions by searching through all menus
            scan_qr_action = self.find_action_by_text("Scan QR Code")
            add_emp_action = self.find_action_by_text("Add Employee")
            record_att_action = self.find_action_by_text("Record Attendance")
            reports_action = self.find_action_by_text("Attendance Reports")
            settings_action = self.find_action_by_text("General Settings")
            sync_now_action = self.find_action_by_text("Sync Now")
            
            # Add toolbar actions
            if scan_qr_action:
                self.main_toolbar.addAction(scan_qr_action)
            self.main_toolbar.addSeparator()
            
            if add_emp_action:
                self.main_toolbar.addAction(add_emp_action)
            if record_att_action:
                self.main_toolbar.addAction(record_att_action)
            self.main_toolbar.addSeparator()
            
            if reports_action:
                self.main_toolbar.addAction(reports_action)
            if settings_action:
                self.main_toolbar.addAction(settings_action)
            self.main_toolbar.addSeparator()
            
            if sync_now_action:
                self.main_toolbar.addAction(sync_now_action)
    
    def find_action_by_text(self, text):
        """Find action by text in all menus"""
        menubar = self.menuBar()
        for action in menubar.actions():
            if action.text() == text:
                return action
            # Check submenus
            if action.menu():
                for sub_action in action.menu().actions():
                    if sub_action.text() == text:
                        return sub_action
        return None
    
    def create_file_menu(self, menubar):
        """Create File menu"""
        file_menu = menubar.addMenu("&File")
        
        # New Project
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new project")
        new_action.triggered.connect(lambda: self.menu_action_triggered.emit("File", "New Project"))
        file_menu.addAction(new_action)
        
        # Open Project
        open_action = QAction("&Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Open Project"))
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save Project
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save current project")
        save_action.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Save Project"))
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Export Data
        export_menu = QMenu("&Export Data", self)
        export_excel = QAction("Export to &Excel", self)
        export_excel.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Export Excel"))
        export_menu.addAction(export_excel)
        
        export_pdf = QAction("Export to &PDF", self)
        export_pdf.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Export PDF"))
        export_menu.addAction(export_pdf)
        
        export_csv = QAction("Export to &CSV", self)
        export_csv.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Export CSV"))
        export_menu.addAction(export_csv)
        
        file_menu.addMenu(export_menu)
        
        # Import Data
        import_menu = QMenu("&Import Data", self)
        import_excel = QAction("Import from &Excel", self)
        import_excel.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Import Excel"))
        import_menu.addAction(import_excel)
        
        import_csv = QAction("Import from &CSV", self)
        import_csv.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Import CSV"))
        import_menu.addAction(import_csv)
        
        file_menu.addMenu(import_menu)
        
        file_menu.addSeparator()
        
        # Print Reports
        print_action = QAction("&Print Reports", self)
        print_action.setShortcut("Ctrl+P")
        print_action.setStatusTip("Print current reports")
        print_action.triggered.connect(lambda: self.menu_action_triggered.emit("File", "Print Reports"))
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def create_qr_scanner_menu(self, menubar):
        """Create QR Scanner menu"""
        qr_menu = menubar.addMenu("&QR Scanner")
        
        # Scan QR Code
        scan_qr_action = QAction("Scan &QR Code", self)
        scan_qr_action.setShortcut("F1")
        scan_qr_action.setStatusTip("Scan QR code for attendance")
        scan_qr_action.triggered.connect(lambda: self.menu_action_triggered.emit("QR Scanner", "Scan QR Code"))
        qr_menu.addAction(scan_qr_action)
        
        # Scan Barcode
        scan_barcode_action = QAction("Scan &Barcode", self)
        scan_barcode_action.setShortcut("F2")
        scan_barcode_action.setStatusTip("Scan barcode for attendance")
        scan_barcode_action.triggered.connect(lambda: self.menu_action_triggered.emit("QR Scanner", "Scan Barcode"))
        qr_menu.addAction(scan_barcode_action)
        
        # Manual Entry
        manual_entry_action = QAction("&Manual Entry", self)
        manual_entry_action.setShortcut("F3")
        manual_entry_action.setStatusTip("Manual attendance entry")
        manual_entry_action.triggered.connect(lambda: self.menu_action_triggered.emit("QR Scanner", "Manual Entry"))
        qr_menu.addAction(manual_entry_action)
        
        qr_menu.addSeparator()
        
        # QR Settings
        qr_settings_action = QAction("QR &Settings", self)
        qr_settings_action.setStatusTip("Configure QR scanner settings")
        qr_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("QR Scanner", "QR Settings"))
        qr_menu.addAction(qr_settings_action)
        
        # Advanced QR Tools
        advanced_qr_action = QAction("&Advanced QR Tools", self)
        advanced_qr_action.setStatusTip("Advanced QR scanning tools")
        advanced_qr_action.triggered.connect(lambda: self.menu_action_triggered.emit("QR Scanner", "Advanced QR Tools"))
        qr_menu.addAction(advanced_qr_action)
    
    def create_employees_menu(self, menubar):
        """Create Employees menu"""
        emp_menu = menubar.addMenu("&Employees")
        
        # Add Employee
        add_emp_action = QAction("&Add Employee", self)
        add_emp_action.setShortcut("Ctrl+E")
        add_emp_action.setStatusTip("Add new employee")
        add_emp_action.triggered.connect(lambda: self.menu_action_triggered.emit("Employees", "Add Employee"))
        emp_menu.addAction(add_emp_action)
        
        # Edit Employee
        edit_emp_action = QAction("&Edit Employee", self)
        edit_emp_action.setShortcut("Ctrl+Shift+E")
        edit_emp_action.setStatusTip("Edit existing employee")
        edit_emp_action.triggered.connect(lambda: self.menu_action_triggered.emit("Employees", "Edit Employee"))
        emp_menu.addAction(edit_emp_action)
        
        # Delete Employee
        delete_emp_action = QAction("&Delete Employee", self)
        delete_emp_action.setShortcut("Ctrl+Del")
        delete_emp_action.setStatusTip("Delete employee")
        delete_emp_action.triggered.connect(lambda: self.menu_action_triggered.emit("Employees", "Delete Employee"))
        emp_menu.addAction(delete_emp_action)
        
        emp_menu.addSeparator()
        
        # Search Employee
        search_emp_action = QAction("&Search Employee", self)
        search_emp_action.setShortcut("Ctrl+F")
        search_emp_action.setStatusTip("Search for employee")
        search_emp_action.triggered.connect(lambda: self.menu_action_triggered.emit("Employees", "Search Employee"))
        emp_menu.addAction(search_emp_action)
        
        # Employee List
        emp_list_action = QAction("Employee &List", self)
        emp_list_action.setShortcut("Ctrl+L")
        emp_list_action.setStatusTip("View all employees")
        emp_list_action.triggered.connect(lambda: self.menu_action_triggered.emit("Employees", "Employee List"))
        emp_menu.addAction(emp_list_action)
        
        emp_menu.addSeparator()
        
        # Import/Export
        import_emp_action = QAction("&Import Employees", self)
        import_emp_action.setStatusTip("Import employees from file")
        import_emp_action.triggered.connect(lambda: self.menu_action_triggered.emit("Employees", "Import Employees"))
        emp_menu.addAction(import_emp_action)
        
        export_emp_action = QAction("&Export Employees", self)
        export_emp_action.setStatusTip("Export employees to file")
        export_emp_action.triggered.connect(lambda: self.menu_action_triggered.emit("Employees", "Export Employees"))
        emp_menu.addAction(export_emp_action)
    
    def create_attendance_menu(self, menubar):
        """Create Attendance menu"""
        att_menu = menubar.addMenu("&Attendance")
        
        # Record Attendance
        record_att_action = QAction("&Record Attendance", self)
        record_att_action.setShortcut("F5")
        record_att_action.setStatusTip("Record new attendance")
        record_att_action.triggered.connect(lambda: self.menu_action_triggered.emit("Attendance", "Record Attendance"))
        att_menu.addAction(record_att_action)
        
        # View Attendance
        view_att_action = QAction("&View Attendance", self)
        view_att_action.setShortcut("F6")
        view_att_action.setStatusTip("View attendance records")
        view_att_action.triggered.connect(lambda: self.menu_action_triggered.emit("Attendance", "View Attendance"))
        att_menu.addAction(view_att_action)
        
        # Attendance History
        history_att_action = QAction("Attendance &History", self)
        history_att_action.setShortcut("F7")
        history_att_action.setStatusTip("View attendance history")
        history_att_action.triggered.connect(lambda: self.menu_action_triggered.emit("Attendance", "Attendance History"))
        att_menu.addAction(history_att_action)
        
        att_menu.addSeparator()
        
        # Daily Summary
        daily_summary_action = QAction("&Daily Summary", self)
        daily_summary_action.setShortcut("Ctrl+D")
        daily_summary_action.setStatusTip("View daily attendance summary")
        daily_summary_action.triggered.connect(lambda: self.menu_action_triggered.emit("Attendance", "Daily Summary"))
        att_menu.addAction(daily_summary_action)
        
        # Reports
        reports_att_action = QAction("Attendance &Reports", self)
        reports_att_action.setShortcut("Ctrl+R")
        reports_att_action.setStatusTip("Generate attendance reports")
        reports_att_action.triggered.connect(lambda: self.menu_action_triggered.emit("Attendance", "Attendance Reports"))
        att_menu.addAction(reports_att_action)
    
    def create_reports_menu(self, menubar):
        """Create Reports menu"""
        rep_menu = menubar.addMenu("&Reports")
        
        # Attendance Reports
        att_reports_action = QAction("&Attendance Reports", self)
        att_reports_action.setShortcut("Ctrl+Shift+R")
        att_reports_action.setStatusTip("Generate attendance reports")
        att_reports_action.triggered.connect(lambda: self.menu_action_triggered.emit("Reports", "Attendance Reports"))
        rep_menu.addAction(att_reports_action)
        
        # Employee Reports
        emp_reports_action = QAction("&Employee Reports", self)
        emp_reports_action.setStatusTip("Generate employee reports")
        emp_reports_action.triggered.connect(lambda: self.menu_action_triggered.emit("Reports", "Employee Reports"))
        rep_menu.addAction(emp_reports_action)
        
        # Analytics
        analytics_action = QAction("&Analytics", self)
        analytics_action.setStatusTip("View analytics and insights")
        analytics_action.triggered.connect(lambda: self.menu_action_triggered.emit("Reports", "Analytics"))
        rep_menu.addAction(analytics_action)
        
        # Custom Reports
        custom_reports_action = QAction("&Custom Reports", self)
        custom_reports_action.setStatusTip("Create custom reports")
        custom_reports_action.triggered.connect(lambda: self.menu_action_triggered.emit("Reports", "Custom Reports"))
        rep_menu.addAction(custom_reports_action)
        
        rep_menu.addSeparator()
        
        # Export Reports
        export_reports_action = QAction("&Export Reports", self)
        export_reports_action.setStatusTip("Export reports to various formats")
        export_reports_action.triggered.connect(lambda: self.menu_action_triggered.emit("Reports", "Export Reports"))
        rep_menu.addAction(export_reports_action)
    
    def create_company_menu(self, menubar):
        """Create Company menu"""
        comp_menu = menubar.addMenu("&Company")
        
        # Locations
        locations_action = QAction("&Locations", self)
        locations_action.setStatusTip("Manage company locations")
        locations_action.triggered.connect(lambda: self.menu_action_triggered.emit("Company", "Locations"))
        comp_menu.addAction(locations_action)
        
        # Holidays
        holidays_action = QAction("&Holidays", self)
        holidays_action.setStatusTip("Manage company holidays")
        holidays_action.triggered.connect(lambda: self.menu_action_triggered.emit("Company", "Holidays"))
        comp_menu.addAction(holidays_action)
        
        # Departments
        departments_action = QAction("&Departments", self)
        departments_action.setStatusTip("Manage company departments")
        departments_action.triggered.connect(lambda: self.menu_action_triggered.emit("Company", "Departments"))
        comp_menu.addAction(departments_action)
        
        comp_menu.addSeparator()
        
        # Company Settings
        comp_settings_action = QAction("Company &Settings", self)
        comp_settings_action.setStatusTip("Configure company settings")
        comp_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Company", "Company Settings"))
        comp_menu.addAction(comp_settings_action)
    
    def create_users_menu(self, menubar):
        """Create Users menu"""
        users_menu = menubar.addMenu("&Users")
        
        # Add User
        add_user_action = QAction("&Add User", self)
        add_user_action.setShortcut("Ctrl+U")
        add_user_action.setStatusTip("Add new user")
        add_user_action.triggered.connect(lambda: self.menu_action_triggered.emit("Users", "Add User"))
        users_menu.addAction(add_user_action)
        
        # Edit User
        edit_user_action = QAction("&Edit User", self)
        edit_user_action.setShortcut("Ctrl+Shift+U")
        edit_user_action.setStatusTip("Edit existing user")
        edit_user_action.triggered.connect(lambda: self.menu_action_triggered.emit("Users", "Edit User"))
        users_menu.addAction(edit_user_action)
        
        # Delete User
        delete_user_action = QAction("&Delete User", self)
        delete_user_action.setStatusTip("Delete user")
        delete_user_action.triggered.connect(lambda: self.menu_action_triggered.emit("Users", "Delete User"))
        users_menu.addAction(delete_user_action)
        
        users_menu.addSeparator()
        
        # User Management
        user_mgmt_action = QAction("User &Management", self)
        user_mgmt_action.setStatusTip("Manage user accounts")
        user_mgmt_action.triggered.connect(lambda: self.menu_action_triggered.emit("Users", "User Management"))
        users_menu.addAction(user_mgmt_action)
        
        # Roles & Permissions
        roles_action = QAction("&Roles & Permissions", self)
        roles_action.setStatusTip("Manage user roles and permissions")
        roles_action.triggered.connect(lambda: self.menu_action_triggered.emit("Users", "Roles & Permissions"))
        users_menu.addAction(roles_action)
    
    def create_settings_menu(self, menubar):
        """Create Settings menu"""
        settings_menu = menubar.addMenu("&Settings")
        
        # General Settings
        general_settings_action = QAction("&General Settings", self)
        general_settings_action.setShortcut("Ctrl+,")
        general_settings_action.setStatusTip("Configure general settings")
        general_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Settings", "General Settings"))
        settings_menu.addAction(general_settings_action)
        
        # Database Settings
        db_settings_action = QAction("&Database Settings", self)
        db_settings_action.setStatusTip("Configure database settings")
        db_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Settings", "Database Settings"))
        settings_menu.addAction(db_settings_action)
        
        # Sync Settings
        sync_settings_action = QAction("&Sync Settings", self)
        sync_settings_action.setStatusTip("Configure synchronization settings")
        sync_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Settings", "Sync Settings"))
        settings_menu.addAction(sync_settings_action)
        
        # QR Settings
        qr_settings_action = QAction("&QR Settings", self)
        qr_settings_action.setStatusTip("Configure QR scanner settings")
        qr_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Settings", "QR Settings"))
        settings_menu.addAction(qr_settings_action)
        
        settings_menu.addSeparator()
        
        # System Preferences
        sys_prefs_action = QAction("&System Preferences", self)
        sys_prefs_action.setStatusTip("Configure system preferences")
        sys_prefs_action.triggered.connect(lambda: self.menu_action_triggered.emit("Settings", "System Preferences"))
        settings_menu.addAction(sys_prefs_action)
    
    def create_sync_menu(self, menubar):
        """Create Sync menu"""
        sync_menu = menubar.addMenu("&Sync")
        
        # Sync Now
        sync_now_action = QAction("&Sync Now", self)
        sync_now_action.setShortcut("F12")
        sync_now_action.setStatusTip("Force immediate synchronization")
        sync_now_action.triggered.connect(self.sync_now)
        sync_menu.addAction(sync_now_action)
        
        # Auto Sync
        auto_sync_action = QAction("&Auto Sync", self)
        auto_sync_action.setStatusTip("Toggle automatic synchronization")
        auto_sync_action.setCheckable(True)
        auto_sync_action.setChecked(True)
        auto_sync_action.triggered.connect(self.toggle_auto_sync)
        sync_menu.addAction(auto_sync_action)
        
        sync_menu.addSeparator()
        
        # Sync Status
        sync_status_action = QAction("Sync &Status", self)
        sync_status_action.setStatusTip("View synchronization status")
        sync_status_action.triggered.connect(lambda: self.menu_action_triggered.emit("Sync", "Sync Status"))
        sync_menu.addAction(sync_status_action)
        
        # Sync Settings
        sync_settings_action = QAction("Sync &Settings", self)
        sync_settings_action.setStatusTip("Configure synchronization settings")
        sync_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Sync", "Sync Settings"))
        sync_menu.addAction(sync_settings_action)
        
        sync_menu.addSeparator()
        
        # Database Sync
        db_sync_action = QAction("&Database Sync", self)
        db_sync_action.setStatusTip("Synchronize local and cloud databases")
        db_sync_action.triggered.connect(lambda: self.menu_action_triggered.emit("Sync", "Database Sync"))
        sync_menu.addAction(db_sync_action)
    
    def create_notifications_menu(self, menubar):
        """Create Notifications menu"""
        notif_menu = menubar.addMenu("&Notifications")
        
        # View Notifications
        view_notif_action = QAction("&View Notifications", self)
        view_notif_action.setShortcut("Ctrl+N")
        view_notif_action.setStatusTip("View all notifications")
        view_notif_action.triggered.connect(lambda: self.menu_action_triggered.emit("Notifications", "View Notifications"))
        notif_menu.addAction(view_notif_action)
        
        # Notification Settings
        notif_settings_action = QAction("Notification &Settings", self)
        notif_settings_action.setStatusTip("Configure notification settings")
        notif_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Notifications", "Notification Settings"))
        notif_menu.addAction(notif_settings_action)
        
        notif_menu.addSeparator()
        
        # Admin Notifications
        admin_notif_action = QAction("&Admin Notifications", self)
        admin_notif_action.setStatusTip("View admin notifications")
        admin_notif_action.triggered.connect(lambda: self.menu_action_triggered.emit("Notifications", "Admin Notifications"))
        notif_menu.addAction(admin_notif_action)
        
        # User Notifications
        user_notif_action = QAction("&User Notifications", self)
        user_notif_action.setStatusTip("View user notifications")
        user_notif_action.triggered.connect(lambda: self.menu_action_triggered.emit("Notifications", "User Notifications"))
        notif_menu.addAction(user_notif_action)
    
    def create_ai_assistant_menu(self, menubar):
        """Create AI Assistant menu"""
        ai_menu = menubar.addMenu("&AI Assistant")
        
        # AI Chat
        ai_chat_action = QAction("AI &Chat", self)
        ai_chat_action.setShortcut("Ctrl+Shift+A")
        ai_chat_action.setStatusTip("Chat with AI assistant")
        ai_chat_action.triggered.connect(lambda: self.menu_action_triggered.emit("AI Assistant", "AI Chat"))
        ai_menu.addAction(ai_chat_action)
        
        # AI Help
        ai_help_action = QAction("AI &Help", self)
        ai_help_action.setStatusTip("Get AI-powered help")
        ai_help_action.triggered.connect(lambda: self.menu_action_triggered.emit("AI Assistant", "AI Help"))
        ai_menu.addAction(ai_help_action)
        
        # AI Settings
        ai_settings_action = QAction("AI &Settings", self)
        ai_settings_action.setStatusTip("Configure AI assistant settings")
        ai_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("AI Assistant", "AI Settings"))
        ai_menu.addAction(ai_settings_action)
        
        ai_menu.addSeparator()
        
        # AI Analytics
        ai_analytics_action = QAction("AI &Analytics", self)
        ai_analytics_action.setStatusTip("AI-powered analytics and insights")
        ai_analytics_action.triggered.connect(lambda: self.menu_action_triggered.emit("AI Assistant", "AI Analytics"))
        ai_menu.addAction(ai_analytics_action)
    
    def create_analytics_menu(self, menubar):
        """Create Analytics menu"""
        analytics_menu = menubar.addMenu("&Analytics")
        
        # Advanced Analytics
        advanced_analytics_action = QAction("&Advanced Analytics", self)
        advanced_analytics_action.setShortcut("Ctrl+Shift+L")
        advanced_analytics_action.setStatusTip("View advanced analytics")
        advanced_analytics_action.triggered.connect(lambda: self.menu_action_triggered.emit("Analytics", "Advanced Analytics"))
        analytics_menu.addAction(advanced_analytics_action)
        
        # Charts & Graphs
        charts_action = QAction("&Charts & Graphs", self)
        charts_action.setStatusTip("View charts and graphs")
        charts_action.triggered.connect(lambda: self.menu_action_triggered.emit("Analytics", "Charts & Graphs"))
        analytics_menu.addAction(charts_action)
        
        # Performance Metrics
        performance_action = QAction("&Performance Metrics", self)
        performance_action.setStatusTip("View performance metrics")
        performance_action.triggered.connect(lambda: self.menu_action_triggered.emit("Analytics", "Performance Metrics"))
        analytics_menu.addAction(performance_action)
        
        # Data Insights
        insights_action = QAction("&Data Insights", self)
        insights_action.setStatusTip("View data insights")
        insights_action.triggered.connect(lambda: self.menu_action_triggered.emit("Analytics", "Data Insights"))
        analytics_menu.addAction(insights_action)
    
    def create_security_menu(self, menubar):
        """Create Security menu"""
        security_menu = menubar.addMenu("&Security")
        
        # User Authentication
        auth_action = QAction("User &Authentication", self)
        auth_action.setStatusTip("Manage user authentication")
        auth_action.triggered.connect(lambda: self.menu_action_triggered.emit("Security", "User Authentication"))
        security_menu.addAction(auth_action)
        
        # Access Control
        access_action = QAction("&Access Control", self)
        access_action.setStatusTip("Manage access control")
        access_action.triggered.connect(lambda: self.menu_action_triggered.emit("Security", "Access Control"))
        security_menu.addAction(access_action)
        
        # Password Management
        password_action = QAction("&Password Management", self)
        password_action.setStatusTip("Manage passwords")
        password_action.triggered.connect(lambda: self.menu_action_triggered.emit("Security", "Password Management"))
        security_menu.addAction(password_action)
        
        security_menu.addSeparator()
        
        # Security Settings
        security_settings_action = QAction("Security &Settings", self)
        security_settings_action.setStatusTip("Configure security settings")
        security_settings_action.triggered.connect(lambda: self.menu_action_triggered.emit("Security", "Security Settings"))
        security_menu.addAction(security_settings_action)
    
    def create_help_menu(self, menubar):
        """Create Help menu"""
        help_menu = menubar.addMenu("&Help")
        
        # User Manual
        manual_action = QAction("&User Manual", self)
        manual_action.setShortcut("F1")
        manual_action.setStatusTip("Open user manual")
        manual_action.triggered.connect(lambda: self.menu_action_triggered.emit("Help", "User Manual"))
        help_menu.addAction(manual_action)
        
        # About
        about_action = QAction("&About", self)
        about_action.setStatusTip("About the application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # System Info
        sys_info_action = QAction("&System Information", self)
        sys_info_action.setStatusTip("View system information")
        sys_info_action.triggered.connect(lambda: self.menu_action_triggered.emit("Help", "System Information"))
        help_menu.addAction(sys_info_action)
        
        help_menu.addSeparator()
        
        # Check Updates
        updates_action = QAction("Check for &Updates", self)
        updates_action.setStatusTip("Check for application updates")
        updates_action.triggered.connect(lambda: self.menu_action_triggered.emit("Help", "Check Updates"))
        help_menu.addAction(updates_action)
    
    def init_tool_bar(self):
        """Initialize the tool bar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(True)
        toolbar.setFloatable(False)
        
        # Store toolbar reference
        self.main_toolbar = toolbar
        
        # Add toolbar actions - we'll add them after menu creation
        # These will be populated in create_toolbar_actions()
    
    def init_status_bar(self):
        """Initialize the status bar"""
        self.statusBar().showMessage("Ready")
        
        # Add sync status indicator
        from PyQt5.QtWidgets import QLabel
        self.sync_status_label = QLabel("🔄 Synced")
        self.statusBar().addPermanentWidget(self.sync_status_label)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Don't connect to self to avoid recursion
        # self.menu_action_triggered.connect(self.handle_menu_action)
        pass
    
    def handle_menu_action(self, menu_name, action_name):
        """Handle menu action triggers"""
        print(f"Menu Action: {menu_name} -> {action_name}")
        # Don't emit signal to avoid recursion
        # self.menu_action_triggered.emit(menu_name, action_name)
    
    def sync_now(self):
        """Force immediate synchronization"""
        self.statusBar().showMessage("Synchronizing...")
        # TODO: Implement actual sync logic
        QTimer.singleShot(2000, lambda: self.statusBar().showMessage("Sync completed"))
    
    def toggle_auto_sync(self, checked):
        """Toggle automatic synchronization"""
        if checked:
            self.sync_timer.start()
            self.statusBar().showMessage("Auto sync enabled")
        else:
            self.sync_timer.stop()
            self.statusBar().showMessage("Auto sync disabled")
    
    def auto_sync(self):
        """Automatic synchronization"""
        self.statusBar().showMessage("Auto syncing...")
        # TODO: Implement actual auto sync logic
        QTimer.singleShot(1000, lambda: self.statusBar().showMessage("Auto sync completed"))
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Fingerprint Attendance System\n"
                         "Professional Edition\n\n"
                         "Version 2.0\n"
                         "© 2024 All Rights Reserved")
    
    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(self, 'Exit', 
                                   'Are you sure you want to exit?',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainMenuBar()
    window.show()
    sys.exit(app.exec_())
