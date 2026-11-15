#!/usr/bin/env python3
"""
LoyaltyOS — Offline LLIRE Benchmark Evaluator
Used exclusively for offline development and evaluation of anomaly detection algorithms.
Evaluates detection precision, recall, and F1 scores against Phase 3 labelled ground-truth manifests.
This is NOT a production runtime server. Production LoyaltyOS runs 100% on Supabase.
"""

import sys
import os
import asyncio

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.intelligence.evaluator import IntelligenceEvaluator


async def run_evaluation():
    print("==================================================================")
    print(" LoyaltyOS — Offline LLIRE Intelligence Benchmark Evaluator")
    print(" Note: Production backend is 100% Supabase (PostgreSQL + RPC + RLS)")
    print("==================================================================")

    res = await IntelligenceEvaluator.evaluate()

    print(f"\nEvaluated At: {res.evaluated_at.isoformat()}")
    print(f"Dataset Scale: {res.dataset_scale}")
    print(f"Ground Truth Anomalies: {res.total_ground_truth_anomalies}")
    print(f"Detected Anomalies:     {res.total_detected_anomalies}")

    print("\n---------------------------------------------------------------------------------")
    print(f"{'Anomaly Category':<24} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10}")
    print("---------------------------------------------------------------------------------")

    for cat_name, m in res.categories.items():
        p_str = f"{m.precision * 100:.1f}%"
        r_str = f"{m.recall * 100:.1f}%"
        f1_str = f"{m.f1_score * 100:.1f}%"
        print(f"{cat_name:<24} | {m.true_positives:<4} | {m.false_positives:<4} | {m.false_negatives:<4} | {p_str:<10} | {r_str:<10} | {f1_str:<10}")

    agg = res.aggregate
    print("---------------------------------------------------------------------------------")
    print(f"{'OVERALL AGGREGATE':<24} | {agg.true_positives:<4} | {agg.false_positives:<4} | {agg.false_negatives:<4} | {agg.precision*100:.1f}%{'':<5} | {agg.recall*100:.1f}%{'':<5} | {agg.f1_score*100:.1f}%")
    print("---------------------------------------------------------------------------------")
    print("\n[OK] Benchmark evaluation completed successfully.")


def main():
    asyncio.run(run_evaluation())
    return 0


if __name__ == "__main__":
    sys.exit(main())
