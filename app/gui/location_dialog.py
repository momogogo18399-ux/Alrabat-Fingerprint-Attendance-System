from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QMessageBox, QSpinBox, QDoubleSpinBox, QPushButton, QHBoxLayout, QLabel
)
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QFont

from app.utils.location_parser import extract_lat_lon_from_url

class LocationDialog(QDialog):
    """
    نافذة حوار لAdd أو Edit موقع معتمد، مع إمكانية لصق الرابط.
    """
    def __init__(self, location_data=None, parent=None):
        super().__init__(parent)
        self.is_edit_mode = location_data is not None
        self.location_data = location_data or {}

        title = self.tr("Edit Location") if self.is_edit_mode else self.tr("Add New Location")
        self.setWindowTitle(title)
        self.setMinimumWidth(450)

        # --- بداية التصحيح: تعريف كل الحقول أولاً ---
        # 1. إنشاء كل عناصر الواجهة
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText(self.tr("Paste Google Maps link here..."))
        
        self.fetch_button = QPushButton(self.tr("Fetch Coordinates"))
        
        self.name_input = QLineEdit(self.location_data.get('name', ''))
        

        
        self.latitude_input = QDoubleSpinBox()
        self.latitude_input.setRange(-90.0, 90.0)
        self.latitude_input.setDecimals(6)
        self.latitude_input.setValue(self.location_data.get('latitude', 0.0))
        
        self.longitude_input = QDoubleSpinBox()
        self.longitude_input.setRange(-180.0, 180.0)
        self.longitude_input.setDecimals(6)
        self.longitude_input.setValue(self.location_data.get('longitude', 0.0))
        
        self.radius_input = QSpinBox()
        self.radius_input.setRange(10, 5000)
        self.radius_input.setSuffix(f" {self.tr('meters')}")
        self.radius_input.setValue(self.location_data.get('radius_meters', 100))
        # --- نهاية التصحيح ---
        
        # 2. بناء التصميم
        layout = QVBoxLayout(self)
        
        link_layout = QHBoxLayout()
        link_layout.addWidget(self.link_input)
        link_layout.addWidget(self.fetch_button)

        form = QFormLayout()
        form.addRow(f"{self.tr('Location Name')} (*):", self.name_input)
        form.addRow(QLabel("----------------------------------")) # فاصل مرئي
        form.addRow(f"{self.tr('Location Link')}:", link_layout)
        form.addRow(f"{self.tr('Latitude')}:", self.latitude_input)
        form.addRow(f"{self.tr('Longitude')}:", self.longitude_input)
        form.addRow(f"{self.tr('Allowed Radius')}:", self.radius_input)
        
        layout.addLayout(form)
        
        # 3. ربط الأحداث
        self.fetch_button.clicked.connect(self._fetch_coordinates_from_link)

        # 4. الأزرار النهائية
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fetch_coordinates_from_link(self):
        url = self.link_input.text().strip()
        if not url:
            QMessageBox.warning(self, self.tr("Input Missing"), self.tr("Please paste a link first."))
            return

        coordinates = extract_lat_lon_from_url(url)
        
        if coordinates:
            lat, lon = coordinates
            self.latitude_input.setValue(lat)
            self.longitude_input.setValue(lon)
            QMessageBox.information(self, self.tr("Success"), self.tr("Coordinates extracted successfully!"))
        else:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Could not find valid coordinates in the provided link."))

    def get_data(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr("Missing Information"), self.tr("Location Name cannot be empty."))
            return None
        data = {
            'name': name, 
            'latitude': self.latitude_input.value(),
            'longitude': self.longitude_input.value(), 
            'radius_meters': self.radius_input.value(),
        }
        if self.is_edit_mode: data['id'] = self.location_data['id']
        return data
    
    def tr(self, text):
        return QCoreApplication.translate("LocationDialog", text)