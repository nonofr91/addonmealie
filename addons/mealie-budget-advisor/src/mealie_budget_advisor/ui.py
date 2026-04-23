"""Streamlit Web UI — Mealie Budget Advisor."""

from __future__ import annotations

import os
import subprocess
import sys

import requests
import streamlit as st

API_URL = os.environ.get("ADDON_API_URL", "http://localhost:8003")
_SECRET = os.environ.get("ADDON_SECRET_KEY", "")
_MEALIE_BASE = os.environ.get("MEALIE_BASE_URL", "").rstrip("/")

_HEADERS: dict[str, str] = {}
if _SECRET:
    _HEADERS["X-Addon-Key"] = _SECRET


def _api(method: str, path: str, **kwargs) -> dict:
    """Effectue un appel API."""
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


# Configuration de la page
st.set_page_config(
    page_title="Mealie Budget Advisor",
    page_icon="💰",
    layout="wide",
)

# En-tête
col_title, col_btn = st.columns([6, 1])
with col_title:
    st.title("💰 Mealie Budget Advisor")
    st.caption("Estimation des coûts et assistance au choix des recettes")

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

# Onglets
tabs = st.tabs(["📊 Statut", "💰 Budget", "� Planning", "�️ Prix", "📈 Coûts"])

# Tab Statut
with tabs[0]:
    st.header("Statut du système")

    status = _api("GET", "/status")
    if status.get("success"):
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Mealie",
            "✅ Connecté" if status.get("mealie_connected") else "❌ Déconnecté",
        )
        col2.metric(
            "Recettes",
            status.get("total_recipes", 0),
        )
        col3.metric(
            "Prix manuels",
            status.get("manual_prices_count", 0),
        )

        # Feature flags
        st.subheader("Feature Flags")
        config = status.get("config", {})
        st.write(f"- **Open Prices**: {'✅ Activé' if config.get('enable_open_prices') else '⬜ Désactivé'}")
        st.write(f"- **Prix manuels**: {'✅ Activé' if config.get('enable_manual_prices') else '⬜ Désactivé'}")
        st.write(f"- **Budget planning**: {'✅ Activé' if config.get('enable_budget_planning') else '⬜ Désactivé'}")
    else:
        st.error(f"Erreur: {status.get('error')}")

# Tab Budget
with tabs[1]:
    st.header("💰 Gestion du budget mensuel")
    st.caption("Définissez et suivez votre budget mensuel")

    col_current, col_list = st.columns([2, 1])

    with col_current:
        st.subheader("Budget actuel")
        current_budget = _api("GET", "/budget")
        if current_budget.get("success") and current_budget.get("budget"):
            budget = current_budget.get("budget", {})
            b1, b2, b3 = st.columns(3)
            b1.metric("Budget total", f"{budget.get('total_budget', 0):.2f} €")
            b2.metric("Budget effectif", f"{budget.get('effective_budget', 0):.2f} €")
            b3.metric("Par repas", f"{budget.get('budget_per_meal', 0):.2f} €")

            st.caption(f"Période: {budget.get('period', {}).get('period_label', '')}")
        else:
            st.info("Aucun budget défini pour ce mois")

    with col_list:
        st.subheader("Historique")
        budgets_list = _api("GET", "/budget/list")
        if budgets_list.get("success"):
            budgets = budgets_list.get("budgets", [])
            if budgets:
                for b in budgets[:5]:
                    with st.expander(f"{b.get('period', {}).get('period_label')}"):
                        st.write(f"Total: {b.get('total_budget', 0):.2f} €")
                        st.write(f"Effectif: {b.get('effective_budget', 0):.2f} €")
            else:
                st.info("Aucun budget sauvegardé")

    st.divider()
    st.subheader("📝 Définir un nouveau budget")

    with st.form("budget_form"):
        col_year, col_month = st.columns(2)
        with col_year:
            year = st.number_input("Année", min_value=2020, max_value=2100, value=2026)
        with col_month:
            month = st.number_input("Mois", min_value=1, max_value=12, value=4)

        total_budget = st.number_input("Budget total (€)", min_value=0.0, value=500.0, step=10.0)
        condiments = st.number_input("Forfait condiments (€)", min_value=0.0, value=20.0, step=5.0)
        meals_per_day = st.number_input("Repas/jour", min_value=1, max_value=10, value=3)
        days_per_month = st.number_input("Jours/mois", min_value=1, max_value=31, value=30)

        if st.form_submit_button("💾 Enregistrer"):
            budget_data = {
                "period": {"year": year, "month": month},
                "total_budget": total_budget,
                "condiments_forfait": condiments,
                "meals_per_day": meals_per_day,
                "days_per_month": days_per_month,
            }
            resp = _api("POST", "/budget", params={}, json=budget_data)
            if resp.get("success"):
                st.success(f"Budget enregistré pour {year}-{month:02d}")
                st.rerun()
            else:
                st.error(f"Erreur: {resp.get('error')}")

