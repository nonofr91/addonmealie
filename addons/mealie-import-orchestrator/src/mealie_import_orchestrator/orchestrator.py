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
        self._auth_wrapper: ModuleType | None = None

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
        scrape_url: str | None = None,
    ) -> dict[str, Any]:
        workflow_orchestrator = self._get_workflow_orchestrator()
        arguments: dict[str, Any] = {}

        if sources is not None:
            arguments["sources"] = sources
        if scraped_filename is not None:
            arguments["scraped_filename"] = scraped_filename
        if structured_filename is not None:
            arguments["structured_filename"] = structured_filename
        if scrape_url is not None:
            arguments["scrape_url"] = scrape_url

        if step == "scraping" or step == "scrape":
            self._ensure_scraping_allowed()

        return self._ensure_result(workflow_orchestrator.run_step_by_step(step, **arguments))

    def get_status(self) -> dict[str, Any]:
        workflow_orchestrator = self._get_workflow_orchestrator()
        return self._ensure_result(workflow_orchestrator.get_workflow_status())

    def import_from_url(self, url: str) -> dict[str, Any]:
        """Scrape + structure + import une recette depuis une URL unique."""
        import os, contextlib, sys
        import requests

        if not url or not url.startswith("http"):
            return {"success": False, "error": "URL invalide"}

        workflow_orchestrator = self._get_workflow_orchestrator()

        # 1. Scraping (force-enable quel que soit le flag de config)
        with contextlib.redirect_stdout(sys.stderr):
            scrape = workflow_orchestrator.run_step_by_step("scraping", sources=[url])
        if not scrape.get("success"):
            return {"success": False, "error": "Scraping échoué", "details": scrape}

        scraped_file = scrape.get("filename")

        # 2. Structuration
        with contextlib.redirect_stdout(sys.stderr):
            structure = workflow_orchestrator.run_step_by_step(
                "structuring", scraped_filename=scraped_file
            )
        if not structure.get("success"):
            return {"success": False, "error": "Structuration échouée", "details": structure}

        structured_file = structure.get("filename")

        # 3. Import Mealie
        with contextlib.redirect_stdout(sys.stderr):
            result = workflow_orchestrator.run_step_by_step(
                "importing", structured_filename=structured_file
            )

        if not result.get("success"):
            return {"success": False, "error": "Import échoué", "details": result}

        imported = result.get("imported_recipes", [])
        first = imported[0] if imported else {}
        slug = first.get("slug", "")
        
        # 4. Nutrition enrichment (if enabled)
        nutrition_data = None
        if self.config.enable_nutrition and slug:
            try:
                headers = {}
                if self.config.addon_secret_key:
                    headers["X-Addon-Key"] = self.config.addon_secret_key
                
                nutrition_resp = requests.post(
                    f"{self.config.nutrition_api_url}/nutrition/recipe/{slug}",
                    headers=headers,
                    timeout=60,
                )
                if nutrition_resp.status_code == 200:
                    nutrition_data = nutrition_resp.json()
            except Exception as exc:
                # Don't fail import if nutrition enrichment fails
                pass
        
        response = {
            "success": True,
            "slug": slug,
            "name": first.get("name", ""),
            "total_imported": result.get("total_imported", len(imported)),
            "mealie_url": (
                f"{self.config.mealie_base_url}/g/home/r/{slug}"
                if slug
                else None
            ),
        }
        
        if nutrition_data and nutrition_data.get("success"):
            response["nutrition"] = {
                "calories": nutrition_data.get("calories"),
                "protein": nutrition_data.get("protein"),
                "fat": nutrition_data.get("fat"),
                "carbohydrates": nutrition_data.get("carbohydrates"),
            }
        
        return response

    def audit(self, fix: bool = False) -> dict[str, Any]:
        """Lance l'audit qualité via mcp_auth_wrapper.audit_recipes()."""
        wrapper = self._get_auth_wrapper()
        try:
            return wrapper.audit_recipes(fix=fix)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_health(self) -> dict[str, Any]:
        """Vérifie la connectivité Mealie et l'état de la config."""
        import requests as _req

        cfg = self.config
        mealie_ok = False
        mealie_version = None
        if cfg.mealie_base_url:
            try:
                r = _req.get(f"{cfg.mealie_base_url}/api/app/about", timeout=5)
                if r.status_code == 200:
                    mealie_ok = True
                    mealie_version = r.json().get("version")
            except Exception:
                pass

        return {
            "success": True,
            "mealie_reachable": mealie_ok,
            "mealie_version": mealie_version,
            "mealie_base_url": cfg.mealie_base_url or "(non configurée)",
            "ai_enabled": cfg.ai_enabled,
            "ai_model": cfg.ai_model if cfg.ai_enabled else None,
            "ai_provider": cfg.ai_provider,
            "scraping_enabled": cfg.scraping_enabled,
        }

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

    def _get_auth_wrapper(self) -> ModuleType:
        if self._auth_wrapper is not None:
            return self._auth_wrapper

        wrapper_path = self.config.workflow_directory / "mcp_auth_wrapper.py"
        if not wrapper_path.is_file():
            raise AddonConfigurationError(
                f"mcp_auth_wrapper.py not found at {wrapper_path}"
            )
        spec = importlib.util.spec_from_file_location("_mcp_auth_wrapper", wrapper_path)
        if spec is None or spec.loader is None:
            raise AddonConfigurationError("Cannot load mcp_auth_wrapper")
        module = importlib.util.module_from_spec(spec)
        sys.modules["_mcp_auth_wrapper"] = module
        spec.loader.exec_module(module)
        self._auth_wrapper = module
        return module

    @staticmethod
    def _ensure_result(result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise AddonExecutionError("Workflow returned a non-dict result")
        return result
