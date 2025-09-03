#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced AI Manager
مدير الذكاء الاصطناعي المتقدم
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

class AdvancedAIManager:
    """Advanced AI Manager"""
    
    def __init__(self, config_file: str = "ai_config.json"):
        """Initialize AI Manager"""
        # Create logger first
        self.logger = self._setup_logger()
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Setup AI services
        self.setup_ai_services()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging system"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
        
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default settings
            return {
                "google_ai": {
                    "api_key": "AIzaSyDjAUfp_iO5bWItP300hd-RuUW-OCsphlM",
                    "model": "gemini-1.5-flash"
                },
                "analysis": {
                    "enable_predictions": True,
                    "enable_anomaly_detection": True,
                    "chart_theme": "plotly_white"
                }
            }
    
    def setup_ai_services(self):
        """Setup AI services"""
        try:
            # Setup Google Generative AI
            api_key = self.config.get("google_ai", {}).get("api_key")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.logger.info("✅ Google Generative AI setup successful")
            else:
                self.logger.warning("⚠️ Google AI API key not found")
                self.gemini_model = None
            
            # Setup LangChain
            if api_key:
                self.langchain_model = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=api_key,
                    temperature=0.7
                )
                self.logger.info("✅ LangChain setup successful")
            else:
                self.langchain_model = None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to setup AI services: {e}")
            self.gemini_model = None
            self.langchain_model = None
    
    def analyze_attendance_patterns(self, attendance_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze attendance patterns using AI"""
        try:
            if attendance_data.empty:
                return {"error": "No attendance data available"}
            
            analysis_results = {
                "basic_stats": {},
                "patterns": {},
                "anomalies": [],
                "trends": {},
                "recommendations": []
            }
            
            # Basic statistics
            analysis_results["basic_stats"] = {
                "total_records": len(attendance_data),
                "unique_employees": attendance_data.get('employee_id', pd.Series()).nunique(),
                "date_range": {
                    "start": attendance_data.get('date', pd.Series()).min(),
                    "end": attendance_data.get('date', pd.Series()).max()
                }
            }
            
            # Pattern analysis
            if 'date' in attendance_data.columns and 'employee_id' in attendance_data.columns:
                daily_counts = attendance_data.groupby('date').size()
                analysis_results["patterns"]["daily_attendance"] = {
                    "mean": daily_counts.mean(),
                    "std": daily_counts.std(),
                    "min": daily_counts.min(),
                    "max": daily_counts.max()
                }
            
            # Anomaly detection
            if 'time' in attendance_data.columns:
                time_series = pd.to_datetime(attendance_data['time'])
                late_arrivals = time_series.dt.hour > 9  # After 9 AM
                analysis_results["anomalies"].append({
                    "type": "late_arrivals",
                    "count": late_arrivals.sum(),
                    "percentage": (late_arrivals.sum() / len(attendance_data)) * 100
                })
            
            # Trend analysis
            if 'date' in attendance_data.columns:
                date_counts = attendance_data.groupby('date').size().reset_index()
                date_counts.columns = ['date', 'count']
                date_counts['date'] = pd.to_datetime(date_counts['date'])
                date_counts = date_counts.sort_values('date')
                
                if len(date_counts) > 1:
                    # Simple prediction model
                    X = np.arange(len(date_counts)).reshape(-1, 1)
                    y = date_counts['count'].values
                    
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    analysis_results["trends"]["linear_trend"] = {
                        "slope": model.coef_[0],
                        "direction": "increasing" if model.coef_[0] > 0 else "decreasing",
                        "r2_score": model.score(X, y)
                    }
            
            # Recommendations
            if analysis_results["anomalies"]:
                analysis_results["recommendations"].append(
                    "Monitor late employees and apply attendance policies"
                )
            
            if analysis_results["trends"].get("linear_trend", {}).get("direction") == "decreasing":
                analysis_results["recommendations"].append(
                    "Analyze reasons for declining attendance rate"
                )
            
            self.logger.info("✅ Attendance pattern analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ Failed in attendance pattern analysis: {e}")
            return {"error": f"Failed in analysis: {str(e)}"}
    
    def create_interactive_charts(self, attendance_data: pd.DataFrame) -> Dict[str, str]:
        """Create interactive charts"""
        try:
            if attendance_data.empty:
                return {"error": "No attendance data available"}
            
            charts = {}
            
            # Daily chart
            if 'date' in attendance_data.columns:
                daily_counts = attendance_data.groupby('date').size().reset_index()
                daily_counts.columns = ['date', 'count']
                
                fig = px.line(daily_counts, x='date', y='count', 
                            title='Daily Attendance Rate',
                            labels={'date': 'Date', 'count': 'Attendance Count'})
                fig.update_layout(template=self.config.get("analysis", {}).get("chart_theme", "plotly_white"))
                
                # Save chart as HTML file
                chart_file = f"daily_attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                fig.write_html(chart_file)
                charts["daily_chart"] = chart_file
            
            # Weekly chart
            if 'date' in attendance_data.columns:
                attendance_data_copy = attendance_data.copy()
                attendance_data_copy['date'] = pd.to_datetime(attendance_data_copy['date'])
                attendance_data_copy['week'] = attendance_data_copy['date'].dt.isocalendar().week
                
                weekly_counts = attendance_data_copy.groupby('week').size().reset_index()
                weekly_counts.columns = ['week', 'count']
                
                fig = px.bar(weekly_counts, x='week', y='count',
                            title='Weekly Attendance Rate',
                            labels={'week': 'Week', 'count': 'Attendance Count'})
                fig.update_layout(template=self.config.get("analysis", {}).get("chart_theme", "plotly_white"))
                
                chart_file = f"weekly_attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                fig.write_html(chart_file)
                charts["weekly_chart"] = chart_file
            
            # Heatmap
            if 'date' in attendance_data.columns and 'employee_id' in attendance_data.columns:
                attendance_data_copy = attendance_data.copy()
                attendance_data_copy['date'] = pd.to_datetime(attendance_data_copy['date'])
                attendance_data_copy['hour'] = pd.to_datetime(attendance_data_copy.get('time', '00:00')).dt.hour
                
                pivot_data = attendance_data_copy.pivot_table(
                    index='date', columns='hour', values='employee_id', 
                    aggfunc='count', fill_value=0
                )
                
                fig = px.imshow(pivot_data, 
                              title='Attendance Heatmap by Time and Date',
                              labels={'x': 'Hour', 'y': 'Date', 'color': 'Attendance Count'})
                fig.update_layout(template=self.config.get("analysis", {}).get("chart_theme", "plotly_white"))
                
                chart_file = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                fig.write_html(chart_file)
                charts["heatmap"] = chart_file
            
            self.logger.info("✅ Interactive charts created successfully")
            return charts
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create interactive charts: {e}")
            return {"error": f"Failed to create charts: {str(e)}"}
    
    def generate_smart_qr(self, data: Dict[str, Any]) -> str:
        """Create smart QR code with embedded data"""
        try:
            import qrcode
            from PIL import Image
            
            # Convert data to JSON
            json_data = json.dumps(data, ensure_ascii=False)
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json_data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save image
            filename = f"smart_qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(filename)
            
            self.logger.info(f"✅ Smart QR code created: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create QR code: {e}")
            return ""
    
    def decode_smart_qr(self, qr_image_path: str) -> Dict[str, Any]:
        """Decode smart QR code"""
        try:
            from pyzbar.pyzbar import decode
            from PIL import Image
            
            # Read image
            image = Image.open(qr_image_path)
            
            # Decode QR code
            decoded_objects = decode(image)
            
            if decoded_objects:
                data = decoded_objects[0].data.decode('utf-8')
                return json.loads(data)
            else:
                return {"error": "QR code not found"}
                
        except Exception as e:
            self.logger.error(f"❌ Failed to decode QR code: {e}")
            return {"error": f"Failed to decode: {str(e)}"}
    
    def predict_attendance_trends(self, attendance_data: pd.DataFrame, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict future attendance trends"""
        try:
            if attendance_data.empty or 'date' not in attendance_data.columns:
                return {"error": "Insufficient data for prediction"}
            
            # Aggregate daily data
            daily_counts = attendance_data.groupby('date').size().reset_index()
            daily_counts.columns = ['date', 'count']
            daily_counts['date'] = pd.to_datetime(daily_counts['date'])
            daily_counts = daily_counts.sort_values('date')
            
            if len(daily_counts) < 3:
                return {"error": "Need more data for prediction"}
            
            # Prepare data for prediction
            X = np.arange(len(daily_counts)).reshape(-1, 1)
            y = daily_counts['count'].values
            
            # Linear regression model
            model = LinearRegression()
            model.fit(X, y)
            
            # Prediction
            future_days = np.arange(len(daily_counts), len(daily_counts) + days_ahead).reshape(-1, 1)
            predictions = model.predict(future_days)
            
            # Create future dates
            last_date = daily_counts['date'].max()
            future_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
            
            prediction_results = {
                "model_info": {
                    "type": "Linear Regression",
                    "r2_score": model.score(X, y),
                    "slope": model.coef_[0],
                    "intercept": model.intercept_
                },
                "predictions": [
                    {
                        "date": date.strftime('%Y-%m-%d'),
                        "predicted_count": int(pred),
                        "confidence": "medium"  # Can be improved
                    }
                    for date, pred in zip(future_dates, predictions)
                ],
                "trend": "increasing" if model.coef_[0] > 0 else "decreasing"
            }
            
            self.logger.info(f"✅ Predicted {days_ahead} future days")
            return prediction_results
            
        except Exception as e:
            self.logger.error(f"❌ Failed in prediction: {e}")
            return {"error": f"Failed in prediction: {str(e)}"}
    
    def get_smart_assistant_response(self, user_query: str) -> str:
        """Get response from smart assistant"""
        try:
            if not self.gemini_model:
                return "Sorry, the smart assistant service is not available at the moment"
            
            # Setup context
            context = f"""
            You are a smart assistant for an attendance management system. 
            You can help users with:
            - Analyzing attendance data
            - Understanding patterns and trends
            - Providing recommendations to improve productivity
            - Answering questions about the system
            
            IMPORTANT: Always respond in English language only.
            
            Question: {user_query}
            """
            
            # Get response
            response = self.gemini_model.generate_content(context)
            
            if response and hasattr(response, 'text'):
                return response.text
            else:
                return "Sorry, I couldn't get an appropriate response"
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get smart assistant response: {e}")
            return f"Sorry, an error occurred: {str(e)}"
    
    def generate_smart_report(self, attendance_data: pd.DataFrame) -> Dict[str, Any]:
        """Create comprehensive smart report"""
        try:
            if attendance_data.empty:
                return {"error": "No attendance data available"}
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": {},
                "analysis": {},
                "charts": {},
                "predictions": {},
                "recommendations": []
            }
            
            # Basic analysis
            analysis = self.analyze_attendance_patterns(attendance_data)
            report["analysis"] = analysis
            
            # Charts
            charts = self.create_interactive_charts(attendance_data)
            report["charts"] = charts
            
            # Predictions
            predictions = self.predict_attendance_trends(attendance_data, days_ahead=7)
            report["predictions"] = predictions
            
            # Summary
            report["summary"] = {
                "total_records": len(attendance_data),
                "analysis_status": "completed" if "error" not in analysis else "failed",
                "charts_created": len([k for k in charts.keys() if k != "error"]),
                "predictions_made": "error" not in predictions
            }
            
            # Recommendations
            if "recommendations" in analysis:
                report["recommendations"].extend(analysis["recommendations"])
            
            if predictions.get("trend") == "decreasing":
                report["recommendations"].append(
                    "Analyze reasons for declining attendance rate and take corrective actions"
                )
            
            self.logger.info("✅ Smart report created successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Failed في إنشاء التقرير الذكي: {e}")
            return {"error": f"Failed في إنشاء التقرير: {str(e)}"}
    
    def verify_attendance_authenticity(self, attendance_record: Dict[str, Any]) -> Dict[str, Any]:
        """التحقق من صحة سجل الحضور"""
        try:
            verification_results = {
                "is_authentic": True,
                "confidence_score": 0.0,
                "warnings": [],
                "verification_methods": []
            }
            
            # التحقق من صحة التاريخ
            if 'date' in attendance_record:
                try:
                    date = pd.to_datetime(attendance_record['date'])
                    if date > datetime.now():
                        verification_results["warnings"].append("تاريخ في المستقبل")
                        verification_results["is_authentic"] = False
                except:
                    verification_results["warnings"].append("تاريخ غير صحيح")
                    verification_results["is_authentic"] = False
            
            # التحقق من صحة الوقت
            if 'time' in attendance_record:
                try:
                    time = pd.to_datetime(attendance_record['time']).time()
                    if time.hour < 0 or time.hour > 23:
                        verification_results["warnings"].append("وقت غير صحيح")
                        verification_results["is_authentic"] = False
                except:
                    verification_results["warnings"].append("تنسيق وقت غير صحيح")
                    verification_results["is_authentic"] = False
            
            # حساب درجة الثقة
            total_checks = 2
            passed_checks = total_checks - len(verification_results["warnings"])
            verification_results["confidence_score"] = (passed_checks / total_checks) * 100
            
            verification_results["verification_methods"] = [
                "date_validation",
                "time_validation"
            ]
            
            self.logger.info(f"✅ تم التحقق من صحة السجل: {verification_results['confidence_score']}%")
            return verification_results
            
        except Exception as e:
            self.logger.error(f"❌ Failed في التحقق من صحة السجل: {e}")
            return {"error": f"Failed في التحقق: {str(e)}"}
    
    def optimize_performance(self) -> Dict[str, Any]:
        """تحسين أداء النظام"""
        try:
            optimization_suggestions = {
                "database": [
                    "إنشاء فهارس على الأعمدة المستخدمة بكثرة في الSearch",
                    "تنظيف البيانات القديمة بانتظام",
                    "استخدام الاستعلامات المحسنة"
                ],
                "memory": [
                    "تطبيق التخزين المؤقت للبيانات المتكررة",
                    "تحسين حجم البيانات المحملة في الذاكرة",
                    "استخدام الضغط للبيانات الكبيرة"
                ],
                "processing": [
                    "تطبيق المعالجة المتوازية للعمليات الثقيلة",
                    "تحسين خوارزميات الSearch والفرز",
                    "استخدام التخزين المؤقت للعمليات المتكررة"
                ]
            }
            
            self.logger.info("✅ تم إنشاء اقتراحات تحسين الأداء")
            return optimization_suggestions
            
        except Exception as e:
            self.logger.error(f"❌ Failed في إنشاء اقتراحات التحسين: {e}")
            return {"error": f"Failed في إنشاء اقتراحات التحسين: {str(e)}"}
