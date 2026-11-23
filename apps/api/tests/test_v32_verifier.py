"""The verification runner must never select the operator's persistent stores."""
from scripts.verify_v32 import isolated_environment, run_check
import sys


def test_verifier_discards_inherited_storage_and_credentials(tmp_path):
    parent = {"PATH": "retained", "SONIC_DB_PATH": "production.db",
              "SONIC_INTEGRITY_DB": "production-ledger.db", "SONIC_DESKTOP_TOKEN": "secret",
              "SONIC_OPENAI_API_KEY": "secret", "OPENAI_API_KEY": "secret",
              "SONIC_OAUTH_ISSUER": "https://issuer.test", "PYTHONPATH": "untrusted"}
    env = isolated_environment(parent, tmp_path)
    assert env["SONIC_DB_PATH"] == str(tmp_path / "app.db")
    assert env["SONIC_INTEGRITY_DB"] == str(tmp_path / "integrity.db")
    assert env["SONIC_EVENT_DB"] == str(tmp_path / "events.db")
    assert env["PYTHON_DOTENV_DISABLED"] == "1"
    assert env["PATH"] == "retained"
    assert not set(env) & {"SONIC_DESKTOP_TOKEN", "SONIC_OPENAI_API_KEY", "OPENAI_API_KEY", "SONIC_OAUTH_ISSUER"}
    assert parent["SONIC_DB_PATH"] == "production.db"


def test_verifier_records_failure_and_output(tmp_path):
    result = run_check("fixture", [sys.executable, "-c", "print('fixture failure'); raise SystemExit(7)"],
                       isolated_environment({}, tmp_path), tmp_path, 10)
    assert not result["passed"]
    assert result["exit_code"] == 7
    assert "fixture failure" in (tmp_path / "fixture.log").read_text()
