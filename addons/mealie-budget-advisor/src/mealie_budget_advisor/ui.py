"""Streamlit web UI — Mealie Budget Advisor."""

from __future__ import annotations

import os

import requests
import streamlit as st

API_URL = os.environ.get("ADDON_API_URL", "http://localhost:8003")
_SECRET = os.environ.get("ADDON_SECRET_KEY", "")
_MEALIE_BASE = os.environ.get("MEALIE_BASE_URL", "").rstrip("/")

_HEADERS: dict[str, str] = {}
if _SECRET:
    _HEADERS["X-Addon-Key"] = _SECRET


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
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


st.set_page_config(page_title="Mealie Budget Advisor", page_icon="💰", layout="wide")

col_title, col_btn = st.columns([6, 1])
with col_title:
    st.title("💰 Mealie Budget Advisor")
with col_btn:
    if _MEALIE_BASE:
        st.markdown(
            f'<div style="padding-top:1.4rem">'
            f'<a href="{_MEALIE_BASE}" target="_blank" style="'
            f'display:inline-block;padding:0.4rem 0.8rem;background:#FF4B4B;'
            f'color:white;border-radius:6px;text-decoration:none;font-size:0.9rem">'
            f"🏠 Mealie</a></div>",
            unsafe_allow_html=True,
        )

tab_budget, tab_prices, tab_cost, tab_plan = st.tabs(
    ["🗓️ Budget", "🏷️ Prix", "🧮 Coût recette", "📋 Planning"]
)

# --------------------------------------------------------------------------- budget tab

with tab_budget:
    st.header("Budget mensuel")
    st.caption("Définir un budget global pour le mois. Le forfait condiments est retranché pour le calcul.")
    month = st.text_input("Mois (YYYY-MM)", value=_api("GET", "/budget").get("settings", {}).get("month", ""), key="budget_month")

    col_view, col_edit = st.columns(2)
    with col_view:
        if st.button("🔍 Afficher le budget", key="show_budget"):
            payload = _api("GET", "/budget", params={"month": month} if month else None)
            st.session_state["budget_view"] = payload

    view = st.session_state.get("budget_view")
    if view:
        if view.get("success"):
            s = view["settings"]
            st.metric("Budget total", f"{s['total_budget']:.2f} {s['currency']}")
            st.metric("Forfait condiments", f"{s['condiments_forfait']:.2f} {s['currency']}")
            st.metric("Budget effectif", f"{view['effective_budget']:.2f} {s['currency']}")
            st.metric("Par repas", f"{view['budget_per_meal']:.2f} {s['currency']}")
            st.metric("Par jour", f"{view['budget_per_day']:.2f} {s['currency']}")
        else:
            st.error(view.get("error"))

    with col_edit:
        with st.form("budget_form"):
            form_month = st.text_input("Mois", value=month or "", key="budget_form_month")
            total = st.number_input("Budget total (€)", min_value=0.0, value=400.0, step=10.0)
            forfait = st.number_input("Forfait condiments (€)", min_value=0.0, value=20.0, step=5.0)
            meals_per_day = st.number_input("Repas / jour", min_value=1, max_value=6, value=3)
            days_per_month = st.number_input("Jours / mois", min_value=28, max_value=31, value=30)
            currency = st.text_input("Devise", value="EUR", max_chars=3)
            submit = st.form_submit_button("💾 Enregistrer")
            if submit:
                result = _api(
                    "POST",
                    "/budget",
                    json={
                        "settings": {
                            "month": form_month,
                            "total_budget": total,
                            "condiments_forfait": forfait,
                            "meals_per_day": int(meals_per_day),
                            "days_per_month": int(days_per_month),
                            "currency": currency.upper(),
                        }
                    },
                )
                if result.get("success"):
                    st.success(f"Budget enregistré pour {form_month}")
                else:
                    st.error(result.get("error"))

# --------------------------------------------------------------------------- prices tab

with tab_prices:
    st.header("Base de prix manuels")
    st.caption("Ajouter un prix pour un ingrédient (par kg, par litre, ou par pièce).")

    with st.form("price_form"):
        name = st.text_input("Nom de l'ingrédient (normalisé)")
        unit = st.selectbox("Unité de vente", ["kg", "g", "l", "ml", "unit"])
        price_val = st.number_input("Prix", min_value=0.0, value=2.0, step=0.1)
        currency = st.text_input("Devise", value="EUR", max_chars=3)
        note = st.text_input("Note (optionnel)")
        submit = st.form_submit_button("💾 Ajouter / mettre à jour")
        if submit and name.strip():
            result = _api(
                "POST",
                "/prices/manual",
                json={
                    "price": {
                        "ingredient_name": name,
                        "unit": unit,
                        "price_per_unit": price_val,
                        "currency": currency.upper(),
                        "note": note or None,
                    }
                },
            )
            if result.get("success"):
                st.success(f"Prix enregistré pour {name}")
            else:
                st.error(result.get("error"))

    if st.button("🔄 Rafraîchir la liste"):
        st.session_state["price_list"] = _api("GET", "/prices/manual")

    price_list = st.session_state.get("price_list") or _api("GET", "/prices/manual")
    if price_list.get("success"):
        items = price_list.get("items", [])
        if not items:
            st.info("Aucun prix manuel enregistré pour le moment.")
        else:
            st.dataframe(items, use_container_width=True)
    else:
        st.error(price_list.get("error"))

    st.divider()
    st.subheader("Recherche Open Prices")
    search_q = st.text_input("Recherche produit", key="open_prices_q")
    if st.button("🔍 Rechercher", key="open_prices_btn") and search_q.strip():
        out = _api("GET", "/prices/search", params={"q": search_q})
        if out.get("success"):
            st.write(f"Médiane: {out.get('median')}")
            st.dataframe(out.get("items", []), use_container_width=True)
        else:
            st.error(out.get("error"))

