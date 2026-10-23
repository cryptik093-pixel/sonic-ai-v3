# Session Transaction Controller V1

Status: implemented as **read-only planning**. No actual DAW control, rendering or commit is performed.

The controller verifies all selected local project and asset bytes against the durable ledger, checks the expected revision and SHA-256 state hash, and only then issues a deterministic proposal with a SHA-256 fingerprint. Supported plan actions are `analyze_audio`, `render_candidate_offline`, and `propose_midi`. These names are intent labels; they do not execute those operations.

## API (internal Python)

```python
from apps.api.session_integrity import IntegrityLedger
from apps.api.session_transactions import SessionTransactionController

ledger = IntegrityLedger()
current = ledger.get(session_id)
controller = SessionTransactionController(ledger, workspace_root)
proposal = controller.plan(
    session_id, current["revision"], current["sha256"],
    "analyze_audio", {"window_ms": 20}
)
```

## Non-negotiable safety boundaries

- `plan` does not change the DAW, original files, or ledger state.
- Host/plugin/mixer/automation recovery remains **unverified** and disabled.
- A plan is **not a lease**. Revalidate manifest and files immediately before any future execution; a successful proposal alone cannot authorize execution.
- All referenced source files must be inside the approved local directory, existing, of allowed type, with matching SHA-256 and length.
- Reject stale revisions, modified or missing assets, bad hashes, unsupported operations, and non-finite or excessively large parameters.
- For irreversible or live operations, require explicit approval and validated host-native rollback first.
- This module cannot guarantee atomic filesystem snapshots of actively edited files. Only use saved, stable project copies for acceptance testing.

## Windows verification

Run `python -m unittest apps.api.test_session_transactions apps.api.test_session_integrity apps.api.test_fl_studio_integrity apps.api.test_fl_studio_probe_import -v`.

Tested on Windows with Python 3.14 against an isolated worktree: **22 tests passed**. Native FL Studio host state and VST state were not tested. The active `throw away project for testing.flp` and six captured WAV files remain out of the test harness and unmodified by these tests.

## Next stage

Introduce an execution adapter only when atomic output staging, revalidation immediately before commit, host snapshot capability, rollback evidence, permissions and user approval are demonstrated.
