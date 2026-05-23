"""
WSGI entry point for PythonAnywhere deployment.
Place this file in your PythonAnywhere project root.

IMPORTANT: Update the path below to match your PythonAnywhere home directory.
Your username on PythonAnywhere will be different.
"""
import sys
import os

# ============================================================
# CONFIGURATION - UPDATE THESE PATHS FOR YOUR PYTHONANYWHERE ACCOUNT
# ============================================================
# Replace 'yourusername' with your actual PythonAnywhere username
PROJECT_ROOT = f'/home/yourusername/data-analytics-platform'

# Add project to Python path
sys.path.insert(0, PROJECT_ROOT)

# Set environment variable so Flask knows it's in production
os.environ['FLASK_ENV'] = 'production'

# Change working directory to project root
os.chdir(PROJECT_ROOT)

# Import and create the Flask app
from app import app as application

# ============================================================
# PythonAnywhere Web App Configuration:
# ============================================================
# 1. Go to PythonAnywhere -> Web tab -> Add a new web app
# 2. Choose "Manual configuration" (not Flask template)
# 3. Select Python 3.x
# 4. Set the following in your Web tab:
#    - Source code: /home/yourusername/data-analytics-platform
#    - Working directory: /home/yourusername/data-analytics-platform
#    - WSGI configuration file: /home/yourusername/data-analytics-platform/deployment/wsgi.py
#    - Virtualenv: (create one and set the path)
# 5. Install requirements in your virtualenv:
#    pip install flask flask-cors numpy pandas scikit-learn matplotlib reportlab scipy openpyxl xlrd
# ============================================================
