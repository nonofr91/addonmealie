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
ENABLE_MENU_PLANNING_UI = os.environ.get("ENABLE_MENU_PLANNING_UI", "true").lower() == "true"
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

def _map_medical_conditions_to_english(conditions: list[str]) -> list[str]:
    """Map French medical conditions to English."""
    mapping = {
        "diabète": "diabetes",
        "hypertension": "hypertension",
        "cholestérol_élevé": "high_cholesterol",
        "goutte": "gout",
        "rfg": "gerd",
        "maladie_rénale": "kidney_disease",
        "foie_gras": "fatty_liver",
        "colon_irritable": "irritable_bowel",
    }
    return [mapping.get(c, c) for c in conditions]

def _map_medical_conditions_to_french(conditions: list[str]) -> list[str]:
    """Map English medical conditions to French."""
    mapping = {
        "diabetes": "diabète",
        "hypertension": "hypertension",
        "high_cholesterol": "cholestérol_élevé",
        "gout": "goutte",
        "gerd": "rfg",
        "kidney_disease": "maladie_rénale",
        "fatty_liver": "foie_gras",
        "irritable_bowel": "colon_irritable",
    }
    return [mapping.get(c, c) for c in conditions]


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
if ENABLE_MENU_PLANNER and ENABLE_MENU_PLANNING_UI:
    tabs.append("📅 Planning")
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
                        default=_map_medical_conditions_to_french(editing_member.get('medical_conditions', [])),
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
                            "medical_conditions": _map_medical_conditions_to_english(conditions),
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

