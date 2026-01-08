"""
Benchmark Dashboard - Gruppe 18
Streamlit-basiertes Web-Dashboard für den Filialvergleich
VERSION 2: Modulares Multi-Store System
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.db_connect import get_connection
from src.config import MONTH_NAMES
from src.styles import DASHBOARD_CSS
from src.utils import format_currency, safe_sum, safe_mean
from src.stores_config import STORES, PRODUCT_CATEGORIES, get_category_color

# =============================================================================
# SEITEN-KONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Gruppe 18 - Benchmark Dashboard",
    page_icon="📊",
    layout="wide"
)

# Dark Theme CSS
st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

# Dynamischer Header basierend auf konfigurierten Stores
store_names = " vs. ".join([s['name'] for s in STORES])
st.markdown(f"""
<div class="main-header">
    <h1>Benchmark Dashboard</h1>
    <p>Gruppe 18 | {store_names}</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# DATEN LADEN
# =============================================================================
@st.cache_data(ttl=60)  # Cache auf 60 Sekunden reduziert für schnellere Updates
def load_data():
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Datenbankverbindung fehlgeschlagen: {e}")
        return None

@st.cache_data(ttl=300)
def load_sales_agg_data():
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM list_views.V_LIST_G18_BENCHMARK_SALES_AGG", conn)
        conn.close()
        return df
    except:
        return None

@st.cache_data(ttl=300)
def load_costs_detail_data():
    """Lädt detaillierte Kostendaten für Kostenanalyse"""
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM list_views.V_LIST_G18_BENCHMARK_COSTS_DETAIL", conn)
        conn.close()
        return df
    except:
        return None

@st.cache_data(ttl=300)
def load_waterfall_data():
    """Lädt Waterfall-Daten (Umsatz -> Kosten -> Gewinn)"""
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM list_views.V_LIST_G18_BENCHMARK_WATERFALL", conn)
        conn.close()
        return df
    except:
        return None

@st.cache_data(ttl=300)
def load_marketing_costs():
    """Lädt Marketing-Kosten direkt aus V_LIST_MONTHLY_COSTS"""
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT
                ID_STORE,
                SUM(WertEUR) AS MarketingKosten
            FROM dbo.V_LIST_MONTHLY_COSTS
            WHERE Kostenkategorie = 'Marketing Campaign'
            AND ID_STORE IN (3, 5, 14)
            GROUP BY ID_STORE
        """, conn)
        conn.close()
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def load_marketing_monthly():
    """Lädt monatliche Marketing-Kosten für Trend-Analyse"""
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT
                c.ID_STORE,
                c.StoreName,
                FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS Monat,
                SUM(c.WertEUR) AS MarketingEur
            FROM dbo.V_LIST_MONTHLY_COSTS c
            WHERE c.Kostenkategorie LIKE 'Marketing Campaign%'
            AND c.ID_STORE IN (3, 5, 14)
            GROUP BY c.ID_STORE, c.StoreName, FORMAT(c.ID_CALMONTH, 'yyyy-MM')
            ORDER BY c.ID_STORE, FORMAT(c.ID_CALMONTH, 'yyyy-MM')
        """, conn)
        conn.close()
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def load_marketing_roas_data():
    """Lädt Daten für korrekte ROAS-Berechnung:
    - Umsatz MIT Marketing (ID_CAMPAIGN != 0)
    - Umsatz OHNE Marketing (ID_CAMPAIGN = 0)
    - Marketing-Kosten
    - Stückzahlen für CPA
    """
    try:
        conn = get_connection()
        # Umsatz mit und ohne Marketing aus Sales + Stückzahlen
        umsatz_df = pd.read_sql("""
            SELECT
                so.STORE_LOCATION AS StoreName,
                s.ID_STORE,
                SUM(CASE WHEN s.ID_CAMPAIGN != 0 THEN s.RevenueEUR ELSE 0 END) as UmsatzMitMarketing,
                SUM(CASE WHEN s.ID_CAMPAIGN = 0 THEN s.RevenueEUR ELSE 0 END) as UmsatzOhneMarketing,
                SUM(s.RevenueEUR) as UmsatzGesamt,
                SUM(CASE WHEN s.ID_CAMPAIGN != 0 THEN s.SalesAmount ELSE 0 END) as StueckMitMarketing,
                SUM(s.SalesAmount) as StueckGesamt
            FROM dbo.V_LIST_MONTHLY_SALES s
            INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
            WHERE s.ID_STORE IN (3, 5, 14)
            GROUP BY so.STORE_LOCATION, s.ID_STORE
        """, conn)

        # Marketing-Kosten
        marketing_df = pd.read_sql("""
            SELECT
                so.STORE_LOCATION AS StoreName,
                SUM(c.WertEUR) as MarketingKosten
            FROM dbo.V_LIST_MONTHLY_COSTS c
            INNER JOIN dbo.T_SALESORG so ON c.ID_STORE = so.SALESORG_ID
            WHERE c.Kostenkategorie LIKE 'Marketing Campaign%'
            AND c.ID_STORE IN (3, 5, 14)
            GROUP BY so.STORE_LOCATION
        """, conn)

        conn.close()

        # Merge
        merged = umsatz_df.merge(marketing_df, on='StoreName')
        # ROAS berechnen: Umsatz MIT Marketing / Marketing-Kosten
        merged['ROAS'] = merged['UmsatzMitMarketing'] / merged['MarketingKosten']
        # CPA berechnen: Marketing-Kosten / Stück mit Marketing
        merged['CPA'] = merged['MarketingKosten'] / merged['StueckMitMarketing']
        return merged
    except Exception as e:
        return None

