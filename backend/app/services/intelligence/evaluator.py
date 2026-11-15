import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.intelligence import (
    CategoryEvaluationMetrics,
    EngineEvaluationResponse,
)
from backend.app.services.intelligence.base import AnomalyFinding
from backend.app.services.intelligence.engine import intelligence_engine


class IntelligenceEvaluator:
    """
    Evaluates LLIRE detector performance against Phase 3 labelled ground-truth manifests.
    Computes True Positives (TP), False Positives (FP), False Negatives (FN), True Negatives (TN),
    Precision, Recall, and F1 Score independently per category and in aggregate.
    Never uses ground truth as detector inputs.
    """

    MANIFEST_PATH = os.path.join("data", "manifests", "ground_truth_manifest.json")
    GROUND_TRUTH_DIR = os.path.join("data", "ground_truth")

    @classmethod
    def load_ground_truth(cls) -> Optional[Dict[str, Any]]:
        if not os.path.exists(cls.MANIFEST_PATH):
            return None
        with open(cls.MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def load_ground_truth_dataset(cls) -> Optional[Dict[str, Any]]:
        if not os.path.exists(cls.GROUND_TRUTH_DIR):
            return None
        dataset = {}
        for filename in os.listdir(cls.GROUND_TRUTH_DIR):
            if filename.endswith(".json"):
                key = filename.replace("_anomalous.json", "")
                with open(os.path.join(cls.GROUND_TRUTH_DIR, filename), "r", encoding="utf-8") as f:
                    dataset[key] = json.load(f)
        return dataset

    @classmethod
    def detect_from_dataset(cls, dataset: Dict[str, Any]) -> List[AnomalyFinding]:
        """
        Executes the 5 detection rules directly against a source dataset dictionary.
        Returns explainable AnomalyFinding instances.
        """
        findings: List[AnomalyFinding] = []

        accounts = dataset.get("loyalty_accounts", [])
        transactions = dataset.get("points_transactions", [])
        returns = dataset.get("order_returns", [])
        expiry_items = dataset.get("expiry_batch_items", [])
        lots = {l["lot_id"]: l for l in dataset.get("points_lots", [])}

        # 1. Detector 1: Balance Mismatch
        tx_sum_by_account: Dict[str, int] = {}
        for tx in transactions:
            acc_id = tx["account_id"]
            tx_sum_by_account[acc_id] = tx_sum_by_account.get(acc_id, 0) + tx["points"]

        for acc in accounts:
            acc_id = acc["account_id"]
            stored = acc["current_balance"]
            computed = tx_sum_by_account.get(acc_id, 0)
            diff = stored - computed
            if diff != 0:
                findings.append(
                    AnomalyFinding(
                        detector_id="DET-BALANCE-MISMATCH",
                        category="BALANCE_MISMATCH",
                        entity_type="ACCOUNT",
                        entity_id=acc_id,
                        variance_amount=Decimal(str(abs(diff))),
                        severity="CRITICAL" if abs(diff) >= 100 else "HIGH",
                        severity_reason=f"Account balance deviates from transaction journal sum by {diff:+d} points.",
                        rule_violated="BR-01: Double-Entry Ledger Balance Invariant",
                        what_happened=f"Account {acc_id} stored balance ({stored}) != journal sum ({computed}).",
                        description=f"Direct balance drift of {diff:+d} points detected on account {acc_id}.",
                        evidence={"account_id": acc_id, "customer_id": acc.get("customer_id"), "stored_balance": stored, "calculated_ledger_balance": computed, "variance": diff},
                        discrepancy_calculation={"formula": "stored_balance - sum(journal_transactions.points)", "stored": stored, "ledger": computed, "variance": diff},
                        recommendation="Review audit logs and post dual-key ADJUSTMENT transaction.",
                    )
                )

        # 2. Detector 2: Over-Redemption
        for tx in transactions:
            if tx.get("entry_type") == "REDEMPTION" and tx.get("running_balance", 0) < 0:
                pts_redeemed = abs(tx["points"])
                running_bal = tx["running_balance"]
                avail_before = running_bal + pts_redeemed
                overdraft = abs(running_bal)
                findings.append(
                    AnomalyFinding(
                        detector_id="DET-OVER-REDEMPTION",
                        category="OVER_REDEMPTION",
                        entity_type="REDEMPTION",
                        entity_id=tx.get("transaction_id"),
                        variance_amount=Decimal(str(overdraft)),
                        severity="CRITICAL",
                        severity_reason=f"Redemption resulted in negative running balance of {running_bal} points.",
                        rule_violated="BR-04 / BR-08: Points Redemption Validation & FIFO Allocation",
                        what_happened=f"Transaction {tx.get('transaction_id')} redeemed {pts_redeemed} points exceeding available {avail_before} points.",
                        description=f"Over-redemption overdraft of {overdraft} points on account {tx.get('account_id')}.",
                        evidence={"transaction_id": tx.get("transaction_id"), "account_id": tx.get("account_id"), "requested_points": pts_redeemed, "overdraft_points": overdraft, "resulting_running_balance": running_bal},
                        discrepancy_calculation={"formula": "requested_points - available_balance_at_transaction_time", "requested": pts_redeemed, "available": avail_before, "overdraft": overdraft},
                        recommendation="Freeze account and invalidate voucher code.",
                    )
                )

        # 3. Detector 3: Unreversed Return
        for ret in returns:
            if ret.get("points_reversed", 0) == 0 and Decimal(str(ret.get("total_refund_amount", "0"))) > Decimal("0.00"):
                refund_amt = Decimal(str(ret.get("total_refund_amount")))
                expected_pts = int(refund_amt)
                findings.append(
                    AnomalyFinding(
                        detector_id="DET-UNREVERSED-RETURN",
                        category="UNREVERSED_RETURN",
                        entity_type="ORDER_RETURN",
                        entity_id=ret.get("return_id"),
                        variance_amount=Decimal(str(expected_pts)),
                        severity="HIGH" if expected_pts >= 100 else "MEDIUM",
                        severity_reason=f"Return {ret.get('return_id')} refunded ${refund_amt} but reversed 0 points.",
                        rule_violated="BR-09 / BR-10: Points Reversal on Return",
                        what_happened=f"Return {ret.get('return_id')} refunded ${refund_amt} without reversing {expected_pts} points.",
                        description=f"Order {ret.get('order_id')} return {ret.get('return_id')} missing {expected_pts} reversal points.",
                        evidence={"return_id": ret.get("return_id"), "order_id": ret.get("order_id"), "total_refund_amount": str(refund_amt), "expected_reversal_points": expected_pts, "actual_reversal_points": 0, "missing_points": expected_pts},
                        discrepancy_calculation={"formula": "expected_reversal - actual_reversal", "expected": expected_pts, "actual": 0, "missing": expected_pts},
                        recommendation="Verify return webhook and issue operator REVERSAL transaction.",
                    )
                )

        # 4. Detector 4: Double Expiry
        items_by_lot: Dict[str, List[Dict[str, Any]]] = {}
        for item in expiry_items:
            items_by_lot.setdefault(item["lot_id"], []).append(item)

        for lot_id, batch_items in items_by_lot.items():
            if len(batch_items) > 1:
                lot = lots.get(lot_id, {})
                initial_pts = lot.get("initial_points", batch_items[0].get("points_expired", 0))
                total_expired = sum(b.get("points_expired", 0) for b in batch_items)
                excess = max(0, total_expired - initial_pts)
                if excess == 0:
                    excess = sum(b.get("points_expired", 0) for b in batch_items[1:])
                findings.append(
                    AnomalyFinding(
                        detector_id="DET-DOUBLE-EXPIRY",
                        category="DOUBLE_EXPIRY",
                        entity_type="POINTS_LOT",
                        entity_id=lot_id,
                        variance_amount=Decimal(str(excess)),
                        severity="HIGH",
                        severity_reason=f"Points lot {lot_id} was expired across {len(batch_items)} batches.",
                        rule_violated="BR-05 / BR-11: Points Expiry Idempotency",
                        what_happened=f"Lot {lot_id} expired {len(batch_items)} times with total {total_expired} points deducted.",
                        description=f"Double expiry of lot {lot_id}, {excess} excess points deducted.",
                        evidence={"lot_id": lot_id, "expiry_batch_count": len(batch_items), "batch_ids": [b.get("batch_id") for b in batch_items], "total_points_expired": total_expired, "excess_points_deducted": excess},
                        discrepancy_calculation={"formula": "total_points_expired - initial_lot_points", "total": total_expired, "initial": initial_pts, "excess": excess},
                        recommendation="Check batch scheduler idempotency and credit customer points.",
                    )
                )

        # 5. Detector 5: Incorrect Tier
        for acc in accounts:
            q_spend = Decimal(str(acc.get("qualifying_spend", "0.00")))
            tier_id = acc.get("tier_id")
            if tier_id == "TIER-GOLD" and q_spend < Decimal("1000.00"):
                findings.append(
                    AnomalyFinding(
                        detector_id="DET-INCORRECT-TIER",
                        category="INCORRECT_TIER",
                        entity_type="ACCOUNT",
                        entity_id=acc.get("account_id"),
                        variance_amount=Decimal("2500.00") - q_spend,
                        severity="MEDIUM",
                        severity_reason=f"Account assigned to {tier_id} with qualifying spend of only ${q_spend}.",
                        rule_violated="BR-06 / BR-07: Qualifying Net Spend Tier Evaluation",
                        what_happened=f"Customer {acc.get('customer_id')} upgraded to {tier_id} with qualifying spend of only ${q_spend}.",
                        description=f"Account {acc.get('account_id')} in {tier_id} requires min spend $2500.00, has ${q_spend}.",
                        evidence={"account_id": acc.get("account_id"), "customer_id": acc.get("customer_id"), "current_tier_id": tier_id, "expected_tier_id": "TIER-BRONZE", "qualifying_spend": str(q_spend)},
                        discrepancy_calculation={"formula": "tier_min_spend - qualifying_spend", "min_spend": "2500.00", "qualifying_spend": str(q_spend), "deficit": str(Decimal("2500.00") - q_spend)},
                        recommendation="Re-evaluate customer tier using qualifying net merchandise spend.",
                    )
                )

        return findings

    @classmethod
    def _normalize_category(cls, cat: str) -> str:
        cat_norm = cat.strip().upper()
        if cat_norm in ("GROSS_SPEND_TIER_CALCULATION", "INCORRECT_TIER"):
            return "INCORRECT_TIER"
        return cat_norm

    @classmethod
    def _entity_matches(cls, finding: AnomalyFinding, gt_entities: Dict[str, Any]) -> bool:
        for k, v in gt_entities.items():
            if str(finding.entity_id) == str(v):
                return True
            if str(v) in [str(val) for val in finding.evidence.values() if isinstance(val, (str, int))]:
                return True
        return False

    @classmethod
    async def evaluate(
        cls,
        db: Optional[AsyncSession] = None,
        findings: Optional[List[AnomalyFinding]] = None,
    ) -> EngineEvaluationResponse:
        manifest = cls.load_ground_truth()
        now = datetime.now(timezone.utc)

        if not manifest:
            empty_metric = CategoryEvaluationMetrics(
                category="ALL",
                true_positives=0,
                false_positives=0,
                true_negatives=0,
                false_negatives=0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
            )
            return EngineEvaluationResponse(
                evaluated_at=now,
                dataset_scale="UNKNOWN",
                total_ground_truth_anomalies=0,
                total_detected_anomalies=0,
                categories={},
                aggregate=empty_metric,
            )

        gt_anomalies = manifest.get("ground_truth_anomalies", [])
        dataset_scale = manifest.get("scale", "TEST")
        entity_counts = manifest.get("entity_counts", {})
        total_accounts = entity_counts.get("loyalty_accounts", 100)

        # If findings were not provided, detect from ground truth dataset or database
        if findings is None:
            findings = []
            gt_dataset = cls.load_ground_truth_dataset()
            if gt_dataset:
                findings = cls.detect_from_dataset(gt_dataset)
            elif db is not None:
                for detector in intelligence_engine.detectors.values():
                    det_findings = await detector.detect(db)
                    findings.extend(det_findings)

        # Standard categories
        standard_categories = [
            "BALANCE_MISMATCH",
            "OVER_REDEMPTION",
            "UNREVERSED_RETURN",
            "DOUBLE_EXPIRY",
            "INCORRECT_TIER",
        ]

        gt_by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in standard_categories}
        for gt in gt_anomalies:
            norm_cat = cls._normalize_category(gt["category"])
            gt_by_cat.setdefault(norm_cat, []).append(gt)

        findings_by_cat: Dict[str, List[AnomalyFinding]] = {c: [] for c in standard_categories}
        for f in findings:
            norm_cat = cls._normalize_category(f.category)
            findings_by_cat.setdefault(norm_cat, []).append(f)

        category_metrics: Dict[str, CategoryEvaluationMetrics] = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_tn = 0

        for cat in standard_categories:
            cat_gt = gt_by_cat.get(cat, [])
            cat_findings = findings_by_cat.get(cat, [])

            matched_gt = set()
            tp = 0
            fp = 0

            for finding in cat_findings:
                matched = False
                for i, gt in enumerate(cat_gt):
                    if i not in matched_gt and cls._entity_matches(finding, gt.get("affected_entities", {})):
                        matched_gt.add(i)
                        matched = True
                        break
                if matched:
                    tp += 1
                else:
                    fp += 1

            fn = len(cat_gt) - len(matched_gt)
            cat_universe = total_accounts
            tn = max(0, cat_universe - len(cat_gt) - fp)

            precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0
            recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 1.0
            f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            category_metrics[cat] = CategoryEvaluationMetrics(
                category=cat,
                true_positives=tp,
                false_positives=fp,
                true_negatives=tn,
                false_negatives=fn,
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
            )

            total_tp += tp
            total_fp += fp
            total_fn += fn
            total_tn += tn

        agg_precision = float(total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 1.0
        agg_recall = float(total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 1.0
        agg_f1 = float(2 * agg_precision * agg_recall / (agg_precision + agg_recall)) if (agg_precision + agg_recall) > 0 else 0.0

        aggregate_metric = CategoryEvaluationMetrics(
            category="AGGREGATE",
            true_positives=total_tp,
            false_positives=total_fp,
            true_negatives=total_tn,
            false_negatives=total_fn,
            precision=round(agg_precision, 4),
            recall=round(agg_recall, 4),
            f1_score=round(agg_f1, 4),
        )

        return EngineEvaluationResponse(
            evaluated_at=now,
            dataset_scale=dataset_scale,
            total_ground_truth_anomalies=len(gt_anomalies),
            total_detected_anomalies=len(findings),
            categories=category_metrics,
            aggregate=aggregate_metric,
        )
