#!/bin/bash

# Vercel Build Script for Fingerprint Attendance System
echo "🚀 Starting Vercel build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p temp

# Set environment variables
echo "🔧 Setting environment variables..."
export PYTHONPATH="."
export FLASK_ENV="production"

# Test the application
echo "🧪 Testing application..."
python -c "import web_app; print('✅ Web app imports successfully')"

echo "✅ Vercel build completed successfully!"
