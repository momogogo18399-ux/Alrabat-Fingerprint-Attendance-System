import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment variable to indicate we're running from the root
os.environ['RUN_FROM_ROOT'] = '1'

# Import and run the main application
from app.main import main

if __name__ == "__main__":
    main()
