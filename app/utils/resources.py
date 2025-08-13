import os
import sys

def resource_path(relative_path: str) -> str:
    """
    يُعيد مسار مورد صالح سواءً كان التطبيق يعمل من السورس أو من ملف تنفيذي مُجمّع (PyInstaller).
    """
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    except Exception:
        base_path = os.path.abspath(".")
    candidate_path = os.path.join(base_path, relative_path)
    if os.path.exists(candidate_path):
        return candidate_path
    # محاولة نهائية: المسار النسبي كما هو (للعمل أثناء التطوير)
    return relative_path



