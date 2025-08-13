from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import QCoreApplication
from app.database.database_manager import DatabaseManager
from app.gui.location_dialog import LocationDialog

class LocationsWidget(QWidget):
    """
    واجهة لإدارة المواقع المعتمدة (إضافة، تعديل، حذف).
    """
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.connect_signals()
        self.load_locations_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton(f"➕ {self.tr('Add Location')}")
        self.add_button.setToolTip(self.tr("Create a new approved location"))
        self.edit_button = QPushButton(f"✏️ {self.tr('Edit Selected')}")
        self.edit_button.setToolTip(self.tr("Edit the selected location"))
        self.delete_button = QPushButton(f"🗑️ {self.tr('Delete Selected')}")
        self.delete_button.setToolTip(self.tr("Delete the selected location"))
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", self.tr("Name"), self.tr("Latitude"), self.tr("Longitude"), self.tr("Radius (m)")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_location)
        self.edit_button.clicked.connect(self.edit_location)
        self.delete_button.clicked.connect(self.delete_location)

    def load_locations_data(self):
        locations = self.db_manager.get_all_locations() or []
        self.table.setRowCount(0)
        self.table.setRowCount(len(locations))
        for row, loc in enumerate(locations):
            self.table.setItem(row, 0, QTableWidgetItem(str(loc['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(loc['name']))
            self.table.setItem(row, 2, QTableWidgetItem(str(loc['latitude'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(loc['longitude'])))
            self.table.setItem(row, 4, QTableWidgetItem(str(loc['radius_meters'])))

    def add_location(self):
        dialog = LocationDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data and self.db_manager.add_location(data):
                QMessageBox.information(self, self.tr("Success"), self.tr("Location added successfully."))
                self.load_locations_data()
            elif data:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to add location. The name might already be in use."))

    def edit_location(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return

        loc_id = int(self.table.item(selected_row, 0).text())
        loc_data = {
            'id': loc_id,
            'name': self.table.item(selected_row, 1).text(),
            'latitude': float(self.table.item(selected_row, 2).text()),
            'longitude': float(self.table.item(selected_row, 3).text()),
            'radius_meters': int(self.table.item(selected_row, 4).text())
        }
        
        dialog = LocationDialog(location_data=loc_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data and self.db_manager.update_location(data):
                QMessageBox.information(self, self.tr("Success"), self.tr("Location updated successfully."))
                self.load_locations_data()

    def delete_location(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
            
        loc_id = int(self.table.item(selected_row, 0).text())
        loc_name = self.table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"), f"{self.tr('Delete location')} <b>{loc_name}</b>?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_location(loc_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("Location deleted successfully."))
                self.load_locations_data()
    
    def tr(self, text):
        return QCoreApplication.translate("LocationsWidget", text)