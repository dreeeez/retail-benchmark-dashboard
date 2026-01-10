"""
Benchmark Dashboard - Gruppe 18
Data Repository

Alle Daten-Loader zentral. Jeder Loader:
1. Holt Store-IDs dynamisch
2. Baut Monatsfilter in SQL (nicht in Pandas!)
3. Cached mit Streamlit
"""

import streamlit as st
import pandas as pd

from src.db.connection import db_connection
from src.db.queries import (
    build_month_filter,
    SQL_EXPORT_MONTHLY,
    SQL_KPI,
    SQL_MARKETING_KPI,
    SQL_MARKETING_BY_CAMPAIGN,
    SQL_COSTS_AGG,
    SQL_COSTS_DETAIL,
    SQL_RENT_REVENUE_M2,
    SQL_SALES_AGG,
    SQL_PRICE_SEGMENT,
)
from src.config.stores import get_store_ids_sql


# =============================================================================
# TAB 1: FINANZPERFORMANCE
# =============================================================================

@st.cache_data(ttl=60)
def load_export_monthly(month: str = 'all'):
    """Lädt Daten aus V_LIST_G18_BENCHMARK_EXPORT_MONTHLY

    Für: Tab Finanzperformance (Trend-Charts) + Tab Export
    """
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month, 'Monat')
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_EXPORT_MONTHLY.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        return df
    except Exception as e:
        st.error(f"Datenbankverbindung fehlgeschlagen: {e}")
        return None


@st.cache_data(ttl=60)
def load_kpi(month: str = 'all'):
    """Lädt KPIs direkt aus V_LIST_G18_BENCHMARK_KPI

    Für: Tab Finanzperformance (KPI-Cards, Margen, Kostenquote)
    ERSETZT: calculate_kpis() - keine Python-Berechnung mehr nötig!
    """
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month)
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_KPI.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        return df
    except Exception:
        return None


# =============================================================================
# TAB 2: MARKETING
# =============================================================================

@st.cache_data(ttl=300)
def load_marketing_kpi(month: str = 'all'):
    """Lädt Marketing-KPIs aus V_LIST_G18_MARKETING_KPI_MONTHLY

    Für: Tab Marketing (ROAS, CPA, Marketing-Quote, Trend)
    """
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month)
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_MARKETING_KPI.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        return df
    except Exception:
        return None


@st.cache_data(ttl=300)
def load_marketing_by_campaign():
    """Lädt ROAS pro Kampagne aus V_LIST_G18_MARKETING_BY_CAMPAIGN

    Für: Tab Marketing (Kampagnen-Breakdown)
    """
    store_ids = get_store_ids_sql()
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_MARKETING_BY_CAMPAIGN.format(store_ids=store_ids),
                conn
            )
        return df
    except Exception:
        return None


# =============================================================================
# TAB 3: KOSTENANALYSE
# =============================================================================

@st.cache_data(ttl=300)
def load_costs_agg(month: str = 'all'):
    """Lädt aggregierte Kosten aus V_LIST_G18_BENCHMARK_COSTS_AGG"""
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month)
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_COSTS_AGG.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        return df
    except Exception:
        return None


@st.cache_data(ttl=300)
def load_costs_detail(month: str = 'all'):
    """Lädt detaillierte Kosten aus V_LIST_G18_BENCHMARK_COSTS_DETAIL"""
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month)
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_COSTS_DETAIL.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        return df
    except Exception:
        return None


@st.cache_data(ttl=300)
def load_rent_and_revenue_per_m2():
    """Lädt Mietkosten und Umsatz pro m²"""
    store_ids = get_store_ids_sql()
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_RENT_REVENUE_M2.format(store_ids=store_ids),
                conn
            )
        return df
    except Exception:
        return None


# =============================================================================
# TAB 4: PRODUKTKATEGORIEN
# =============================================================================

@st.cache_data(ttl=300)
def load_sales_agg(month: str = 'all'):
    """Lädt aggregierte Sales aus V_LIST_G18_BENCHMARK_SALES_AGG"""
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month)
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_SALES_AGG.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        return df
    except Exception:
        return None


@st.cache_data(ttl=300)
def load_price_segment_data(month: str = 'all'):
    """Lädt Umsatzverteilung nach Preissegment"""
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month, "FORMAT(s.ID_CALMONTH, 'yyyy-MM')")
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_PRICE_SEGMENT.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        return df
    except Exception:
        return None


# =============================================================================
# LEGACY WRAPPER (für Abwärtskompatibilität)
# =============================================================================

def load_data():
    """LEGACY: Wrapper für load_export_monthly('all')"""
    return load_export_monthly('all')


def load_sales_agg_data():
    """LEGACY: Wrapper für load_sales_agg('all')"""
    return load_sales_agg('all')


def load_costs_detail_data():
    """LEGACY: Wrapper für load_costs_detail('all')"""
    return load_costs_detail('all')


def load_waterfall_data():
    """LEGACY: Nutzt jetzt load_kpi()"""
    return load_kpi('all')
