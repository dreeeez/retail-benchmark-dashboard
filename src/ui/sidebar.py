"""
Benchmark Dashboard - Gruppe 18
Sidebar Components

Persistente Filter und User-Info in der Sidebar
"""

import streamlit as st
from src.config.stores import get_stores
from src.config.settings import MONTH_NAMES
from src.auth.login_ui import get_current_user, logout


def render_sidebar(df, monat_col: str) -> tuple:
    """Rendert die komplette Sidebar mit Filtern und User-Info

    Args:
        df: DataFrame mit allen Daten
        monat_col: Name der Monatsspalte

    Returns:
        tuple: (selected_stores, selected_month)
    """
    with st.sidebar:
        # User Info Section
        render_user_info()

        st.divider()

        # Store Filter
        selected_stores = render_store_filter()

        st.divider()

        # Month Filter
        selected_month = render_month_filter(df, monat_col)

        return selected_stores, selected_month


def render_user_info():
    """Zeigt User-Info + Logout-Button"""
    user = get_current_user()

    if user:
        st.markdown(f"**👤 {user['username']}**")
        st.caption(f"Security Level: {user['security_level']}")

        if st.button("🚪 Logout", width="stretch", type="secondary"):
            logout()


def render_store_filter() -> list:
    """Store Multiselect Filter

    Returns:
        list: Ausgewählte Store-Namen
    """
    stores = get_stores()
    selected = st.multiselect(
        "🏪 Filialen",
        options=[s['name'] for s in stores],
        default=[s['name'] for s in stores],
        key="store_filter"
    )
    return selected


def render_month_filter(df, monat_col: str) -> str:
    """Month Selectbox Filter

    Args:
        df: DataFrame mit Daten
        monat_col: Name der Monatsspalte

    Returns:
        str: Ausgewählter Monat ('all' oder 'YYYY-MM')
    """
    available_months = ['all'] + sorted(df[monat_col].unique().tolist())
    month_options = {m: MONTH_NAMES.get(m, m) for m in available_months}

    selected = st.selectbox(
        "📅 Zeitraum",
        options=list(month_options.keys()),
        format_func=lambda x: month_options[x],
        key="month_filter"
    )
    return selected
