# app/utils/location_parser.py

import re

def extract_lat_lon_from_url(url: str):
    """
    يستخلص خطوط الطول والعرض من رابط خرائط جوجل.
    
    يSearch عن النمط الشائع مثل @latitude,longitude
    أو ?q=latitude,longitude

    :param url: رابط خرائط جوجل كنص.
    :return: tuple يحتوي على (latitude, longitude) إذا Success، أو None إذا Failed.
    """
    if not url:
        return None

    # استخدام التعبيرات النمطية (Regular Expressions) للSearch عن الإحداثيات
    # هذا النمط يSearch عن رقمين عشريين (قد يكونان سالبين) بينهما فاصلة
    pattern = r'@(-?\d+\.\d+),(-?\d+\.\d+)|q=(-?\d+\.\d+),(-?\d+\.\d+)'
    
    match = re.search(pattern, url)
    
    if match:
        # re.search يجد كل المجموعات، ونحن نأخذ المجموعات التي تحتوي على قيم
        # (lat1, lon1, lat2, lon2) -> سيتم ملء إما (lat1, lon1) أو (lat2, lon2)
        groups = match.groups()
        lat = float(groups[0] or groups[2])
        lon = float(groups[1] or groups[3])
        return lat, lon
        
    return None