#!/usr/bin/env python3
"""
LoyaltyOS — Seed Data CLI Entry Point
Execute synthetic data generation, validation, export, and optional database loading.

Usage:
    python scripts/seed_data.py --scale TEST --export-dir data
    python scripts/seed_data.py --seed 20261022 --scale FULL --export-dir data
    python scripts/seed_data.py --load-db --scale TEST
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.seed.cli import main

if __name__ == "__main__":
    main()
