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


def _api(method: str, path: str, *, timeout: int = 120, **kwargs) -> dict:
    try:
        r = requests.request(
            method,
            f"{API_URL}{path}",
            headers=_HEADERS,
            timeout=timeout,
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

tab_import, tab_audit, tab_ingredients, tab_nutrition, tab_status = st.tabs(["📥 Import", "🔍 Audit", "� Ingrédients", "�🥗 Nutrition", "📊 Statut"])

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
# Tab 3 — Ingredients cleanup
# ---------------------------------------------------------------------------
with tab_ingredients:
    st.header("Nettoyage des ingrédients")
    st.caption(
        "Détecte et corrige les foods mal formés : unité incluse dans le nom, "
        "modificateurs de préparation (haché, émincé…), commentaires entre parenthèses. "
        "**Séparation matière/préparation** : le modificateur est transféré dans le champ "
        "'note' de l'ingrédient (ex: 'persil haché' → food 'persil' + note 'haché'). "
        "Cela permet une nutrition précise et le regroupement des ingrédients en courses."
    )

    # Option pour mettre à jour les unités dans les recettes
    update_units = st.checkbox(
        "✅ Mettre à jour les unités dans les recettes (recommandé pour nutrition et courses)",
        value=True,
        key="ing_update_units"
    )
    if update_units:
        st.info(
            "Les ingrédients des recettes seront mis à jour : "
            "• Unité extraite (ex: 'g de beurre' → food 'beurre' + unité 'g') "
            "• Préparation conservée (ex: 'persil haché' → food 'persil' + note 'haché')"
        )

    col_scan_i, col_fix_i = st.columns(2)
    with col_scan_i:
        if st.button("🔍 Scanner les ingrédients", type="secondary", key="ing_scan_btn"):
            with st.spinner("Analyse en cours…"):
                report = _api("GET", "/ingredients/scan", timeout=600)
            st.session_state["ing_report"] = report

    with col_fix_i:
        if st.button("🔧 Corriger automatiquement", type="primary", key="ing_fix_all_btn"):
            with st.spinner("Corrections en cours…"):
                report = _api("POST", "/ingredients/fix", timeout=600, json={
                    "food_ids": None,
                    "update_recipe_units": update_units
                })
            st.session_state["ing_report"] = report

    report = st.session_state.get("ing_report")
    if report:
        if not report.get("success", True) and report.get("error"):
            st.error(report["error"])
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Foods analysés", report.get("total_scanned", 0))
            col2.metric("Problèmes détectés", report.get("issues_count", 0))
            col3.metric("Corrections appliquées", report.get("fixed_count", 0))

            errors = report.get("errors", [])
            if errors:
                with st.expander(f"⚠️ {len(errors)} avertissements"):
                    for e in errors:
                        st.warning(e)

            fixed = report.get("fixed", [])
            if fixed:
                with st.expander(f"✅ {len(fixed)} corrections appliquées", expanded=True):
                    for f in fixed:
                        st.success(f)

            issues = report.get("issues", [])
            if issues:
                st.subheader("Foods problématiques")
                st.caption("Sélectionne les foods à corriger individuellement ou utilise 'Corriger automatiquement' pour tout traiter.")

                selected_ids = []
                for i, issue in enumerate(issues):
                    issue_type_label = {
                        "unit_in_name": "🔴 Unité dans le nom",
                        "modifier_in_name": "🟡 Modificateur de préparation",
                    }.get(issue["issue_type"], "⚪ Autre")

                    col_cb, col_info = st.columns([1, 8])
                    with col_cb:
                        checked = st.checkbox(
                            f"Sélectionner {issue['food_name']}",
                            key=f"ing_cb_{i}",
                            value=False,
                            label_visibility="collapsed",
                        )
                        if checked:
                            selected_ids.append(issue["food_id"])
                    with col_info:
                        # Construire les détails des extractions
                        details = []
                        if issue.get("extracted_unit"):
                            details.append(f"unité: {issue['extracted_unit']}")
                        if issue.get("extracted_modifier"):
                            details.append(f"préparation: {issue['extracted_modifier']}")

                        detail_str = ""
                        if details:
                            detail_str = f" *(" + ", ".join(details) + ")*"

                        st.markdown(
                            f"{issue_type_label} — "
                            f"`{issue['food_name']}` → **`{issue['suggested_name']}`**"
                            + detail_str
                        )

                if selected_ids:
                    if st.button(f"🔧 Corriger la sélection ({len(selected_ids)} foods)", type="primary", key="ing_fix_sel_btn"):
                        with st.spinner("Corrections en cours…"):
                            result = _api("POST", "/ingredients/fix", timeout=600, json={
                                "food_ids": selected_ids,
                                "update_recipe_units": update_units
                            })
                        st.session_state["ing_report"] = result
                        st.rerun()

    # -----------------------------------------------------------------------
    # Sous-section : Unités manquantes dans les ingrédients de recettes
    # (orthogonal au scanner de foods ci-dessus)
    # -----------------------------------------------------------------------
    st.divider()
    st.subheader("🧪 Unités manquantes dans les recettes")
    st.caption(
        "Détecte les ingrédients de recettes où l'unité n'a pas été extraite "
        "par le parser Mealie (ex: `500 g de julienne de légumes` sans unité)."
    )

    col_scan_ru, col_fix_ru = st.columns(2)
    with col_scan_ru:
        if st.button("🔍 Scanner les recettes", type="secondary", key="ru_scan_btn"):
            with st.spinner("Scan des recettes en cours (peut prendre 1 min)…"):
                ru_report = _api("GET", "/ingredients/scan-recipe-units", timeout=600)
            st.session_state["ru_report"] = ru_report

    with col_fix_ru:
        if st.button("🔧 Corriger toutes les unités", type="primary", key="ru_fix_all_btn"):
            with st.spinner("Corrections en cours…"):
                ru_report = _api(
                    "POST", "/ingredients/fix-recipe-units",
                    timeout=600, json={"reference_ids": None}
                )
            st.session_state["ru_report"] = ru_report

    ru_report = st.session_state.get("ru_report")
    if ru_report:
        if not ru_report.get("success", True) and ru_report.get("error"):
            st.error(ru_report["error"])
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Recettes scannées", ru_report.get("total_recipes", 0))
            c2.metric("Ingrédients", ru_report.get("total_ingredients", 0))
            c3.metric("Unités manquantes", ru_report.get("issues_count", 0))

            if ru_report.get("fixed"):
                st.success(f"✅ {len(ru_report['fixed'])} corrections appliquées")
                with st.expander("Voir les corrections"):
                    for f in ru_report["fixed"]:
                        st.markdown(f"- {f}")

            if ru_report.get("errors"):
                with st.expander(f"⚠️ {len(ru_report['errors'])} erreurs"):
                    for e in ru_report["errors"]:
                        st.markdown(f"- {e}")

            issues = ru_report.get("issues", [])
            if issues and not ru_report.get("fixed"):
                st.markdown(f"**{len(issues)} ingrédients à corriger :**")
                for i, issue in enumerate(issues[:50]):
                    st.markdown(
                        f"- **{issue['food_name']}** → unité `{issue['extracted_unit']}` "
                        f"(recette *{issue['recipe_name']}*)  \n"
                        f"  `{issue['original_text']}`"
                    )
                if len(issues) > 50:
                    st.caption(f"… et {len(issues) - 50} autres")


# ---------------------------------------------------------------------------
# Tab 4 — Nutrition
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
