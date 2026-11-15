# LoyaltyOS — Testing & Evaluation Guide

**Repository:** https://github.com/dandetejaswini/LoyaltyOS  
**Architecture:** Pure Supabase (PostgreSQL 15+, RPC, RLS) + React 18 / Vite Frontend  
**Offline Test Suite:** Pytest 9.2 (85 / 85 Passing — 100%)  
**Frontend Compilation:** TypeScript + Vite Build (0 Errors)  
**LLIRE Benchmark Accuracy:** 100.0% Precision | 100.0% Recall | 100.0% F1 Score  

---

## 1. Automated Test Suite Summary

The automated offline test suite verifies mathematical invariants, financial reconciliation, schema integrity, and dual-key governance rules:

| # | Test Suite File | Tests | Primary Scope | Status | Execution Time |
| :-: | :--- | :-: | :--- | :-: | :-: |
| 1 | `backend/tests/test_auth.py` | 22 | JWT token validation (HS256/RS256), signature verification, RBAC guards | **PASSED** | 0.45s |
| 2 | `backend/tests/test_intelligence.py` | 14 | LLIRE 5 anomaly detectors, severity rules, explainability, offline benchmark | **PASSED** | 1.10s |
| 3 | `backend/tests/test_remediation.py` | 15 | Dual-key approvals (`BR-09 proposer != approver`), safe ledger compensating actions | **PASSED** | 0.82s |
| 4 | `backend/tests/test_schema.py` | 9 | 21 relational tables, 5 database engine immutability triggers, Supabase RLS parity | **PASSED** | 0.25s |
| 5 | `backend/tests/test_seed.py` | 12 | Deterministic generation (PRNG seed), mathematical invariants, anomaly injection | **PASSED** | 0.35s |
| 6 | `backend/tests/test_workflows.py` | 13 | Core loyalty workflows A–G (floor rounding, FIFO depletion, negative returns) | **PASSED** | 0.21s |
| **Total** | **6 Test Files** | **85** | **Comprehensive Mathematical, Ledger & Security Verification** | **100%** | **3.18s** |

---

## 2. All 85 Automated Test Cases (Detailed Tables)

### 2.1 Authentication & Token Security (`test_auth.py` — 22 Tests)

| # | Test Case Name | Mathematical / Security Verification | Result |
| :-: | :--- | :--- | :-: |
| 1 | `test_decode_empty_token` | Rejects empty JWT strings with `UnauthorizedError` | Passed |
| 2 | `test_decode_malformed_token` | Rejects non-base64 or malformed JWT structures | Passed |
| 3 | `test_token_with_alg_none` | Strictly forbids `alg: none` unsigned tokens | Passed |
| 4 | `test_token_missing_subject` | Rejects tokens lacking the mandatory `sub` identity claim | Passed |
| 5 | `test_supabase_token_unverified_strictly_prohibited` | Blocks unverified Supabase tokens without cryptographic signature | Passed |
| 6 | `test_supabase_token_invalid_signature` | Rejects tokens signed with mismatched HMAC secret | Passed |
| 7 | `test_supabase_token_expiration` | Rejects expired tokens past their `exp` timestamp | Passed |
| 8 | `test_supabase_token_valid` | Validates authentic HS256 signed Supabase tokens | Passed |
| 9 | `test_firebase_token_valid_with_mock_cert` | Validates RS256 Google Firebase tokens against public JWKS | Passed |
| 10 | `test_firebase_token_invalid_signature` | Rejects forged RS256 signatures from secondary key pairs | Passed |
| 11 | `test_firebase_token_expired` | Rejects expired Firebase tokens with clear error detail | Passed |
| 12 | `test_firebase_token_incorrect_audience` | Rejects Firebase tokens with mismatched audience (`aud`) | Passed |
| 13 | `test_firebase_token_incorrect_issuer` | Rejects Firebase tokens with invalid issuer URL (`iss`) | Passed |
| 14 | `test_firebase_token_service_unavailable` | Handles Google JWKS endpoint outages gracefully | Passed |
| 15 | `test_matching_email_does_not_automatically_merge_accounts` | Prevents account takeover attacks via unverified email collision | Passed |
| 16 | `test_explicit_account_linking_success` | Allows authenticated users to link verified external identities | Passed |
| 17 | `test_explicit_account_linking_duplicate_rejected` | Prevents linking an identity already bound to another customer | Passed |
| 18 | `test_account_linking_cannot_elevate_role` | Prohibits identity linking from elevating customer roles | Passed |
| 19 | `test_inactive_user_cannot_link_identities` | Suspended or inactive accounts cannot attach new credentials | Passed |
| 20 | `test_auth_service_role_determination` | User roles are determined from database identity tables | Passed |
| 21 | `test_rbac_require_role_authorized` | Authorizes callers with valid role memberships | Passed |
| 22 | `test_rbac_require_role_forbidden` | Rejects unauthorized roles with HTTP 403 Forbidden | Passed |

---

