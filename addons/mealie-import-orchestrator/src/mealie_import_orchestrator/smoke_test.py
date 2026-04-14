from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(os.environ.get("MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT", Path.cwd()))
    src_path = repo_root / "addons" / "mealie-import-orchestrator" / "src"

    env = os.environ.copy()
    env.setdefault("MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT", str(repo_root))

    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(src_path)
    )

    completed = subprocess.run(
        [sys.executable, "-m", "mealie_import_orchestrator", "status"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        print(completed.stderr, file=sys.stderr, end="")
        return completed.returncode

    payload = json.loads(completed.stdout)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("success", False) else 1
