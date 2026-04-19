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

# Feature flags
ENABLE_PROFILE_UI = os.environ.get("ENABLE_PROFILE_UI", "true").lower() == "true"
ENABLE_MENU_PLANNER = os.environ.get("ENABLE_MENU_PLANNER", "true").lower() == "true"
ENABLE_NUTRITION_ANALYSIS = os.environ.get("ENABLE_NUTRITION_ANALYSIS", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _map_activity_level(value: str) -> str:
    """Map English activity levels to French."""
    mapping = {
        "sedentary": "sédentaire",
        "lightly_active": "peu_actif",
        "moderately_active": "modérément_actif",
        "very_active": "très_actif",
        "extra_active": "extra_actif",
    }
    return mapping.get(value, value)

def _map_goal(value: str) -> str:
    """Map English goals to French."""
    mapping = {
        "weight_loss": "perte_de_poids",
        "maintenance": "maintien",
        "muscle_gain": "prise_de_masse",
    }
    return mapping.get(value, value)

def _map_activity_level_to_english(value: str) -> str:
    """Map French activity levels to English."""
    mapping = {
        "sédentaire": "sedentary",
        "peu_actif": "lightly_active",
        "modérément_actif": "moderately_active",
        "très_actif": "very_active",
        "extra_actif": "extra_active",
    }
    return mapping.get(value, value)

def _map_goal_to_english(value: str) -> str:
    """Map French goals to English."""
    mapping = {
        "perte_de_poids": "weight_loss",
        "maintien": "maintenance",
        "prise_de_masse": "muscle_gain",
    }
    return mapping.get(value, value)


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

# Créer les onglets selon les feature flags actifs
tabs = []
if ENABLE_NUTRITION_ANALYSIS:
    tabs.append("🔬 Enrichissement")
if ENABLE_PROFILE_UI:
    tabs.append("👥 Profils")
tabs.append("📊 Statut")

if not tabs:
    st.error("Aucune fonctionnalité activée. Veuillez configurer au moins un feature flag.")
    st.stop()

tabs_ui = st.tabs(tabs)

# ---------------------------------------------------------------------------
# Tabs dynamiques selon les feature flags
# ---------------------------------------------------------------------------
tab_index = 0
if ENABLE_NUTRITION_ANALYSIS:
    with tabs_ui[tab_index]:
        st.header("Enrichissement nutritionnel")
        st.caption("Calcule et ajoute les valeurs nutritionnelles aux recettes Mealie.")

        col_scan, col_enrich = st.columns(2)

        with col_scan:
            if st.button("🔍 Scanner", type="secondary", key="scan"):
                with st.spinner("Analyse en cours…"):
                    report = _api("GET", "/nutrition/scan")
                st.session_state["scan_report"] = report

        with col_enrich:
            force = st.checkbox("--force (recalculer tout)", value=False, key="force")
            if st.button("🚀 Enrichir tout", type="primary", key="enrich"):
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
    tab_index += 1

if ENABLE_PROFILE_UI:
    with tabs_ui[tab_index]:
        # Tab 2 — Profils
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

                            col_btns = st.columns(2)
                            with col_btns[0]:
                                if st.button(f"✏️ Modifier", key=f"edit_{member.get('name')}"):
                                    st.session_state["editing_member"] = member
                                    st.rerun()
                            with col_btns[1]:
                                if st.button(f"🗑️ Supprimer", key=f"del_{member.get('name')}"):
                                    delete_resp = _api("DELETE", f"/profiles/{member.get('name')}")
                                    if delete_resp.get("success"):
                                        st.success(f"{member.get('name')} supprimé")
                                        st.rerun()
                                    else:
                                        st.error(f"Erreur: {delete_resp.get('error')}")
            else:
                st.error(f"Erreur chargement profils: {profiles_response.get('error')}")

        with col_form:
            editing_member = st.session_state.get("editing_member")
            if editing_member:
                st.subheader(f"✏️ Modifier : {editing_member.get('name')}")
                if st.button("❌ Annuler la modification"):
                    st.session_state.pop("editing_member", None)
                    st.rerun()
            else:
                st.subheader("Ajouter/Modifier un membre")

            with st.form("profile_form"):
                if editing_member:
                    name = st.text_input("Nom *", value=editing_member.get('name', ''))
                    age = st.number_input("Âge *", min_value=1, max_value=120, value=editing_member.get('age', 30))
                    sex = st.selectbox("Sexe *", ["male", "female"], index=0 if editing_member.get('sex') == 'male' else 1)
                    weight = st.number_input("Poids (kg) *", min_value=1.0, max_value=500.0, value=editing_member.get('weight_kg', 70.0))
                    height = st.number_input("Taille (cm) *", min_value=1.0, max_value=300.0, value=editing_member.get('height_cm', 170.0))
                    activity_level_mapped = _map_activity_level(editing_member.get('activity_level', 'modérément_actif'))
                    activity = st.selectbox("Niveau d'activité",
                        ["sédentaire", "peu_actif", "modérément_actif", "très_actif", "extra_actif"],
                        index=["sédentaire", "peu_actif", "modérément_actif", "très_actif", "extra_actif"].index(activity_level_mapped))
                    goal_mapped = _map_goal(editing_member.get('goal', 'maintien'))
                    goal = st.selectbox("Objectif", ["perte_de_poids", "maintien", "prise_de_masse"],
                        index=["perte_de_poids", "maintien", "prise_de_masse"].index(goal_mapped))
                    allergies_text = st.text_input("Allergies (séparées par virgules)", value=', '.join(editing_member.get('allergies', [])))
                    foods_to_avoid_text = st.text_input("Aliments à éviter (séparées par virgules)", value=', '.join(editing_member.get('foods_to_avoid', [])))
                else:
                    name = st.text_input("Nom *")
                    age = st.number_input("Âge *", min_value=1, max_value=120, value=30)
                    sex = st.selectbox("Sexe *", ["male", "female"])
                    weight = st.number_input("Poids (kg) *", min_value=1.0, max_value=500.0, value=70.0)
                    height = st.number_input("Taille (cm) *", min_value=1.0, max_value=300.0, value=170.0)
                    activity = st.selectbox("Niveau d'activité",
                        ["sédentaire", "peu_actif", "modérément_actif", "très_actif", "extra_actif"])
                    goal = st.selectbox("Objectif", ["perte_de_poids", "maintien", "prise_de_masse"])

                st.write("**Pathologies médicales**")
                if editing_member:
                    conditions = st.multiselect(
                        "Sélectionnez si applicable",
                        ["diabète", "hypertension", "cholestérol_élevé", "goutte", "rfg", "maladie_rénale", "foie_gras", "colon_irritable"],
                        default=editing_member.get('medical_conditions', []),
                        key="conditions_edit"
                    )
                else:
                    conditions = st.multiselect(
                        "Sélectionnez si applicable",
                        ["diabète", "hypertension", "cholestérol_élevé", "goutte", "rfg", "maladie_rénale", "foie_gras", "colon_irritable"],
                        key="conditions_new"
                    )

                if editing_member:
                    restrictions = st.multiselect(
                        "Restrictions alimentaires",
                        ["vegetarian", "vegan", "gluten_free", "dairy_free", "low_sodium"],
                        default=editing_member.get('dietary_restrictions', []),
                        key="restrictions_edit"
                    )
                else:
                    restrictions = st.multiselect(
                        "Restrictions alimentaires",
                        ["vegetarian", "vegan", "gluten_free", "dairy_free", "low_sodium"],
                        key="restrictions_new"
                    )

                st.write("**Allergies et aliments à éviter**")
                if editing_member:
                    allergies_text = st.text_input("Allergies (séparées par virgules)", value=', '.join(editing_member.get('allergies', [])))
                    foods_to_avoid_text = st.text_input("Aliments à éviter (séparées par virgules)", value=', '.join(editing_member.get('foods_to_avoid', [])))
                else:
                    allergies_text = st.text_input("Allergies (séparées par virgules)")
                    foods_to_avoid_text = st.text_input("Aliments à éviter (séparées par virgules)")

                allergies = [a.strip() for a in allergies_text.split(",")] if allergies_text else []
                foods_to_avoid = [f.strip() for f in foods_to_avoid_text.split(",")] if foods_to_avoid_text else []

                submitted = st.form_submit_button("💾 Sauvegarder")
                if submitted:
                    if not name:
                        st.error("Le nom est obligatoire")
                    else:
                        from mealie_nutrition_advisor.models.profile import MemberProfile
                        member_data = {
                            "name": name,
                            "age": age,
                            "sex": sex,
                            "weight_kg": weight,
                            "height_cm": height,
                            "activity_level": _map_activity_level_to_english(activity),
                            "goal": _map_goal_to_english(goal),
                            "medical_conditions": conditions,
                            "dietary_restrictions": restrictions,
                            "allergies": allergies,
                            "foods_to_avoid": foods_to_avoid,
                        }
                        if editing_member:
                            update_resp = _api("PUT", f"/profiles/{editing_member.get('name')}", json={"member": member_data})
                            if update_resp.get("success"):
                                st.success(f"{name} mis à jour")
                                st.session_state.pop("editing_member", None)
                                st.rerun()
                            else:
                                st.error(f"Erreur: {update_resp.get('error')}")
                        else:
                            create_resp = _api("POST", "/profiles", json={"member": member_data})
                            if create_resp.get("success"):
                                st.success(f"{name} ajouté")
                                st.rerun()
                            else:
                                st.error(f"Erreur: {create_resp.get('error')}")
    tab_index += 1

# ---------------------------------------------------------------------------
# Tab Statut (toujours présent)
# ---------------------------------------------------------------------------
with tabs_ui[tab_index]:
    st.header("Statut du système")
    st.caption("Informations sur l'instance Mealie et l'addon.")

    status_response = _api("GET", "/status")
    if status_response.get("success"):
        s = status_response
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

        # Afficher les feature flags actifs
        st.subheader("Feature Flags actifs")
        st.write(f"- **Profile UI**: {'✅ Activé' if ENABLE_PROFILE_UI else '⬜ Désactivé'}")
        st.write(f"- **Menu Planner**: {'✅ Activé' if ENABLE_MENU_PLANNER else '⬜ Désactivé'}")
        st.write(f"- **Nutrition Analysis**: {'✅ Activé' if ENABLE_NUTRITION_ANALYSIS else '⬜ Désactivé'}")
    else:
        st.error(f"Erreur chargement statut: {status_response.get('error')}")


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
