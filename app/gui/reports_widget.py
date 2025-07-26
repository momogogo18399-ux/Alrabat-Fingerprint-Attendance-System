from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, 
    QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QDate, QCoreApplication
from PyQt6.QtGui import QFont
from app.database.database_manager import DatabaseManager
import pandas as pd

class ReportsWidget(QWidget):
    """
    A widget for generating and exporting attendance reports to Excel.
    """
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setup_ui()

    def setup_ui(self):
        """Creates and arranges the UI elements for the widget."""
        layout = QVBoxLayout(self)
        
        title_label = QLabel(f"<h2>{self.tr('Generate Attendance Report')}</h2>")
        layout.addWidget(title_label)

        # --- Date selection layout ---
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel(f"{self.tr('From Date')}:"))
        self.start_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate().addMonths(-1))
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.start_date_edit)

        date_layout.addWidget(QLabel(f"{self.tr('To Date')}:"))
        self.end_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.end_date_edit)
        layout.addLayout(date_layout)

        # --- Export button ---
        export_button = QPushButton(f"🚀 {self.tr('Export to Excel')}")
        export_button.setFont(QFont("Arial", 12))
        export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(export_button)
        
        layout.addStretch()

    def export_to_excel(self):
        """Fetches data for the selected date range and exports it to an Excel file."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # Fetch data from the database using the new function
        data = self.db_manager.get_attendance_between_dates(start_date, end_date) 

        if not data:
            QMessageBox.warning(
                self, 
                self.tr("No Data"), 
                self.tr("No attendance records were found in the selected date range.")
            )
            return

        # Let the user choose where to save the file
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            self.tr("Save Report"), 
            f"Attendance_Report_{start_date}_to_{end_date}.xlsx",
            f"{self.tr('Excel Files (*.xlsx)')}"
        )
        if not file_path:
            return

        try:
            # Convert data to a pandas DataFrame for easy export
            df = pd.DataFrame(data)

            # Improve column names for the report
            df.rename(columns={
                'date': self.tr('Date'),
                'name': self.tr('Employee Name'),
                'type': self.tr('Action'),
                'check_time': self.tr('Time'),
                'work_duration_hours': self.tr('Work Duration (H)'),
                'location_lat': self.tr('Latitude'),
                'location_lon': self.tr('Longitude')
            }, inplace=True)

            # Export DataFrame to Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            QMessageBox.information(
                self, 
                self.tr("Success"), 
                self.tr("Report saved successfully at:\n") + file_path
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                self.tr("Error"), 
                self.tr("Failed to save the report: ") + str(e)
            )

    def tr(self, text):
        """Helper function for translation."""
        return QCoreApplication.translate("ReportsWidget", text)