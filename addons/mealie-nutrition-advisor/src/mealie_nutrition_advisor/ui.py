"""Streamlit Web UI — Mealie Nutrition Advisor."""
from __future__ import annotations

import os
import subprocess
import sys

import requests
import streamlit as st

API_URL = os.environ.get("ADDON_API_URL", "http://localhost:8001")
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
    page_title="Mealie Nutrition Advisor",
    page_icon="🔬",
    layout="wide",
)

col_title, col_btn = st.columns([6, 1])
with col_title:
    st.title("🔬 Mealie Nutrition Advisor")
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

tab_enrich, tab_profiles, tab_status = st.tabs(["🔬 Enrichissement", "👥 Profils", "📊 Statut"])

# ---------------------------------------------------------------------------
# Tab 1 — Enrichissement
# ---------------------------------------------------------------------------
with tab_enrich:
    st.header("Enrichissement nutritionnel")
    st.caption("Calcule et ajoute les valeurs nutritionnelles aux recettes Mealie.")

    col_scan, col_enrich = st.columns(2)

    with col_scan:
        if st.button("🔍 Scanner", type="secondary"):
            with st.spinner("Analyse en cours…"):
                report = _api("GET", "/nutrition/scan")
            st.session_state["scan_report"] = report

    with col_enrich:
        force = st.checkbox("--force (recalculer tout)", value=False)
        if st.button("🚀 Enrichir tout", type="primary"):
            with st.spinner("Enrichissement en cours…"):
                report = _api("POST", "/nutrition/enrich", json={"force": force})
            st.session_state["enrich_report"] = report

    # Scan report
    scan_report = st.session_state.get("scan_report")
    if scan_report:
        if not scan_report.get("success", True) and scan_report.get("error"):
            st.error(scan_report["error"])
        else:
            total = scan_report.get("total", 0)
            to_enrich = scan_report.get("to_enrich", 0)
            with_nutrition = scan_report.get("with_nutrition", [])
            without_nutrition = scan_report.get("without_nutrition", [])

            st.metric("Total recettes", total)
            col1, col2 = st.columns(2)
            col1.metric("Sans nutrition", to_enrich)
            col2.metric("Avec nutrition", total - to_enrich)

            if without_nutrition:
                st.subheader("Recettes sans nutrition")
                for item in without_nutrition:
                    with st.expander(f"⚠️ {item.get('name', item.get('slug', '?'))}"):
                        slug = item.get("slug", "")
                        if slug and _MEALIE_BASE:
                            st.markdown(f"[🔗 Ouvrir dans Mealie]({_MEALIE_BASE}/g/home/r/{slug})")

    # Enrich report
    enrich_report = st.session_state.get("enrich_report")
    if enrich_report:
        if not enrich_report.get("success", True) and enrich_report.get("error"):
            st.error(enrich_report["error"])
        else:
            total = enrich_report.get("total", 0)
            enriched = enrich_report.get("enriched", [])
            skipped = enrich_report.get("skipped", [])
            failed = enrich_report.get("failed", [])

            st.metric("Recettes traitées", total)
            col1, col2, col3 = st.columns(3)
            col1.metric("Enrichies", len(enriched))
            col2.metric("Ignorées", len(skipped))
            col3.metric("Échecs", len(failed))

            if enriched:
                st.subheader("Recettes enrichies")
                for item in enriched:
                    slug = item.get("slug", "")
                    name = item.get("name", slug)
                    calories = item.get("calories", 0)
                    st.success(f"✅ {name} — {calories:.0f} kcal")
                    if slug and _MEALIE_BASE:
                        st.markdown(f"[🔗 Voir dans Mealie]({_MEALIE_BASE}/g/home/r/{slug})")

            if failed:
                st.subheader("Échecs")
                for item in failed:
                    st.error(f"❌ {item.get('name', item.get('slug', '?'))}: {item.get('error', 'Unknown')}")

