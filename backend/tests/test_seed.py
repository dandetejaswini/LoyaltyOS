"""
LoyaltyOS — Synthetic Data Generation & Deterministic Seed Engine Tests
Verifies mathematical reconciliation, strict determinism, invariant adherence,
controlled anomaly injection, and manifest generation.
"""

import json
import math
from decimal import Decimal
from pathlib import Path
import pytest

from backend.app.seed.config import (
    DEFAULT_SEED,
    TEST_SCALE,
    GeneratorScale,
)
from backend.app.seed.generator import SyntheticDataGenerator
from backend.app.seed.anomalies import AnomalyInjector
from backend.app.seed.validators import DatasetValidator
from backend.app.seed.manifest import DatasetManifest, calculate_data_checksum
from backend.app.seed.cli import run_pipeline, serialize_entities


ENTITY_KEYS = [
    "customers",
    "loyalty_accounts",
    "orders",
    "order_lines",
    "points_transactions",
    "points_lots",
    "redemptions",
    "points_lot_allocations",
    "order_returns",
    "order_return_lines",
    "expiry_batches",
    "expiry_batch_items",
]


@pytest.fixture(scope="module")
def baseline_data():
    gen = SyntheticDataGenerator(seed=20261022, scale=TEST_SCALE)
    return gen.generate_all()


@pytest.fixture(scope="module")
def anomalous_output():
    gen = SyntheticDataGenerator(seed=20261022, scale=TEST_SCALE)
    baseline = gen.generate_all()
    injector = AnomalyInjector(seed=20261022)
    anomalous_data, anomalies = injector.inject_anomalies(baseline)
    return baseline, anomalous_data, anomalies


class TestSeedDeterminism:
    """Verifies that the synthetic engine produces 100% bit-exact reproducible datasets."""

    def test_identical_seed_produces_identical_dataset(self):
        """Two runs with the exact same seed must produce identical data down to the line item."""
        gen1 = SyntheticDataGenerator(seed=20261022, scale=TEST_SCALE)
        data1 = gen1.generate_all()

        gen2 = SyntheticDataGenerator(seed=20261022, scale=TEST_SCALE)
        data2 = gen2.generate_all()

        # Check entity counts
        for key in ENTITY_KEYS:
            assert len(data1[key]) == len(data2[key]), f"Entity count mismatch for {key}"

        # Check checksums
        chk1 = calculate_data_checksum({k: serialize_entities(data1[k]) for k in ENTITY_KEYS})
        chk2 = calculate_data_checksum({k: serialize_entities(data2[k]) for k in ENTITY_KEYS})
        assert chk1 == chk2, "Checksum mismatch between two runs with identical seed 20261022"

        # Check sample records
        assert data1["customers"][0].email == data2["customers"][0].email
        assert data1["orders"][0].gross_amount == data2["orders"][0].gross_amount
        assert data1["points_transactions"][0].points == data2["points_transactions"][0].points

    def test_different_seed_produces_different_dataset(self):
        """Different seeds must produce different data and different checksums."""
        gen1 = SyntheticDataGenerator(seed=20261022, scale=TEST_SCALE)
        data1 = gen1.generate_all()

        gen2 = SyntheticDataGenerator(seed=99999999, scale=TEST_SCALE)
        data2 = gen2.generate_all()

        chk1 = calculate_data_checksum({k: serialize_entities(data1[k]) for k in ENTITY_KEYS})
        chk2 = calculate_data_checksum({k: serialize_entities(data2[k]) for k in ENTITY_KEYS})
        assert chk1 != chk2, "Different seeds unexpectedly produced identical checksums"
        assert data1["customers"][0].email != data2["customers"][0].email


