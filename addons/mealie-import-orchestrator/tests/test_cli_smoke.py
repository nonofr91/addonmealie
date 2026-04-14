from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class MealieImportOrchestratorCliSmokeTest(unittest.TestCase):
    def test_status_command_returns_json(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        env = os.environ.copy()
        env["MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT"] = str(repo_root)

        src_path = repo_root / "addons" / "mealie-import-orchestrator" / "src"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{src_path}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(src_path)
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mealie_import_orchestrator",
                "status",
            ],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)
        self.assertIn("success", payload)


if __name__ == "__main__":
    unittest.main()
