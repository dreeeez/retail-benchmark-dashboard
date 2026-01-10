"""
Charts Package - Benchmark Dashboard Gruppe 18
Alle Plotly-Chart-Funktionen
"""

from src.charts.finance import (
    create_revenue_trend_chart,
    create_revenue_bar_chart,
    create_ebit_chart,
    create_margin_chart,
    create_cost_ratio_chart,
)
from src.charts.marketing import (
    create_marketing_trend_chart,
    create_marketing_quote_chart,
)
from src.charts.categories import (
    create_revenue_distribution_chart,
    create_quantity_heatmap,
    create_margin_by_category_chart,
    create_profit_distribution_chart,
    create_price_segment_chart,
)
from src.charts.base import get_base_layout

__all__ = [
    # Base
    'get_base_layout',
    # Finance
    'create_revenue_trend_chart',
    'create_revenue_bar_chart',
    'create_ebit_chart',
    'create_margin_chart',
    'create_cost_ratio_chart',
    # Marketing
    'create_marketing_trend_chart',
    'create_marketing_quote_chart',
    # Categories
    'create_revenue_distribution_chart',
    'create_quantity_heatmap',
    'create_margin_by_category_chart',
    'create_profit_distribution_chart',
    'create_price_segment_chart',
]