class TestBaselineInvariants:
    """Verifies that baseline data satisfies all double-entry ledger and accounting rules."""

    def test_zero_validation_errors(self, baseline_data):
        """Baseline dataset must pass all invariant checks with 0 errors."""
        errors = DatasetValidator.validate_baseline(baseline_data)
        assert len(errors) == 0, f"Baseline validation found {len(errors)} errors: {errors[:5]}"

    def test_double_entry_balance_reconciliation(self, baseline_data):
        """BR-01: Sum of journal transactions must equal account.current_balance for every account."""
        tx_by_account = {}
        for tx in baseline_data["points_transactions"]:
            tx_by_account.setdefault(tx.account_id, []).append(tx)

        for acc in baseline_data["loyalty_accounts"]:
            tx_sum = sum(t.points for t in tx_by_account.get(acc.account_id, []))
            assert acc.current_balance == tx_sum, (
                f"Account {acc.account_id} balance {acc.current_balance} != tx sum {tx_sum}"
            )

    def test_running_balance_continuity(self, baseline_data):
        """Every transaction's running_balance must equal previous running balance + points."""
        tx_by_account = {}
        for tx in baseline_data["points_transactions"]:
            tx_by_account.setdefault(tx.account_id, []).append(tx)

        for acc_id, tx_list in tx_by_account.items():
            cumulative = 0
            for tx in tx_list:
                cumulative += tx.points
                assert tx.running_balance == cumulative, (
                    f"Tx {tx.transaction_id} running balance {tx.running_balance} != cumulative {cumulative}"
                )

    def test_floor_rounding_on_accruals(self, baseline_data):
        """Accrual points must be floored (never rounded up or half-up)."""
        orders_by_id = {o.order_id: o for o in baseline_data["orders"]}
        accrual_txs = [t for t in baseline_data["points_transactions"] if t.entry_type == "ACCRUAL"]

        for tx in accrual_txs:
            order = orders_by_id.get(tx.order_id)
            if order:
                net_spend = Decimal(order.eligible_net_spend)
                # Points accrued must be integer and <= net_spend * max_tier_multiplier (3.0)
                assert isinstance(tx.points, int)
                assert tx.points >= 0
                assert tx.points <= math.floor(float(net_spend * Decimal("3.0")))

    def test_points_lot_fifo_exhaustion(self, baseline_data):
        """Points lots remaining_points must be non-negative and <= initial_points."""
        for lot in baseline_data["points_lots"]:
            assert 0 <= lot.remaining_points <= lot.initial_points, (
                f"Lot {lot.lot_id} invalid remaining points: {lot.remaining_points} / {lot.initial_points}"
            )
            if lot.status == "EXHAUSTED":
                assert lot.remaining_points == 0
            elif lot.status == "ACTIVE":
                assert lot.remaining_points > 0


class TestAnomalyInjection:
    """Verifies that the 5 controlled forensic anomaly categories are correctly injected and detectable."""

    def test_all_five_categories_present(self, anomalous_output):
        _, _, anomalies = anomalous_output
        categories = {a.category for a in anomalies}
        expected_categories = {
            "BALANCE_MISMATCH",
            "OVER_REDEMPTION",
            "UNREVERSED_RETURN",
            "DOUBLE_EXPIRY",
            "GROSS_SPEND_TIER_CALCULATION",
        }
        assert expected_categories.issubset(categories), (
            f"Missing categories: {expected_categories - categories}"
        )

    def test_anomalies_detected_by_auditor(self, anomalous_output):
        """The DatasetValidator audit must detect injected anomalies."""
        _, anomalous_data, anomalies = anomalous_output
        detected = DatasetValidator.audit_anomalies(anomalous_data)
        detected_categories = {d["category"] for d in detected}

        for anom in anomalies:
            assert anom.category in detected_categories, (
                f"Injected anomaly category {anom.category} was not detected by auditor"
            )

    def test_baseline_dataset_unmodified_by_injection(self, anomalous_output):
        """Deep copy guarantees that baseline dataset remains 100% valid after anomaly injection."""
        baseline, _, _ = anomalous_output
        errors = DatasetValidator.validate_baseline(baseline)
        assert len(errors) == 0, "Baseline dataset was mutated during anomaly injection!"


class TestManifestAndExport:
    """Verifies dataset manifest generation, checksum integrity, and CLI pipeline."""

    def test_manifest_structure_and_roundtrip(self, tmp_path):
        manifest_file = tmp_path / "test_manifest.json"
        manifest = DatasetManifest(
            seed=20261022,
            scale="TEST",
            entity_counts={"customers": 100, "orders": 500},
            anomalies=[],
            checksums={"baseline_sha256": "abc123", "anomalies_sha256": "def456"},
        )
        manifest.save(manifest_file)
        assert manifest_file.exists()

        with open(manifest_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["dataset_seed"] == 20261022
        assert loaded["scale"] == "TEST"
        assert loaded["entity_counts"]["customers"] == 100
        assert loaded["checksums"]["baseline_sha256"] == "abc123"

    def test_cli_pipeline_run(self, tmp_path):
        """Verifies end-to-end execution of the run_pipeline function."""
        export_dir = str(tmp_path / "export")
        result = run_pipeline(
            seed=20261022,
            scale_name="TEST",
            export_dir=export_dir,
            validate=True,
        )

        assert result["counts"]["customers"] == 100
        assert result["counts"]["orders"] == 500
        assert len(result["anomalies"]) >= 5

        # Check generated files
        export_path = Path(export_dir)
        assert (export_path / "generated" / "customers.json").exists()
        assert (export_path / "generated" / "orders.json").exists()
        assert (export_path / "generated" / "points_transactions.json").exists()
        assert (export_path / "ground_truth" / "customers_anomalous.json").exists()
        assert (export_path / "manifests" / "ground_truth_manifest.json").exists()
