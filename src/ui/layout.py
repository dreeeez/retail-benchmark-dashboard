"""
Benchmark Dashboard - Gruppe 18
Layout-Komponenten

Seiten-Setup, Header und Filter.
"""

import streamlit as st

from src.ui.styles import DASHBOARD_CSS
from src.config.stores import STORES
from src.config.settings import MONTH_NAMES


def setup_page():
    """Konfiguriert die Streamlit-Seite"""
    st.set_page_config(
        page_title="Gruppe 18 - Benchmark Dashboard",
        page_icon="📊",
        layout="wide"
    )
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


def render_header():
    """Rendert den Dashboard-Header"""
    st.markdown("""
    <div class="main-header">
        <h1>Benchmark Dashboard</h1>
        <div class="header-subtitle">Gruppe 18</div>
    </div>
    """, unsafe_allow_html=True)


def render_month_filter(available_months: list) -> str:
    """Rendert den Monatsfilter und gibt ausgewählten Monat zurück

    Args:
        available_months: Liste der verfügbaren Monate aus den Daten

    Returns:
        Ausgewählter Monat ('all' oder 'YYYY-MM')
    """
    col_filter, col_indicator = st.columns([1, 3])

    month_options = {m: MONTH_NAMES.get(m, m) for m in available_months}

    with col_filter:
        selected_month = st.selectbox(
            "Zeitraum:",
            options=list(month_options.keys()),
            format_func=lambda x: month_options[x]
        )

    with col_indicator:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="month-indicator">{month_options[selected_month]}</div>',
            unsafe_allow_html=True
        )

    return selected_month
