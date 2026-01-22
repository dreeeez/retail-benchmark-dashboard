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
    create_cost_treemap,
)
from src.charts.marketing import (
    create_marketing_trend_chart,
    create_marketing_quote_chart,
    create_marketing_revenue_share_chart,
    create_campaign_revenue_bar_chart,
    create_campaign_cost_bar_chart,
    create_cpa_monthly_chart,
    create_cpa_top5_per_store_chart,
    create_romi_monthly_chart,
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
    'create_cost_treemap',
    # Marketing
    'create_marketing_trend_chart',
    'create_marketing_quote_chart',
    'create_marketing_revenue_share_chart',
    'create_campaign_revenue_bar_chart',
    'create_campaign_cost_bar_chart',
    'create_cpa_monthly_chart',
    'create_cpa_top5_per_store_chart',
    'create_romi_monthly_chart',
    # Categories
    'create_revenue_distribution_chart',
    'create_quantity_heatmap',
    'create_margin_by_category_chart',
    'create_profit_distribution_chart',
    'create_price_segment_chart',
]
