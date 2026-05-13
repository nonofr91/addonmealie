"""Unified Streamlit UI for Menu Orchestrator."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import requests
import streamlit as st

from mealie_menu_orchestrator.config import MenuOrchestratorConfig

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Mealie Menu Orchestrator",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def get_config() -> MenuOrchestratorConfig:
    """Get configuration."""
    return MenuOrchestratorConfig()


def get_api_url() -> str:
    """Get API URL from config."""
    config = get_config()
    return f"http://{config.api_host}:{config.api_port}"


def call_api(endpoint: str, method: str = "GET", data: dict | None = None) -> dict | None:
    """Call the Menu Orchestrator API."""
    api_url = get_api_url()
    url = f"{api_url}{endpoint}"
    
    headers = {}
    config = get_config()
    if config.addon_secret_key:
        headers["X-Addon-Key"] = config.addon_secret_key
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"API Error: {exc}")
        return None


def render_sidebar() -> None:
    """Render the sidebar with configuration and status."""
    st.sidebar.title("⚙️ Configuration")
    
    config = get_config()
    
    # Connection status
    st.sidebar.subheader("Connection Status")
    try:
        health = call_api("/health")
        if health:
            st.sidebar.success("✅ API Connected")
        else:
            st.sidebar.error("❌ API Disconnected")
    except Exception as exc:
        st.sidebar.error(f"❌ API Error: {exc}")
    
    # Configuration display
    with st.sidebar.expander("View Configuration"):
        st.json(config.to_dict())
    
    # Feature flags
    st.sidebar.subheader("Features")
    st.sidebar.checkbox("Menu Generation", value=config.enable_menu_generation, disabled=True)
    st.sidebar.checkbox("Variety Tracking", value=config.enable_variety_tracking, disabled=True)
    st.sidebar.checkbox("Seasonality", value=config.enable_seasonality, disabled=True)
    
    # Scoring weights
    st.sidebar.subheader("Scoring Weights")
    st.sidebar.slider("Nutrition", 0.0, 1.0, config.weight_nutrition, disabled=True)
    st.sidebar.slider("Budget", 0.0, 1.0, config.weight_budget, disabled=True)
    st.sidebar.slider("Variety", 0.0, 1.0, config.weight_variety, disabled=True)
    st.sidebar.slider("Season", 0.0, 1.0, config.weight_season, disabled=True)


def render_menu_generation() -> None:
    """Render the menu generation tab."""
    st.header("📋 Generate Menu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", date.today())
    
    with col2:
        end_date = st.date_input("End Date", date.today() + timedelta(days=6))
    
    col3, col4 = st.columns(2)
    
    with col3:
        budget_limit = st.number_input("Budget Limit (€)", min_value=0.0, value=200.0, step=10.0)
    
    with col4:
        st.write("Priority Weights (coming soon)")
    
    # Meal types
    st.subheader("Meal Types")
    col5, col6, col7 = st.columns(3)
    with col5:
        include_breakfast = st.checkbox("Breakfast", value=True)
    with col6:
        include_lunch = st.checkbox("Lunch", value=True)
    with col7:
        include_dinner = st.checkbox("Dinner", value=True)
    
    # Generate button
    if st.button("🚀 Generate Menu", type="primary", use_container_width=True):
        with st.spinner("Generating menu..."):
            request_data = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "budget_limit": budget_limit,
                "include_breakfast": include_breakfast,
                "include_lunch": include_lunch,
                "include_dinner": include_dinner,
            }
            
            menu = call_api("/menus/generate", method="POST", data=request_data)
            
            if menu:
                st.success(f"✅ Generated menu with {len(menu.get('entries', []))} entries")
                st.session_state.current_menu = menu
                st.session_state.menu_id = menu.get("id")
                
                # Display menu summary
                st.subheader("Menu Summary")
                col8, col9, col10 = st.columns(3)
                with col8:
                    st.metric("Total Cost", f"€{menu.get('total_cost', 0):.2f}")
                with col9:
                    st.metric("Entries", len(menu.get('entries', [])))
                with col10:
                    st.metric("Nutrition Score", f"{menu.get('scores', {}).get('nutrition', 0):.2f}")


def render_menu_exploration() -> None:
    """Render the menu exploration tab."""
    st.header("🔍 Explore Recipes")
    st.info("Recipe exploration feature coming soon")


def render_quantities() -> None:
    """Render the quantities tab."""
    st.header("🔢 Update Quantities")
    
    if "current_menu" not in st.session_state or not st.session_state.current_menu:
        st.warning("Generate a menu first in the 'Generate' tab")
        return
    
    menu = st.session_state.current_menu
    st.subheader(f"Menu: {menu.get('start_date')} to {menu.get('end_date')}")
    
    entries = menu.get("entries", [])
    
    # Display entries with quantity controls
    quantities = {}
    for i, entry in enumerate(entries):
        with st.expander(f"{entry.get('date')} - {entry.get('meal_type')} - {entry.get('recipe_name')}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"Recipe: {entry.get('recipe_name')}")
            with col2:
                quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    value=entry.get("quantity", 1),
                    key=f"qty_{i}",
                )
                quantities[str(i)] = quantity
    
    # Update button
    if st.button("💾 Update Quantities", type="primary", use_container_width=True):
        menu_id = st.session_state.menu_id
        with st.spinner("Updating quantities..."):
            result = call_api(
                f"/menus/{menu_id}/quantities",
                method="POST",
                data={"quantities": quantities},
            )
            
            if result:
                st.success("✅ Quantities updated")
                st.session_state.current_menu = result
                st.rerun()


def render_history() -> None:
    """Render the history tab."""
    st.header("📚 Menu History")
    st.info("Menu history feature coming soon")


def render_mealie_sync() -> None:
    """Render the Mealie sync tab."""
    st.header("🔄 Sync with Mealie")
    
    if "current_menu" not in st.session_state or not st.session_state.current_menu:
        st.warning("Generate a menu first in the 'Generate' tab")
        return
    
    menu = st.session_state.current_menu
    menu_id = st.session_state.menu_id
    
    st.subheader("Menu Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Cost", f"€{menu.get('total_cost', 0):.2f}")
    with col2:
        st.metric("Entries", len(menu.get('entries', [])))
    
    st.subheader("Scores")
    scores = menu.get('scores', {})
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Nutrition", f"{scores.get('nutrition', 0):.2f}")
        st.metric("Budget", f"{scores.get('budget', 0):.2f}")
    with col4:
        st.metric("Variety", f"{scores.get('variety', 0):.2f}")
        st.metric("Season", f"{scores.get('season', 0):.2f}")
    
    # Push button
    if st.button("📤 Push to Mealie", type="primary", use_container_width=True):
        with st.spinner("Pushing to Mealie..."):
            result = call_api(f"/menus/{menu_id}/push-to-mealie", method="POST")
            
            if result and result.get("success"):
                st.success("✅ Menu pushed to Mealie successfully")
            else:
                st.error("❌ Failed to push menu to Mealie")


def main() -> None:
    """Main UI entry point."""
    st.title("🍽️ Mealie Menu Orchestrator")
    st.markdown("Coordinate nutrition and budget for multi-criteria menu planning")
    
    # Sidebar
    render_sidebar()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Generate",
        "🔍 Explore",
        "🔢 Quantities",
        "📚 History",
        "🔄 Sync",
    ])
    
    with tab1:
        render_menu_generation()
    
    with tab2:
        render_menu_exploration()
    
    with tab3:
        render_quantities()
    
    with tab4:
        render_history()
    
    with tab5:
        render_mealie_sync()


if __name__ == "__main__":
    main()
