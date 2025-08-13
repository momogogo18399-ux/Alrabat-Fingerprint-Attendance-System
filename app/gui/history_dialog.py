from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLabel, QAbstractItemView
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QCoreApplication

class HistoryDialog(QDialog):
    """
    نافذة حوار تعرض سجل الحضور الكامل لموظف معين.
    """
    def __init__(self, employee_name, history_data, parent=None):
        super().__init__(parent)
        
        # --- إعدادات الواجهة ---
        self.setWindowTitle(f"{self.tr('Attendance History for:')} {employee_name}")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        
        # --- عنوان ---
        title_label = QLabel(f"<b>{self.tr('Attendance Log for Employee:')}</b> {employee_name}")
        title_label.setFont(QFont("Arial", 14))
        layout.addWidget(title_label)
        
        # --- جدول السجل ---
        table = QTableWidget()
        table.setColumnCount(4) # تمت إضافة عمود للملاحظات
        table.setHorizontalHeaderLabels([
            self.tr("Date"), 
            self.tr("Time"), 
            self.tr("Action"),
            self.tr("Notes") # عمود الملاحظات الجديد
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # --- تحسينات تجربة المستخدم ---
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # جعل الجدول للقراءة فقط
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True) # السماح للمستخدم بالفرز

        # --- ملء الجدول بالبيانات ---
        table.setRowCount(len(history_data))
        for row_index, record in enumerate(history_data):
            table.setItem(row_index, 0, QTableWidgetItem(record.get('date', '')))
            table.setItem(row_index, 1, QTableWidgetItem(record.get('check_time', '')))
            table.setItem(row_index, 2, QTableWidgetItem(record.get('type', '')))
            table.setItem(row_index, 3, QTableWidgetItem(record.get('notes', ''))) # عرض الملاحظات
            
        layout.addWidget(table)

    def tr(self, text):
        """دالة مساعدة للترجمة."""
        return QCoreApplication.translate("HistoryDialog", text)