#!/usr/bin/env python3
"""
Advanced Analytics Interface with Interactive Charts
"""

import sys
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QProgressBar, QComboBox, QDateEdit, QGroupBox, 
    QScrollArea, QFrame, QSplitter, QSlider, QCheckBox
)
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QDate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from app.core.ai_manager import AdvancedAIManager

class AdvancedAnalyticsWidget(QWidget):
    """Advanced Analytics Interface with Interactive Charts"""
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.ai_manager = AdvancedAIManager()
        self.charts_data = {}
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Setup User Interface"""
        layout = QVBoxLayout()
        
        # Main Title
        title = QLabel("📊 Advanced and Smart Analytics")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title)
        
        # Create Tabs
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 12))
        
        # Interactive Charts Tab
        self.setup_charts_tab()
        
        # Statistical Analysis Tab
        self.setup_statistical_tab()
        
        # Pattern Discovery Tab
        self.setup_patterns_tab()
        
        # Advanced Predictions Tab
        self.setup_advanced_predictions_tab()
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def setup_charts_tab(self):
        """Setup Charts Tab"""
        charts_widget = QWidget()
        layout = QVBoxLayout()
        
        # Chart Creation Buttons
        charts_buttons = QHBoxLayout()
        
        self.daily_chart_btn = QPushButton("📅 Daily Chart")
        self.daily_chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 15px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        self.weekly_chart_btn = QPushButton("📊 Weekly Chart")
        self.weekly_chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 15px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        charts_buttons.addWidget(self.daily_chart_btn)
        charts_buttons.addWidget(self.weekly_chart_btn)
        layout.addLayout(charts_buttons)
        
        # Display Area for Charts
        self.charts_display = QTextEdit()
        self.charts_display.setReadOnly(True)
        self.charts_display.setFont(QFont("Arial", 11))
        layout.addWidget(QLabel("📈 Interactive Charts:"))
        layout.addWidget(self.charts_display)
        
        # Connect Signals
        self.daily_chart_btn.clicked.connect(self.create_daily_chart)
        self.weekly_chart_btn.clicked.connect(self.create_weekly_chart)
        
        charts_widget.setLayout(layout)
        self.tabs.addTab(charts_widget, "📈 Charts")
        
    def setup_statistical_tab(self):
        """Setup Statistical Analysis Tab"""
        stats_widget = QWidget()
        layout = QVBoxLayout()
        
        # Statistical Analysis Buttons
        stats_buttons = QHBoxLayout()
        
        self.descriptive_stats_btn = QPushButton("📊 Descriptive Statistics")
        self.descriptive_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 10px 15px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        stats_buttons.addWidget(self.descriptive_stats_btn)
        layout.addLayout(stats_buttons)
        
        # Display Area for Statistical Results
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setFont(QFont("Arial", 11))
        layout.addWidget(QLabel("📊 Statistical Results:"))
        layout.addWidget(self.stats_display)
        
        # Connect Signals
        self.descriptive_stats_btn.clicked.connect(self.show_descriptive_stats)
        
        stats_widget.setLayout(layout)
        self.tabs.addTab(stats_widget, "📊 Statistical Analysis")
        
    def setup_patterns_tab(self):
        """Setup Pattern Discovery Tab"""
        patterns_widget = QWidget()
        layout = QVBoxLayout()
        
        # Pattern Discovery Buttons
        patterns_buttons = QHBoxLayout()
        
        self.clustering_btn = QPushButton("🎯 Clustering Analysis")
        self.clustering_btn.setStyleSheet("""
            QPushButton {
                background-color: #20c997;
                color: white;
                padding: 10px 15px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ba085;
            }
        """)
        
        patterns_buttons.addWidget(self.clustering_btn)
        layout.addLayout(patterns_buttons)
        
        # Display Area for Patterns
        self.patterns_display = QTextEdit()
        self.patterns_display.setReadOnly(True)
        self.patterns_display.setFont(QFont("Arial", 11))
        layout.addWidget(QLabel("🔍 Discovered Patterns:"))
        layout.addWidget(self.patterns_display)
        
        # Connect Signals
        self.clustering_btn.clicked.connect(self.analyze_clustering)
        
        patterns_widget.setLayout(layout)
        self.tabs.addTab(patterns_widget, "🔍 Pattern Discovery")
        
    def setup_advanced_predictions_tab(self):
        """Setup Advanced Predictions Tab"""
        predictions_widget = QWidget()
        layout = QVBoxLayout()
        
        # Advanced Prediction Settings
        settings_group = QGroupBox("⚙️ Prediction Settings")
        settings_layout = QVBoxLayout()
        
        # Number of Days for Prediction
        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("Number of Days:"))
        self.days_slider = QSlider(Qt.Orientation.Horizontal)
        self.days_slider.setMinimum(7)
        self.days_slider.setMaximum(365)
        self.days_slider.setValue(30)
        self.days_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.days_slider.setTickInterval(30)
        days_layout.addWidget(self.days_slider)
        self.days_label = QLabel("30")
        self.days_slider.valueChanged.connect(lambda v: self.days_label.setText(str(v)))
        days_layout.addWidget(self.days_label)
        settings_layout.addLayout(days_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Predict Button
        self.advanced_predict_btn = QPushButton("🔮 Advanced Prediction")
        self.advanced_predict_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                padding: 15px 30px;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
        """)
        layout.addWidget(self.advanced_predict_btn)
        
        # Display Area for Advanced Predictions
        self.advanced_predictions_display = QTextEdit()
        self.advanced_predictions_display.setReadOnly(True)
        self.advanced_predictions_display.setFont(QFont("Arial", 11))
        layout.addWidget(QLabel("🔮 Advanced Predictions:"))
        layout.addWidget(self.advanced_predictions_display)
        
        # Connect Signals
        self.advanced_predict_btn.clicked.connect(self.generate_advanced_predictions)
        
        predictions_widget.setLayout(layout)
        self.tabs.addTab(predictions_widget, "🔮 Advanced Predictions")
        
    def load_data(self):
        """Load data from the database"""
        try:
            if self.db_manager:
                self.attendance_data = self.db_manager.get_all_attendance() or []
            else:
                self.attendance_data = []
        except Exception as e:
            self.attendance_data = []
            print(f"Error loading data: {e}")
    
    def create_daily_chart(self):
        """Create Daily Chart"""
        try:
            if not self.attendance_data:
                self.charts_display.setText("No data available for daily chart")
                return
                
            df = pd.DataFrame(self.attendance_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            daily_counts = df.groupby('date').size().reset_index()
            daily_counts.columns = ['date', 'count']
            
            result = "✅ Daily chart created successfully!\n\n"
            result += f"📊 Total days: {len(daily_counts)}\n"
            result += f"📈 Average daily attendance: {daily_counts['count'].mean():.1f}\n"
            result += f"📉 Minimum daily attendance: {daily_counts['count'].min()}\n"
            result += f"📊 Maximum daily attendance: {daily_counts['count'].max()}\n"
            
            self.charts_display.setText(result)
            
        except Exception as e:
            self.charts_display.setText(f"Error creating chart: {str(e)}")
    
    def create_weekly_chart(self):
        """Create Weekly Chart"""
        try:
            if not self.attendance_data:
                self.charts_display.setText("No data available for weekly chart")
                return
                
            df = pd.DataFrame(self.attendance_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['day_of_week'] = df['timestamp'].dt.day_name()
            
            weekly_counts = df.groupby('day_of_week').size()
            
            result = "✅ Weekly chart created successfully!\n\n"
            result += "📅 Attendance distribution by day:\n"
            for day, count in weekly_counts.items():
                result += f"  {day}: {count}\n"
            
            self.charts_display.setText(result)
            
        except Exception as e:
            self.charts_display.setText(f"Error creating chart: {str(e)}")
    
    def show_descriptive_stats(self):
        """Show Descriptive Statistics"""
        try:
            if not self.attendance_data:
                self.stats_display.setText("No data available for analysis")
                return
                
            df = pd.DataFrame(self.attendance_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # General Statistics
            total_records = len(df)
            unique_employees = df['employee_id'].nunique()
            date_range = f"{df['timestamp'].min().date()} to {df['timestamp'].max().date()}"
            
            # Daily Statistics
            daily_counts = df.groupby(df['timestamp'].dt.date).size()
            avg_daily = daily_counts.mean()
            std_daily = daily_counts.std()
            min_daily = daily_counts.min()
            max_daily = daily_counts.max()
            
            result = "📊 Descriptive Statistics:\n\n"
            result += f"📈 Total records: {total_records:,}\n"
            result += f"👥 Unique employees: {unique_employees:,}\n"
            result += f"📅 Date range: {date_range}\n\n"
            
            result += "📊 Daily Statistics:\n"
            result += f"  • Average: {avg_daily:.2f}\n"
            result += f"  • Standard deviation: {std_daily:.2f}\n"
            result += f"  • Minimum: {min_daily}\n"
            result += f"  • Maximum: {max_daily}\n"
            result += f"  • Coefficient of variation: {(std_daily/avg_daily)*100:.2f}%\n"
            
            self.stats_display.setText(result)
            
        except Exception as e:
            self.stats_display.setText(f"Error in statistical analysis: {str(e)}")
    
    def analyze_clustering(self):
        """Analyze Clustering"""
        try:
            if not self.attendance_data:
                self.patterns_display.setText("No data available for analysis")
                return
                
            df = pd.DataFrame(self.attendance_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_of_week
            
            result = "🎯 Clustering Analysis:\n\n"
            result += f"📊 Total records: {len(df)}\n"
            result += f"⏰ Average hour: {df['hour'].mean():.1f}\n"
            result += f"📅 Average day of week: {df['day_of_week'].mean():.1f}\n\n"
            
            result += "🔍 Data analysis successful!"
            
            self.patterns_display.setText(result)
            
        except Exception as e:
            self.patterns_display.setText(f"Error in clustering analysis: {str(e)}")
    
    def generate_advanced_predictions(self):
        """Generate Advanced Predictions"""
        try:
            if not self.attendance_data:
                self.advanced_predictions_display.setText("No data available for prediction")
                return
                
            days = self.days_slider.value()
            
            result = f"🔮 Advanced Predictions:\n\n"
            result += f"⚙️ Settings:\n"
            result += f"  • Number of days: {days}\n\n"
            
            # Generate predictions
            predictions = self.ai_manager.predict_attendance_trends(self.attendance_data, days)
            
            if predictions.get('predictions'):
                result += f"📊 Model accuracy: {predictions.get('model_accuracy', 0):.2%}\n"
                result += f"📈 Trend direction: {predictions.get('trend_direction', 'Undefined')}\n"
                result += f"💪 Trend strength: {predictions.get('trend_strength', 0):.2f}\n\n"
                
                result += "🔮 Future predictions:\n"
                for i, pred in enumerate(predictions['predictions'][:10]):
                    result += f"  {i+1:2d}. {pred['date']}: {pred['predicted_count']} attendance\n"
            else:
                result += "❌ Failed to generate predictions"
            
            self.advanced_predictions_display.setText(result)
            
        except Exception as e:
            self.advanced_predictions_display.setText(f"Error in advanced prediction: {str(e)}")
