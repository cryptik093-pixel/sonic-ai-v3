"""Local only read-only FLP evidence command. Run from repository root.

python -m apps.api.fl_studio_integrity_cli capture --root "C:\\Studio" --project "song.flp"
python -m apps.api.fl_studio_integrity_cli verify --root "C:\\Studio" --session-id ID
"""
import argparse
import json

from .fl_studio_integrity import capture_project, verify_project
from .session_integrity import IntegrityLedger

def main():
    parser = argparse.ArgumentParser(description="Read-only FL Studio file integrity")
    parser.add_argument("action", choices=["capture", "verify"])
    parser.add_argument("--root", required=True, help="Approved local studio folder")
    parser.add_argument("--project", help="Saved FLP within root, for capture")
    parser.add_argument("--asset", action="append", default=[], help="Asset file within root (repeatable)")
    parser.add_argument("--session-id", help="Existing manifest session ID")
    parser.add_argument("--expected-revision", type=int)
    args = parser.parse_args()
    ledger = IntegrityLedger()
    if args.action == "capture":
        if not args.project:
            parser.error("--project required for capture")
        result = capture_project(ledger, args.root, args.project, args.session_id,
                                 args.expected_revision, args.asset)
    else:
        if not args.session_id:
            parser.error("--session-id required for verify")
        result = verify_project(ledger.get(args.session_id), args.root)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
