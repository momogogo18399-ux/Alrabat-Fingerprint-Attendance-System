from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QFont
from app.database.database_manager import DatabaseManager

class SearchWidget(QWidget):
    """
    A widget for searching employees by name or phone number with live results.
    """
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Creates and arranges the UI elements for the widget."""
        layout = QVBoxLayout(self)
        
        # --- Search input layout ---
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(f"<b>{self.tr('Search Employee')}:</b>"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Enter part of a name or phone number..."))
        search_layout.addWidget(self.search_input)
        
        # Optional search button (live search is the primary method)
        self.search_button = QPushButton(f"🔍 {self.tr('Search')}")
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # --- Results table ---
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "ID", self.tr("Full Name"), self.tr("Job Title"), self.tr("Phone Number")
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # --- UX Improvements ---
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSortingEnabled(True)
        
        layout.addWidget(self.results_table)

    def connect_signals(self):
        """Connects UI element signals to their corresponding slots."""
        # Live search triggers on text change
        self.search_input.textChanged.connect(self.perform_search)
        self.search_button.clicked.connect(self.perform_search)

    def perform_search(self):
        """
        Fetches employee data from the database based on the search term
        and populates the results table.
        """
        search_term = self.search_input.text().strip()
        
        # Clear the table if the search box is empty
        if not search_term:
            self.results_table.setRowCount(0)
            return
            
        results = self.db_manager.search_employees(search_term)
        
        self.results_table.setRowCount(0) # Clear previous results
        self.results_table.setRowCount(len(results))
        for row_index, employee in enumerate(results):
            self.results_table.setItem(row_index, 0, QTableWidgetItem(str(employee['id'])))
            self.results_table.setItem(row_index, 1, QTableWidgetItem(employee['name']))
            self.results_table.setItem(row_index, 2, QTableWidgetItem(employee['job_title']))
            self.results_table.setItem(row_index, 3, QTableWidgetItem(employee['phone_number']))

    def tr(self, text):
        """Helper function for translation."""
        return QCoreApplication.translate("SearchWidget", text)