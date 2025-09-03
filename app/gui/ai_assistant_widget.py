#!/usr/bin/env python3
"""
Advanced Smart Assistant Interface
"""

import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar, QComboBox, QDateEdit,
    QGroupBox, QScrollArea, QFrame, QSplitter
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

from app.core.ai_manager import AdvancedAIManager

class AIAssistantWidget(QWidget):
    """Advanced Smart Assistant Interface"""
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.ai_manager = AdvancedAIManager()
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        
        # Main title
        title = QLabel("🤖 Advanced Smart Assistant")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 12))
        
        # Smart Assistant Tab
        self.setup_chat_tab()
        
        # Smart Analysis Tab
        self.setup_analysis_tab()
        
        # Predictions Tab
        self.setup_predictions_tab()
        
        # Smart Reports Tab
        self.setup_reports_tab()
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def setup_chat_tab(self):
        """Setup chat tab"""
        chat_widget = QWidget()
        layout = QVBoxLayout()
        
        # Chat area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 11))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        layout.addWidget(QLabel("💬 Smart Conversation:"))
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Type your question here...")
        self.query_input.setFont(QFont("Arial", 11))
        self.query_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #007bff;
                border-radius: 20px;
                font-size: 14px;
            }
        """)
        
        self.send_button = QPushButton("🚀 Send")
        self.send_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        input_layout.addWidget(self.query_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)
        
        # Quick Questions Buttons
        quick_questions = QGroupBox("❓ Quick Questions")
        quick_layout = QHBoxLayout()
        
        questions = [
            "How can I improve attendance rate?",
            "What are the prevailing patterns?",
            "Are there any system issues?",
            "How can I increase efficiency?"
        ]
        
        for question in questions:
            btn = QPushButton(question)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            btn.clicked.connect(lambda checked, q=question: self.ask_quick_question(q))
            quick_layout.addWidget(btn)
        
        quick_questions.setLayout(quick_layout)
        layout.addWidget(quick_questions)
        
        # Connect signals
        self.send_button.clicked.connect(self.send_query)
        self.query_input.returnPressed.connect(self.send_query)
        
        chat_widget.setLayout(layout)
        self.tabs.addTab(chat_widget, "💬 Smart Assistant")
        
        # Welcome message
        self.add_message("🤖 Smart Assistant", "Hello! I'm your smart assistant. How can I help you today?")
        
    def setup_analysis_tab(self):
        """Setup Smart Analysis Tab"""
        analysis_widget = QWidget()
        layout = QVBoxLayout()
        
        # Analysis buttons
        analysis_buttons = QHBoxLayout()
        
        self.analyze_patterns_btn = QPushButton("🔍 Analyze Patterns")
        self.analyze_patterns_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        self.analyze_anomalies_btn = QPushButton("⚠️ Detect Anomalies")
        self.analyze_anomalies_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        
        self.analyze_trends_btn = QPushButton("📈 Analyze Trends")
        self.analyze_trends_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        analysis_buttons.addWidget(self.analyze_patterns_btn)
        analysis_buttons.addWidget(self.analyze_anomalies_btn)
        analysis_buttons.addWidget(self.analyze_trends_btn)
        layout.addLayout(analysis_buttons)
        
        # Results display area
        self.analysis_display = QTextEdit()
        self.analysis_display.setReadOnly(True)
        self.analysis_display.setFont(QFont("Arial", 11))
        self.analysis_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        layout.addWidget(QLabel("📊 Analysis Results:"))
        layout.addWidget(self.analysis_display)
        
        # Connect signals
        self.analyze_patterns_btn.clicked.connect(self.analyze_patterns)
        self.analyze_anomalies_btn.clicked.connect(self.analyze_anomalies)
        self.analyze_trends_btn.clicked.connect(self.analyze_trends)
        
        analysis_widget.setLayout(layout)
        self.tabs.addTab(analysis_widget, "🔍 Smart Analysis")
        
    def setup_predictions_tab(self):
        """Setup Predictions Tab"""
        predictions_widget = QWidget()
        layout = QVBoxLayout()
        
        # Prediction settings
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Number of days for prediction:"))
        
        self.days_combo = QComboBox()
        self.days_combo.addItems(["7", "14", "30", "60", "90"])
        self.days_combo.setCurrentText("30")
        settings_layout.addWidget(self.days_combo)
        
        self.predict_btn = QPushButton("🔮 Smart Prediction")
        self.predict_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
        """)
        settings_layout.addWidget(self.predict_btn)
        
        layout.addLayout(settings_layout)
        
        # Display Area for Predictions
        self.predictions_display = QTextEdit()
        self.predictions_display.setReadOnly(True)
        self.predictions_display.setFont(QFont("Arial", 11))
        layout.addWidget(QLabel("🔮 Future Predictions:"))
        layout.addWidget(self.predictions_display)
        
        # Connect signals
        self.predict_btn.clicked.connect(self.generate_predictions)
        
        predictions_widget.setLayout(layout)
        self.tabs.addTab(predictions_widget, "🔮 Predictions")
        
    def setup_reports_tab(self):
        """Setup Smart Reports Tab"""
        reports_widget = QWidget()
        layout = QVBoxLayout()
        
        # Report buttons
        reports_buttons = QHBoxLayout()
        
        self.comprehensive_report_btn = QPushButton("📋 Comprehensive Report")
        self.comprehensive_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        self.performance_report_btn = QPushButton("⚡ Performance Report")
        self.performance_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8690b;
            }
        """)
        
        reports_buttons.addWidget(self.comprehensive_report_btn)
        reports_buttons.addWidget(self.performance_report_btn)
        layout.addLayout(reports_buttons)
        
        # Report display area
        self.reports_display = QTextEdit()
        self.reports_display.setReadOnly(True)
        self.reports_display.setFont(QFont("Arial", 11))
        layout.addWidget(QLabel("📊 Smart Reports:"))
        layout.addWidget(self.reports_display)
        
        # Connect signals
        self.comprehensive_report_btn.clicked.connect(self.generate_comprehensive_report)
        self.performance_report_btn.clicked.connect(self.generate_performance_report)
        
        reports_widget.setLayout(layout)
        self.tabs.addTab(reports_widget, "📊 Smart Reports")
        
    def load_data(self):
        """Load data from database"""
        try:
            if self.db_manager:
                self.attendance_data = self.db_manager.get_all_attendance() or []
            else:
                self.attendance_data = []
        except Exception as e:
            self.attendance_data = []
            print(f"Error loading data: {e}")
    
    def add_message(self, sender: str, message: str):
        """Add message to conversation"""
        current_text = self.chat_display.toPlainText()
        timestamp = QDate.currentDate().toString("yyyy-MM-dd")
        new_message = f"[{timestamp}] {sender}: {message}\n\n"
        self.chat_display.append(new_message)
        self.chat_display.ensureCursorVisible()
    
    def send_query(self):
        """Send query to smart assistant"""
        query = self.query_input.text().strip()
        if not query:
            return
            
        # Add user query
        self.add_message("👤 You", query)
        self.query_input.clear()
        
        # Get response from smart assistant
        try:
            response = self.ai_manager.get_smart_assistant_response(query)
            self.add_message("🤖 Smart Assistant", response)
        except Exception as e:
            self.add_message("🤖 Smart Assistant", f"Sorry, an error occurred: {str(e)}")
    
    def ask_quick_question(self, question: str):
        """Ask a quick question"""
        self.query_input.setText(question)
        self.send_query()
    
    def analyze_patterns(self):
        """Analyze patterns"""
        try:
            if not self.attendance_data:
                self.analysis_display.setText("No data available for analysis")
                return
                
            analysis = self.ai_manager.analyze_attendance_patterns(self.attendance_data)
            patterns = analysis.get('patterns', {})
            
            result = "🔍 Pattern Analysis:\n\n"
            result += f"📊 Total Records: {analysis.get('total_records', 0)}\n"
            result += f"👥 Number of Employees: {analysis.get('unique_employees', 0)}\n\n"
            
            if 'day_distribution' in patterns:
                result += "📅 Attendance Distribution by Days:\n"
                for day, count in patterns['day_distribution'].items():
                    result += f"  {day}: {count}\n"
                result += "\n"
            
            if 'hour_distribution' in patterns:
                result += "⏰ Attendance Distribution by Hours:\n"
                for hour, count in patterns['hour_distribution'].items():
                    result += f"  {hour}:00 - {count}\n"
                result += "\n"
            
            self.analysis_display.setText(result)
            
        except Exception as e:
            self.analysis_display.setText(f"Error in analysis: {str(e)}")
    
    def analyze_anomalies(self):
        """Detect anomalies"""
        try:
            if not self.attendance_data:
                self.analysis_display.setText("No data available for analysis")
                return
                
            analysis = self.ai_manager.analyze_attendance_patterns(self.attendance_data)
            anomalies = analysis.get('anomalies', [])
            
            result = "⚠️ Anomaly Detection:\n\n"
            
            if anomalies:
                for anomaly in anomalies:
                    result += f"🔴 Type: {anomaly.get('type', 'Not specified')}\n"
                    result += f"   Employee: {anomaly.get('employee_id', 'Not specified')}\n"
                    result += f"   Severity: {anomaly.get('severity', 'Not specified')}\n"
                    if 'delay_minutes' in anomaly:
                        result += f"   Delay: {anomaly.get('delay_minutes', 0)} minutes\n"
                    result += "\n"
            else:
                result += "✅ No anomalies detected in the data"
            
            self.analysis_display.setText(result)
            
        except Exception as e:
            self.analysis_display.setText(f"Error in analysis: {str(e)}")
    
    def analyze_trends(self):
        """Analyze trends"""
        try:
            if not self.attendance_data:
                self.analysis_display.setText("No data available for analysis")
                return
                
            analysis = self.ai_manager.analyze_attendance_patterns(self.attendance_data)
            trends = analysis.get('trends', {})
            
            result = "📈 Trend Analysis:\n\n"
            
            if 'monthly_growth' in trends:
                growth = trends['monthly_growth']
                direction = "📈 Increase" if growth > 0 else "📉 Decrease"
                result += f"Monthly Growth Rate: {growth:.2f}%\n"
                result += f"Growth Direction: {direction}\n\n"
            
            if 'trend_direction' in trends:
                result += f"General Trend: {trends['trend_direction']}\n"
            
            if 'weekly_slope' in trends:
                slope = trends['weekly_slope']
                result += f"Weekly Trend Slope: {slope:.2f}\n"
            
            self.analysis_display.setText(result)
            
        except Exception as e:
            self.analysis_display.setText(f"Error in analysis: {str(e)}")
    
    def generate_predictions(self):
        """Generate predictions"""
        try:
            if not self.attendance_data:
                self.predictions_display.setText("No data available for prediction")
                return
                
            days = int(self.days_combo.currentText())
            predictions = self.ai_manager.predict_attendance_trends(self.attendance_data, days)
            
            result = f"🔮 Predictions for the next {days} days:\n\n"
            
            if predictions.get('predictions'):
                result += f"📊 Model Accuracy: {predictions.get('model_accuracy', 0):.2%}\n"
                result += f"📈 Trend Direction: {predictions.get('trend_direction', 'Not specified')}\n"
                result += f"💪 Trend Strength: {predictions.get('trend_strength', 0):.2f}\n\n"
                
                result += "Daily predictions:\n"
                for pred in predictions['predictions'][:10]:  # Show first 10 predictions
                    result += f"  {pred['date']}: {pred['predicted_count']} (confidence: {pred['confidence']:.1%})\n"
            else:
                result += "❌ Failed to generate predictions"
            
            self.predictions_display.setText(result)
            
        except Exception as e:
            self.predictions_display.setText(f"Error in prediction: {str(e)}")
    
    def generate_comprehensive_report(self):
        """Generate comprehensive report"""
        try:
            if not self.attendance_data:
                self.reports_display.setText("No data available for report")
                return
                
            report = self.ai_manager.generate_smart_report(self.attendance_data, "comprehensive")
            
            result = "📋 Comprehensive Report:\n\n"
            result += f"📅 Generation Date: {report.get('generated_at', 'Not specified')}\n"
            result += f"📊 Report Type: {report.get('report_type', 'Not specified')}\n\n"
            
            if 'summary' in report:
                result += "📝 Executive Summary:\n"
                result += report['summary'] + "\n\n"
            
            if 'recommendations' in report:
                result += "💡 Recommendations:\n"
                for rec in report['recommendations']:
                    result += f"  • {rec}\n"
                result += "\n"
            
            self.reports_display.setText(result)
            
        except Exception as e:
            self.reports_display.setText(f"Error in report: {str(e)}")
    
    def generate_performance_report(self):
        """Generate performance report"""
        try:
            if not self.attendance_data:
                self.reports_display.setText("No data available for report")
                return
                
            # Performance analysis
            df = pd.DataFrame(self.attendance_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            result = "⚡ Performance Report:\n\n"
            
            # General statistics
            result += f"📊 Total Records: {len(df)}\n"
            result += f"👥 Number of Employees: {df['employee_id'].nunique()}\n"
            result += f"📅 Date Range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}\n\n"
            
            # Daily performance analysis
            daily_counts = df.groupby(df['timestamp'].dt.date).size()
            result += f"📈 Average Daily Attendance: {daily_counts.mean():.1f}\n"
            result += f"📉 Lowest Attendance Day: {daily_counts.min()} (on {daily_counts.idxmin()})\n"
            result += f"📊 Highest Attendance Day: {daily_counts.max()} (on {daily_counts.idxmax()})\n\n"
            
            # Weekly performance analysis
            df['day_of_week'] = df['timestamp'].dt.day_name()
            weekly_counts = df.groupby('day_of_week').size()
            result += "📅 Weekly Performance:\n"
            for day, count in weekly_counts.items():
                result += f"  {day}: {count}\n"
            
            self.reports_display.setText(result)
            
        except Exception as e:
            self.reports_display.setText(f"Error في التقرير: {str(e)}")