if ENABLE_MENU_PLANNER and ENABLE_MENU_PLANNING_UI:
    with tabs_ui[tab_index]:
        st.header("📅 Planning de menus")
        st.caption("Générez et gérez des menus hebdomadaires interactifs.")

        # Section: Générer un nouveau draft
        with st.expander("➕ Générer un nouveau menu", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                week_label = st.text_input(
                    "Semaine (format YYYY-Www)",
                    value=st.session_state.get("new_week_label", ""),
                    placeholder="ex: 2026-W16",
                    help="Entrez la semaine au format ISO, ex: 2026-W16"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("🚀 Générer", type="primary", use_container_width=True):
                    if not week_label:
                        st.error("Veuillez entrer une semaine")
                    else:
                        with st.spinner("Génération du menu en cours..."):
                            resp = _api("POST", "/drafts/generate", json={"week_label": week_label})
                        if resp.get("success"):
                            st.success(f"Menu généré: {resp.get('draft_id')}")
                            st.session_state["selected_draft_id"] = resp.get("draft_id")
                            st.rerun()
                        else:
                            st.error(f"Erreur: {resp.get('error')}")

        # Liste des drafts existants
        st.subheader("📋 Menus existants")
        drafts_resp = _api("GET", "/drafts/list")

        if drafts_resp.get("success"):
            drafts = drafts_resp.get("drafts", [])
            if not drafts:
                st.info("Aucun menu généré. Créez-en un nouveau ci-dessus.")
            else:
                # Tableau des drafts
                draft_data = []
                for d in drafts:
                    draft_data.append({
                        "ID": d.get("draft_id", "")[:8] + "...",
                        "Semaine": d.get("week_label", "—"),
                        "Statut": d.get("status", "—"),
                        "Score": f"{d.get('overall_score', 0):.2f}",
                        "Slots": d.get("num_slots", 0),
                        "Généré": d.get("generated_at", "—")[:10] if d.get("generated_at") else "—",
                    })

                st.dataframe(draft_data, use_container_width=True, hide_index=True)

                # Sélection d'un draft pour visualisation/détails
                st.subheader("🔍 Détails d'un menu")
                draft_options = {f"{d.get('week_label', '?')} ({d.get('draft_id', '?')[:8]}...)": d.get("draft_id") for d in drafts}
                selected_label = st.selectbox(
                    "Sélectionner un menu",
                    options=list(draft_options.keys()),
                    index=0 if not st.session_state.get("selected_draft_id") else
                          list(draft_options.values()).index(st.session_state.get("selected_draft_id")) 
                          if st.session_state.get("selected_draft_id") in draft_options.values() else 0
                )
                selected_draft_id = draft_options.get(selected_label)

                if selected_draft_id:
                    # Charger le détail du draft
                    draft_detail = _api("GET", f"/drafts/{selected_draft_id}")

                    if draft_detail.get("success") and draft_detail.get("draft"):
                        draft = draft_detail.get("draft")

                        # Info générale
                        col_info1, col_info2, col_info3 = st.columns(3)
                        col_info1.metric("Semaine", draft.get("week_label", "—"))
                        col_info2.metric("Score global", f"{draft.get('overall_score', 0):.2f}")
                        col_info3.metric("Statut", draft.get("status", "—"))

                        # Affichage du menu par jour
                        st.subheader("📆 Menu de la semaine")
                        days = draft.get("days", [])

                        for day in days:
                            day_date = day.get("date", "—")
                            day_name = day.get("day_name", "—")
                            slots = day.get("slots", [])

                            with st.expander(f"{day_name} ({day_date})"):
                                if not slots:
                                    st.info("Aucun repas prévu ce jour")
                                else:
                                    for slot in slots:
                                        meal_type = slot.get("meal_type", "—")
                                        recipe_name = slot.get("recipe_name", "—")
                                        recipe_slug = slot.get("recipe_slug", "")
                                        score = slot.get("score", 0)
                                        servings = slot.get("servings", 0)

                                        col_slot1, col_slot2, col_slot3 = st.columns([3, 1, 1])

                                        with col_slot1:
                                            meal_emoji = {"breakfast": "🥐", "lunch": "🍽️", "dinner": "🍽️", "snack": "🍎"}.get(meal_type, "🍽️")
                                            st.write(f"**{meal_emoji} {meal_type.upper()}**: {recipe_name}")
                                            if recipe_slug and _MEALIE_BASE:
                                                st.caption(f"[🔗 Voir dans Mealie]({_MEALIE_BASE}/g/home/r/{recipe_slug})")

                                        with col_slot2:
                                            st.caption(f"Score: {score:.2f}")

                                        with col_slot3:
                                            # Bouton pour swap
                                            if st.button("🔄 Changer", key=f"swap_{slot.get('slot_id')}"):
                                                st.session_state["swapping_slot"] = {
                                                    "draft_id": selected_draft_id,
                                                    "day": day_date,
                                                    "meal_type": meal_type,
                                                    "current_recipe": recipe_name,
                                                    "slot_id": slot.get("slot_id")
                                                }
                                                st.rerun()

                        # Section swap de recette
                        if st.session_state.get("swapping_slot"):
                            swap_info = st.session_state.get("swapping_slot")
                            st.divider()
                            st.subheader(f"🔄 Alternatives pour {swap_info['current_recipe']}")

                            # Charger les alternatives
                            alt_resp = _api("GET", f"/drafts/{swap_info['draft_id']}/alternatives", params={
                                "day": swap_info['day'],
                                "meal_type": swap_info['meal_type']
                            })

                            if alt_resp.get("success"):
                                alternatives = alt_resp.get("alternatives", [])
                                if alternatives:
                                    for alt in alternatives:
                                        col_alt1, col_alt2, col_alt3 = st.columns([3, 2, 1])

                                        with col_alt1:
                                            st.write(f"**{alt.get('recipe_name', '—')}**")
                                            st.caption(f"Score: {alt.get('score', 0):.2f} | {alt.get('reason', '')}")

                                        with col_alt2:
                                            nutrition = alt.get("nutrition_per_serving", {})
                                            cal = nutrition.get("calories_kcal", 0)
                                            prot = nutrition.get("protein_g", 0)
                                            st.caption(f"{cal:.0f} kcal | {prot:.1f}g prot")

                                        with col_alt3:
                                            if st.button("✅ Choisir", key=f"choose_{alt.get('recipe_slug')}", use_container_width=True):
                                                # Effectuer le swap
                                                swap_resp = _api("POST", f"/drafts/{swap_info['draft_id']}/swap", params={
                                                    "day": swap_info['day'],
                                                    "meal_type": swap_info['meal_type']
                                                }, json={"new_recipe_slug": alt.get("recipe_slug")})

                                                if swap_resp.get("success"):
                                                    st.success(f"Recette changée !")
                                                    st.session_state.pop("swapping_slot", None)
                                                    st.rerun()
                                                else:
                                                    st.error(f"Erreur: {swap_resp.get('error')}")
                                else:
                                    st.info("Aucune alternative trouvée pour ce slot")

                            if st.button("❌ Annuler le changement"):
                                st.session_state.pop("swapping_slot", None)
                                st.rerun()

                        # Actions sur le draft
                        st.divider()
                        st.subheader("📤 Actions")
                        col_action1, col_action2, col_action3 = st.columns(3)

                        with col_action1:
                            if draft.get("status") == "draft":
                                if st.button("✅ Valider le menu", use_container_width=True):
                                    validate_resp = _api("POST", f"/drafts/{selected_draft_id}/validate")
                                    if validate_resp.get("success"):
                                        st.success("Menu validé !")
                                        st.rerun()
                                    else:
                                        st.error(f"Erreur: {validate_resp.get('error')}")
                            else:
                                st.success("✅ Menu déjà validé")

                        with col_action2:
                            if draft.get("status") == "validated":
                                if st.button("🚀 Pousser vers Mealie", type="primary", use_container_width=True):
                                    push_resp = _api("POST", f"/drafts/{selected_draft_id}/push")
                                    if push_resp.get("success"):
                                        st.success(f"Menu poussé ! ({push_resp.get('pushed_count', 0)} entrées)")
                                    else:
                                        st.error(f"Erreur: {push_resp.get('message')}")

                        with col_action3:
                            if st.button("🗑️ Supprimer", use_container_width=True):
                                delete_resp = _api("DELETE", f"/drafts/{selected_draft_id}")
                                if delete_resp.get("success"):
                                    st.success("Menu supprimé")
                                    st.rerun()
                                else:
                                    st.error(f"Erreur: {delete_resp.get('error')}")

                    else:
                        st.error(f"Erreur chargement du menu: {draft_detail.get('error')}")
        else:
            st.error(f"Erreur chargement des menus: {drafts_resp.get('error')}")

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
        st.write(f"- **Menu Planning UI**: {'✅ Activé' if ENABLE_MENU_PLANNING_UI else '⬜ Désactivé'}")
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
