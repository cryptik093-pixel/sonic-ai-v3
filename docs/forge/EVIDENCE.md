# Forge integration evidence — 2026-10-18

Repository: `cryptik093-pixel/sonic-ai-v3`.
Observed canonical `main`: `285be0202dcccb9d6e42c5ba534a0f60da927129`.
Implementation branch: `feature/forge-foundation-v1`.
The PR head identifies the resulting implementation commit; no merge/deployment
was performed. Work took place in an isolated checkout. Unrelated dirty recovery
work was preserved; the task's initial prototype was removed from that checkout.

The supplied archive SHA-256 and machine-readable results are retained in
[verification.json](evidence/verification.json). Original foundation documents are
under `contracts/`; they remain design material where not implemented.

## Executed checks

Interpreter: recovery checkout `.venv/Scripts/python.exe`, Python 3.14, with the
canonical `apps/api/requirements.txt` installed. That environment initially lacked
`mido`, NumPy and SoundFile; the first collection attempt failed. The declared
dependencies were installed before the successful runs below. Test execution used
temporary SQLite databases, with dotenv disabled by the existing conftest.

| Check | Result |
| --- | --- |
| Untouched `git archive` of canonical baseline; all `apps/api/tests` | **103 passed**, 0 failures/skips |
| Integrated `python -m pytest apps/api/tests -q --tb=short --basetemp=output/forge-regression-final-20261018 --junitxml=output/forge-regression-final.xml` | **149 passed**, 0 failures/skips |
| Final focused suite after bounding metadata-list queries: `python -m pytest apps/api/tests/test_forge_core_foundation.py apps/api/tests/test_forge_workflow.py -q --tb=short --basetemp=output/forge-focused-bounded-20261018 --junitxml=output/forge-focused-bounded.xml` | **46 passed**, including all **17 bundled tests** |
| `python -m compileall -q` for new Forge core, format validator, service, repository, router and auth modules | PASS |
| `node --check apps/api/workbench/static/app.js` and `node --check apps/api/workbench/static/forge.js` | PASS |
| `Draft202012Validator.check_schema` for both supplied schemas; actual HTTP-exported manifest validated against manifest schema | PASS |
| `python scripts/verify-forge-local.py --serve` | PASS: actual loopback API upload/review/approve/export/download; 2 synthetic assets byte-verified; anonymous download rejected |
| Playwright CLI with Chromium, actual `/workbench` | PASS: file picker upload, select-all, batch taxonomy, explicit rights clearance, nested path edit, save, revision approval, ZIP download and unpublished CSV download |
| Browser-downloaded ZIP byte/hash comparison and CSV read-back | PASS: exact original asset bytes, new taxonomy/path, `Published=FALSE`, `Status=draft` |
| `git diff --check` | PASS |

Existing pytest warnings concern deprecated UTC timestamps and the installed
Starlette/httpx TestClient combination. They did not fail these runs. An earlier
global pytest temp-junction cleanup permission error was avoided by using fresh,
explicit test scratch directories, not by deleting unknown temp files.

The bundled traversal test exposed Windows ZIP normalization on write **and read**.
The fixture now puts backslashes into raw ZIP headers, and the production core
checks `orig_filename` before `ZipInfo.filename` normalization. The initial
unpatched run failed that case; final runs above pass it.

## Safety coverage

Executed negative cases include traversal/absolute/Windows paths, reserved device
names, duplicate/case-colliding members, symlinks, unsupported extensions,
compression bombs/member limits, spoofed/truncated audio and invalid JSON,
unknown/invalid metadata, unsafe output paths, format-changing renames, changed
source ZIP hashes, missing commerce rights, foreign owner/workspace records,
missing/wrong authentication, hostile Origins, stale revisions, approval
invalidation, conflicting request IDs, concurrent review and repeated exports.
Injected export storage failure proves rollback leaves the previously approved
state and no partial artifact. Failed authorized mutations retain failure evidence.

Tenant-negative tests place foreign owner/workspace records in the actual database
and exercise actual API paths; they **do not establish hosted multiuser identity**.
The verified auth model is Sonic's existing loopback single-operator Workbench.

## Actual output

The HTTP smoke fixture is generated locally by the included smoke script, using a
valid PCM WAV and text. No proprietary audio, customer identity, credentials or
real pack licenses are added to the repository.

* Source ZIP SHA-256: `0d9cbd13fa8ffaccfcac1086c9efb5acbbd6e47820f3c85729b3869a3f8bba08`
* HTTP export SHA-256: `969760bf9066e3acc0f530e217cd142629ca37dd31ba1db0f52d7b21f725c71d`
* Separately reviewed browser export SHA-256: `bece7f89d4d16d1c334f8d52a317dc41a1e5b832086b1362409ff66d5e7ff99d`

The original ZIP was unchanged; each exported member was compared byte-for-byte
against the corresponding input. The browser export intentionally has different
review metadata and one renamed path. [Actual Workbench screenshot](evidence/workbench.png).
Smoke artifacts/databases and raw test reports remain in local `output/`, outside
the focused commit.

## Release gates

| Supplied gate | Current verdict |
| --- | --- |
| F0 foundation | PASS: 17 bundled tests plus API adversarial cases and byte lineage |
| F1 canonical integration | PASS for local review: canonical baseline, additive code, 149 green tests, authenticated API and browser evidence |
| F2 music inference | NOT IMPLEMENTED: BPM/key remain null; manual overrides are explicitly attributed; curated licensed truth-labeled calibration absent |
| F3 operational Forge | PARTIALLY VALIDATED: local owner/workspace, revisions, rollback, authorized downloads and synthetic browser/API flow pass. Real licensed pack, hosted identity, hard process-kill recovery and migration rollback not tested |
| A0 Acquire/live Shopify | NOT TESTED: offline CSV only; no provider authentication/scope/commerce validation performed |
| S0 Signal | NOT IMPLEMENTED by this change |

Next gate: validate an operator-authorized real licensed nested pack through this
same Workbench and retain import/export hashes and review evidence. Do not infer
music-estimator accuracy, legal rights, deployment, or live integrations from the
synthetic tests.