# Tab Planning
with tabs[2]:
    st.header("🎯 Planning budget-aware")
    st.caption("Suggestions d'alternatives respectant votre budget")

    # Vérifier si un budget est défini
    current_budget = _api("GET", "/budget")
    if not current_budget.get("success") or not current_budget.get("budget"):
        st.warning("⚠️ Définissez d'abord un budget dans l'onglet 💰 Budget")
        st.stop()

    budget = current_budget.get("budget", {})
    budget_per_meal = budget.get("budget_per_meal", 0)

    # Suggestion d'alternatives
    st.subheader("💡 Suggérer des alternatives moins chères")
    col_slug, col_limit = st.columns([3, 1])
    with col_slug:
        slug = st.text_input("Slug de la recette actuelle", placeholder="ex: carbonara-marmiton")
    with col_limit:
        limit = st.number_input("Max suggestions", min_value=1, max_value=20, value=5)

    if slug and st.button("🔍 Chercher des alternatives", type="primary"):
        with st.spinner("Recherche en cours..."):
            resp = _api("GET", "/planning/suggest-alternatives", params={"current_slug": slug, "limit": limit})
        if resp.get("success"):
            current = resp.get("current_recipe", {})
            suggestions = resp.get("suggestions", [])

            st.info(f"Budget par repas: {budget_per_meal:.2f} €")
            st.caption(f"Coût actuel: {current.get('cost_per_serving', 0):.2f} €")

            if suggestions:
                st.success(f"✅ {len(suggestions)} alternatives respectant le budget trouvées")
                for s in suggestions:
                    with st.expander(f"{s.get('slug')} - {s.get('cost_per_serving'):.2f} €/portion"):
                        st.write(f"Économie: {s.get('savings', 0):.2f} € par portion")
                        st.write(f"Coût: {s.get('cost_per_serving', 0):.2f} €")
            else:
                st.warning("Aucune alternative moins chère trouvée")
        else:
            st.error(f"Erreur: {resp.get('error')}")

    # Rapport coût vs budget
    st.divider()
    st.subheader("📊 Rapport coût vs budget")
    st.caption("Analysez plusieurs recettes par rapport à votre budget")
    slugs_input = st.text_input("Slugs des recettes (séparés par des virgules)", placeholder="ex: carbonara, bolognese, pizza")

    if slugs_input and st.button("Générer le rapport"):
        slugs = [s.strip() for s in slugs_input.split(",") if s.strip()]
        with st.spinner("Calcul en cours..."):
            resp = _api("GET", "/planning/cost-report", params={"slugs": slugs})
        if resp.get("success"):
            report = resp.get("report", {})

            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Recettes analysées", report.get("total_recipes", 0))
            col2.metric("Coût moyen", f"{report.get('avg_cost_per_serving', 0):.2f} €")
            col3.metric("Dans le budget", f"{report.get('within_budget_pct', 0):.0f}%")
            col4.metric("Repas possibles", report.get("meals_possible", 0))

            # Détails
            st.divider()
            col_wb, col_ob = st.columns(2)
            with col_wb:
                st.metric("Recettes dans le budget", report.get("within_budget_count", 0))
            with col_ob:
                st.metric("Recettes hors budget", report.get("over_budget_count", 0))
        else:
            st.error(f"Erreur: {resp.get('error')}")

