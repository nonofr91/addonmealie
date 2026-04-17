"""Streamlit Web UI — Mealie Import Addon."""
from __future__ import annotations

import os
import subprocess
import sys

import requests
import streamlit as st

API_URL = os.environ.get("ADDON_API_URL", "http://localhost:8000")
_SECRET = os.environ.get("ADDON_SECRET_KEY", "")
_MEALIE_BASE = os.environ.get("MEALIE_BASE_URL", "").rstrip("/")

_HEADERS: dict[str, str] = {}
if _SECRET:
    _HEADERS["X-Addon-Key"] = _SECRET


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api(method: str, path: str, **kwargs) -> dict:
    try:
        r = requests.request(
            method,
            f"{API_URL}{path}",
            headers=_HEADERS,
            timeout=120,
            **kwargs,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "API non joignable — l'addon est-il démarré ?"}
    except requests.exceptions.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        return {"success": False, "error": detail}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Mealie Import Addon",
    page_icon="🍽️",
    layout="wide",
)

col_title, col_btn = st.columns([6, 1])
with col_title:
    st.title("🍽️ Mealie Import Addon")
with col_btn:
    if _MEALIE_BASE:
        st.markdown(
            f'<div style="padding-top:1.4rem">'
            f'<a href="{_MEALIE_BASE}" target="_blank" style="'
            f'display:inline-block;padding:0.4rem 0.8rem;background:#FF4B4B;'
            f'color:white;border-radius:6px;text-decoration:none;font-size:0.9rem">'
            f'🏠 Mealie</a></div>',
            unsafe_allow_html=True,
        )

tab_import, tab_audit, tab_nutrition, tab_status = st.tabs(["📥 Import", "🔍 Audit", "🥗 Nutrition", "📊 Statut"])

# ---------------------------------------------------------------------------
# Tab 1 — Import
# ---------------------------------------------------------------------------
with tab_import:
    st.header("Importer une recette")
    st.caption("Colle l'URL d'une recette (Marmiton, 750g, …) et clique sur Importer.")

    url_input = st.text_input(
        "URL de la recette",
        placeholder="https://www.marmiton.org/recettes/...",
    )

    if st.button("🚀 Importer", type="primary", disabled=not url_input, key="import_button_unique"):
        with st.spinner("Import en cours… (scraping → structuration → Mealie)"):
            result = _api("POST", "/import", json={"url": url_input})

        if result.get("success"):
            st.success(f"✅ Recette importée : **{result.get('name', '—')}**")
            mealie_url = result.get("mealie_url")
            if mealie_url:
                st.markdown(f"[🔗 Voir dans Mealie]({mealie_url})")
            else:
                slug = result.get("slug", "")
                if slug and _MEALIE_BASE:
                    st.markdown(f"[🔗 Voir dans Mealie]({_MEALIE_BASE}/g/home/r/{slug})")
        else:
            st.error(f"❌ {result.get('error', 'Erreur inconnue')}")
            with st.expander("Détails"):
                st.json(result)

# ---------------------------------------------------------------------------
# Tab 2 — Audit
# ---------------------------------------------------------------------------
with tab_audit:
    st.header("Audit qualité des recettes")
    st.caption("Détecte les recettes sans image, les tags test, les doublons probables.")

    col_scan, col_fix = st.columns(2)

    with col_scan:
        if st.button("🔍 Scanner", type="secondary", key="audit_scan_button"):
            with st.spinner("Analyse en cours…"):
                report = _api("GET", "/audit")
            st.session_state["audit_report"] = report

    with col_fix:
        if st.button("🔧 Corriger automatiquement", type="primary", key="audit_fix_button"):
            with st.spinner("Corrections en cours…"):
                report = _api("POST", "/audit/fix")
            st.session_state["audit_report"] = report

    report = st.session_state.get("audit_report")
    if report:
        if not report.get("success", True) and report.get("error"):
            st.error(report["error"])
        else:
            issues = report.get("issues", [])
            total = report.get("total", 0)
            fixed = report.get("fixed", [])

            st.metric("Recettes analysées", total)
            col1, col2 = st.columns(2)
            col1.metric("Problèmes détectés", len(issues))
            col2.metric("Corrections appliquées", len(fixed))

            if issues:
                st.subheader("Recettes avec problèmes")
                for item in issues:
                    with st.expander(f"⚠️ {item.get('name', item.get('slug', '?'))}"):
                        for iss in item.get("issues", []):
                            st.markdown(f"- `{iss}`")
                        slug = item.get("slug", "")
                        if slug and _MEALIE_BASE:
                            st.markdown(f"[🔗 Ouvrir dans Mealie]({_MEALIE_BASE}/g/home/r/{slug})")

            if fixed:
                st.subheader("Corrections appliquées")
                for fix in fixed:
                    st.success(f"✅ {fix}")

