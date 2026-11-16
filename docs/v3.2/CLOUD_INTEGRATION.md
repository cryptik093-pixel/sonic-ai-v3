# Sonic AI V3.2 — legacy source integration

Observed November 16, 2026. This milestone integrates committed legacy modules into the existing canonical product. It does not replace the Windows working tree, certify its preservation job, or mark the full V3.2 upgrade complete.

## Source authority

| Source | Pinned commit | Decision |
| --- | --- | --- |
| Canonical main | `7d2a2b90d9ab730790aa28b3cfaf1b9faf797a43` | Retain desktop, workbench, API, MCP and current company documentation |
| `feature/forge-foundation-v1` | `17871f327173664fd3d1bce0e65688c9f1a41d21` | Merge authenticated ZIP review, approval, immutable exports, UI and tests |
| `engineering/session-evidence-bridge-20261021` | `9077eb4a038c6645abee6ad825ccb62d17afd63c` | Merge integrity ledger, saved-file fingerprints, scoped intelligence bridge and tests |
| Windows local development | Last report: `ebc308af17aea46ce17b19d45c79d26437720722` plus staged, unstaged and untracked work | Not fetched or merged: DESKTOP-GU8N23U is offline |

`recovery/runtime-baseline-integration` is already an ancestor of canonical main. The older `recovery/actual-project-state` contains superseded API/frontend copies, backup directories and database files; it was compared but not blanket-merged. No legacy database, credential, backup app or generated environment was copied into the runtime.

The Forge merge's README conflict was resolved by preserving current campaign/founder documentation and adding the Forge entry. Source histories are retained as merge parents. See [machine-readable source inventory](legacy_sources.json).

## Infrastructure delivered

- One FastAPI runtime serves the existing workbench plus Forge; Forge uses the existing local identity and run/event records.
- Integrity routes fail closed outside desktop mode as well as inside it. Missing token returns 503, missing/wrong credentials 401, and rejected host/origin 403.
- The integrity ledger follows the desktop data directory, with an explicit legacy-path override. No existing ledger is silently moved or replaced.
- The intelligence store closes SQLite connections deterministically, including on Windows.
- `scripts/verify_v32.py` clears inherited Sonic locations/credentials, disables dotenv loading and runs the foundation validator, all API/legacy tests and the desktop source HTTP smoke using disposable data. It stops on failure, retains logs and refuses to overwrite earlier evidence.
- `.github/workflows/sonic-v32.yml` runs the verifier on Linux and Windows and uploads evidence. Existing desktop packaging/browser checks remain independent.
- Browser acceptance now includes the merged Forge's upload → review → approve → ZIP/CSV download behavior and mobile overflow check.

## Verification observed locally

| Check | Result |
| --- | --- |
| Canonical pre-merge API suite | 103 passed |
| Forge + canonical API suite | 149 passed |
| Full integrated API/legacy suite | 175 passed after canonical package-import regression; deprecation warnings remain |
| Foundation validator | Passed |
| Desktop source launcher HTTP smoke | Passed: startup, bundled assets, generated MIDI parse, ZIP download, token rejection |
| Python compile / workbench JavaScript syntax / diff whitespace | Passed |
| Web production build with pnpm 10.28.1 and frozen lockfile | Passed: compilation, lint/type checks and static page generation |
| Browser execution | Blocked locally: bundled browser unavailable; download returned invalid ZIP; installed Chromium refused process-singleton socket creation |
| Windows installed runtime, preservation, native window, FL/VST3 | Not tested: workstation offline |

Remote CI outcomes must be checked for the published integration commit; local success is not a remote CI result. No provider, Shopify publication, message, paid tool or purchase is required by this verification.

## Reproduce the source checks

Use Python 3.12 and the repository requirements; Node 20 or newer is required for the foundation check. From the repository root:

```sh
python -m pip install -r apps/api/requirements.txt
python scripts/verify_v32.py --output artifacts/v3.2/verification.json
```

Use a different output filename for a later run. Passing `source_checks_passed` explicitly leaves `upgrade_complete` false. A source smoke's historical `packaged_http_boot` check label describes the shared HTTP routine, not proof that a packaged executable was built.

The web shell is built separately with the repository's pinned pnpm 10.28.1 and frozen lockfile. The existing desktop workflow owns Chromium interaction and native Windows packaging. Tests use synthetic fixtures; passing them does not validate customer assets or record a paid sale.

## Continue on DESKTOP-GU8N23U

1. Reconnect Desktop Commander and verify hostname and checkout identity. Do not restart or duplicate the existing preservation job based on this source milestone.
2. Inspect the terminal preservation/restore reports and independently verify file/Git/index/database recovery, links, exclusions and source drift. The last report showed an incomplete restore; that is not present-day certification.
3. Preserve the current staged/unstaged/untracked differences, including `docs/v3.2` and FL snapshot work. Do not reset, clean, checkout over or merge directly into that dirty checkout.
4. Fetch this integration into a separate worktree after preservation is certified. Compare the committed source pins and the current local work, especially `main.py`, auth, storage, intelligence, Forge and handoff documents. Reconcile path-by-path, retaining source and patch evidence.
5. Run the verifier against disposable storage, then test compatibility on independent restored database copies. Never aim destructive tests at the production databases.
6. Run the native desktop build/window checks and FL Studio save/reopen, audio, routing and VST3 state tests on working copies. A ledger restore does not restore DAW state.

The existing workstation phase gates remain authoritative for that checkout. This branch does not rewrite those gates or its uncommitted handoff files. Commercial relevance is pack review, metadata lineage and usable release drafts; live sales evidence and the first $500 target need authenticated order/settlement evidence in later work.

## Rollback

Revert the task's source integration commits in a clean branch after preserving newer work. Do not delete local data. Forge tables are additive and retained on rollback; older code will not display their records. Keep the explicit `SONIC_INTEGRITY_DB` override when using a legacy ledger in another directory. Source rollback and a verified database restore are separate operations.
