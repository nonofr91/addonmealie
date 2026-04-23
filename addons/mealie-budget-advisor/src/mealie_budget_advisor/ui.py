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
tabs = st.tabs(["📊 Statut", "🏷️ Prix", "📈 Coûts"])

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

# Tab Prix
with tabs[1]:
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
with tabs[2]:
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
