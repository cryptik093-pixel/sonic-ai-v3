"""Copy only the product's source and specifications, excluding generated caches."""
import shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];destination=Path(sys.argv[1]).resolve()
assert destination.is_dir() and destination != root
for name in ('core','plugin','contracts','tests','tools','presets','docs'):
    shutil.copytree(root/name,destination/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ('CMakeLists.txt','AGENTS.md','README.md','CODEX_FIRST_TASK.md','VERIFICATION.md','.gitignore'):
    shutil.copy2(root/name,destination/name)
