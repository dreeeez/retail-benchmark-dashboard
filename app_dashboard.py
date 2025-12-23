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
        dashboard_all_sections = ['KPI-Karten', 'Margen-Vergleich', 'Kostenstruktur']
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
            # TAB 2: KOSTENANALYSE (NEU - SUCCESS-konform)
            # =============================================================
            with tab_costs:
                # Gesamtkosten-KPIs für alle Filialen
                st.markdown(chart_header(
                    "💰 Gesamtkosten je Filiale",
                    "<strong>Gesamtkosten = Wareneinsatz + Betriebskosten + Personalkosten + Beschaffungskosten</strong><br>Wareneinsatz = Umsatz - Bruttogewinn. Personalkosten = Gehalt + Sozialkosten + Provision. Betriebskosten = Miete + Marketing."
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

                # Kostenstruktur-Vergleich (100% Stacked Bar)
                st.markdown(chart_header(
                    "📊 Kostenstruktur im Vergleich",
                    "<strong>Prozentuale Aufschlüsselung der Gesamtkosten</strong><br>Zeigt den Anteil jeder Kostenkategorie an den Gesamtkosten. Ideal für Effizienzvergleiche zwischen Filialen."
                ), unsafe_allow_html=True)

                fig = go.Figure()

                # Store-Namen und Kosten für alle Stores sammeln
                store_names = [store['name'] for store in active_stores]
                wareneinsatz_values = [stores_kpis[store['name']]['wareneinsatz'] for store in active_stores]
                personal_values = [stores_kpis[store['name']]['personalkosten'] for store in active_stores]
                betrieb_values = [stores_kpis[store['name']]['betriebskosten'] for store in active_stores]
                beschaffung_values = [stores_kpis[store['name']]['beschaffungskosten'] for store in active_stores]

                # Gesamtkosten für Prozentberechnung
                total_values = [stores_kpis[store['name']]['kosten'] for store in active_stores]

                # Prozentuale Anteile berechnen
                wareneinsatz_pct = [(w / t * 100) if t > 0 else 0 for w, t in zip(wareneinsatz_values, total_values)]
                personal_pct = [(p / t * 100) if t > 0 else 0 for p, t in zip(personal_values, total_values)]
                betrieb_pct = [(b / t * 100) if t > 0 else 0 for b, t in zip(betrieb_values, total_values)]
                beschaffung_pct = [(b / t * 100) if t > 0 else 0 for b, t in zip(beschaffung_values, total_values)]

                # Ein Trace pro Kostenkategorie mit Prozentwerten
                fig.add_trace(go.Bar(
                    name='Beschaffung',
                    x=store_names,
                    y=beschaffung_pct,
                    marker_color='#a55eea',
                    text=[f"{v:.1f}%" for v in beschaffung_pct],
                    textposition='inside'
                ))
                fig.add_trace(go.Bar(
                    name='Betriebskosten',
                    x=store_names,
                    y=betrieb_pct,
                    marker_color='#ffd93d',
                    text=[f"{v:.1f}%" for v in betrieb_pct],
                    textposition='inside'
                ))
                fig.add_trace(go.Bar(
                    name='Personalkosten',
                    x=store_names,
                    y=personal_pct,
                    marker_color='#ff6b6b',
                    text=[f"{v:.1f}%" for v in personal_pct],
                    textposition='inside'
                ))
                fig.add_trace(go.Bar(
                    name='Wareneinsatz',
                    x=store_names,
                    y=wareneinsatz_pct,
                    marker_color='#74b9ff',
                    text=[f"{v:.1f}%" for v in wareneinsatz_pct],
                    textposition='inside'
                ))

                fig.update_layout(
                    barmode='stack',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    yaxis_title="Anteil (%)",
                    yaxis=dict(range=[0, 100]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    transition={'duration': 500}
                )
                st.plotly_chart(fig, use_container_width=True)

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
