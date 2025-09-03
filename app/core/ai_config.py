#!/usr/bin/env python3
"""
ملف تكوين الذكاء الاصطناعي
"""

import os
import json
from typing import Dict, Any

class AIConfig:
    """تكوين الذكاء الاصطناعي"""
    
    def __init__(self, config_file: str = "ai_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """تحميل التكوين"""
        default_config = {
            "google_ai": {
                "api_key": "AIzaSyDjAUfp_iO5bWItP300hd-RuUW-OCsphlM",
                "model": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "analysis": {
                "enable_face_recognition": True,
                "enable_qr_generation": True,
                "enable_predictions": True,
                "enable_anomaly_detection": True,
                "cache_enabled": True,
                "cache_duration": 3600
            },
            "charts": {
                "enable_interactive": True,
                "default_theme": "plotly_white",
                "colors": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"],
                "max_data_points": 1000
            },
            "performance": {
                "enable_optimization": True,
                "max_threads": 4,
                "batch_size": 100,
                "timeout": 30
            },
            "security": {
                "enable_verification": True,
                "max_retries": 3,
                "log_suspicious": True
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # دمج التكوين المحمل مع التكوين الافتراضي
                    self.merge_configs(default_config, loaded_config)
            else:
                # إنشاء ملف التكوين الافتراضي
                self.save_config(default_config)
                
        except Exception as e:
            print(f"Error في تحميل التكوين: {e}")
            
        return default_config
    
    def merge_configs(self, default: Dict, loaded: Dict):
        """دمج التكوينات"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self.merge_configs(default[key], value)
                else:
                    default[key] = value
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save التكوين"""
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print("✅ تم Save التكوين بنجاح")
        except Exception as e:
            print(f"❌ Failed في Save التكوين: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة من التكوين"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """تعيين قيمة في التكوين"""
        keys = key.split('.')
        config = self.config
        
        # التنقل إلى المستوى المطلوب
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # تعيين القيمة
        config[keys[-1]] = value
        
        # Save التكوين
        self.save_config()
    
    def update_google_ai_key(self, new_key: str):
        """Update مفتاح Google AI"""
        self.set("google_ai.api_key", new_key)
        print("✅ تم Update مفتاح Google AI")
    
    def get_google_ai_config(self) -> Dict[str, Any]:
        """الحصول على تكوين Google AI"""
        return self.get("google_ai", {})
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """الحصول على تكوين التحليل"""
        return self.get("analysis", {})
    
    def get_charts_config(self) -> Dict[str, Any]:
        """الحصول على تكوين الرسوم البيانية"""
        return self.get("charts", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """الحصول على تكوين الأداء"""
        return self.get("performance", {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """الحصول على تكوين الأمان"""
        return self.get("security", {})
    
    def is_feature_enabled(self, feature: str) -> bool:
        """التحقق من تفعيل ميزة معينة"""
        return self.get(f"analysis.enable_{feature}", False)
    
    def get_cache_duration(self) -> int:
        """الحصول على مدة التخزين المؤقت"""
        return self.get("analysis.cache_duration", 3600)
    
    def get_max_threads(self) -> int:
        """الحصول على الحد الأقصى للخيوط"""
        return self.get("performance.max_threads", 4)
    
    def get_batch_size(self) -> int:
        """الحصول على حجم الدفعة"""
        return self.get("performance.batch_size", 100)
    
    def get_timeout(self) -> int:
        """الحصول على مهلة الانتظار"""
        return self.get("performance.timeout", 30)
    
    def get_max_retries(self) -> int:
        """الحصول على الحد الأقصى للمحاولات"""
        return self.get("security.max_retries", 3)
    
    def get_chart_colors(self) -> list:
        """الحصول على ألوان الرسوم البيانية"""
        return self.get("charts.colors", ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"])
    
    def get_chart_theme(self) -> str:
        """الحصول على ثيم الرسوم البيانية"""
        return self.get("charts.default_theme", "plotly_white")
    
    def get_max_data_points(self) -> int:
        """الحصول على الحد الأقصى لنقاط البيانات"""
        return self.get("charts.max_data_points", 1000)
    
    def reset_to_defaults(self):
        """إعادة تعيين التكوين إلى القيم الافتراضية"""
        default_config = {
            "google_ai": {
                "api_key": "AIzaSyDjAUfp_iO5bWItP300hd-RuUW-OCsphlM",
                "model": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "analysis": {
                "enable_face_recognition": True,
                "enable_qr_generation": True,
                "enable_predictions": True,
                "enable_anomaly_detection": True,
                "cache_enabled": True,
                "cache_duration": 3600
            },
            "charts": {
                "enable_interactive": True,
                "default_theme": "plotly_white",
                "colors": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"],
                "max_data_points": 1000
            },
            "performance": {
                "enable_optimization": True,
                "max_threads": 4,
                "batch_size": 100,
                "timeout": 30
            },
            "security": {
                "enable_verification": True,
                "max_retries": 3,
                "log_suspicious": True
            }
        }
        
        self.config = default_config
        self.save_config()
        print("✅ تم إعادة تعيين التكوين إلى القيم الافتراضية")
    
    def export_config(self, export_file: str = "ai_config_export.json"):
        """تصدير التكوين"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ تم تصدير التكوين إلى {export_file}")
        except Exception as e:
            print(f"❌ Failed في تصدير التكوين: {e}")
    
    def import_config(self, import_file: str):
        """استيراد التكوين"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # دمج التكوين المستورد
            self.merge_configs(self.config, imported_config)
            self.save_config()
            print(f"✅ تم استيراد التكوين من {import_file}")
            
        except Exception as e:
            print(f"❌ Failed في استيراد التكوين: {e}")
    
    def validate_config(self) -> bool:
        """التحقق من صحة التكوين"""
        try:
            required_keys = [
                "google_ai.api_key",
                "google_ai.model",
                "analysis.enable_face_recognition",
                "analysis.enable_qr_generation",
                "performance.max_threads"
            ]
            
            for key in required_keys:
                if self.get(key) is None:
                    print(f"❌ مفتاح مطلوب مفقود: {key}")
                    return False
            
            # التحقق من صحة مفتاح API
            api_key = self.get("google_ai.api_key")
            if not api_key or len(api_key) < 10:
                print("❌ مفتاح API غير صالح")
                return False
            
            print("✅ التكوين صالح")
            return True
            
        except Exception as e:
            print(f"❌ Error في التحقق من التكوين: {e}")
            return False
