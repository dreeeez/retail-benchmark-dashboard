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
                StoreName,
                ID_STORE,
                SUM(CASE WHEN ID_CAMPAIGN != 0 THEN RevenueEUR ELSE 0 END) as UmsatzMitMarketing,
                SUM(CASE WHEN ID_CAMPAIGN = 0 THEN RevenueEUR ELSE 0 END) as UmsatzOhneMarketing,
                SUM(RevenueEUR) as UmsatzGesamt,
                SUM(CASE WHEN ID_CAMPAIGN != 0 THEN SalesAmount ELSE 0 END) as StueckMitMarketing,
                SUM(SalesAmount) as StueckGesamt
            FROM dbo.V_LIST_MONTHLY_SALES
            WHERE ID_STORE IN (3, 5, 14)
            GROUP BY StoreName, ID_STORE
        """, conn)

        # Marketing-Kosten
        marketing_df = pd.read_sql("""
            SELECT
                StoreName,
                SUM(WertEUR) as MarketingKosten
            FROM dbo.V_LIST_MONTHLY_COSTS
            WHERE Kostenkategorie LIKE 'Marketing Campaign%'
            AND ID_STORE IN (3, 5, 14)
            GROUP BY StoreName
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

@st.cache_data(ttl=300)
def load_marketing_mix_data():
    """Lädt Marketing-Mix Daten: Umsatz pro Kampagne

    Verwendet V_LIST_MONTHLY_SALES für Umsatz pro Kampagne (ID_CAMPAIGN)
    """
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT
                s.ID_STORE,
                so.STORE_LOCATION AS StoreName,
                CASE
                    WHEN s.ID_CAMPAIGN = 0 THEN 'Organisch'
                    ELSE c.CAMP_TYPE + ' / ' + c.CAMP_NAME
                END AS Kanal,
                SUM(s.RevenueEUR) AS Umsatz
            FROM dbo.V_LIST_MONTHLY_SALES s
            LEFT JOIN dbo.T_CAMPAIGN c ON s.ID_CAMPAIGN = c.ID_CAMPAIGN
            INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
            WHERE s.ID_STORE IN (3, 5, 14)
            GROUP BY s.ID_STORE, so.STORE_LOCATION, s.ID_CAMPAIGN, c.CAMP_TYPE, c.CAMP_NAME
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
        dashboard_all_sections = ['KPI-Karten', 'Margen-Vergleich', 'Kostenstruktur', 'Marketing-Analyse']
        cat_all_sections = ['Top/Flop Kategorien', 'Umsatzverteilung (Donut)', 'Umsatz-Vergleich',
                            'Stückzahlen', 'Bruttogewinn', 'Umsatz-Trend', 'Detaildaten']

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
        tab_summary, tab_main, tab_costs, tab_categories, tab_data = st.tabs([
            "🏆 Executive Summary", "📊 Dashboard", "💸 Kostenanalyse", "🚲 Produktkategorien", "📋 Rohdaten"
        ])

        if len(active_stores) >= 2:
            # =============================================================
            # TAB 0: EXECUTIVE SUMMARY
            # =============================================================
            with tab_summary:
                st.subheader("🏆 Executive Summary")

                # Gewinner ermitteln (basierend auf Nettogewinn)
                store_profits = {name: kpis['nettogewinn'] for name, kpis in stores_kpis.items()}
                winner_name = max(store_profits, key=store_profits.get)
                winner_store = next(s for s in active_stores if s['name'] == winner_name)

                # Alle Stores sortiert nach Performance
                sorted_stores = sorted(store_profits.items(), key=lambda x: x[1], reverse=True)
                gewinn_vorteil = sorted_stores[0][1] - sorted_stores[1][1] if len(sorted_stores) > 1 else 0

                # Alle Stores in einer Reihe mit gleicher Breite
                summary_cols = st.columns(len(active_stores))

                # Medaillen für Plätze
                medals = ["🥇", "🥈", "🥉"]

                for idx, (store_name, profit) in enumerate(sorted_stores):
                    store = next(s for s in active_stores if s['name'] == store_name)
                    medal = medals[idx] if idx < 3 else f"#{idx+1}"

                    with summary_cols[idx]:
                        if idx == 0:
                            # Gewinner (Gold)
                            st.markdown(f"""
                            <div class="hover-card" style="background: linear-gradient(135deg, rgba(0,255,136,0.2), rgba(0,255,136,0.05));
                                        border: 2px solid #00ff88; border-radius: 15px; padding: 25px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                                <div style="font-size: 3em;">{medal}</div>
                                <div style="font-size: 1.5em; font-weight: bold; color: {store['color']}; margin: 5px 0;">{store_name}</div>
                                <div style="color: #aaa; font-size: 0.9em;">+{format_currency(gewinn_vorteil)} Vorsprung</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Silber, Bronze
                            st.markdown(f"""
                            <div class="hover-card" style="background: rgba(255,255,255,0.05);
                                        border: 1px solid {store['color']}; border-radius: 15px; padding: 25px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                                <div style="font-size: 3em;">{medal}</div>
                                <div style="font-size: 1.5em; font-weight: bold; color: {store['color']}; margin: 5px 0;">{store_name}</div>
                                <div style="color: #aaa; font-size: 0.9em;">{format_currency(profit)} Nettogewinn</div>
                            </div>
                            """, unsafe_allow_html=True)

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

                # =========================================================
                # MARKETING-ANALYSE
                # =========================================================
                if 'Marketing-Analyse' in selected_dashboard_sections:
                    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.1); margin: 30px 0;'>", unsafe_allow_html=True)
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
                                            <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Umsatz mit Marketing</div>
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

                        # Marketing-Trend und Marketing-Quote nebeneinander (wie EBIT-Margen)
                        if selected_month == 'all':
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

                            # Marketing-Mix (Kanal-Vergleich)
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown(chart_header(
                                "📊 Marketing-Mix (Kanal-Vergleich)",
                                "<strong>Umsatz-Anteil pro Kanal</strong><br>"
                                "Zeigt den Anteil jedes Marketing-Kanals am Gesamt-Werbeumsatz."
                            ), unsafe_allow_html=True)
                            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

                            marketing_mix = load_marketing_mix_data()

                            if marketing_mix is not None and not marketing_mix.empty:
                                # Chart pro Store nebeneinander
                                mix_cols = st.columns(len(active_stores))

                                for idx, store in enumerate(active_stores):
                                    with mix_cols[idx]:
                                        # Daten für diesen Store
                                        store_mix = marketing_mix[
                                            marketing_mix['StoreName'].str.contains(store['name'], case=False, na=False)
                                        ].copy()

                                        if not store_mix.empty:
                                            # Berechne Umsatz-Anteil (%)
                                            total_umsatz = store_mix['Umsatz'].sum()
                                            store_mix['UmsatzAnteil'] = (store_mix['Umsatz'] / total_umsatz * 100) if total_umsatz > 0 else 0

                                            # Top 5 Kanäle nach Umsatz-Anteil
                                            store_mix = store_mix.nlargest(5, 'UmsatzAnteil')

                                            fig_mix = go.Figure()

                                            # Balken: Umsatz-Anteil (Farbe des Stores)
                                            fig_mix.add_trace(go.Bar(
                                                name='Umsatz-Anteil',
                                                x=store_mix['Kanal'],
                                                y=store_mix['UmsatzAnteil'],
                                                marker_color=store['color'],
                                                text=[f"{a:.1f}%" for a in store_mix['UmsatzAnteil']],
                                                textposition='outside',
                                                textfont=dict(size=10)
                                            ))

                                            max_val = store_mix['UmsatzAnteil'].max()

                                            fig_mix.update_layout(
                                                title=dict(text=store['name'], font=dict(color=store['color'], size=14)),
                                                paper_bgcolor='rgba(0,0,0,0)',
                                                plot_bgcolor='rgba(0,0,0,0)',
                                                font_color='white',
                                                showlegend=False,
                                                height=400,
                                                margin=dict(t=60, b=100),
                                                xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
                                                yaxis=dict(title="Anteil (%)", range=[0, max_val * 1.3] if max_val > 0 else [0, 100])
                                            )
                                            st.plotly_chart(fig_mix, use_container_width=True)
                                        else:
                                            st.info(f"Keine Marketing-Kanal-Daten für {store['name']}")
                            else:
                                st.info("Keine Marketing-Mix Daten verfügbar.")
                    else:
                        st.info("Keine Marketing-Daten verfügbar.")

            # =============================================================
            # TAB 2: KOSTENANALYSE (NEU - SUCCESS-konform)
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

            # =============================================================
            # TAB 3: PRODUKTKATEGORIEN
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

                st.subheader("🚲 Produktkategorien-Analyse")

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

                        # SUCCESS: SAY - Kategorie-Insights
                        cat_totals = df_filtered_cat.groupby(cat_col)[revenue_col].sum()
                        top_cat = cat_totals.idxmax()
                        top_cat_value = cat_totals.max()
                        bottom_cat = cat_totals.idxmin()

                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(255,159,67,0.1), rgba(123,44,191,0.1));
                                    border-left: 4px solid #ff9f43; padding: 15px; border-radius: 0 10px 10px 0; margin-bottom: 20px;">
                            <strong style="color: #ff9f43;">🚲 Kategorie-Insight:</strong>
                            <span style="color: white;"><strong>{top_cat}</strong> ist die umsatzstärkste Kategorie mit {format_currency(top_cat_value)}.
                            Schwächste Kategorie: <strong>{bottom_cat}</strong></span>
                        </div>
                        """, unsafe_allow_html=True)

                        # Top/Flop Kategorien
                        if 'Top/Flop Kategorien' in selected_cat_sections:
                            st.markdown(chart_header(
                                "🏆 Top & Flop Kategorien",
                                "<strong>Ranking nach Gesamtumsatz</strong><br>Zeigt die umsatzstärksten (Top 3) und umsatzschwächsten (Bottom 3) Produktkategorien über alle Filialen."
                            ), unsafe_allow_html=True)

                            cat_revenue = df_filtered_cat.groupby(cat_col)[revenue_col].sum().sort_values(ascending=False)

                            col_top, col_flop = st.columns(2)

                            with col_top:
                                st.markdown("**🔝 Top 3 Kategorien**")
                                for i, (cat, rev) in enumerate(cat_revenue.head(3).items()):
                                    color = get_category_color(cat)
                                    st.markdown(f"""
                                    <div style="background: rgba(0,255,136,0.1); border-left: 4px solid {color};
                                                padding: 10px; margin: 5px 0; border-radius: 0 8px 8px 0;">
                                        <strong>{i+1}. {cat}</strong><br>
                                        <span style="color: #00ff88;">{format_currency(rev)}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                            with col_flop:
                                st.markdown("**📉 Bottom 3 Kategorien**")
                                for i, (cat, rev) in enumerate(cat_revenue.tail(3).items()):
                                    color = get_category_color(cat)
                                    st.markdown(f"""
                                    <div style="background: rgba(255,71,87,0.1); border-left: 4px solid {color};
                                                padding: 10px; margin: 5px 0; border-radius: 0 8px 8px 0;">
                                        <strong>{6-i}. {cat}</strong><br>
                                        <span style="color: #ff4757;">{format_currency(rev)}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                        # Umsatzverteilung Donut
                        if 'Umsatzverteilung (Donut)' in selected_cat_sections:
                            st.markdown(chart_header(
                                "🍩 Umsatzverteilung nach Kategorie",
                                "<strong>Anteil jeder Kategorie am Gesamtumsatz</strong><br>Donut-Charts zeigen prozentuale Umsatzverteilung pro Filiale. Größere Segmente = höherer Umsatzanteil."
                            ), unsafe_allow_html=True)

                            donut_cols = st.columns(len(active_stores))

                            for idx, store in enumerate(active_stores):
                                with donut_cols[idx]:
                                    store_cat_data = filter_by_store(df_filtered_cat, store)
                                    cat_sums = store_cat_data.groupby(cat_col)[revenue_col].sum()

                                    if len(cat_sums) > 0:
                                        fig = go.Figure(data=[go.Pie(
                                            labels=cat_sums.index,
                                            values=cat_sums.values,
                                            hole=0.5,
                                            marker_colors=[get_category_color(c) for c in cat_sums.index]
                                        )])
                                        fig.update_layout(
                                            title=dict(text=store['name'], font=dict(color=store['color'])),
                                            paper_bgcolor='rgba(0,0,0,0)',
                                            font_color='white',
                                            showlegend=True,
                                            legend=dict(font=dict(size=10)),
                                            transition={'duration': 500}
                                        )
                                        st.plotly_chart(fig, use_container_width=True)

                        # Umsatz-Vergleich nach Kategorie
                        if 'Umsatz-Vergleich' in selected_cat_sections:
                            st.markdown(chart_header(
                                "📊 Umsatz-Vergleich nach Kategorie",
                                "<strong>Direkter Filialvergleich pro Kategorie</strong><br>Balkendiagramm zeigt Umsatz (EUR) jeder Filiale nebeneinander. Ideal für Performance-Vergleiche."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()

                            for store in active_stores:
                                store_cat_data = filter_by_store(df_filtered_cat, store)
                                cat_sums = store_cat_data.groupby(cat_col)[revenue_col].sum()

                                fig.add_trace(go.Bar(
                                    name=store['name'],
                                    x=cat_sums.index,
                                    y=cat_sums.values,
                                    marker_color=store['color']
                                ))

                            fig.update_layout(
                                barmode='group',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                xaxis_title="Kategorie",
                                yaxis_title="Umsatz (€)",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                                transition={'duration': 500}
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        # Stückzahlen
                        if 'Stückzahlen' in selected_cat_sections and quantity_col:
                            st.markdown(chart_header(
                                "📦 Stückzahlen nach Kategorie",
                                "<strong>Verkaufte Einheiten pro Kategorie</strong><br>Anzahl verkaufter Fahrräder je Kategorie und Filiale. Hohe Stückzahlen bei niedrigem Umsatz = günstige Produkte."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()

                            for store in active_stores:
                                store_cat_data = filter_by_store(df_filtered_cat, store)
                                cat_sums = store_cat_data.groupby(cat_col)[quantity_col].sum()

                                fig.add_trace(go.Bar(
                                    name=store['name'],
                                    x=cat_sums.index,
                                    y=cat_sums.values,
                                    marker_color=store['color']
                                ))

                            fig.update_layout(
                                barmode='group',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                xaxis_title="Kategorie",
                                yaxis_title="Stückzahl",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                                transition={'duration': 500}
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        # Bruttogewinn
                        if 'Bruttogewinn' in selected_cat_sections and profit_col:
                            st.markdown(chart_header(
                                "💰 Bruttogewinn nach Kategorie",
                                "<strong>Bruttogewinn = Umsatz - Einkaufskosten</strong><br>Gewinn vor Abzug von Betriebskosten. Hoher Bruttogewinn = gute Marge auf die Produkte."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()

                            for store in active_stores:
                                store_cat_data = filter_by_store(df_filtered_cat, store)
                                cat_sums = store_cat_data.groupby(cat_col)[profit_col].sum()

                                fig.add_trace(go.Bar(
                                    name=store['name'],
                                    x=cat_sums.index,
                                    y=cat_sums.values,
                                    marker_color=store['color']
                                ))

                            fig.update_layout(
                                barmode='group',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                xaxis_title="Kategorie",
                                yaxis_title="Bruttogewinn (€)",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                                transition={'duration': 500}
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        # Detaildaten
                        if 'Detaildaten' in selected_cat_sections:
                            st.markdown(chart_header(
                                "📋 Detaildaten Kategorien",
                                "<strong>Aggregierte Kategoriedaten</strong><br>Alle Kategoriedaten inkl. Umsatz, Stückzahlen, Preise und Gewinne pro Filiale und Monat."
                            ), unsafe_allow_html=True)
                            st.dataframe(df_filtered_cat, use_container_width=True)
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