@st.cache_data(ttl=60)
def load_revenue_with_without_campaign_monthly():
    """Lädt monatlichen Umsatz MIT vs OHNE Kampagne für Jahresverlauf-Graph

    Kampagne = NULL bedeutet OHNE Werbung
    Kampagne != NULL bedeutet MIT Werbung
    """
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT
                s.ID_STORE,
                so.STORE_LOCATION AS StoreName,
                FORMAT(s.ID_CALMONTH, 'yyyy-MM') AS Monat,
                SUM(CASE WHEN s.ID_CAMPAIGN IS NULL OR s.ID_CAMPAIGN = 0 THEN s.RevenueEUR ELSE 0 END) AS UmsatzOhneKampagne,
                SUM(CASE WHEN s.ID_CAMPAIGN IS NOT NULL AND s.ID_CAMPAIGN != 0 THEN s.RevenueEUR ELSE 0 END) AS UmsatzMitKampagne
            FROM dbo.V_LIST_MONTHLY_SALES s
            INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
            WHERE s.ID_STORE IN (3, 5, 14)
            GROUP BY s.ID_STORE, so.STORE_LOCATION, FORMAT(s.ID_CALMONTH, 'yyyy-MM')
            ORDER BY s.ID_STORE, FORMAT(s.ID_CALMONTH, 'yyyy-MM')
        """, conn)
        conn.close()
        return df
    except Exception as e:
        st.session_state['debug_revenue_error'] = str(e)
        return None

@st.cache_data(ttl=60)
def load_campaign_revenue_data():
    """Lädt Umsatz pro Marketing-Kampagne pro Filiale mit Kosten und ROAS

    Einfacher Ansatz:
    1. Umsatz pro Kampagne aus V_LIST_MONTHLY_SALES (ID_CAMPAIGN != 0)
    2. Kosten pro Kampagne aus V_LIST_MONTHLY_COSTS (Kostenkategorie enthält Campaign ID)
    3. ROAS = Umsatz / Kosten
    """
    import re
    try:
        conn = get_connection()

        # Umsatz pro Kampagne pro Store
        umsatz_df = pd.read_sql("""
            SELECT
                s.ID_STORE,
                so.STORE_LOCATION AS StoreName,
                s.ID_CAMPAIGN,
                c.CAMP_TYPE + ': ' + c.CAMP_NAME AS Kampagne,
                SUM(s.RevenueEUR) AS Umsatz
            FROM dbo.V_LIST_MONTHLY_SALES s
            INNER JOIN dbo.T_CAMPAIGN c ON s.ID_CAMPAIGN = c.ID_CAMPAIGN
            INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
            WHERE s.ID_STORE IN (3, 5, 14)
            AND s.ID_CAMPAIGN != 0
            GROUP BY s.ID_STORE, so.STORE_LOCATION, s.ID_CAMPAIGN, c.CAMP_TYPE, c.CAMP_NAME
        """, conn)

        # Lade alle Marketing-Kosten - Campaign-ID ist in BESCHREIBUNG!
        # Format Beschreibung: "Marketing Campaign [22]: Google Ads" -> ID = 22
        all_marketing_costs = pd.read_sql("""
            SELECT ID_STORE, Beschreibung, SUM(WertEUR) as Kosten
            FROM dbo.V_LIST_MONTHLY_COSTS
            WHERE Kostenkategorie = 'Marketing Campaign'
            AND ID_STORE IN (3, 5, 14)
            GROUP BY ID_STORE, Beschreibung
        """, conn)

        # Debug: Speichere alle Marketing-Kategorien
        st.session_state['debug_kategorien'] = all_marketing_costs.copy()

        conn.close()

        # Extrahiere Campaign-ID aus Beschreibung mit Python Regex
        def extract_campaign_id(beschreibung):
            match = re.search(r'\[(\d+)\]', str(beschreibung))
            if match:
                return int(match.group(1))
            return None

        if not all_marketing_costs.empty:
            all_marketing_costs['ID_CAMPAIGN'] = all_marketing_costs['Beschreibung'].apply(extract_campaign_id)
            # Filtere nur Zeilen mit gültiger Campaign-ID
            kosten_df = all_marketing_costs[all_marketing_costs['ID_CAMPAIGN'].notna()].copy()
            kosten_df = kosten_df.groupby(['ID_STORE', 'ID_CAMPAIGN'])['Kosten'].sum().reset_index()
            kosten_df['ID_CAMPAIGN'] = kosten_df['ID_CAMPAIGN'].astype(int)
        else:
            kosten_df = pd.DataFrame(columns=['ID_STORE', 'ID_CAMPAIGN', 'Kosten'])

        # Debug: Speichere Kosten-Info
        st.session_state['debug_kosten_df'] = kosten_df if not kosten_df.empty else pd.DataFrame()

        if umsatz_df.empty:
            return None

        # Merge Umsatz mit Kosten
        merged = umsatz_df.merge(
            kosten_df,
            on=['ID_STORE', 'ID_CAMPAIGN'],
            how='left'
        )
        merged['Kosten'] = merged['Kosten'].fillna(0)

        # Gesamtumsatz pro Store für Anteil-Berechnung
        store_totals = merged.groupby('ID_STORE')['Umsatz'].sum().reset_index()
        store_totals.columns = ['ID_STORE', 'GesamtUmsatz']
        merged = merged.merge(store_totals, on='ID_STORE')

        # Anteil und ROAS berechnen
        merged['AnteilProzent'] = (merged['Umsatz'] / merged['GesamtUmsatz'] * 100).round(2)
        merged['ROAS'] = merged.apply(
            lambda row: round(row['Umsatz'] / row['Kosten'], 2) if row['Kosten'] > 0 else None,
            axis=1
        )

        # Sortieren nach Store und Umsatz
        merged = merged.sort_values(['ID_STORE', 'Umsatz'], ascending=[True, False])

        return merged

    except Exception as e:
        st.session_state['debug_error'] = str(e)
        return None

@st.cache_data(ttl=300)
def load_price_segment_data():
    """Lädt Umsatzverteilung nach Preissegment (Premium, Standard, Budget) pro Filiale"""
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT
                s.ID_STORE,
                so.STORE_LOCATION AS StoreName,
                ps.SEGMENT AS Preissegment,
                SUM(s.RevenueEUR) AS Umsatz,
                SUM(s.SalesAmount) AS Stueckzahl
            FROM dbo.V_LIST_MONTHLY_SALES s
            INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
            INNER JOIN dbo.T_MATERIAL m ON s.ID_MATERIAL = m.ID_MAT
            INNER JOIN dbo.T_PRICE_SEGMENT ps ON m.ID_SEGMENT = ps.ID_SEGMENT
            WHERE s.ID_STORE IN (3, 5, 14)
            GROUP BY s.ID_STORE, so.STORE_LOCATION, ps.SEGMENT
            ORDER BY s.ID_STORE, SUM(s.RevenueEUR) DESC
        """, conn)
        conn.close()
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def load_location_data():
    """Lädt Filialdaten aus T_LOCATION für Mietberechnung"""
    try:
        conn = get_connection()
        # Lade nur die Benchmark-Filialen (IDs 3, 5, 14)
        df = pd.read_sql("""
            SELECT
                l.ID_STORE,
                s.STORE_LOCATION AS StoreName,
                l.LOC_SIZE_M2,
                l.LOC_RENT_EUR_M2,
                l.LOC_NEBENKOSTEN_EUR,
                (l.LOC_SIZE_M2 * (l.LOC_RENT_EUR_M2 + l.LOC_NEBENKOSTEN_EUR)) AS MonthlyRentCalculated
            FROM dbo.T_LOCATION l
            INNER JOIN dbo.T_SALESORG s ON l.ID_STORE = s.SALESORG_ID
            WHERE l.ID_STORE IN (3, 5, 14)
        """, conn)
        conn.close()
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def load_rent_and_revenue_per_m2():
    """Lädt Mietkosten und berechnet Umsatz pro m² für jede Filiale"""
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT
                l.ID_STORE,
                so.STORE_LOCATION AS StoreName,
                l.LOC_SIZE_M2 AS StoreM2,
                -- Mietkosten aus V_LIST_MONTHLY_COSTS (Summe aller Monthly Rent)
                ISNULL(rent.MietkostenGesamt, 0) AS MietkostenGesamt,
                -- Umsatz aus V_LIST_MONTHLY_SALES
                ISNULL(sales.UmsatzGesamt, 0) AS UmsatzGesamt,
                -- Umsatz pro m²
                CASE
                    WHEN l.LOC_SIZE_M2 > 0 THEN ISNULL(sales.UmsatzGesamt, 0) / l.LOC_SIZE_M2
                    ELSE 0
                END AS UmsatzProM2
            FROM dbo.T_LOCATION l
            INNER JOIN dbo.T_SALESORG so ON l.ID_STORE = so.SALESORG_ID
            LEFT JOIN (
                SELECT ID_STORE, SUM(WertEUR) AS MietkostenGesamt
                FROM dbo.V_LIST_MONTHLY_COSTS
                WHERE Kostenkategorie = 'Monthly Rent'
                AND ID_STORE IN (3, 5, 14)
                GROUP BY ID_STORE
            ) rent ON l.ID_STORE = rent.ID_STORE
            LEFT JOIN (
                SELECT ID_STORE, SUM(RevenueEUR) AS UmsatzGesamt
                FROM dbo.V_LIST_MONTHLY_SALES
                WHERE ID_STORE IN (3, 5, 14)
                GROUP BY ID_STORE
            ) sales ON l.ID_STORE = sales.ID_STORE
            WHERE l.ID_STORE IN (3, 5, 14)
        """, conn)
        conn.close()
        return df
    except Exception as e:
        return None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_store_data(df, filiale_col, store_name):
    """Filtert DataFrame für einen Store"""
    return df[df[filiale_col].str.contains(store_name, case=False, na=False)]

def calculate_kpis(store_df):
    """Berechnet KPIs für einen Store

    Gesamtkosten-Formel:
    Gesamtkosten = Wareneinsatz (TransferPrice) + OPEX
    OPEX = HumanResources + FacilityManagement + Logistics + Marketing

    Kostenquote = Gesamtkosten / Umsatz × 100
    """
    umsatz = safe_sum(store_df, 'umsatz')
    bruttogewinn = safe_sum(store_df, 'bruttogewinn')

    # Wareneinsatz = Umsatz - Bruttogewinn (= TransferPriceEUR)
    wareneinsatz = umsatz - bruttogewinn

    # Einzelne Kostenkomponenten (OPEX)
    personalkosten = safe_sum(store_df, 'humanresources')  # HumanResourcesEur
    betriebskosten = safe_sum(store_df, 'facilitymanagement')  # FacilityManagementEur (Miete)
    beschaffungskosten = safe_sum(store_df, 'logistics')  # LogisticsEur
    marketing = safe_sum(store_df, 'marketing')  # MarketingEur

    # Gesamtkosten = Wareneinsatz (TransferPrice) + OPEX
    # OPEX = Personal + Miete + Logistik + Marketing
    gesamtkosten = wareneinsatz + personalkosten + betriebskosten + beschaffungskosten + marketing

    return {
        'umsatz': umsatz,
        'nettogewinn': safe_sum(store_df, 'nettogewinn'),
        'marge': safe_mean(store_df, 'nettogewinnmarge'),
        'bruttogewinn': bruttogewinn,
        'kosten': gesamtkosten,  # TransferPrice + OPEX
        'wareneinsatz': wareneinsatz,  # TransferPrice
        'personalkosten': personalkosten,  # HumanResources
        'betriebskosten': betriebskosten,  # FacilityManagement
        'beschaffungskosten': beschaffungskosten,  # Logistics
        'marketingkosten': marketing  # Marketing
    }

def render_kpi_card(title, value, color, comparison=None):
    """Rendert eine KPI-Karte"""
    comp_html = ""
    if comparison:
        comp_class = "kpi-comparison-positive" if comparison > 0 else "kpi-comparison-negative" if comparison < 0 else "kpi-comparison-neutral"
        comp_text = f"+{comparison:.1f}%" if comparison > 0 else f"{comparison:.1f}%"
        comp_html = f'<div class="{comp_class}">{comp_text}</div>'

    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div style="font-size: 1.5em; font-weight: bold; color: {color}; height: 50px; line-height: 50px;">{value}</div>
        {comp_html}
    </div>
    """

