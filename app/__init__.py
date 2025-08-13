import os

try:
    # Load .env from project root if present
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
except Exception:
    pass


