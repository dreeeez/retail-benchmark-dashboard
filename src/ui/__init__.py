"""
UI Package - Benchmark Dashboard Gruppe 18
Styles, Components und Layout
"""

from src.ui.styles import DASHBOARD_CSS
from src.ui.components import (
    render_kpi_card,
    chart_header,
    render_store_kpi_card,
    render_cost_card,
    render_html_table,
)
from src.ui.layout import setup_page, render_header, render_month_filter

__all__ = [
    # Styles
    'DASHBOARD_CSS',
    # Components
    'render_kpi_card',
    'chart_header',
    'render_store_kpi_card',
    'render_cost_card',
    'render_html_table',
    # Layout
    'setup_page',
    'render_header',
    'render_month_filter',
]