### 2.2 LLIRE Anomaly Intelligence & Benchmark (`test_intelligence.py` — 14 Tests)

| # | Test Case Name | Mathematical / Security Verification | Result |
| :-: | :--- | :--- | :-: |
| 23 | `test_balance_mismatch_detected` | Flags ledger drift where stored balance diverges from transaction sum | Passed |
| 24 | `test_valid_account_not_incorrectly_flagged` | Zero false positives on mathematically reconciled accounts | Passed |
| 25 | `test_over_redemption_detected` | Detects accounts where redeemed points exceed accrued points | Passed |
| 26 | `test_legitimate_return_negative_balance_not_misclassified` | Allows negative balances resulting from legitimate order returns | Passed |
| 27 | `test_missing_return_reversal_detected` | Flags merchandise returns lacking corresponding ledger reversal debits | Passed |
| 28 | `test_partial_return_reversal_calculation` | Computes proportional points reversal on partial returns | Passed |
| 29 | `test_duplicate_expiry_detected` | Catches points lots subjected to repeated expiration debits | Passed |
| 30 | `test_correct_single_expiry_not_flagged` | Confirms valid single expiry batches are not flagged | Passed |
| 31 | `test_incorrect_gross_spend_tier_detected` | Detects customers assigned tiers based on gross instead of net spend | Passed |
| 32 | `test_correct_qualifying_spend_tier_not_flagged` | Validates accurate tier qualification based on 365-day net spend | Passed |
| 33 | `test_severity_classification_rules` | Validates severity assignment (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) | Passed |
| 34 | `test_explainability_evidence_completeness` | Verifies all 7 explainability sections are present in finding payload | Passed |
| 35 | `test_repeated_detection_idempotency` | Idempotent detection runs avoid duplicate incident creation | Passed |
| 36 | `test_offline_ground_truth_benchmark_evaluation` | Evaluates all 5 detectors against ground truth (100% P, R, F1) | Passed |

---

### 2.3 Dual-Key Remediation & Safe Ledger (`test_remediation.py` — 15 Tests)

| # | Test Case Name | Mathematical / Security Verification | Result |
| :-: | :--- | :--- | :-: |
| 37 | `test_investigation_creation_and_status_transition` | Opens investigation cases and logs initial audit notes | Passed |
| 38 | `test_invalid_status_transition_on_resolved_incident` | Prevents modifying already resolved anomaly findings | Passed |
| 39 | `test_add_investigation_notes` | Appends timestamped audit notes to open investigations | Passed |
| 40 | `test_propose_corrective_action_credit` | Creates structured compensating transaction proposals | Passed |
| 41 | `test_propose_action_invalid_points` | Rejects proposals with non-positive or irrational point amounts | Passed |
| 42 | `test_self_approval_strictly_rejected` | **BR-09 Dual-Key:** Proposer self-approval is strictly forbidden | Passed |
| 43 | `test_unauthorized_role_approval_rejected` | Only OPERATIONS_MANAGER role can review proposals | Passed |
| 44 | `test_rejection_requires_mandatory_reason` | Rejecting a proposal requires a non-empty explanation | Passed |
| 45 | `test_rejected_action_creates_no_ledger_transaction` | Rejected proposals create zero ledger transactions | Passed |
| 46 | `test_second_person_approval_and_idempotency` | Independent second manager approval succeeds idempotently | Passed |
| 47 | `test_approved_credit_adjustment_and_reconciliation_success` | Posts compensating journal credit and reconciles balance | Passed |
| 48 | `test_approved_debit_adjustment` | Posts compensating journal debit and updates lots | Passed |
| 49 | `test_finding_remains_open_when_reconciliation_fails` | Prevents closing incidents if ledger remains unreconciled | Passed |
| 50 | `test_duplicate_execution_prevented` | Prevents double-execution of approved compensating actions | Passed |
| 51 | `test_account_freeze_and_unfreeze_actions` | Supports account lock/unlock operations during fraud audits | Passed |

---

### 2.4 Database Schema, Triggers & RLS Parity (`test_schema.py` — 9 Tests)

| # | Test Case Name | Mathematical / Security Verification | Result |
| :-: | :--- | :--- | :-: |
| 52 | `test_schema_model_registration` | Verifies all 21 core domain tables are defined in database metadata | Passed |
| 53 | `test_points_transactions_constraints` | Validates append-only journal schema, types, and primary/foreign keys | Passed |
| 54 | `test_points_lots_constraints` | Validates FIFO points lot constraints (`points_remaining <= points_accrued`) | Passed |
| 55 | `test_identity_mappings_constraints` | Validates multi-identity provider mappings and foreign keys | Passed |
| 56 | `test_audit_events_constraints` | Validates append-only audit event schema and metadata constraints | Passed |
| 57 | `test_points_lot_allocations_constraints` | Validates lot redemption allocation linkages | Passed |
| 58 | `test_expiry_batch_items_constraints` | Validates lot expiration batch item relationships | Passed |
| 59 | `test_immutability_triggers_parity_between_ddl_and_supabase` | Verifies all 5 database engine triggers exist in Supabase migrations | Passed |
| 60 | `test_rls_policies_parity_between_ddl_and_supabase` | Verifies Row-Level Security enablement and customer isolation policies | Passed |

