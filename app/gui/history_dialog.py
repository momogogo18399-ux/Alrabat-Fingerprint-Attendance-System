from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLabel, QAbstractItemView
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QCoreApplication

class HistoryDialog(QDialog):
    """
    A dialog window that displays the complete attendance history for a specific employee.
    """
    def __init__(self, employee_name, history_data, parent=None):
        super().__init__(parent)
        
        # --- UI Setup ---
        self.setWindowTitle(f"{self.tr('Attendance History for:')} {employee_name}")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        
        # --- Title Label ---
        title_label = QLabel(f"<b>{self.tr('Attendance Log for Employee:')}</b> {employee_name}")
        title_label.setFont(QFont("Arial", 14))
        layout.addWidget(title_label)
        
        # --- History Table ---
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([
            self.tr("Date"), 
            self.tr("Time"), 
            self.tr("Action")
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # --- UX Improvements ---
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Make table read-only
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True) # Allow user to sort columns

        # --- Populate Table with Data ---
        table.setRowCount(len(history_data))
        for row_index, record in enumerate(history_data):
            table.setItem(row_index, 0, QTableWidgetItem(record['date']))
            table.setItem(row_index, 1, QTableWidgetItem(record['check_time']))
            table.setItem(row_index, 2, QTableWidgetItem(record['type']))
            
        layout.addWidget(table)

    def tr(self, text):
        """Helper function for translation."""
        return QCoreApplication.translate("HistoryDialog", text)