# ---------------------------------------------------------------------------
# Tab 2 — Profils
# ---------------------------------------------------------------------------
with tab_profiles:
    st.header("Gestion des profils du foyer")
    st.caption("Gérez les profils nutritionnels des membres du foyer.")

    col_list, col_form = st.columns([1, 2])

    with col_list:
        st.subheader("Membres du foyer")
        profiles_response = _api("GET", "/profiles")
        
        if profiles_response.get("success"):
            members = profiles_response.get("members", [])
            if not members:
                st.info("Aucun membre. Ajoutez-en un via le formulaire.")
            else:
                for member in members:
                    with st.expander(f"👤 {member.get('name', '?')}"):
                        st.write(f"**Âge:** {member.get('age')} ans")
                        st.write(f"**Sexe:** {member.get('sex')}")
                        st.write(f"**Poids:** {member.get('weight_kg')} kg")
                        st.write(f"**Taille:** {member.get('height_cm')} cm")
                        st.write(f"**Activité:** {member.get('activity_level')}")
                        st.write(f"**Objectif:** {member.get('goal')}")
                        
                        conditions = member.get('medical_conditions', [])
                        if conditions:
                            st.write(f"**Pathologies:** {', '.join(conditions)}")
                        
                        allergies = member.get('allergies', [])
                        if allergies:
                            st.write(f"**Allergies:** {', '.join(allergies)}")
                        
                        if st.button(f"Supprimer {member.get('name')}", key=f"del_{member.get('name')}"):
                            delete_resp = _api("DELETE", f"/profiles/{member.get('name')}")
                            if delete_resp.get("success"):
                                st.success(f"{member.get('name')} supprimé")
                                st.rerun()
                            else:
                                st.error(f"Erreur: {delete_resp.get('error')}")
        else:
            st.error(f"Erreur chargement profils: {profiles_response.get('error')}")

    with col_form:
        st.subheader("Ajouter/Modifier un membre")
        
        with st.form("profile_form"):
            name = st.text_input("Nom *")
            age = st.number_input("Âge *", min_value=1, max_value=120, value=30)
            sex = st.selectbox("Sexe *", ["male", "female"])
            weight = st.number_input("Poids (kg) *", min_value=1.0, max_value=500.0, value=70.0)
            height = st.number_input("Taille (cm) *", min_value=1.0, max_value=300.0, value=170.0)
            activity = st.selectbox("Niveau d'activité", 
                ["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"])
            goal = st.selectbox("Objectif", ["weight_loss", "maintenance", "muscle_gain"])
            
            st.write("**Pathologies médicales**")
            conditions = st.multiselect(
                "Sélectionnez si applicable",
                ["diabetes", "hypertension", "high_cholesterol", "gout", "gerd", "kidney_disease"]
            )
            
            allergies_text = st.text_input("Allergies (séparées par virgules)")
            allergies = [a.strip() for a in allergies_text.split(",") if a.strip()]
            
            submitted = st.form_submit_button("Enregistrer")
            
            if submitted and name:
                member_data = {
                    "name": name,
                    "age": age,
                    "sex": sex,
                    "weight_kg": weight,
                    "height_cm": height,
                    "activity_level": activity,
                    "goal": goal,
                    "medical_conditions": conditions,
                    "allergies": allergies,
                    "dietary_restrictions": [],
                    "weekly_presence": {
                        "presence": {
                            "monday": ["breakfast", "lunch", "dinner"],
                            "tuesday": ["breakfast", "lunch", "dinner"],
                            "wednesday": ["breakfast", "lunch", "dinner"],
                            "thursday": ["breakfast", "lunch", "dinner"],
                            "friday": ["breakfast", "lunch", "dinner"],
                            "saturday": ["breakfast", "lunch", "dinner"],
                            "sunday": ["breakfast", "lunch", "dinner"]
                        }
                    },
                    "custom_targets": {}
                }
                
                create_resp = _api("POST", "/profiles", json={"member": member_data})
                if create_resp.get("success"):
                    st.success(f"{name} ajouté avec succès")
                    st.rerun()
                else:
                    st.error(f"Erreur: {create_resp.get('error')}")

# ---------------------------------------------------------------------------
# Tab 3 — Statut
# ---------------------------------------------------------------------------
with tab_status:
    st.header("Statut de l'addon")

    if st.button("🔄 Rafraîchir"):
        st.session_state["status"] = _api("GET", "/status")

    s = st.session_state.get("status")
    if s is None:
        s = _api("GET", "/status")
        st.session_state["status"] = s

    if s.get("error"):
        st.error(s["error"])
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Recettes Mealie",
            s.get("total_recipes", 0),
            f"{s.get('recipes_with_nutrition', 0)} avec nutrition",
        )
        col2.metric(
            "IA",
            "✅ Active" if s.get("use_ai_estimation") else "⬜ Désactivée",
            s.get("ai_provider") or "Aucun",
        )
        col3.metric(
            "À enrichir",
            s.get("recipes_without_nutrition", 0),
        )
        st.caption(f"Instance Mealie : `{s.get('mealie_base_url', '—')}`")


# ---------------------------------------------------------------------------
# CLI launcher
# ---------------------------------------------------------------------------


def main() -> None:
    """Lanceur CLI : démarre streamlit sur ce fichier."""
    ui_file = os.path.abspath(__file__)
    port = os.environ.get("ADDON_UI_PORT", "8502")
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


if __name__ == "__main__":
    main()