# --------------------------------------------------------------------------- cost tab

with tab_cost:
    st.header("Coût d'une recette")
    st.caption(
        "Le coût est calculé à partir des ingrédients. "
        "Vous pouvez ensuite le publier dans Mealie (`extras.cout_*`) "
        "pour l'afficher sur la fiche recette et le modifier manuellement."
    )
    slug = st.text_input("Slug de la recette Mealie")
    col_calc, col_sync = st.columns([1, 1])
    with col_calc:
        if st.button("🧮 Calculer", key="cost_calc") and slug.strip():
            st.session_state["cost_result"] = _api("GET", f"/recipes/{slug}/cost")
    with col_sync:
        if st.button("📤 Publier dans Mealie", key="cost_sync", help="Écrit cout_* dans extras") and slug.strip():
            st.session_state["cost_sync_result"] = _api(
                "POST", f"/recipes/{slug}/sync-cost",
            )

    result = st.session_state.get("cost_result")
    if result:
        if result.get("success"):
            cost = result["cost"]
            st.metric("Coût total", f"{cost['total_cost']:.2f} {cost['currency']}")
            st.metric("Par portion", f"{cost['cost_per_serving']:.2f} {cost['currency']}")
            st.metric("Confiance", f"{cost['confidence'] * 100:.0f}%")
            st.dataframe(cost["ingredient_breakdown"], use_container_width=True)
        else:
            st.error(result.get("error"))

    sync_result = st.session_state.get("cost_sync_result")
    if sync_result:
        if sync_result.get("success"):
            msg = f"Publié dans Mealie (mois {sync_result.get('month')})"
            if sync_result.get("override_preserved"):
                msg += " — override manuel préservé"
            st.success(msg)
        else:
            st.error(sync_result.get("error"))

# --------------------------------------------------------------------------- plan tab

with tab_plan:
    st.header("Planning budget-aware")
    st.caption(
        "Sélectionne les recettes les moins chères qui tiennent dans le budget effectif. "
        "Si une recette a un `cout_manuel_par_portion` dans ses extras Mealie, c'est ce prix qui est utilisé."
    )
    plan_month = st.text_input("Mois (optionnel)", key="plan_month")
    meals_target = st.number_input("Nombre de repas à planifier", min_value=1, max_value=200, value=21)

    col_gen, col_refresh = st.columns([1, 1])
    with col_gen:
        if st.button("🚀 Générer", key="plan_btn"):
            st.session_state["plan_result"] = _api(
                "POST",
                "/plan/budget-aware",
                json={
                    "month": plan_month or None,
                    "meals_target": int(meals_target),
                },
            )
    with col_refresh:
        if st.button(
            "🔄 Rafraîchir coûts Mealie",
            key="refresh_all_btn",
            help="Recalcule et écrit cout_* pour toutes les recettes",
        ):
            st.session_state["refresh_result"] = _api(
                "POST",
                "/recipes/refresh-costs",
                json={"month": plan_month or None},
            )

    refresh = st.session_state.get("refresh_result")
    if refresh:
        if refresh.get("success"):
            rpt = refresh["report"]
            st.success(
                f"Coûts rafraîchis pour {rpt.get('month')}: "
                f"{rpt.get('updated', 0)} mises à jour, "
                f"{rpt.get('skipped', 0)} ignorées, "
                f"{len(rpt.get('failed', []))} échecs, "
                f"{rpt.get('override_preserved', 0)} overrides préservés"
            )
        else:
            st.error(refresh.get("error"))

    result = st.session_state.get("plan_result")
    if result:
        if result.get("success"):
            report = result["report"]
            st.metric("Coût total", f"{report['total_cost']:.2f} {report['currency']}")
            st.metric("Budget cible", f"{report['effective_budget']:.2f} {report['currency']}")
            st.metric("Écart", f"{report['delta']:.2f} {report['currency']}")
            if report.get("over_budget"):
                st.warning("Le plan dépasse le budget cible.")
            st.dataframe(report.get("recipes", []), use_container_width=True)
        else:
            st.error(result.get("error"))
