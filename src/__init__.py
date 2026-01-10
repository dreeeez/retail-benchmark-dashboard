"""
Benchmark Dashboard - Gruppe 18
Root src package

Für Abwärtskompatibilität: Re-exportiert alles aus den neuen Modulen.
"""

# Re-exports für Abwärtskompatibilität mit alten Imports
from src.config.stores import (
    STORES,
    get_store_ids_sql,
    get_store_color,
    get_store_color_bg,
)
from src.config.settings import COLORS, MONTH_NAMES
from src.config.categories import (
    PRODUCT_CATEGORIES,
    get_category_color,
    COLOR_PALETTE,
    get_color_for_index,
)

from src.db.connection import get_connection
from src.db.repository import (
    load_data,
    load_kpi,
    load_export_monthly,
    load_marketing_kpi,
    load_marketing_by_campaign,
    load_costs_agg,
    load_costs_detail,
    load_rent_and_revenue_per_m2,
    load_sales_agg,
    load_price_segment_data,
)

from src.ui.styles import DASHBOARD_CSS

from src.utils.formatting import format_currency, format_percent
from src.utils.safe import safe_sum, safe_mean, get_trend_arrow