# Tab Prix
with tabs[3]:
    st.header("🏷️ Gestion des prix")
    st.caption("Prix manuels et recherche Open Prices")

    col_search, col_manual = st.columns(2)

    with col_search:
        st.subheader("🔍 Recherche Open Prices")
        query = st.text_input("Produit à rechercher", placeholder="ex: farine de blé")
        if query and st.button("Rechercher"):
            with st.spinner("Recherche..."):
                resp = _api("GET", "/prices/search", params={"q": query, "limit": 5})
            if resp.get("success"):
                prices = resp.get("prices", [])
                if prices:
                    for p in prices:
                        with st.expander(f"{p.get('product_name')} - {p.get('price')} {p.get('currency')}"):
                            st.write(f"**Produit**: {p.get('product_name')}")
                            st.write(f"**Prix**: {p.get('price')} {p.get('currency')}")
                            st.write(f"**Quantité**: {p.get('quantity')} {p.get('unit')}")
                            if p.get('store_name'):
                                st.write(f"**Magasin**: {p.get('store_name')}")
                else:
                    st.info("Aucun prix trouvé")
            else:
                st.error(f"Erreur: {resp.get('error')}")

    with col_manual:
        st.subheader("✏️ Ajouter un prix manuel")
        with st.form("manual_price"):
            ing_name = st.text_input("Ingrédient", placeholder="ex: farine")
            price = st.number_input("Prix par unité (€)", min_value=0.01, value=1.0, step=0.01)
            unit = st.selectbox("Unité", ["kg", "g", "l", "ml", "unit"])
            store = st.text_input("Magasin (optionnel)", placeholder="ex: Carrefour")

            if st.form_submit_button("💾 Enregistrer"):
                resp = _api(
                    "POST",
                    "/prices/manual",
                    params={
                        "ingredient_name": ing_name,
                        "price_per_unit": price,
                        "unit": unit,
                        "store": store,
                    },
                )
                if resp.get("success"):
                    st.success(f"Prix enregistré pour {ing_name}")
                else:
                    st.error(f"Erreur: {resp.get('error')}")

    # Liste des prix manuels avec édition/suppression
    st.divider()
    st.subheader("📋 Prix manuels enregistrés")
    prices_resp = _api("GET", "/prices/manual")
    if prices_resp.get("success"):
        prices = prices_resp.get("prices", [])
        if prices:
            for p in prices:
                with st.expander(f"💰 {p.get('ingredient_name')} - {p.get('price_per_unit')}€/{p.get('unit')}"):
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    with col1:
                        st.write(f"**Ingrédient**: {p.get('ingredient_name')}")
                    with col2:
                        st.write(f"**Prix**: {p.get('price_per_unit')}€/{p.get('unit')}")
                    with col3:
                        st.write(f"**Magasin**: {p.get('store', '—')}")
                    with col4:
                        if st.button("🗑️", key=f"del_{p.get('ingredient_name')}", help="Supprimer"):
                            # Note: suppression non implémentée côté API pour l'instant
                            st.warning("Suppression à implémenter (TODO)")
        else:
            st.info("Aucun prix manuel enregistré")
    else:
        st.error(f"Erreur: {prices_resp.get('error')}")

