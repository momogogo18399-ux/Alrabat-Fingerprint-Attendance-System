"""
Vercel Serverless Function Entry Point
This file serves as the main entry point for Vercel deployment
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from web_app
from web_app import app

# Export the Flask app for Vercel
handler = app
