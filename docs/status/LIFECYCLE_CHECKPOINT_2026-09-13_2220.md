---
document_id: SAV3-STATUS-LIFECYCLE-2026-09-13-2220
knowledge_class: status
observed_at: 2026-09-13T22:20:00-05:00
commit_scope: main@e29a3df8a7369d45b62b3fb7411523de87c4f070
lifecycle: current
claim_state: SUPPORTED
evidence_refs:
  - ClickFunnels connected workspace inspection 2026-09-13
  - ChatGPT Ads Manager onboarding inspection 2026-09-13
  - Shopify SKU OHB-FPS-001 live product inspection 2026-09-13
  - GitHub recent commit and PR inspection 2026-09-13
  - Daniel lifecycle checkpoint report 2026-09-13 22:20 CDT
---

# Omega House Lifecycle Checkpoint — 2026-09-13 22:20 CDT

## Purpose

Reconcile the evening operator report with connected-system evidence and preserve only state changes that materially affect revenue operations, Sonic engineering, or lifecycle cleanup.

## VERIFIED — connected systems

### ClickFunnels

- One connected workspace is available: **OMEGA HOUSE STUDIO LLC|ONE FUNNEL AWAY**.
- The controlled acquisition documentation on `main` now promotes ClickFunnels as the primary $5 Starter acquisition control.
- The canonical control route remains `mvp.omega-house.online/flagship-entry-offer`.

### Ads Manager

- Accessible ad account: **Omega house studio LLC**.
- Account state: active.
- Review state: approved.
- Account logo: present.
- Billing setup: **required**.
- Ads cannot serve until billing, tax, and payment setup are complete.
- Step-up identity/persona verification may still be required when prompted.
- Current recommended action is to continue campaign, ad group, and ad setup after or alongside onboarding completion, but serving remains blocked by billing setup.

### Shopify — Flagship Producer Starter

- SKU `OHB-FPS-001` remains ACTIVE at **$5.00**.
- Variant remains **Basic License**.
- Current inventory: 495.
- Live featured media still points to `FLAGSHIP_BEATS_PACKAGING_BETA.png`.
- Shopify reports the product was last updated on 2026-09-09.
- Therefore the newly created Flagship variant visual is **not yet evidenced as live on the Shopify product**.

### Sonic repository

The canonical repository received four commerce-documentation commits at approximately 19:26 CDT:

1. acquisition evidence contract;
2. Starter controlled acquisition experiment;
3. ClickFunnels promoted as Starter acquisition control;
4. experiment indexed in the status README.

Latest observed `main` commit at this checkpoint: `e29a3df` — **docs: index Starter acquisition experiment**.

Open legacy/draft PR cleanup remains outstanding and should be handled deliberately rather than by bulk deletion.

## USER-VERIFIED / LOCAL RUNTIME

Daniel reports the following completed state changes:

- watched the ClickFunnels setup video;
- configured the ClickFunnels workspace name and image;
- verified `mcp.omega-house.online` is active;
- removed the stale Facebook phone number;
- activated Sonic locally;
- Codex is running with no MCP errors currently observed;
- created a new Flagship product-variant visual.

These are accepted as operator-verified checkpoint evidence. They are not all independently reproducible from the GitHub/Shopify surfaces inspected in this checkpoint.

## RECONCILIATION

### Completed

- ClickFunnels workspace identity configured.
- Sonic local runtime restored sufficiently for Codex operation without the previously observed MCP startup error.
- Stale Facebook contact data removed.
- Flagship visual asset created.
- Acquisition control/evidence model committed to the Sonic repository.

### Still open

- Finish Ads Manager billing, tax, and payment onboarding.
- Complete any required step-up verification presented by Ads Manager.
- Create/configure the first controlled campaign, ad group, and ad against the documented acquisition experiment.
- Upload/assign the newly created Flagship visual to the intended Shopify product/media position and verify storefront rendering.
- Capture reproducible Sonic runtime evidence after the restored local session: API health, MCP handshake, and clean/understood `git status`.
- Reconcile stale Sonic branches and open draft PRs in a separate controlled cleanup pass.

## Highest-leverage next action

Finish Ads Manager onboarding to the point where campaign infrastructure can be created and the only remaining serving gate is an intentional launch decision.

Do not increase spend until the ClickFunnels -> Shopify attribution chain records a genuine non-test event under the documented campaign/creative identifiers.

## Next checkpoint focus

Confirm whether Ads Manager onboarding is complete, whether the campaign skeleton exists, whether the new Flagship visual is live in Shopify, and whether Sonic still starts cleanly without MCP errors.
