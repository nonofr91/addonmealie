from __future__ import annotations

import importlib.util
import sys
from types import ModuleType
from typing import Any

from .config import AddonConfig, AddonConfigurationError


class AddonExecutionError(Exception):
    pass


class MealieImportOrchestrator:
    def __init__(self, config: AddonConfig | None = None) -> None:
        self.config = config or AddonConfig.load()
        self._workflow_module: ModuleType | None = None
        self._workflow_orchestrator: Any | None = None

    def run_full_workflow(self, sources: list[str] | None = None) -> dict[str, Any]:
        self._ensure_scraping_allowed()
        workflow_orchestrator = self._get_workflow_orchestrator()
        return self._ensure_result(workflow_orchestrator.run_complete_workflow(sources))

    def run_workflow_step(
        self,
        step: str,
        *,
        sources: list[str] | None = None,
        scraped_filename: str | None = None,
        structured_filename: str | None = None,
    ) -> dict[str, Any]:
        workflow_orchestrator = self._get_workflow_orchestrator()
        arguments: dict[str, Any] = {}

        if sources is not None:
            arguments["sources"] = sources
        if scraped_filename is not None:
            arguments["scraped_filename"] = scraped_filename
        if structured_filename is not None:
            arguments["structured_filename"] = structured_filename

        if step == "scraping":
            self._ensure_scraping_allowed()

        return self._ensure_result(workflow_orchestrator.run_step_by_step(step, **arguments))

    def get_status(self) -> dict[str, Any]:
        workflow_orchestrator = self._get_workflow_orchestrator()
        return self._ensure_result(workflow_orchestrator.get_workflow_status())

    def _ensure_scraping_allowed(self) -> None:
        if self.config.scraping_enabled:
            return

        raise AddonExecutionError(
            "Scraping is disabled for this addon runtime. Enable MEALIE_IMPORT_ORCHESTRATOR_ENABLE_SCRAPING only when a real scraping backend is available."
        )

    def _get_workflow_orchestrator(self) -> Any:
        if self._workflow_orchestrator is not None:
            return self._workflow_orchestrator

        workflow_module = self._load_workflow_module()
        orchestrator_class = getattr(workflow_module, "MealieWorkflowOrchestrator", None)
        if orchestrator_class is None:
            raise AddonConfigurationError(
                "MealieWorkflowOrchestrator not found in canonical workflow module"
            )

        self._workflow_orchestrator = orchestrator_class()
        return self._workflow_orchestrator

    def _load_workflow_module(self) -> ModuleType:
        if self._workflow_module is not None:
            return self._workflow_module

        spec = importlib.util.spec_from_file_location(
            "mealie_workflow_orchestrator",
            self.config.workflow_entrypoint,
        )
        if spec is None or spec.loader is None:
            raise AddonConfigurationError(
                f"Unable to load workflow module from {self.config.workflow_entrypoint}"
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self._workflow_module = module
        return module

    @staticmethod
    def _ensure_result(result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise AddonExecutionError("Workflow returned a non-dict result")
        return result
