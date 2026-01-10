"""
DB Package - Benchmark Dashboard Gruppe 18
Datenbankverbindung, Queries und Repository
"""

from src.db.connection import get_connection, db_connection
from src.db.queries import (
    build_month_filter,
    SQL_EXPORT_MONTHLY,
    SQL_KPI,
    SQL_MARKETING_KPI,
    SQL_MARKETING_BY_CAMPAIGN,
    SQL_COSTS_AGG,
    SQL_COSTS_DETAIL,
    SQL_STORE_DETAILS,
    SQL_SALES_AGG,
    SQL_PRICE_SEGMENT,
)
from src.db.repository import (
    load_export_monthly,
    load_kpi,
    load_marketing_kpi,
    load_marketing_by_campaign,
    load_costs_agg,
    load_costs_detail,
    load_store_details,
    load_sales_agg,
    load_price_segment_data,
    # Legacy wrappers
    load_data,
    load_sales_agg_data,
    load_costs_detail_data,
    load_waterfall_data,
    load_rent_and_revenue_per_m2,
)

__all__ = [
    # Connection
    'get_connection',
    'db_connection',
    # Queries
    'build_month_filter',
    'SQL_EXPORT_MONTHLY',
    'SQL_KPI',
    'SQL_MARKETING_KPI',
    'SQL_MARKETING_BY_CAMPAIGN',
    'SQL_COSTS_AGG',
    'SQL_COSTS_DETAIL',
    'SQL_STORE_DETAILS',
    'SQL_SALES_AGG',
    'SQL_PRICE_SEGMENT',
    # Repository
    'load_export_monthly',
    'load_kpi',
    'load_marketing_kpi',
    'load_marketing_by_campaign',
    'load_costs_agg',
    'load_costs_detail',
    'load_store_details',
    'load_rent_and_revenue_per_m2',
    'load_sales_agg',
    'load_price_segment_data',
    'load_data',
    'load_sales_agg_data',
    'load_costs_detail_data',
    'load_waterfall_data',
]
