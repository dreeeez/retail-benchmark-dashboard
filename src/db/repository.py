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
    build_quarter_filter_db,
    SQL_EXPORT_MONTHLY,
    SQL_KPI,
    SQL_MARKETING_KPI,
    SQL_MARKETING_BY_CAMPAIGN,
    SQL_COSTS_AGG,
    SQL_COSTS_DETAIL,
    SQL_STORE_DETAILS,
    SQL_SALES_AGG,
    SQL_PRICE_SEGMENT,
    SQL_DECKUNGSBEITRAG,
)
# Import von get_store_ids_sql entfernt - wird in Funktionen importiert um zirkuläre Abhängigkeit zu vermeiden


# =============================================================================
# TAB 1: FINANZPERFORMANCE
# =============================================================================

@st.cache_data(ttl=60)
def load_export_monthly(month: str = 'all'):
    """Lädt Daten aus V_LIST_G18_BENCHMARK_EXPORT_MONTHLY

    Für: Tab Finanzperformance (Trend-Charts) + Tab Export
    """
    from src.config.stores import get_store_ids_sql
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
        import traceback
        st.error(f"Details:\n{traceback.format_exc()}")
        return None


@st.cache_data(ttl=60)
def load_kpi(month: str = 'all'):
    """Lädt KPIs direkt aus V_LIST_G18_BENCHMARK_KPI

    Für: Tab Finanzperformance (KPI-Cards, Margen, Kostenquote)
    ERSETZT: calculate_kpis() - keine Python-Berechnung mehr nötig!
    """
    from src.config.stores import get_store_ids_sql
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
    from src.config.stores import get_store_ids_sql
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
    from src.config.stores import get_store_ids_sql
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
    from src.config.stores import get_store_ids_sql
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
    from src.config.stores import get_store_ids_sql
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
def load_store_details(month: str = 'all'):
    """Lädt Store-Details aus V_LIST_G18_STORE_DETAILS

    Für: Tab Kostenanalyse (Filialdetails: Fläche, Miete, Umsatz/m²)
    Bei month='all' werden die Werte über alle Monate aggregiert.
    """
    from src.config.stores import get_store_ids_sql
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month)
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_STORE_DETAILS.format(store_ids=store_ids, month_filter=month_filter),
                conn
            )
        # Bei 'all' müssen wir pro Store aggregieren
        if month == 'all' and df is not None and not df.empty:
            df = df.groupby(['IdStore', 'StoreName']).agg({
                'StoreM2': 'max',
                'Mietkosten': 'sum',
                'Umsatz': 'sum'
            }).reset_index()
            df['UmsatzProM2'] = df.apply(
                lambda row: row['Umsatz'] / row['StoreM2'] if row['StoreM2'] > 0 else 0,
                axis=1
            )
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Store-Details: {e}")
        import traceback
        st.error(f"Details:\n{traceback.format_exc()}")
        return None


# Legacy-Wrapper für Abwärtskompatibilität
def load_rent_and_revenue_per_m2(month: str = 'all'):
    """LEGACY: Wrapper für load_store_details()"""
    return load_store_details(month)


# =============================================================================
# TAB 4: PRODUKTKATEGORIEN
# =============================================================================

@st.cache_data(ttl=300)
def load_sales_agg(month: str = 'all'):
    """Lädt aggregierte Sales aus V_LIST_G18_BENCHMARK_SALES_AGG"""
    from src.config.stores import get_store_ids_sql
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
    from src.config.stores import get_store_ids_sql
    store_ids = get_store_ids_sql()
    month_filter = build_month_filter(month)
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


# =============================================================================
# TAB 5: DECKUNGSBEITRAG
# =============================================================================

@st.cache_data(ttl=300)
def load_deckungsbeitrag(quarter: str = 'all'):
    """Lädt Deckungsbeitragsdaten aus V_LIST_G15_GESAMT_DBSCHEMA_FINAL

    Für: Tab Deckungsbeitrag (DB I, DB II, DB III)

    Args:
        quarter: 'all', 'Q1', 'Q2', 'Q3', 'Q4' oder einzelner Monat wie '2024-01'
    """
    from src.config.stores import get_stores
    stores = get_stores()
    store_names = ", ".join([f"'{s['name']}'" for s in stores])
    quarter_filter = build_quarter_filter_db(quarter)
    try:
        with db_connection() as conn:
            df = pd.read_sql(
                SQL_DECKUNGSBEITRAG.format(store_names=store_names, quarter_filter=quarter_filter),
                conn
            )
        return df
    except Exception:
        return None
