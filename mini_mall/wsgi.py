"""
WSGI entry point for PythonAnywhere deployment.
Path: /home/你的用户名/mini_mall/wsgi.py
"""

import sys
import os

# Project root
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Create Flask app
from app import create_app
application = create_app('production')
