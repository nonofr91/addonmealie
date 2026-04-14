from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


class AddonConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class AddonConfig:
    repo_root: Path
    workflow_directory: Path
    workflow_entrypoint: Path
    scraping_enabled: bool

    @classmethod
    def load(cls, workflow_directory: str | None = None) -> "AddonConfig":
        cls._load_environment_files()
        configured_repo_root = os.environ.get("MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT")
        if configured_repo_root:
            repo_root = Path(configured_repo_root).expanduser().resolve()
        else:
            repo_root = Path(__file__).resolve().parents[4]
        configured_path = workflow_directory or os.environ.get(
            "MEALIE_IMPORT_ORCHESTRATOR_WORKFLOW_PATH"
        )
        resolved_workflow_directory = cls._resolve_workflow_directory(
            configured_path=configured_path,
            repo_root=repo_root,
        )
        config = cls(
            repo_root=repo_root,
            workflow_directory=resolved_workflow_directory,
            workflow_entrypoint=resolved_workflow_directory / "workflow_orchestrator.py",
            scraping_enabled=cls._parse_bool(
                os.environ.get("MEALIE_IMPORT_ORCHESTRATOR_ENABLE_SCRAPING")
            ),
        )
        config.validate()
        return config

    @staticmethod
    def _load_environment_files() -> None:
        current_working_directory = Path.cwd()
        addon_root = Path(__file__).resolve().parents[2]

        load_dotenv(current_working_directory / ".env", override=False)
        load_dotenv(addon_root / ".env", override=False)

    @staticmethod
    def _parse_bool(value: str | None) -> bool:
        if value is None:
            return False

        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _resolve_workflow_directory(
        configured_path: str | None,
        repo_root: Path,
    ) -> Path:
        if not configured_path:
            return (repo_root / "mealie-workflow").resolve()

        path = Path(configured_path).expanduser()
        if not path.is_absolute():
            path = repo_root / path
        return path.resolve()

    def validate(self) -> None:
        if not self.workflow_directory.exists():
            raise AddonConfigurationError(
                f"Workflow directory not found: {self.workflow_directory}"
            )

        if not self.workflow_entrypoint.is_file():
            raise AddonConfigurationError(
                f"Workflow entrypoint not found: {self.workflow_entrypoint}"
            )
