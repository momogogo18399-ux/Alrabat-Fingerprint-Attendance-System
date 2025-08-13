from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
    QDateEdit, QLineEdit, QDialog, QLabel # <-- تمت إضافته هنا
)
from PyQt6.QtCore import QDate, QCoreApplication
from app.database.database_manager import DatabaseManager

class HolidaysWidget(QWidget):
    """
    واجهة لإدارة الإجازات الرسمية والأعياد.
    """
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.connect_signals()
        self.load_holidays_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # قسم الإضافة
        add_layout = QHBoxLayout()
        self.date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(self.tr("Holiday Description (e.g., New Year)"))
        self.add_button = QPushButton(f"➕ {self.tr('Add Holiday')}")
        self.add_button.setToolTip(self.tr("Add a new official holiday"))
        add_layout.addWidget(QLabel(self.tr("Date:")))
        add_layout.addWidget(self.date_edit)
        add_layout.addWidget(QLabel(self.tr("Description:")))
        add_layout.addWidget(self.description_input, 1) # يأخذ المساحة المتبقية
        add_layout.addWidget(self.add_button)
        layout.addLayout(add_layout)
        
        # الجدول والحذف
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", self.tr("Date"), self.tr("Description")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.delete_button = QPushButton(f"🗑️ {self.tr('Delete Selected Holiday')}")
        self.delete_button.setToolTip(self.tr("Delete the selected holiday"))
        
        layout.addWidget(self.table)
        layout.addWidget(self.delete_button)

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_holiday)
        self.delete_button.clicked.connect(self.delete_holiday)

    def load_holidays_data(self):
        holidays = self.db_manager.get_all_holidays()
        self.table.setRowCount(0)
        self.table.setRowCount(len(holidays))
        for row, holiday in enumerate(holidays):
            self.table.setItem(row, 0, QTableWidgetItem(str(holiday['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(holiday['date']))
            self.table.setItem(row, 2, QTableWidgetItem(holiday['description']))

    def add_holiday(self):
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        description = self.description_input.text().strip()
        if not description:
            QMessageBox.warning(self, self.tr("Input Missing"), self.tr("Description cannot be empty."))
            return
            
        if self.db_manager.add_holiday(date_str, description):
            QMessageBox.information(self, self.tr("Success"), self.tr("Holiday added successfully."))
            self.description_input.clear()
            self.load_holidays_data()
        else:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to add holiday. The date might already exist."))

    def delete_holiday(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
        
        holiday_id = int(self.table.item(selected_row, 0).text())
        desc = self.table.item(selected_row, 2).text()
        
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"), f"{self.tr('Delete holiday')} <b>{desc}</b>?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_holiday(holiday_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("Holiday deleted successfully."))
                self.load_holidays_data()

    def tr(self, text):
        return QCoreApplication.translate("HolidaysWidget", text)