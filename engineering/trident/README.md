# TRIDENT commerce snapshot audit

Read-only standard-library diagnostic for the approved Omega House $40 and $60 BFCM bundle contracts. It reads captured Shopify JSON and emits explicit blockers; it never calls providers, publishes, changes prices, installs plugins or approves rights.

Run `python engineering/trident/tools/commerce_gate.py <snapshot.json>` from the repository root. Add `--require-qualified` to return exit 2 when blocked. Invalid input returns 1; ordinary report generation returns 0. Test with `python -m unittest discover -s engineering/trident/tests -v`.

Input: products, themes and files lists, plus optional product-bound structured evidence in verified_delivery. Product nodes from Shopify search and get-product are supported. Keep snapshots outside source control. Evidence hashes and references are structurally checked, not authenticated or read from disk by this tool. Its qualified_from_supplied_evidence flag is a diagnostic, not release approval or a trusted authorization gate.

The auditor enforces Decimal/USD approved pricing, asset/SKU presence, component manifests, delivery/license/checkout observations and six plugin gates when ADLIB93 is a binary. MAIN theme protection follows the API role. Zero inventory alone does not prove sold out. Filename key differences are metadata conflicts, not audio analysis.

Development acceptance: 18 tests cover malformed input, currency, evidence shape, bundle identity, missing fulfillment, MAIN-theme safety and exact Detroit preview label conflicts. Native Windows results must be retained separately. This module does not integrate Pack Forge into Shopify; live delivery and checkout require distinct evidence and approvals.
