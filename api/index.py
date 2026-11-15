"""
LoyaltyOS — Vercel Python Serverless Function Entrypoint
Binds the FastAPI application to Vercel's serverless runtime.
"""
import sys
from pathlib import Path

# Ensure project root and backend are in Python search path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.app.main import app
