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
    mealie_base_url: str
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    ai_provider: str
    ai_model: str | None
    ai_enabled: bool
    addon_secret_key: str | None
    enable_nutrition: bool
    nutrition_api_url: str

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
        openai_api_key = os.environ.get("OPENAI_API_KEY") or None
        ai_provider = os.environ.get("AI_PROVIDER", "mock").strip().lower()
        ai_model = cls._get_ai_model(ai_provider)
        config = cls(
            repo_root=repo_root,
            workflow_directory=resolved_workflow_directory,
            workflow_entrypoint=resolved_workflow_directory / "workflow_orchestrator.py",
            scraping_enabled=cls._parse_bool(
                os.environ.get("MEALIE_IMPORT_ORCHESTRATOR_ENABLE_SCRAPING")
            ),
            mealie_base_url=(
                os.environ.get("MEALIE_BASE_URL", "")
                or os.environ.get("MEALIE_IMPORT_ORCHESTRATOR_BASE_URL", "")
            ).rstrip("/"),
            openai_api_key=openai_api_key,
            openai_base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            ai_provider=ai_provider,
            ai_model=ai_model,
            ai_enabled=cls._is_ai_enabled(ai_provider),
            addon_secret_key=os.environ.get("ADDON_SECRET_KEY") or None,
            enable_nutrition=cls._parse_bool(
                os.environ.get("ENABLE_NUTRITION", "true")
            ),
            nutrition_api_url=os.environ.get("NUTRITION_API_URL", "http://localhost:8001"),
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
    def _is_ai_enabled(provider: str) -> bool:
        if provider == "openai":
            return bool(os.environ.get("OPENAI_API_KEY"))
        if provider == "anthropic":
            return bool(os.environ.get("ANTHROPIC_API_KEY"))
        if provider == "mistral":
            return bool(os.environ.get("MISTRAL_API_KEY"))
        return False

    @staticmethod
    def _get_ai_model(provider: str) -> str | None:
        if provider == "openai":
            return os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        if provider == "anthropic":
            return os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        if provider == "mistral":
            return os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
        return None

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