# Tab Coûts
with tabs[4]:
    st.header("📈 Coût des recettes")
    st.caption("Calculez le coût de vos recettes Mealie")

    # Calcul coût d'une recette
    st.subheader("🔢 Calculer le coût d'une recette")
    col_slug, col_opts = st.columns([3, 1])
    with col_slug:
        slug = st.text_input("Slug de la recette", placeholder="ex: carbonara-marmiton")
    with col_opts:
        use_open_prices = st.checkbox("Open Prices", value=True, help="Utiliser Open Prices comme fallback")

    if slug and st.button("💰 Calculer le coût", type="primary"):
        with st.spinner("Calcul en cours..."):
            resp = _api("GET", f"/recipes/{slug}/cost", params={"use_open_prices": use_open_prices})
        if resp.get("success"):
            cost = resp.get("cost", {})
            breakdown = cost.get("breakdown", {})

            # Métriques principales
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Coût total", f"{cost.get('total_cost', 0):.2f} €")
            col_m2.metric("Par portion", f"{cost.get('cost_per_serving', 0):.2f} €")
            col_m3.metric(
                "Confiance",
                f"{cost.get('confidence', 0) * 100:.0f}%",
                delta=f"{cost.get('breakdown', {}).get('num_known_prices', 0)}/{cost.get('breakdown', {}).get('num_total_ingredients', 0)} prix connus"
            )
            col_m4.metric("Portions", f"{cost.get('servings', 1)}")

            # Détail des ingrédients
            st.divider()
            st.subheader("📝 Détail des ingrédients")
            ingredients = breakdown.get("ingredients", [])
            if ingredients:
                # Colorer par source de prix
                def get_source_color(source):
                    colors = {
                        "manual": "🟢",
                        "open_prices": "🔵",
                        "estimated": "🟡",
                        "unknown": "⚪",
                    }
                    return colors.get(source, "⚪")

                ing_data = []
                for ing in ingredients:
                    ing_data.append({
                        "Source": get_source_color(ing.get("price_source")),
                        "Ingrédient": ing.get("ingredient_name"),
                        "Quantité": f"{ing.get('quantity')} {ing.get('unit')}",
                        "Coût (€)": f"{ing.get('total_cost'):.2f}",
                        "Confiance": f"{ing.get('confidence') * 100:.0f}%",
                    })

                st.dataframe(ing_data, use_container_width=True, hide_index=True)

                # Répartition des sources
                st.divider()
                sources = cost.get("price_sources_breakdown", {})
                if sources:
                    st.caption("Répartition des sources de prix:")
                    cols = st.columns(len(sources))
                    for i, (src, count) in enumerate(sources.items()):
                        with cols[i]:
                            st.metric(src, count)

            else:
                st.info("Aucun ingrédient trouvé")

            # Comparaison avec le budget
            if _MEALIE_BASE:
                st.divider()
                st.subheader("📊 Comparaison avec le budget")
                current_budget = _api("GET", "/budget")
                if current_budget.get("success") and current_budget.get("budget"):
                    budget = current_budget.get("budget", {})
                    budget_per_meal = budget.get("budget_per_meal", 0)
                    cost_per_serving = cost.get("cost_per_serving", 0)

                    if budget_per_meal > 0:
                        ratio = (cost_per_serving / budget_per_meal) * 100
                        if ratio <= 100:
                            st.success(f"✅ Cette recette respecte le budget ({ratio:.0f}% du budget par repas)")
                        else:
                            st.warning(f"⚠️ Cette recette dépasse le budget ({ratio:.0f}% du budget par repas)")
                    else:
                        st.info("Budget par repas non défini")
                else:
                    st.info("Définissez un budget pour comparer les coûts")

        else:
            st.error(f"Erreur: {resp.get('error')}")

    # Comparaison de recettes
    st.divider()
    st.subheader("⚖️ Comparer plusieurs recettes")
    st.caption("Entrez plusieurs slugs séparés par des virgules")
    slugs_input = st.text_input("Slugs des recettes", placeholder="ex: carbonara, bolognese, pizza")
    per_serving = st.checkbox("Par portion", value=True)

    if slugs_input and st.button("📊 Comparer"):
        slugs = [s.strip() for s in slugs_input.split(",") if s.strip()]
        resp = _api("GET", "/recipes/compare-costs", params={"slugs": slugs, "per_serving": per_serving})
        if resp.get("success"):
            comparison = resp.get("comparison", [])
            if comparison:
                comp_data = [
                    {
                        "Slug": item.get("slug"),
                        "Coût (€)": f"{item.get('cost'):.2f}",
                        "Par portion": "Oui" if item.get("per_serving") else "Non",
                    }
                    for item in comparison
                ]
                st.dataframe(comp_data, use_container_width=True, hide_index=True)
            else:
                st.info("Aucun résultat de comparaison")
        else:
            st.error(f"Erreur: {resp.get('error')}")


def main() -> None:
    """Lanceur CLI pour Streamlit."""
    ui_file = os.path.abspath(__file__)
    port = os.environ.get("ADDON_UI_PORT", "8503")
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
