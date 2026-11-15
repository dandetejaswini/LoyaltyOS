"""
LoyaltyOS — Ground-Truth Manifest Generator
Creates isolated, reproducible ground-truth anomaly manifests for forensic evaluation.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

from backend.app.seed.models import InjectedAnomaly


class DatasetManifest:
    """
    Encapsulates dataset metadata, entity counts, SHA-256 checksums,
    and ground-truth anomaly labels.
    """

    def __init__(
        self,
        seed: int,
        scale: str,
        entity_counts: Dict[str, int],
        anomalies: List[InjectedAnomaly],
        checksums: Dict[str, str],
        generator_version: str = "1.0.0",
    ):
        self.seed = seed
        self.scale = scale
        self.generator_version = generator_version
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.entity_counts = entity_counts
        self.anomalies = anomalies
        self.checksums = checksums

    def to_dict(self) -> Dict[str, Any]:
        category_counts: Dict[str, int] = {}
        for a in self.anomalies:
            category_counts[a.category] = category_counts.get(a.category, 0) + 1

        return {
            "dataset_seed": self.seed,
            "scale": self.scale,
            "generator_version": self.generator_version,
            "generated_at": self.generated_at,
            "entity_counts": self.entity_counts,
            "total_anomalies_injected": len(self.anomalies),
            "anomaly_counts_by_category": category_counts,
            "checksums": self.checksums,
            "ground_truth_anomalies": [a.to_dict() for a in self.anomalies],
        }

    def save(self, filepath: Path) -> Path:
        """Saves the manifest to the specified path."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self.to_dict(), indent=2)
        filepath.write_text(content, encoding="utf-8")
        return filepath


def calculate_data_checksum(data_dict: Dict[str, Any]) -> str:
    """Calculates deterministic SHA-256 hash of serialized dataset contents."""
    serialized = json.dumps(data_dict, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