# ---------------------------------------------------------------------------
# Tab 3 — Nutrition
# ---------------------------------------------------------------------------
with tab_nutrition:
    st.header("Enrichissement nutritionnel")
    st.caption("Ajoute des données nutritionnelles aux recettes Mealie via OpenFoodFacts et l'IA.")

    col_scan, col_enrich = st.columns(2)

    with col_scan:
        if st.button("🔍 Scanner", type="secondary", key="nutrition_scan_button"):
            with st.spinner("Analyse en cours…"):
                report = _api("GET", "/nutrition/scan")
            st.session_state["nutrition_report"] = report

    with col_enrich:
        force = st.checkbox("Forcer le recalcul", value=False)
        if st.button("🚀 Enrichir", type="primary", key="nutrition_enrich_button"):
            with st.spinner("Enrichissement en cours…"):
                report = _api("POST", "/nutrition/enrich", json={"force": force})
            st.session_state["nutrition_report"] = report

    report = st.session_state.get("nutrition_report")
    if report:
        if not report.get("success", True) and report.get("error"):
            st.error(report["error"])
        else:
            total = report.get("total", 0)
            enriched = report.get("enriched", 0)
            failed = report.get("failed", 0)

            st.metric("Recettes analysées", total)
            col1, col2 = st.columns(2)
            col1.metric("Enrichies avec succès", len(enriched) if isinstance(enriched, list) else enriched)
            col2.metric("Échecs", len(failed) if isinstance(failed, list) else failed)

            if report.get("details"):
                st.subheader("Détails")
                for detail in report["details"]:
                    if detail.get("success"):
                        st.success(f"✅ {detail.get('name', detail.get('slug', '?'))}")
                    else:
                        st.error(f"❌ {detail.get('name', detail.get('slug', '?'))}: {detail.get('error', 'Erreur inconnue')}")

# ---------------------------------------------------------------------------
# Tab 3 — Status
# ---------------------------------------------------------------------------
with tab_status:
    st.header("Statut de l'addon")

    if st.button("🔄 Rafraîchir", key="status_refresh_button_unique"):
        st.session_state["status"] = _api("GET", "/status")

    s = st.session_state.get("status")
    if s is None:
        s = _api("GET", "/status")
        st.session_state["status"] = s

    if s.get("error"):
        st.error(s["error"])
    else:
        col1, col2, col3 = st.columns(3)
        mealie_ok = s.get("mealie_reachable", False)
        col1.metric(
            "Mealie",
            "✅ Connectée" if mealie_ok else "❌ Hors ligne",
            s.get("mealie_version") or "",
        )
        col2.metric(
            "IA",
            "✅ Active" if s.get("ai_enabled") else "⬜ Désactivée",
            s.get("ai_model") or "JSON-LD uniquement",
        )
        col3.metric(
            "Scraping",
            "✅ Activé" if s.get("scraping_enabled") else "⬜ Désactivé",
        )
        st.caption(f"Instance Mealie : `{s.get('mealie_base_url', '—')}`")


# ---------------------------------------------------------------------------
# CLI launcher
# ---------------------------------------------------------------------------


def main() -> None:
    """Lanceur CLI : démarre streamlit sur ce fichier."""
    ui_file = os.path.abspath(__file__)
    port = os.environ.get("ADDON_UI_PORT", "8501")
    sys.exit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                ui_file,
                "--server.port",
                port,
                "--server.address",
                "0.0.0.0",
                "--server.headless",
                "true",
            ]
        )
    )
