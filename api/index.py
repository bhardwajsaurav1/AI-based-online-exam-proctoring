"""
Vercel Serverless Function Entrypoint.
Exposes WSGI app for @vercel/python.
"""
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app import app

# Vercel looks for `app` instance
app = app
