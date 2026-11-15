"""
LoyaltyOS — Synthetic Data Engine Configuration
Seed and scaling constants for deterministic synthetic data generation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Any


DEFAULT_SEED = 20261022


@dataclass(frozen=True)
class GeneratorScale:
    name: str
    num_customers: int
    num_orders: int
    target_transactions: int
    redemption_ratio: float = 0.08  # ~8% of orders trigger redemption
    return_ratio: float = 0.04      # ~4% of orders trigger returns
    expiry_ratio: float = 0.05      # ~5% of lots reach expiration
    anomaly_ratio: float = 0.01     # ~1% anomaly injection rate


# Pre-defined scale profiles
FULL_SCALE = GeneratorScale(
    name="FULL",
    num_customers=20000,
    num_orders=100000,
    target_transactions=300000,
    redemption_ratio=0.08,
    return_ratio=0.04,
    expiry_ratio=0.05,
    anomaly_ratio=0.01,
)

TEST_SCALE = GeneratorScale(
    name="TEST",
    num_customers=100,
    num_orders=500,
    target_transactions=1500,
    redemption_ratio=0.10,
    return_ratio=0.05,
    expiry_ratio=0.05,
    anomaly_ratio=0.02,
)

MEDIUM_SCALE = GeneratorScale(
    name="MEDIUM",
    num_customers=1000,
    num_orders=5000,
    target_transactions=15000,
    redemption_ratio=0.08,
    return_ratio=0.04,
    expiry_ratio=0.05,
    anomaly_ratio=0.01,
)


# Documented Tier Rules (BR-02 & BR-05)
TIERS_CONFIG = [
    {
        "tier_id": "TIER-BRONZE",
        "name": "Bronze",
        "rank": 1,
        "min_spend": Decimal("0.00"),
        "multiplier": Decimal("1.00"),
    },
    {
        "tier_id": "TIER-SILVER",
        "name": "Silver",
        "rank": 2,
        "min_spend": Decimal("500.00"),
        "multiplier": Decimal("1.25"),
    },
    {
        "tier_id": "TIER-GOLD",
        "name": "Gold",
        "rank": 3,
        "min_spend": Decimal("1000.00"),
        "multiplier": Decimal("1.50"),
    },
    {
        "tier_id": "TIER-PLATINUM",
        "name": "Platinum",
        "rank": 4,
        "min_spend": Decimal("2500.00"),
        "multiplier": Decimal("2.00"),
    },
]


# Realistic Product Catalog for Order Lines
PRODUCT_CATALOG: List[Dict[str, Any]] = [
    {"sku": "SKU-TECH-001", "name": "Wireless Noise-Cancelling Headphones", "category": "Electronics", "price": Decimal("149.99"), "is_eligible": True},
    {"sku": "SKU-TECH-002", "name": "Ultra-Slim USB-C Power Bank 20000mAh", "category": "Electronics", "price": Decimal("49.50"), "is_eligible": True},
    {"sku": "SKU-TECH-003", "name": "Mechanical Keyboard RGB", "category": "Electronics", "price": Decimal("89.99"), "is_eligible": True},
    {"sku": "SKU-TECH-004", "name": "4K Ultra-HD Webcam with Microphone", "category": "Electronics", "price": Decimal("79.00"), "is_eligible": True},
    {"sku": "SKU-APP-001", "name": "Merino Wool Thermal Sweater", "category": "Apparel", "price": Decimal("65.00"), "is_eligible": True},
    {"sku": "SKU-APP-002", "name": "Waterproof Trail Running Shoes", "category": "Apparel", "price": Decimal("120.00"), "is_eligible": True},
    {"sku": "SKU-APP-003", "name": "Breathable Performance Jacket", "category": "Apparel", "price": Decimal("95.00"), "is_eligible": True},
    {"sku": "SKU-HOME-001", "name": "Double-Wall Insulated Travel Tumbler", "category": "Home", "price": Decimal("28.00"), "is_eligible": True},
    {"sku": "SKU-HOME-002", "name": "Ergonomic Memory Foam Lumbar Cushion", "category": "Home", "price": Decimal("35.00"), "is_eligible": True},
    {"sku": "SKU-HOME-003", "name": "Cold Brew Coffee Maker 1.5L", "category": "Home", "price": Decimal("42.00"), "is_eligible": True},
    # Ineligible Items (BR-01 Policy: Gift cards, vouchers, deposits do NOT earn points)
    {"sku": "SKU-GIFT-025", "name": "LoyaltyOS Store e-Gift Card $25", "category": "Gift Cards", "price": Decimal("25.00"), "is_eligible": False},
    {"sku": "SKU-GIFT-050", "name": "LoyaltyOS Store e-Gift Card $50", "category": "Gift Cards", "price": Decimal("50.00"), "is_eligible": False},
    {"sku": "SKU-GIFT-100", "name": "LoyaltyOS Store e-Gift Card $100", "category": "Gift Cards", "price": Decimal("100.00"), "is_eligible": False},
]


# Rewards Catalog for Redemptions
REWARDS_CATALOG: List[Dict[str, Any]] = [
    {"reward_id": "REW-VOUCH-05", "name": "$5 Off Any Purchase", "points_required": 500, "monetary_value": Decimal("5.00")},
    {"reward_id": "REW-VOUCH-10", "name": "$10 Off Any Purchase", "points_required": 950, "monetary_value": Decimal("10.00")},
    {"reward_id": "REW-VOUCH-25", "name": "$25 Off Any Purchase", "points_required": 2200, "monetary_value": Decimal("25.00")},
    {"reward_id": "REW-VOUCH-50", "name": "$50 Off Any Purchase", "points_required": 4000, "monetary_value": Decimal("50.00")},
]
