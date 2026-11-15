#!/usr/bin/env python3
"""
LoyaltyOS — Offline Synthetic Data Generator CLI
Used exclusively for offline development, local dataset generation, and synthetic benchmark data creation.
This is NOT a production runtime server. Production LoyaltyOS runs 100% on Supabase.
"""

import sys
import os
import argparse

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.seed.cli import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="LoyaltyOS Offline Synthetic Data Generator (Dev Tool)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic PRNG random seed (default: 42)",
    )
    parser.add_argument(
        "--scale",
        type=str,
        default="TEST",
        choices=["TEST", "MEDIUM", "FULL"],
        help="Dataset scale preset (default: TEST)",
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default="data",
        help="Target output directory for JSON fixtures (default: data)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip strict mathematical invariant validation checks",
    )

    args = parser.parse_args()

    print("==================================================================")
    print(" LoyaltyOS — Offline Synthetic Data Generation Utility")
    print(" Note: Production backend is 100% Supabase (PostgreSQL + RPC + RLS)")
    print("==================================================================")

    res = run_pipeline(
        seed=args.seed,
        scale_name=args.scale,
        export_dir=args.export_dir,
        validate=not args.no_validate,
    )
    print(f"\n[OK] Successfully generated and exported dataset fixtures to '{args.export_dir}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