---

### 2.5 Synthetic Seed Engine & Determinism (`test_seed.py` — 12 Tests)

| # | Test Case Name | Mathematical / Security Verification | Result |
| :-: | :--- | :--- | :-: |
| 61 | `test_identical_seed_produces_identical_dataset` | PRNG seed determinism: identical seed produces bitwise identical data | Passed |
| 62 | `test_different_seed_produces_different_dataset` | Distinct seeds generate distinct customer profiles and orders | Passed |
| 63 | `test_zero_validation_errors` | Baseline generated dataset contains zero math or relation errors | Passed |
| 64 | `test_double_entry_balance_reconciliation` | Reconciles stored balance to journal sum for 100% of generated accounts | Passed |
| 65 | `test_running_balance_continuity` | Verifies running balance continuity across chronological transactions | Passed |
| 66 | `test_floor_rounding_on_accruals` | Enforces mathematical floor rounding on all order accrual points | Passed |
| 67 | `test_points_lot_fifo_exhaustion` | Verifies FIFO consumption order (`expires_at ASC`) across redemptions | Passed |
| 68 | `test_all_five_categories_present` | Ground-truth dataset injects all 5 controlled anomaly categories | Passed |
| 69 | `test_anomalies_detected_by_auditor` | Confirms injected anomalies are detectable by verification audits | Passed |
| 70 | `test_baseline_dataset_unmodified_by_injection` | Controlled injection preserves clean baseline dataset integrity | Passed |
| 71 | `test_manifest_structure_and_roundtrip` | Generates valid JSON manifests with SHA-256 integrity checksums | Passed |
| 72 | `test_cli_pipeline_run` | Verifies end-to-end execution of `tools/seed_generator.py` CLI | Passed |

---

### 2.6 Core Loyalty Workflows A–G (`test_workflows.py` — 13 Tests)

| # | Test Case Name | Mathematical / Security Verification | Result |
| :-: | :--- | :--- | :-: |
| 73 | `test_provision_new_customer_and_account` | Atomically provisions customer, user, and loyalty account in Bronze | Passed |
| 74 | `test_provision_existing_customer_idempotent` | Re-provisioning existing customer returns account without duplicate records | Passed |
| 75 | `test_order_accrual_qualifying_spend_and_floor_rounding` | Accrues points on net spend only: `floor(Net Spend × Multiplier)` | Passed |
| 76 | `test_order_accrual_duplicate_idempotency_rejected` | Rejects duplicate order accrual submissions via idempotency keys | Passed |
| 77 | `test_reconciliation_detects_clean_reconciled_state` | Reports clean status when stored balance equals journal sum | Passed |
| 78 | `test_reconciliation_detects_drift_without_silent_corruption` | Detects intentional ledger drift without silent state mutation | Passed |
| 79 | `test_redemption_fifo_lot_allocation_success` | Allocates points from oldest active lots and deducts balance | Passed |
| 80 | `test_redemption_rejected_when_balance_insufficient` | Rejects redemptions exceeding available customer points balance | Passed |
| 81 | `test_redemption_frozen_when_balance_negative` | Blocks redemptions when customer balance is in negative status | Passed |
| 82 | `test_partial_order_return_reverses_points_and_caps_at_accrual` | Reverses proportional points and caps reversal at original accrual | Passed |
| 83 | `test_return_after_redemption_supports_negative_balance` | Allows account balance to safely go negative following return | Passed |
| 84 | `test_expiry_batch_idempotent_and_updates_status` | Idempotent expiration batch marks lots `EXPIRED` and writes journal debit | Passed |
| 85 | `test_tier_upgrade_on_qualifying_spend_threshold` | Upgrades tier dynamically when rolling spend exceeds thresholds | Passed |

---

## 3. LLIRE Benchmark Evaluation Results

The offline benchmark evaluation tool (`tools/benchmark_evaluator.py`) executes against the labelled ground-truth dataset (`data/ground_truth/`) and manifest (`data/manifests/ground_truth_manifest.json`):

| Anomaly Detector ID | Category Name | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1 Score |
| :--- | :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| `DET-BALANCE-MISMATCH` | `BALANCE_MISMATCH` | 1 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** |
| `DET-OVER-REDEMPTION` | `OVER_REDEMPTION` | 1 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** |
| `DET-UNREVERSED-RETURN` | `UNREVERSED_RETURN` | 1 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** |
| `DET-DOUBLE-EXPIRY` | `DOUBLE_EXPIRY` | 1 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** |
| `DET-INCORRECT-TIER` | `INCORRECT_TIER` | 1 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** |
| **OVERALL AGGREGATE** | **ALL CATEGORIES** | **5** | **0** | **0** | **100.0%** | **100.0%** | **100.0%** |
