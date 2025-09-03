from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import QCoreApplication
from app.database.simple_hybrid_manager import SimpleHybridManager

class SearchWidget(QWidget):
    """
    Interface for searching employees بالاسم أو رقم الهاتف أو الكود الوظيفي مع عرض النتائج بشكل مباشر.
    """
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager or SimpleHybridManager()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """تنشئ وتنظم عناصر الواجهة."""
        layout = QVBoxLayout(self)
        
        # --- تصميم حقل الSearch ---
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(f"<b>{self.tr('Search Employee')}:</b>"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Enter part of a name, phone number, or code..."))
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton(f"🔍 {self.tr('Search')}")
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # --- جدول النتائج ---
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            self.tr("Code"), self.tr("Full Name"), self.tr("Job Title"), self.tr("Phone Number")
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # --- تحسينات تجربة المستخدم ---
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSortingEnabled(True)
        
        layout.addWidget(self.results_table)

    def connect_signals(self):
        """تربط إشارات عناصر الواجهة بالدوال المناسبة."""
        # الSearch المباشر يتم عند تغيير النص
        self.search_input.textChanged.connect(self.perform_search)
        self.search_button.clicked.connect(self.perform_search)

    def perform_search(self):
        """
        تجلب بيانات الموظفين من قاعدة البيانات بناءً على مصطلح الSearch
        وتقوم بملء جدول النتائج.
        """
        search_term = self.search_input.text().strip()
        
        # مسح الجدول إذا كان حقل الSearch فارغًا
        if not search_term:
            self.results_table.setRowCount(0)
            return
            
        results = self.db_manager.search_employees(search_term) or []
        
        self.results_table.setRowCount(0) # مسح النتائج السابقة
        self.results_table.setRowCount(len(results))
        for row_index, employee in enumerate(results):
            self.results_table.setItem(row_index, 0, QTableWidgetItem(employee.get('employee_code', '')))
            self.results_table.setItem(row_index, 1, QTableWidgetItem(employee.get('name', '')))
            self.results_table.setItem(row_index, 2, QTableWidgetItem(employee.get('job_title', '')))
            self.results_table.setItem(row_index, 3, QTableWidgetItem(employee.get('phone_number', '')))

    def tr(self, text):
        """دالة مساعدة للترجمة."""
        return QCoreApplication.translate("SearchWidget", text)