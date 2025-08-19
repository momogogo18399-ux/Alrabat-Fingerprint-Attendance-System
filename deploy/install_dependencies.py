#!/usr/bin/env python3
"""
Script to install missing dependencies for the security check script
"""

import subprocess
import sys
import os

def install_package(package_name):
    """Install a Python package using pip"""
    try:
        print(f"Installing {package_name}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Successfully installed {package_name}")
            return True
        else:
            print(f"✗ Failed to install {package_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error installing {package_name}: {e}")
        return False

def main():
    """Main function to install required dependencies"""
    print("Installing dependencies for security check script...")
    print()
    
    # Try to install from requirements.txt first
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_file):
        print("Installing from requirements.txt...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Successfully installed dependencies from requirements.txt")
                print("You can now run the security check script.")
                return
            else:
                print(f"⚠ Failed to install from requirements.txt: {result.stderr}")
                print("Falling back to individual package installation...")
                print()
        except Exception as e:
            print(f"⚠ Error installing from requirements.txt: {e}")
            print("Falling back to individual package installation...")
            print()
    
    # Fallback to individual package installation
    required_packages = [
        "requests",
        "psycopg2-binary",
        "python-dotenv",
        "psutil"
    ]
    
    success_count = 0
    
    for package in required_packages:
        if install_package(package):
            success_count += 1
        print()
    
    print(f"Installation completed: {success_count}/{len(required_packages)} packages installed successfully")
    
    if success_count == len(required_packages):
        print("✓ All dependencies installed successfully!")
        print("You can now run the security check script.")
    else:
        print("⚠ Some packages failed to install. Please check the errors above.")
        print("You may need to run with elevated privileges: sudo python install_dependencies.py")

if __name__ == "__main__":
    main()
