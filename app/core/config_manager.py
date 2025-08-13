import configparser
import os

# تحديد مسار ملف الإعدادات بشكل ثابت ليكون بجانب هذا السكربت
# هذا يضمن العثور عليه دائمًا بغض النظر عن مكان تشغيل البرنامج
try:
    # هذا يعمل عندما يتم تشغيل المشروع كبرنامج عادي
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # هذا يعمل في بعض البيئات التفاعلية
    APP_DIR = os.getcwd()

CONFIG_FILE = os.path.join(APP_DIR, 'config.ini')

def get_config():
    """
    يقرأ ملف الإعدادات ويعيده ككائن ConfigParser.
    """
    config = configparser.ConfigParser()
    
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE, encoding='utf-8')
    else:
        # إنشاء قيم افتراضية إذا لم يكن الملف موجودًا
        config['Device'] = {
            'ip': '192.168.1.201',
            'port': '4370',
            'password': '0'
        }
        save_config(config) # حفظ الملف بالقيم الافتراضية
        
    return config

def save_config(config):
    """
    يحفظ كائن الإعدادات في ملف config.ini.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except Exception as e:
        print(f"Error saving config file at {CONFIG_FILE}: {e}")