def chart_header(title, tooltip_text):
    """Rendert einen Chart-Titel mit Info-Tooltip"""
    return f"""
    <div class="chart-header">
        <h3 class="chart-title">{title}</h3>
        <div class="info-tooltip">
            i
            <span class="tooltip-text">{tooltip_text}</span>
        </div>
    </div>
    """

# =============================================================================
# HAUPTANWENDUNG
# =============================================================================
df = load_data()

if df is not None and len(df) > 0:
    cols = df.columns.tolist()

    # Spaltennamen finden
    monat_col = next((c for c in cols if 'monat' in c.lower() or 'month' in c.lower()), None)
    filiale_col = next((c for c in cols if 'filial' in c.lower() or 'store' in c.lower() or 'gruppe' in c.lower()), None)

    if monat_col and filiale_col:
        # Alle verfügbaren Sections definieren
        dashboard_all_sections = ['KPI-Karten', 'Margen-Vergleich', 'Kostenstruktur']
        cat_all_sections = ['Umsatzverteilung (Donut)', 'Stückzahl-Anteil (%)', 'Bruttomarge (%)',
                            'Bruttogewinn-Anteil (%)', 'Umsatz-Trend']

        # Filter Section
        col_filter, col_indicator = st.columns([1, 3])

        with col_filter:
            available_months = ['all'] + sorted(df[monat_col].unique().tolist())
            month_options = {m: MONTH_NAMES.get(m, m) for m in available_months}
            selected_month = st.selectbox("Zeitraum:", options=list(month_options.keys()),
                                          format_func=lambda x: month_options[x])

        with col_indicator:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<div class="month-indicator">{month_options[selected_month]}</div>', unsafe_allow_html=True)

        # Session State für Multiselects initialisieren
        if 'dashboard_multiselect' not in st.session_state:
            st.session_state['dashboard_multiselect'] = dashboard_all_sections.copy()
        if 'cat_multiselect' not in st.session_state:
            st.session_state['cat_multiselect'] = cat_all_sections.copy()

        # Daten filtern
        filtered_df = df if selected_month == 'all' else df[df[monat_col] == selected_month]

        # =================================================================
        # STORES DYNAMISCH ERKENNEN
        # =================================================================
        available_stores = filtered_df[filiale_col].unique().tolist()

        # Marketing-Kosten aus V_LIST_MONTHLY_COSTS laden
        marketing_df = load_marketing_costs()
        marketing_costs_by_store = {}
        if marketing_df is not None and not marketing_df.empty:
            for _, row in marketing_df.iterrows():
                marketing_costs_by_store[int(row['ID_STORE'])] = row['MarketingKosten']

        # Store-Daten und KPIs für alle Stores berechnen
        stores_data = {}
        stores_kpis = {}

        for store in STORES:
            # Finde passenden Store-Namen in den Daten
            matching_name = next((s for s in available_stores if store['name'].lower() in s.lower()), None)
            if matching_name:
                stores_data[store['name']] = filtered_df[filtered_df[filiale_col] == matching_name]
                stores_kpis[store['name']] = calculate_kpis(stores_data[store['name']])

        active_stores = [s for s in STORES if s['name'] in stores_data]

        # =================================================================
        # TABS
        # =================================================================
        tab_main, tab_marketing, tab_costs, tab_categories, tab_data = st.tabs([
            "📊 Finanzperformance", "📢 Marketing", "💸 Kostenanalyse", "🚲 Produktkategorien", "📋 Export"
        ])

        if len(active_stores) >= 2:
            # =============================================================
            # TAB 1: DASHBOARD
            # =============================================================
            with tab_main:
                # Settings-Button oben rechts im Tab
                col_dash_space, col_dash_settings = st.columns([15, 1])
                with col_dash_settings:
                    with st.popover("⚙️"):
                        st.markdown("**Anzeigeoptionen**")
                        if st.button("Alle anzeigen", key="reset_dashboard"):
                            st.session_state['dashboard_multiselect'] = dashboard_all_sections.copy()
                            st.rerun()
                        st.multiselect(
                            "Bereiche:",
                            options=dashboard_all_sections,
                            key="dashboard_multiselect",
                            label_visibility="collapsed"
                        )

                selected_dashboard_sections = st.session_state.get('dashboard_multiselect', dashboard_all_sections)

                # KPI Cards - Übersichtlich nach Filiale gruppiert
                if 'KPI-Karten' in selected_dashboard_sections:
                    st.subheader("📈 Vergleich Umsatz & Operativer Gewinn")
                    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

                    kpi_cols = st.columns(len(active_stores))

                    for idx, store in enumerate(active_stores):
                        kpis = stores_kpis[store['name']]

                        with kpi_cols[idx]:
                            st.markdown(f"""
                            <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                        border-radius: 15px; padding: 20px;">
                                <div style="font-size: 1.2em; font-weight: bold; color: {store['color']}; text-align: center; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                                    {store['name']}
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.75em; text-transform: uppercase;">Umsatz</div>
                                        <div style="color: white; font-size: 1.3em; font-weight: bold;">{format_currency(kpis['umsatz'])}</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.75em; text-transform: uppercase;">Operativer Gewinn</div>
                                        <div style="color: #00ff88; font-size: 1.3em; font-weight: bold;">{format_currency(kpis['nettogewinn'])}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # =========================================================
                    # Umsatz- und EBIT-Entwicklung nebeneinander
                    # =========================================================
                    col_chart1, col_chart2 = st.columns(2)

                    with col_chart1:
                        # Bei Einzelmonat: Balkendiagramm, bei allen Monaten: Liniendiagramm
                        if selected_month == 'all':
                            st.markdown(chart_header(
                                "💰 Umsatzentwicklung",
                                "<strong>Umsatz pro Monat</strong><br>Zeigt den Gesamtumsatz (in EUR) jeder Filiale im Zeitverlauf. Steigende Linien deuten auf Wachstum hin, fallende auf Rückgang."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()
                            for store in active_stores:
                                store_df = stores_data[store['name']]
                                if monat_col in store_df.columns:
                                    umsatz_col = next((c for c in store_df.columns if 'umsatz' in c.lower() and 'eur' in c.lower()), None)
                                    if umsatz_col:
                                        monthly = store_df.groupby(monat_col)[umsatz_col].sum().reset_index()
                                        fig.add_trace(go.Scatter(
                                            x=monthly[monat_col],
                                            y=monthly[umsatz_col],
                                            name=store['name'],
                                            line=dict(color=store['color'], width=3),
                                            mode='lines+markers'
                                        ))

                            fig.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                showlegend=True,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                                transition={'duration': 500}
                            )
                        else:
                            # Einzelmonat: Balkendiagramm für Umsatzvergleich
                            month_name = MONTH_NAMES.get(selected_month, selected_month)
                            st.markdown(chart_header(
                                f"💰 Umsatzvergleich {month_name}",
                                "<strong>Umsatz im ausgewählten Monat</strong><br>Vergleich des Gesamtumsatzes (in EUR) aller Filialen im ausgewählten Monat."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()
                            store_names_umsatz = [s['name'] for s in active_stores]
                            umsatz_values = [stores_kpis[s['name']]['umsatz'] for s in active_stores]
                            colors_umsatz = [s['color'] for s in active_stores]

                            fig.add_trace(go.Bar(
                                x=store_names_umsatz,
                                y=umsatz_values,
                                marker_color=colors_umsatz,
                                text=[format_currency(v) for v in umsatz_values],
                                textposition='outside'
                            ))

                            fig.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                showlegend=False,
                                transition={'duration': 500}
                            )

                        st.plotly_chart(fig, use_container_width=True)

                    with col_chart2:
                        # Bei Einzelmonat: angepasster Titel
                        if selected_month == 'all':
                            st.markdown(chart_header(
                                "📊 Operativer Gewinn (EBIT) - Entwicklung",
                                "<strong>EBIT = Umsatz - Wareneinsatz - OPEX</strong><br>Zeigt den operativen Gewinn vor Zinsen und Steuern. OPEX = Personal + Miete + Logistik + Marketing."
                            ), unsafe_allow_html=True)
                        else:
                            month_name = MONTH_NAMES.get(selected_month, selected_month)
                            st.markdown(chart_header(
                                f"📊 Operativer Gewinn (EBIT) - Vergleich {month_name}",
                                "<strong>EBIT = Umsatz - Wareneinsatz - OPEX</strong><br>Vergleich des operativen Gewinns aller Filialen im ausgewählten Monat."
                            ), unsafe_allow_html=True)

                        fig = go.Figure()
                        for store in active_stores:
                            store_df = stores_data[store['name']]
                            if monat_col in store_df.columns:
                                # EBIT-Spalte verwenden, Fallback auf Berechnung
                                ebit_col = next((c for c in store_df.columns if 'ebit' in c.lower()), None)

                                if ebit_col:
                                    monthly = store_df.groupby(monat_col)[ebit_col].sum().reset_index()
                                    fig.add_trace(go.Bar(
                                        x=monthly[monat_col],
                                        y=monthly[ebit_col],
                                        name=store['name'],
                                        marker_color=store['color']
                                    ))
                                else:
                                    # Fallback: EBIT berechnen aus vorhandenen Spalten
                                    bruttogewinn_col = next((c for c in store_df.columns if 'bruttogewinn' in c.lower() and 'marge' not in c.lower() and 'prozent' not in c.lower()), None)
                                    kosten_col = next((c for c in store_df.columns if 'gesamtkosten' in c.lower()), None)
                                    if bruttogewinn_col and kosten_col:
                                        store_df['EBIT_calc'] = store_df[bruttogewinn_col] - store_df[kosten_col]
                                        monthly = store_df.groupby(monat_col)['EBIT_calc'].sum().reset_index()
                                        fig.add_trace(go.Bar(
                                            x=monthly[monat_col],
                                            y=monthly['EBIT_calc'],
                                            name=store['name'],
                                            marker_color=store['color']
                                        ))

                        fig.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            barmode='group',
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02),
                            transition={'duration': 500}
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    # =========================================================
                    # EBIT Margen-Vergleich und Kostenquote nebeneinander
                    # =========================================================
                    if 'Margen-Vergleich' in selected_dashboard_sections:
                        col_ebit, col_kosten = st.columns(2)

                        with col_ebit:
                            st.markdown(chart_header(
                                "📈 EBIT Margen-Vergleich",
                                "<strong>EBIT-Marge = EBIT / Umsatz × 100</strong><br>Zeigt wie viel Prozent vom Umsatz als operativer Gewinn übrig bleibt. Höhere Marge = bessere Profitabilität."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()
                            store_names_list = [s['name'] for s in active_stores]
                            # EBIT-Marge = EBIT / Umsatz × 100
                            margen = [(stores_kpis[s['name']]['nettogewinn'] / stores_kpis[s['name']]['umsatz'] * 100)
                                      if stores_kpis[s['name']]['umsatz'] > 0 else 0 for s in active_stores]
                            colors = [s['color'] for s in active_stores]

                            fig.add_trace(go.Bar(
                                x=store_names_list,
                                y=margen,
                                marker_color=colors,
                                text=[f"{m:.1f}%" for m in margen],
                                textposition='outside'
                            ))

                            fig.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                yaxis_title="EBIT-Marge (%)",
                                transition={'duration': 500}
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        with col_kosten:
                            # Kostenquote (Balkendiagramm)
                            st.markdown(chart_header(
                                "📊 Kostenquote im Vergleich",
                                "<strong>Kostenquote (%) = Gesamtkosten / Umsatz × 100</strong><br>"
                                "<strong>Gesamtkosten = Wareneinsatz + Personal + Miete + Logistik + Marketing</strong><br>"
                                "Niedrigere Werte = effizienter."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()
                            store_names_q = [s['name'] for s in active_stores]

                            # Kostenquote = Gesamtkosten / Umsatz × 100
                            # Gesamtkosten = Wareneinsatz + OPEX (Personal, Miete, Logistik, Marketing)
                            kosten_quoten = [(stores_kpis[s['name']]['kosten'] / stores_kpis[s['name']]['umsatz'] * 100)
                                             if stores_kpis[s['name']]['umsatz'] > 0 else 0 for s in active_stores]

                            fig.add_trace(go.Bar(
                                name='Kostenquote',
                                x=store_names_q,
                                y=kosten_quoten,
                                marker_color=[s['color'] for s in active_stores],
                                text=[f"{v:.1f}%" for v in kosten_quoten],
                                textposition='outside'
                            ))

                            fig.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                yaxis_title="Kostenquote (%)",
                                transition={'duration': 500}
                            )
                            st.plotly_chart(fig, use_container_width=True)

            # =============================================================
            # TAB 2: MARKETING
            # =============================================================
            with tab_marketing:
                st.subheader("📢 Marketing-Effizienz Analyse")
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

                # ROAS-Daten laden (korrekte Berechnung mit Campaign ID)
                roas_data = load_marketing_roas_data()
                marketing_monthly = load_marketing_monthly()

                if roas_data is not None and not roas_data.empty:
                    # Marketing-KPIs aus den korrekten ROAS-Daten
                    marketing_kpis = {}
                    for store in active_stores:
                        # Daten für diesen Store finden
                        store_row = roas_data[roas_data['StoreName'].str.contains(store['name'], case=False, na=False)]
                        if not store_row.empty:
                            row = store_row.iloc[0]
                            umsatz_mit_marketing = row['UmsatzMitMarketing']
                            umsatz_ohne_marketing = row['UmsatzOhneMarketing']
                            umsatz_gesamt = row['UmsatzGesamt']
                            marketing = row['MarketingKosten']
                            roas = row['ROAS']
                            cpa = row['CPA']
                            stueck_mit_marketing = row['StueckMitMarketing']
                            stueck_gesamt = row['StueckGesamt']
                            marketing_quote = (marketing / umsatz_gesamt * 100) if umsatz_gesamt > 0 else 0
                        else:
                            umsatz_mit_marketing = 0
                            umsatz_ohne_marketing = 0
                            umsatz_gesamt = 0
                            marketing = 0
                            roas = 0
                            cpa = 0
                            stueck_mit_marketing = 0
                            stueck_gesamt = 0
                            marketing_quote = 0

                        marketing_kpis[store['name']] = {
                            'umsatz_mit_marketing': umsatz_mit_marketing,
                            'umsatz_ohne_marketing': umsatz_ohne_marketing,
                            'umsatz_gesamt': umsatz_gesamt,
                            'marketing': marketing,
                            'roas': roas,
                            'cpa': cpa,
                            'stueck_mit_marketing': stueck_mit_marketing,
                            'stueck_gesamt': stueck_gesamt,
                            'marketing_quote': marketing_quote
                        }

                    # Marketing-KPI Cards
                    mkt_cols = st.columns(len(active_stores))

                    for idx, store in enumerate(active_stores):
                        mkpi = marketing_kpis[store['name']]
                        with mkt_cols[idx]:
                            st.markdown(f"""
                            <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                        border-radius: 15px; padding: 20px;">
                                <div style="font-size: 1.1em; font-weight: bold; color: {store['color']}; text-align: center; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                                    {store['name']}
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Umsatz direkt zurechenbar zu Marketing</div>
                                        <div style="color: #00ff88; font-size: 1em; font-weight: bold;">{format_currency(mkpi['umsatz_mit_marketing'])}</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Umsatz ohne Marketing</div>
                                        <div style="color: #ff9f43; font-size: 1em; font-weight: bold;">{format_currency(mkpi['umsatz_ohne_marketing'])}</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Marketing-Kosten</div>
                                        <div style="color: white; font-size: 1em; font-weight: bold;">{format_currency(mkpi['marketing'])}</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">ROAS</div>
                                        <div style="color: #00ff88; font-size: 1.2em; font-weight: bold;">{mkpi['roas']:.1f}x</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Marketing-Trend und Marketing-Quote nebeneinander
                    col_trend, col_quote = st.columns(2)

                    with col_trend:
                        st.markdown(chart_header(
                            "📈 Marketing-Ausgaben im Zeitverlauf",
                            "<strong>Monatliche Marketing-Investitionen</strong><br>Zeigt wie sich die Marketing-Ausgaben über die Monate entwickelt haben."
                        ), unsafe_allow_html=True)

                        fig_trend = go.Figure()

                        for store in active_stores:
                            store_mkt = marketing_monthly[marketing_monthly['StoreName'].str.contains(store['name'], case=False, na=False)]
                            if not store_mkt.empty:
                                fig_trend.add_trace(go.Scatter(
                                    x=store_mkt['Monat'],
                                    y=store_mkt['MarketingEur'],
                                    name=store['name'],
                                    line=dict(color=store['color'], width=3),
                                    mode='lines+markers'
                                ))

                        fig_trend.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            yaxis_title="Marketing (€)",
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02),
                            transition={'duration': 500},
                            height=400
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)

                    with col_quote:
                        st.markdown(chart_header(
                            "📊 Marketing-Quote",
                            "<strong>Marketing-Kosten / Gesamtumsatz × 100</strong><br>Zeigt wie viel Prozent vom Umsatz für Marketing ausgegeben wird. Niedrig = organisches Wachstum."
                        ), unsafe_allow_html=True)

                        # Marketing-Quote berechnen und als Bar Chart anzeigen
                        quote_data = []
                        for store in active_stores:
                            mkpi = marketing_kpis[store['name']]
                            quote = (mkpi['marketing'] / mkpi['umsatz_gesamt'] * 100) if mkpi['umsatz_gesamt'] > 0 else 0
                            quote_data.append({
                                'name': store['name'],
                                'quote': quote,
                                'color': store['color']
                            })

                        fig_quote = go.Figure()
                        fig_quote.add_trace(go.Bar(
                            x=[d['name'] for d in quote_data],
                            y=[d['quote'] for d in quote_data],
                            marker_color=[d['color'] for d in quote_data],
                            text=[f"{d['quote']:.2f}%" for d in quote_data],
                            textposition='outside'
                        ))

                        fig_quote.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            yaxis_title="Marketing-Quote (%)",
                            showlegend=False,
                            transition={'duration': 500},
                            height=400,
                            yaxis=dict(range=[0, max([d['quote'] for d in quote_data]) * 1.3])
                        )
                        st.plotly_chart(fig_quote, use_container_width=True)

                    # CPA als KPI-Karten (einfach und übersichtlich)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(chart_header(
                        "💰 CPA - Cost per Acquisition",
                        "<strong>Marketing-Kosten / Verkaufte Stück</strong><br>Was kostet ein verkaufter Artikel an Werbung?"
                    ), unsafe_allow_html=True)
                    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

                    cpa_cols = st.columns(len(active_stores))
                    for idx, store in enumerate(active_stores):
                        mkpi = marketing_kpis[store['name']]
                        with cpa_cols[idx]:
                            st.markdown(f"""
                            <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                        border-radius: 12px; padding: 20px; text-align: center;">
                                <div style="color: {store['color']}; font-weight: bold; margin-bottom: 10px;">{store['name']}</div>
                                <div style="font-size: 2em; font-weight: bold; color: white;">{mkpi['cpa']:.2f} €</div>
                                <div style="color: #aaa; font-size: 0.8em;">pro Stück</div>
                                <div style="color: #aaa; font-size: 0.75em; margin-top: 8px;">{int(mkpi['stueck_mit_marketing']):,} Stück verkauft</div>
                            </div>
                            """, unsafe_allow_html=True)

                else:
                    st.info("Keine Marketing-Daten verfügbar.")

            # =============================================================
            # TAB 3: KOSTENANALYSE (NEU - SUCCESS-konform)
            # =============================================================
            with tab_costs:
                # Gesamtkosten-KPIs für alle Filialen
                st.markdown(chart_header(
                    "💰 Gesamtkosten je Filiale",
                    "<strong>Gesamtkosten = Wareneinsatz + OPEX</strong><br>Wareneinsatz = TransferPrice. OPEX = Personal + Miete + Logistik + Marketing."
                ), unsafe_allow_html=True)

                cost_cols = st.columns(len(active_stores))
                for idx, store in enumerate(active_stores):
                    with cost_cols[idx]:
                        kosten = stores_kpis[store['name']]['kosten']

                        st.markdown(f"""
                        <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                    border-radius: 15px; padding: 20px; text-align: center;">
                            <div style="font-size: 0.9em; color: #aaa;">{store['name']}</div>
                            <div style="font-size: 2em; font-weight: bold; color: {store['color']};">{format_currency(kosten)}</div>
                            <div style="font-size: 0.7em; color: #aaa; margin-top: 5px;">Gesamtkosten</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Kostenstruktur (in % vom Umsatz) - Farbige HTML-Tabelle
                st.markdown(chart_header(
                    "📊 Kostenstruktur (in % vom Umsatz)",
                    "<strong>Jede Kostenstelle als Anteil vom Umsatz</strong><br>Zeigt wie viel Prozent vom Umsatz für jede Kostenkategorie aufgewendet wird. Niedrigere Werte = effizienter."
                ), unsafe_allow_html=True)

                # Farbige HTML-Tabelle erstellen
                table_html = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
                table_html += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'
                table_html += '<th style="padding: 12px; text-align: left;">Filiale</th>'
                table_html += '<th style="padding: 12px; text-align: center;">Wareneinsatz</th>'
                table_html += '<th style="padding: 12px; text-align: center;">Personal</th>'
                table_html += '<th style="padding: 12px; text-align: center;">Miete</th>'
                table_html += '<th style="padding: 12px; text-align: center;">Logistik</th>'
                table_html += '<th style="padding: 12px; text-align: center;">Marketing</th>'
                table_html += '<th style="padding: 12px; text-align: center; font-weight: bold;">Gesamt</th>'
                table_html += '</tr></thead><tbody>'

                for store in active_stores:
                    kpis = stores_kpis[store['name']]
                    umsatz = kpis['umsatz']

                    wareneinsatz_pct = (kpis['wareneinsatz'] / umsatz * 100) if umsatz > 0 else 0
                    personal_pct = (kpis['personalkosten'] / umsatz * 100) if umsatz > 0 else 0
                    miete_pct = (kpis['betriebskosten'] / umsatz * 100) if umsatz > 0 else 0
                    logistik_pct = (kpis['beschaffungskosten'] / umsatz * 100) if umsatz > 0 else 0
                    marketing_pct = (kpis['marketingkosten'] / umsatz * 100) if umsatz > 0 else 0
                    gesamt_pct = (kpis['kosten'] / umsatz * 100) if umsatz > 0 else 0

                    table_html += f'<tr style="background: {store["color_bg"]}; border-left: 4px solid {store["color"]};">'
                    table_html += f'<td style="padding: 15px; font-weight: bold; color: {store["color"]};">{store["name"]}</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{wareneinsatz_pct:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{personal_pct:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{miete_pct:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{logistik_pct:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{marketing_pct:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: {store["color"]}; font-weight: bold; font-size: 1.1em;">{gesamt_pct:.1f}%</td>'
                    table_html += '</tr>'

                table_html += '</tbody></table>'
                st.markdown(table_html, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Mietkosten und Umsatz pro m² laden
                rent_m2_data = load_rent_and_revenue_per_m2()

                if rent_m2_data is not None and not rent_m2_data.empty:
                    # Details-Tabelle mit allen Werten
                    st.markdown(chart_header(
                        "📋 Filialdetails (Fläche & Effizienz)",
                        "<strong>Übersicht Fläche, Miete und Umsatzeffizienz</strong><br>Alle Kennzahlen zur Flächennutzung im Überblick."
                    ), unsafe_allow_html=True)

                    detail_html = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
                    detail_html += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'
                    detail_html += '<th style="padding: 12px; text-align: left;">Filiale</th>'
                    detail_html += '<th style="padding: 12px; text-align: center;">Fläche (m²)</th>'
                    detail_html += '<th style="padding: 12px; text-align: center;">Mietkosten</th>'
                    detail_html += '<th style="padding: 12px; text-align: center;">Umsatz</th>'
                    detail_html += '<th style="padding: 12px; text-align: center; font-weight: bold;">Umsatz/m²</th>'
                    detail_html += '</tr></thead><tbody>'

                    for store in active_stores:
                        store_data = rent_m2_data[rent_m2_data['ID_STORE'] == store['id']]
                        if not store_data.empty:
                            row = store_data.iloc[0]
                            flaeche = row['StoreM2']
                            miete = row['MietkostenGesamt']
                            umsatz = row['UmsatzGesamt']
                            umsatz_m2 = row['UmsatzProM2']

                            detail_html += f'<tr style="background: {store["color_bg"]}; border-left: 4px solid {store["color"]};">'
                            detail_html += f'<td style="padding: 15px; font-weight: bold; color: {store["color"]};">{store["name"]}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{int(flaeche):,} m²</td>'.replace(",", ".")
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{format_currency(miete)}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{format_currency(umsatz)}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: {store["color"]}; font-weight: bold; font-size: 1.1em;">{umsatz_m2:,.0f} €/m²</td>'.replace(",", ".")
                            detail_html += '</tr>'

                    detail_html += '</tbody></table>'
                    st.markdown(detail_html, unsafe_allow_html=True)

            # =============================================================
            # TAB 4: PRODUKTKATEGORIEN
            # =============================================================
            with tab_categories:
                # Settings-Button
                col_cat_space, col_cat_settings = st.columns([15, 1])
                with col_cat_settings:
                    with st.popover("⚙️"):
                        st.markdown("**Anzeigeoptionen**")
                        if st.button("Alle anzeigen", key="reset_cat"):
                            st.session_state['cat_multiselect'] = cat_all_sections.copy()
                            st.rerun()
                        st.multiselect(
                            "Bereiche:",
                            options=cat_all_sections,
                            key="cat_multiselect",
                            label_visibility="collapsed"
                        )

                selected_cat_sections = st.session_state.get('cat_multiselect', cat_all_sections)

                # Kategorien-Daten laden
                df_sales_agg = load_sales_agg_data()

                if df_sales_agg is not None and len(df_sales_agg) > 0:
                    # Spalten finden
                    cat_col = next((c for c in df_sales_agg.columns if 'category' in c.lower() or 'kategorie' in c.lower()), None)
                    # StoreName (String) bevorzugen, sonst IdStore
                    store_name_col = next((c for c in df_sales_agg.columns if 'storename' in c.lower().replace('_', '')), None)
                    store_id_col = next((c for c in df_sales_agg.columns if c.lower() == 'idstore' or c.lower() == 'id_store'), None)
                    store_col_agg = store_name_col if store_name_col else store_id_col
                    revenue_col = next((c for c in df_sales_agg.columns if 'revenue' in c.lower() or 'umsatz' in c.lower()), None)
                    quantity_col = next((c for c in df_sales_agg.columns if 'quantity' in c.lower() or 'menge' in c.lower()), None)
                    profit_col = next((c for c in df_sales_agg.columns if 'profit' in c.lower() or 'gewinn' in c.lower()), None)
                    price_col = next((c for c in df_sales_agg.columns if 'price' in c.lower() or 'preis' in c.lower()), None)

                    # Hilfsfunktion für Store-Filterung (funktioniert mit String oder ID)
                    def filter_by_store(df, store):
                        if store_name_col:
                            return df[df[store_name_col].astype(str).str.contains(store['name'], case=False, na=False)]
                        elif store_id_col:
                            return df[df[store_id_col] == store['id']]
                        return df

                    if cat_col and store_col_agg and revenue_col:
                        # Zeige alle Kategorien aus der Datenbank (kein Filter)
                        df_filtered_cat = df_sales_agg.copy()

                        # Umsatzverteilung Donut
                        if 'Umsatzverteilung (Donut)' in selected_cat_sections:
                            st.markdown(chart_header(
                                "🍩 Umsatzverteilung nach Kategorie",
                                "<strong>Anteil jeder Kategorie am Gesamtumsatz</strong><br>Donut-Charts zeigen prozentuale Umsatzverteilung pro Filiale. Größere Segmente = höherer Umsatzanteil."
                            ), unsafe_allow_html=True)

                            donut_cols = st.columns(len(active_stores))
                            all_categories = []

                            for idx, store in enumerate(active_stores):
                                with donut_cols[idx]:
                                    store_cat_data = filter_by_store(df_filtered_cat, store)
                                    cat_sums = store_cat_data.groupby(cat_col)[revenue_col].sum()

                                    if len(cat_sums) > 0:
                                        # Sammle alle Kategorien für gemeinsame Legende
                                        for cat in cat_sums.index:
                                            if cat not in all_categories:
                                                all_categories.append(cat)

                                        fig = go.Figure(data=[go.Pie(
                                            labels=cat_sums.index,
                                            values=cat_sums.values,
                                            hole=0.5,
                                            marker_colors=[get_category_color(c) for c in cat_sums.index],
                                            textinfo='percent',
                                            textposition='outside'
                                        )])
                                        fig.update_layout(
                                            title=dict(text=store['name'], font=dict(color=store['color'])),
                                            paper_bgcolor='rgba(0,0,0,0)',
                                            font_color='white',
                                            showlegend=False,
                                            transition={'duration': 500},
                                            margin=dict(t=40, b=10, l=10, r=10),
                                            height=280
                                        )
                                        st.plotly_chart(fig, use_container_width=True)

                            # Gemeinsame Legende unter den Charts
                            if all_categories:
                                legend_html = '<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-top: 10px; margin-bottom: 20px;">'
                                for cat in all_categories:
                                    color = get_category_color(cat)
                                    legend_html += f'<div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; background: {color}; border-radius: 2px;"></div><span style="color: white; font-size: 0.85em;">{cat}</span></div>'
                                legend_html += '</div>'
                                st.markdown(legend_html, unsafe_allow_html=True)

                        # Stückzahl-Anteil (%)
                        if 'Stückzahl-Anteil (%)' in selected_cat_sections and quantity_col:
                            st.markdown(chart_header(
                                "📦 Anteil an Gesamtstückzahl je Kategorie (%)",
                                "<strong>Prozentuale Verteilung der verkauften Einheiten</strong><br>Zeigt welchen Anteil jede Kategorie an der Gesamtstückzahl pro Filiale hat."
                            ), unsafe_allow_html=True)

                            # Daten für Tabelle sammeln
                            all_cats = df_filtered_cat[cat_col].unique()
                            store_qty_pct = {}

                            for store in active_stores:
                                store_cat_data = filter_by_store(df_filtered_cat, store)
                                cat_sums = store_cat_data.groupby(cat_col)[quantity_col].sum()
                                total_qty = cat_sums.sum()
                                cat_pct = (cat_sums / total_qty * 100) if total_qty > 0 else cat_sums * 0
                                store_qty_pct[store['name']] = cat_pct

                            # HTML-Tabelle erstellen
                            qty_table = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
                            qty_table += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'
                            qty_table += '<th style="padding: 12px; text-align: left;">Kategorie</th>'
                            for store in active_stores:
                                qty_table += f'<th style="padding: 12px; text-align: center; color: {store["color"]};">{store["name"]}</th>'
                            qty_table += '</tr></thead><tbody>'

                            for cat in sorted(all_cats):
                                qty_table += '<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">'
                                qty_table += f'<td style="padding: 12px; color: white;">{cat}</td>'
                                for store in active_stores:
                                    pct = store_qty_pct[store['name']].get(cat, 0)
                                    qty_table += f'<td style="padding: 12px; text-align: center; color: {store["color"]}; font-weight: bold;">{pct:.1f}%</td>'
                                qty_table += '</tr>'

                            qty_table += '</tbody></table>'
                            st.markdown(qty_table, unsafe_allow_html=True)

                        # Bruttomarge und Bruttogewinn-Anteil nebeneinander
                        show_bruttomarge = 'Bruttomarge (%)' in selected_cat_sections and profit_col and revenue_col
                        show_bruttogewinn_anteil = 'Bruttogewinn-Anteil (%)' in selected_cat_sections and profit_col

                        if show_bruttomarge or show_bruttogewinn_anteil:
                            col_margin, col_profit = st.columns(2)

                            # Bruttomarge (%)
                            if show_bruttomarge:
                                with col_margin:
                                    st.markdown(chart_header(
                                        "📈 Bruttomarge nach Kategorie (%)",
                                        "<strong>Bruttomarge = Bruttogewinn / Umsatz * 100</strong><br>Zeigt die prozentuale Gewinnspanne pro Kategorie. Höhere Werte = profitablere Produkte."
                                    ), unsafe_allow_html=True)

                                    fig = go.Figure()

                                    for store in active_stores:
                                        store_cat_data = filter_by_store(df_filtered_cat, store)
                                        cat_profit = store_cat_data.groupby(cat_col)[profit_col].sum()
                                        cat_revenue = store_cat_data.groupby(cat_col)[revenue_col].sum()
                                        cat_margin = (cat_profit / cat_revenue * 100).fillna(0)

                                        fig.add_trace(go.Bar(
                                            name=store['name'],
                                            x=cat_margin.index,
                                            y=cat_margin.values,
                                            marker_color=store['color'],
                                            text=[f"{v:.1f}%" for v in cat_margin.values],
                                            textposition='outside'
                                        ))

                                    fig.update_layout(
                                        barmode='group',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        font_color='white',
                                        xaxis_title="Kategorie",
                                        yaxis_title="Bruttomarge (%)",
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                                        transition={'duration': 500}
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                            # Bruttogewinn-Anteil (%)
                            if show_bruttogewinn_anteil:
                                with col_profit:
                                    st.markdown(chart_header(
                                        "💰 Bruttogewinn-Anteil je Kategorie (%)",
                                        "<strong>Anteil am Gesamtbruttogewinn</strong><br>Zeigt welchen Anteil jede Kategorie am gesamten Bruttogewinn der Filiale hat."
                                    ), unsafe_allow_html=True)

                                    fig = go.Figure()

                                    for store in active_stores:
                                        store_cat_data = filter_by_store(df_filtered_cat, store)
                                        cat_profit = store_cat_data.groupby(cat_col)[profit_col].sum()
                                        total_profit = cat_profit.sum()
                                        cat_pct = (cat_profit / total_profit * 100) if total_profit > 0 else cat_profit * 0

                                        fig.add_trace(go.Bar(
                                            name=store['name'],
                                            x=cat_pct.index,
                                            y=cat_pct.values,
                                            marker_color=store['color'],
                                            text=[f"{v:.1f}%" for v in cat_pct.values],
                                            textposition='outside'
                                        ))

                                    fig.update_layout(
                                        barmode='group',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        font_color='white',
                                        xaxis_title="Kategorie",
                                        yaxis_title="Anteil am Bruttogewinn (%)",
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                                        transition={'duration': 500}
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                        # Preissegment-Vergleich
                        st.markdown(chart_header(
                            "💎 Umsatzverteilung nach Preissegment (%)",
                            "<strong>Anteil der Preissegmente am Gesamtumsatz</strong><br>Zeigt wie sich der Umsatz auf Premium, Standard und Budget verteilt."
                        ), unsafe_allow_html=True)

                        price_segment_data = load_price_segment_data()

                        if price_segment_data is not None and not price_segment_data.empty:
                            # Prozentuale Verteilung pro Filiale berechnen
                            all_segments = price_segment_data['Preissegment'].unique()
                            store_segment_pct = {}

                            for store in active_stores:
                                store_data = price_segment_data[price_segment_data['ID_STORE'] == store['id']]
                                total_umsatz = store_data['Umsatz'].sum()
                                segment_pct = {}
                                for _, row in store_data.iterrows():
                                    pct = (row['Umsatz'] / total_umsatz * 100) if total_umsatz > 0 else 0
                                    segment_pct[row['Preissegment']] = pct
                                store_segment_pct[store['name']] = segment_pct

                            # HTML-Tabelle erstellen
                            segment_table = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
                            segment_table += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'
                            segment_table += '<th style="padding: 12px; text-align: left;">Preissegment</th>'
                            for store in active_stores:
                                segment_table += f'<th style="padding: 12px; text-align: center; color: {store["color"]};">{store["name"]}</th>'
                            segment_table += '</tr></thead><tbody>'

                            for segment in sorted(all_segments):
                                segment_table += '<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">'
                                segment_table += f'<td style="padding: 12px; color: white;">{segment}</td>'
                                for store in active_stores:
                                    pct = store_segment_pct[store['name']].get(segment, 0)
                                    segment_table += f'<td style="padding: 12px; text-align: center; color: {store["color"]}; font-weight: bold;">{pct:.1f}%</td>'
                                segment_table += '</tr>'

                            segment_table += '</tbody></table>'
                            st.markdown(segment_table, unsafe_allow_html=True)
                        else:
                            st.info("Keine Preissegment-Daten verfügbar.")

                else:
                    st.warning("Keine Kategoriedaten verfügbar.")

            # =============================================================
            # TAB 3: ROHDATEN
            # =============================================================
            with tab_data:
                st.subheader("📋 Rohdaten-Export")
                st.markdown("Alle verfügbaren Daten aus der Datenbank")

                st.dataframe(filtered_df, use_container_width=True)

                # Download Button
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    "📥 Daten als CSV herunterladen",
                    csv,
                    f"benchmark_export_{selected_month}.csv",
                    "text/csv"
                )

        else:
            st.warning(f"Nicht genügend Stores gefunden. Gefunden: {len(active_stores)}, Benötigt: mindestens 2")

    else:
        st.error("Spalten 'Monat' oder 'Filialgruppe' nicht gefunden.")

else:
    st.error("Keine Daten verfügbar. Bitte Datenbankverbindung prüfen.")
