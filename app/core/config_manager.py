import configparser
import os

CONFIG_FILE = 'config.ini'

def get_config():
    """
    يقرأ ملف الإعدادات ويعيده ككائن.
    """
    config = configparser.ConfigParser()
    # يقرأ الملف الموجود أو يستخدم القيم الافتراضية إذا لم يكن موجودًا
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        # قيم افتراضية
        config['Device'] = {
            'ip': '192.168.1.201',
            'port': '4370',
            'password': '0'
        }
    return config

def save_config(config):
    """
    يحفظ كائن الإعدادات في ملف config.ini.
    """
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# مثال للاستخدام
# config = get_config()
# ip = config.get('Device', 'ip')
# print(f"Device IP from config: {ip}")