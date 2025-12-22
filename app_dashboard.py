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
    Gesamtkosten = Wareneinsatz + Betriebskosten + Personalkosten + Beschaffungskosten
    wobei: Wareneinsatz = Umsatz - Bruttogewinn
    """
    umsatz = safe_sum(store_df, 'umsatz')
    bruttogewinn = safe_sum(store_df, 'bruttogewinn')

    # Wareneinsatz = Umsatz - Bruttogewinn
    wareneinsatz = umsatz - bruttogewinn

    # Einzelne Kostenkomponenten
    personalkosten = safe_sum(store_df, 'personalkosten')
    betriebskosten = safe_sum(store_df, 'betriebskosten')
    beschaffungskosten = safe_sum(store_df, 'beschaffungskosten')

    # NEUE FORMEL: Gesamtkosten = Wareneinsatz + Betriebskosten + Personalkosten + Beschaffungskosten
    gesamtkosten = wareneinsatz + betriebskosten + personalkosten + beschaffungskosten

    return {
        'umsatz': umsatz,
        'nettogewinn': safe_sum(store_df, 'nettogewinn'),
        'marge': safe_mean(store_df, 'nettogewinnmarge'),
        'bruttogewinn': bruttogewinn,
        'kosten': gesamtkosten,
        'wareneinsatz': wareneinsatz,
        'personalkosten': personalkosten,
        'betriebskosten': betriebskosten,
        'beschaffungskosten': beschaffungskosten
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
        dashboard_all_sections = ['KPI-Karten', 'Umsatz-Chart', 'Nettogewinn-Chart', 'Margen-Vergleich',
                                  'Kostenstruktur', 'KPI-Radar', 'Datentabelle']
        cat_all_sections = ['Top/Flop Kategorien', 'Umsatzverteilung (Donut)', 'Umsatz-Vergleich',
                            'Stückzahlen', 'Durchschnittspreis', 'Bruttogewinn',
                            'Umsatz-Trend', 'Detaildaten']

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

                for idx, (store_name, profit) in enumerate(sorted_stores):
                    store = next(s for s in active_stores if s['name'] == store_name)
                    with summary_cols[idx]:
                        if idx == 0:
                            # Gewinner
                            st.markdown(f"""
                            <div class="hover-card" style="background: linear-gradient(135deg, rgba(0,255,136,0.2), rgba(0,255,136,0.05));
                                        border: 2px solid #00ff88; border-radius: 15px; padding: 25px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                                <div style="font-size: 2.5em;">🏆</div>
                                <div style="font-size: 1.2em; font-weight: bold; color: #00ff88; margin: 5px 0;">GEWINNER</div>
                                <div style="font-size: 1.5em; font-weight: bold; color: {store['color']};">{store_name}</div>
                                <div style="color: #aaa; font-size: 0.9em; margin-top: 5px;">+{format_currency(gewinn_vorteil)} Vorsprung</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Andere Plätze
                            rank = idx + 1
                            st.markdown(f"""
                            <div class="hover-card" style="background: rgba(255,255,255,0.05);
                                        border: 1px solid {store['color']}; border-radius: 15px; padding: 25px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                                <div style="font-size: 2.5em;">#{rank}</div>
                                <div style="font-size: 1.5em; font-weight: bold; color: {store['color']}; margin: 5px 0;">{store_name}</div>
                                <div style="color: #aaa; font-size: 0.9em;">{format_currency(profit)} Nettogewinn</div>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown("---")

                # Key Insights
                st.markdown("### 💡 Key Insights")

                # Automatisch generierte Insights
                insights = []

                # Umsatz-Leader
                store_revenues = {name: kpis['umsatz'] for name, kpis in stores_kpis.items()}
                umsatz_leader = max(store_revenues, key=store_revenues.get)
                umsatz_max = store_revenues[umsatz_leader]
                umsatz_avg = sum(store_revenues.values()) / len(store_revenues)
                umsatz_diff_pct = ((umsatz_max / umsatz_avg) - 1) * 100 if umsatz_avg > 0 else 0
                insights.append(f"📈 **Umsatz-Leader:** {umsatz_leader} liegt {umsatz_diff_pct:.1f}% über dem Durchschnitt")

                # Marge-Leader
                store_marges = {name: kpis['marge'] for name, kpis in stores_kpis.items()}
                marge_leader = max(store_marges, key=store_marges.get)
                marge_max = store_marges[marge_leader]
                insights.append(f"💰 **Beste Marge:** {marge_leader} mit {marge_max:.1f}% Nettomarge")

                # Empfehlung
                insights.append(f"✅ **Empfehlung:** Best Practices aus {winner_name} auf andere Filialen übertragen")

                for insight in insights:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.05); border-left: 4px solid #00d4ff;
                                padding: 15px; margin: 10px 0; border-radius: 0 10px 10px 0;">
                        {insight}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # Flächendaten laden für faire Vergleiche
                df_location = load_location_data()
                store_sizes = {}
                if df_location is not None and len(df_location) > 0:
                    for _, row in df_location.iterrows():
                        store_name_loc = row['StoreName']
                        # Store-Namen matchen
                        for store in active_stores:
                            if store['name'].lower() in store_name_loc.lower():
                                store_sizes[store['name']] = row['LOC_SIZE_M2']

                # Performance Scorecard mit 3 Metriken
                st.markdown(chart_header(
                    "📊 Performance Scorecard (Flächenbereinigt)",
                    "<strong>3 Kennzahlen für fairen Vergleich:</strong><br>"
                    "• <strong>Gewinn/m²:</strong> Nettogewinn ÷ Fläche - zeigt Flächeneffizienz<br>"
                    "• <strong>Umsatz/m²:</strong> Umsatz ÷ Fläche - zeigt Verkaufsleistung pro m²<br>"
                    "• <strong>Nettomarge:</strong> Nettogewinn ÷ Umsatz × 100 - zeigt Profitabilität unabhängig von Größe"
                ), unsafe_allow_html=True)

                # Berechne Metriken für alle Stores
                store_metrics = {}
                for store in active_stores:
                    kpis = stores_kpis[store['name']]
                    size = store_sizes.get(store['name'], 1)  # Fallback auf 1 wenn keine Fläche

                    gewinn_pro_m2 = kpis['nettogewinn'] / size if size > 0 else 0
                    umsatz_pro_m2 = kpis['umsatz'] / size if size > 0 else 0
                    marge = kpis['marge']

                    store_metrics[store['name']] = {
                        'gewinn_m2': gewinn_pro_m2,
                        'umsatz_m2': umsatz_pro_m2,
                        'marge': marge,
                        'size': size
                    }

                # Durchschnitte berechnen für relative Scores
                avg_gewinn_m2 = sum(m['gewinn_m2'] for m in store_metrics.values()) / len(store_metrics)
                avg_umsatz_m2 = sum(m['umsatz_m2'] for m in store_metrics.values()) / len(store_metrics)
                avg_marge = sum(m['marge'] for m in store_metrics.values()) / len(store_metrics)

                # Farbe basierend auf Score
                def get_score_color(score):
                    if score >= 110:
                        return "#00ff88"  # Grün - überdurchschnittlich
                    elif score >= 90:
                        return "#ffd93d"  # Gelb - durchschnittlich
                    else:
                        return "#ff4757"  # Rot - unterdurchschnittlich

                score_cols = st.columns(len(active_stores))

                for idx, store in enumerate(active_stores):
                    metrics = store_metrics[store['name']]

                    # Relative Scores (100 = Durchschnitt)
                    score_gewinn = (metrics['gewinn_m2'] / avg_gewinn_m2 * 100) if avg_gewinn_m2 > 0 else 0
                    score_umsatz = (metrics['umsatz_m2'] / avg_umsatz_m2 * 100) if avg_umsatz_m2 > 0 else 0
                    score_marge = (metrics['marge'] / avg_marge * 100) if avg_marge > 0 else 0

                    # Farben vorab berechnen
                    color_gewinn = get_score_color(score_gewinn)
                    color_umsatz = get_score_color(score_umsatz)
                    color_marge = get_score_color(score_marge)

                    with score_cols[idx]:
                        st.markdown(f"""
                        <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                    border-radius: 15px; padding: 20px;">
                            <div style="font-size: 1.1em; font-weight: bold; color: {store['color']}; text-align: center; margin-bottom: 15px;">
                                {store['name']}
                            </div>
                            <div style="font-size: 0.75em; color: #aaa; text-align: center; margin-bottom: 10px;">
                                Fläche: {metrics['size']:,.0f} m²
                            </div>
                            <div style="display: grid; gap: 12px;">
                                <div style="background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #aaa; font-size: 0.8em;">Gewinn/m²</span>
                                        <span style="color: {color_gewinn}; font-weight: bold;">{score_gewinn:.0f}</span>
                                    </div>
                                    <div style="color: white; font-size: 1.1em; font-weight: bold;">{metrics['gewinn_m2']:,.2f} €</div>
                                </div>
                                <div style="background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #aaa; font-size: 0.8em;">Umsatz/m²</span>
                                        <span style="color: {color_umsatz}; font-weight: bold;">{score_umsatz:.0f}</span>
                                    </div>
                                    <div style="color: white; font-size: 1.1em; font-weight: bold;">{metrics['umsatz_m2']:,.2f} €</div>
                                </div>
                                <div style="background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #aaa; font-size: 0.8em;">Nettomarge</span>
                                        <span style="color: {color_marge}; font-weight: bold;">{score_marge:.0f}</span>
                                    </div>
                                    <div style="color: white; font-size: 1.1em; font-weight: bold;">{metrics['marge']:.1f}%</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # Legende
                st.markdown("""
                <div style="display: flex; justify-content: center; gap: 30px; margin-top: 15px; font-size: 0.8em;">
                    <span><span style="color: #00ff88;">●</span> Score ≥110 = Überdurchschnittlich</span>
                    <span><span style="color: #ffd93d;">●</span> Score 90-110 = Durchschnittlich</span>
                    <span><span style="color: #ff4757;">●</span> Score &lt;90 = Unterdurchschnittlich</span>
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

                # SUCCESS: SAY - Automatische Insights
                best_margin_store = max(active_stores, key=lambda s: stores_kpis[s['name']]['marge'])
                best_revenue_store = max(active_stores, key=lambda s: stores_kpis[s['name']]['umsatz'])
                best_profit_store = max(active_stores, key=lambda s: stores_kpis[s['name']]['nettogewinn'])

                insights = []
                if best_margin_store['name'] == best_profit_store['name']:
                    insights.append(f"<strong>{best_profit_store['name']}</strong> führt bei Marge UND Gewinn")
                else:
                    insights.append(f"<strong>{best_profit_store['name']}</strong> hat den höchsten Gewinn")
                    insights.append(f"<strong>{best_margin_store['name']}</strong> hat die beste Marge")

                if best_revenue_store['name'] != best_profit_store['name']:
                    insights.append(f"<strong>{best_revenue_store['name']}</strong> hat den höchsten Umsatz, aber nicht den höchsten Gewinn")

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(0,255,136,0.1), rgba(0,212,255,0.1));
                            border-left: 4px solid #00ff88; padding: 15px; border-radius: 0 10px 10px 0; margin-bottom: 20px;">
                    <strong style="color: #00ff88;">💡 Key Insights:</strong>
                    <span style="color: white;">{' | '.join(insights)}</span>
                </div>
                """, unsafe_allow_html=True)

                # KPI Cards
                if 'KPI-Karten' in selected_dashboard_sections:
                    st.subheader("📈 Key Performance Indicators")

                    # Dynamische Spalten basierend auf Anzahl Stores
                    n_stores = len(active_stores)
                    kpi_cols = st.columns(n_stores * 2)  # 2 KPIs pro Store (Umsatz, Gewinn)

                    col_idx = 0
                    for store in active_stores:
                        kpis = stores_kpis[store['name']]

                        # Umsatz
                        with kpi_cols[col_idx]:
                            st.markdown(render_kpi_card(
                                f"UMSATZ {store['name']}",
                                format_currency(kpis['umsatz']),
                                store['color']
                            ), unsafe_allow_html=True)
                        col_idx += 1

                        # Gewinn
                        with kpi_cols[col_idx]:
                            st.markdown(render_kpi_card(
                                f"GEWINN {store['name']}",
                                format_currency(kpis['nettogewinn']),
                                store['color']
                            ), unsafe_allow_html=True)
                        col_idx += 1

                    st.markdown("<br>", unsafe_allow_html=True)

                # Umsatz-Chart
                if 'Umsatz-Chart' in selected_dashboard_sections:
                    col_chart1, col_chart2 = st.columns(2)

                    with col_chart1:
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
                        st.plotly_chart(fig, use_container_width=True)

                    with col_chart2:
                        st.markdown(chart_header(
                            "📊 Nettogewinn-Entwicklung",
                            "<strong>Nettogewinn = Bruttogewinn - Kosten</strong><br>Zeigt den tatsächlichen Gewinn nach Abzug aller Kosten. Positive Werte = Profit, negative = Verlust."
                        ), unsafe_allow_html=True)

                        fig = go.Figure()
                        for store in active_stores:
                            store_df = stores_data[store['name']]
                            if monat_col in store_df.columns:
                                gewinn_col = next((c for c in store_df.columns if 'nettogewinn' in c.lower() and 'marge' not in c.lower() and 'prozent' not in c.lower()), None)
                                if gewinn_col:
                                    monthly = store_df.groupby(monat_col)[gewinn_col].sum().reset_index()
                                    fig.add_trace(go.Bar(
                                        x=monthly[monat_col],
                                        y=monthly[gewinn_col],
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

                # Margen-Vergleich
                if 'Margen-Vergleich' in selected_dashboard_sections:
                    st.markdown(chart_header(
                        "📈 Margen-Vergleich",
                        "<strong>Nettomarge = Nettogewinn / Umsatz × 100</strong><br>Zeigt wie viel Prozent vom Umsatz als Gewinn übrig bleibt. Höhere Marge = bessere Profitabilität."
                    ), unsafe_allow_html=True)

                    fig = go.Figure()
                    store_names_list = [s['name'] for s in active_stores]
                    margen = [stores_kpis[s['name']]['marge'] for s in active_stores]
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
                        yaxis_title="Nettomarge (%)",
                        transition={'duration': 500}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # KPI Radar
                if 'KPI-Radar' in selected_dashboard_sections:
                    st.markdown(chart_header(
                        "🎯 KPI-Radar",
                        "<strong>Normalisierte KPI-Übersicht</strong><br>Vergleicht alle Filialen auf einer Skala von 0-100. Je weiter außen, desto besser die Performance in dieser Kategorie."
                    ), unsafe_allow_html=True)

                    categories = ['Umsatz', 'Nettogewinn', 'Marge', 'Bruttogewinn']

                    fig = go.Figure()

                    for store in active_stores:
                        kpis = stores_kpis[store['name']]
                        # Normalisiere auf 0-100 Skala
                        max_umsatz = max(k['umsatz'] for k in stores_kpis.values())
                        max_gewinn = max(k['nettogewinn'] for k in stores_kpis.values())
                        max_brutto = max(k['bruttogewinn'] for k in stores_kpis.values())

                        values = [
                            (kpis['umsatz'] / max_umsatz * 100) if max_umsatz > 0 else 0,
                            (kpis['nettogewinn'] / max_gewinn * 100) if max_gewinn > 0 else 0,
                            kpis['marge'] * 3,  # Skalieren für bessere Sichtbarkeit
                            (kpis['bruttogewinn'] / max_brutto * 100) if max_brutto > 0 else 0
                        ]

                        fig.add_trace(go.Scatterpolar(
                            r=values + [values[0]],  # Schließe den Kreis
                            theta=categories + [categories[0]],
                            name=store['name'],
                            line_color=store['color'],
                            fill='toself',
                            fillcolor=store['color_bg']
                        ))

                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 100]),
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        showlegend=True,
                        transition={'duration': 500}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Datentabelle
                if 'Datentabelle' in selected_dashboard_sections:
                    st.markdown(chart_header(
                        "📋 Detaildaten",
                        "<strong>Rohdaten-Tabelle</strong><br>Alle Benchmark-Daten im Detail. Enthält Umsatz, Kosten, Margen und weitere KPIs für den gewählten Zeitraum."
                    ), unsafe_allow_html=True)
                    st.dataframe(filtered_df, use_container_width=True)

            # =============================================================
            # TAB 2: KOSTENANALYSE (NEU - SUCCESS-konform)
            # =============================================================
            with tab_costs:
                st.subheader("💸 Kostenanalyse")

                # Insight-Box: Automatische Botschaft (SUCCESS: SAY)
                total_costs = {s['name']: stores_kpis[s['name']]['kosten'] for s in active_stores}
                lowest_cost_store = min(total_costs, key=total_costs.get)
                highest_cost_store = max(total_costs, key=total_costs.get)
                cost_diff = total_costs[highest_cost_store] - total_costs[lowest_cost_store]

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(123,44,191,0.1));
                            border-left: 4px solid #00d4ff; padding: 15px; border-radius: 0 10px 10px 0; margin-bottom: 20px;">
                    <strong style="color: #00d4ff;">📊 Insight:</strong>
                    <span style="color: white;">{lowest_cost_store} hat die niedrigsten Gesamtkosten.
                    Differenz zu {highest_cost_store}: <strong style="color: #00ff88;">{format_currency(cost_diff)}</strong></span>
                </div>
                """, unsafe_allow_html=True)

                # Gesamtkosten-KPIs für alle Filialen
                st.markdown(chart_header(
                    "💰 Gesamtkosten je Filiale",
                    "<strong>Gesamtkosten = Wareneinsatz + Betriebskosten + Personalkosten + Beschaffungskosten</strong><br>Wareneinsatz = Umsatz - Bruttogewinn. Personalkosten = Gehalt + Sozialkosten + Provision. Betriebskosten = Miete + Marketing."
                ), unsafe_allow_html=True)

                cost_cols = st.columns(len(active_stores))
                for idx, store in enumerate(active_stores):
                    with cost_cols[idx]:
                        kosten = stores_kpis[store['name']]['kosten']
                        umsatz = stores_kpis[store['name']]['umsatz']

                        # Rang bestimmen
                        sorted_costs = sorted(total_costs.items(), key=lambda x: x[1])
                        rang = [i+1 for i, (name, _) in enumerate(sorted_costs) if name == store['name']][0]
                        rang_text = ["🥇", "🥈", "🥉"][rang-1] if rang <= 3 else f"#{rang}"

                        st.markdown(f"""
                        <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                    border-radius: 15px; padding: 20px; text-align: center;">
                            <div style="font-size: 0.9em; color: #aaa;">{store['name']}</div>
                            <div style="font-size: 2em; font-weight: bold; color: {store['color']};">{format_currency(kosten)}</div>
                            <div style="font-size: 1.2em; margin-top: 5px;">{rang_text}</div>
                            <div style="font-size: 0.7em; color: #aaa; margin-top: 5px;">Gesamtkosten</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Waterfall-Chart: Vom Umsatz zum Gewinn
                st.markdown(chart_header(
                    "📉 Gewinnbrücke (Waterfall)",
                    "<strong>Von Umsatz zu Nettogewinn</strong><br>Umsatz - Wareneinsatz - Personalkosten - Betriebskosten - Beschaffungskosten = Nettogewinn. Grün = positiv, Rot = Kostenabzug."
                ), unsafe_allow_html=True)

                waterfall_cols = st.columns(len(active_stores))

                for idx, store in enumerate(active_stores):
                    with waterfall_cols[idx]:
                        kpis = stores_kpis[store['name']]

                        # Waterfall-Daten aus KPIs (mit neuer Formel)
                        umsatz = kpis['umsatz']
                        wareneinsatz = kpis['wareneinsatz']
                        personalkosten = kpis['personalkosten']
                        betriebskosten = kpis['betriebskosten']
                        beschaffungskosten = kpis['beschaffungskosten']
                        nettogewinn = kpis['nettogewinn']

                        fig = go.Figure(go.Waterfall(
                            orientation="v",
                            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                            x=["Umsatz", "Wareneinsatz", "Personal", "Betrieb", "Beschaffung", "Nettogewinn"],
                            y=[umsatz, -wareneinsatz, -personalkosten, -betriebskosten, -beschaffungskosten, nettogewinn],
                            connector={"line": {"color": "rgba(255,255,255,0.3)"}},
                            increasing={"marker": {"color": "#00ff88"}},
                            decreasing={"marker": {"color": "#ff4757"}},
                            totals={"marker": {"color": store['color']}},
                            text=[format_currency(umsatz), format_currency(-wareneinsatz),
                                  format_currency(-personalkosten), format_currency(-betriebskosten),
                                  format_currency(-beschaffungskosten), format_currency(nettogewinn)],
                            textposition="outside"
                        ))

                        fig.update_layout(
                            title=dict(text=store['name'], font=dict(color=store['color'], size=14)),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            showlegend=False,
                            height=400,
                            margin=dict(t=50, b=50),
                            transition={'duration': 500}
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # Kostenstruktur-Vergleich (Stacked Bar)
                st.markdown(chart_header(
                    "📊 Kostenstruktur im Vergleich",
                    "<strong>Aufschlüsselung der Gesamtkosten</strong><br>Gesamtkosten = Wareneinsatz + Personalkosten + Betriebskosten + Beschaffungskosten. Ideal für Effizienzvergleiche."
                ), unsafe_allow_html=True)

                fig = go.Figure()

                # Kostenkategorien für alle Stores (mit echten Daten aus KPIs)
                for store in active_stores:
                    kpis = stores_kpis[store['name']]
                    wareneinsatz = kpis['wareneinsatz']
                    personalkosten = kpis['personalkosten']
                    betriebskosten = kpis['betriebskosten']
                    beschaffungskosten = kpis['beschaffungskosten']

                    fig.add_trace(go.Bar(
                        name='Wareneinsatz',
                        x=[store['name']],
                        y=[wareneinsatz],
                        marker_color='#74b9ff',
                        text=[format_currency(wareneinsatz)],
                        textposition='inside',
                        showlegend=True if store == active_stores[0] else False
                    ))
                    fig.add_trace(go.Bar(
                        name='Personalkosten',
                        x=[store['name']],
                        y=[personalkosten],
                        marker_color='#ff6b6b',
                        text=[format_currency(personalkosten)],
                        textposition='inside',
                        showlegend=True if store == active_stores[0] else False
                    ))
                    fig.add_trace(go.Bar(
                        name='Betriebskosten',
                        x=[store['name']],
                        y=[betriebskosten],
                        marker_color='#ffd93d',
                        text=[format_currency(betriebskosten)],
                        textposition='inside',
                        showlegend=True if store == active_stores[0] else False
                    ))
                    fig.add_trace(go.Bar(
                        name='Beschaffung',
                        x=[store['name']],
                        y=[beschaffungskosten],
                        marker_color='#a55eea',
                        text=[format_currency(beschaffungskosten)],
                        textposition='inside',
                        showlegend=True if store == active_stores[0] else False
                    ))

                fig.update_layout(
                    barmode='stack',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    yaxis_title="Kosten (€)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    transition={'duration': 500}
                )
                st.plotly_chart(fig, use_container_width=True)

                # Kosten-Effizienz KPIs
                st.markdown(chart_header(
                    "📈 Kosten-Effizienz",
                    "<strong>Kosten im Verhältnis zum Umsatz</strong><br>Niedrigere Werte = höhere Effizienz. Zeigt wie viel Euro Kosten pro Euro Umsatz anfallen."
                ), unsafe_allow_html=True)

                eff_cols = st.columns(len(active_stores))
                for idx, store in enumerate(active_stores):
                    with eff_cols[idx]:
                        kpis = stores_kpis[store['name']]
                        kosten_quote = (kpis['kosten'] / kpis['umsatz'] * 100) if kpis['umsatz'] > 0 else 0

                        # Effizienz-Bewertung
                        if kosten_quote < 15:
                            eff_color = "#00ff88"
                            eff_label = "Sehr effizient"
                        elif kosten_quote < 20:
                            eff_color = "#ffd93d"
                            eff_label = "Durchschnittlich"
                        else:
                            eff_color = "#ff4757"
                            eff_label = "Optimierbar"

                        st.markdown(f"""
                        <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                    border-radius: 15px; padding: 20px; text-align: center;">
                            <div style="font-size: 0.9em; color: #aaa;">{store['name']}</div>
                            <div style="font-size: 2.5em; font-weight: bold; color: {store['color']};">{kosten_quote:.1f}%</div>
                            <div style="font-size: 0.8em; color: {eff_color};">{eff_label}</div>
                            <div style="font-size: 0.7em; color: #aaa; margin-top: 5px;">Kostenquote</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Mietkosten-Berechnung aus T_Location
                st.markdown(chart_header(
                    "🏢 Mietkosten-Berechnung (T_Location)",
                    "<strong>Formel: Monatliche Miete = Fläche (m²) × (Miete/m² + Nebenkosten/m²)</strong><br>"
                    "Die Mietkosten werden aus den Stammdaten der T_Location Tabelle berechnet. "
                    "Diese Berechnung zeigt die <strong>korrekten</strong> monatlichen Mietkosten basierend auf Fläche und Quadratmeterpreisen."
                ), unsafe_allow_html=True)

                df_location = load_location_data()

                if df_location is not None and len(df_location) > 0:
                    # Tabelle mit Mietberechnung erstellen
                    rent_data = []
                    for _, row in df_location.iterrows():
                        store_name = row['StoreName']
                        size = row['LOC_SIZE_M2']
                        rent_m2 = row['LOC_RENT_EUR_M2']
                        neben_m2 = row['LOC_NEBENKOSTEN_EUR']
                        total_m2 = rent_m2 + neben_m2
                        monthly_rent = row['MonthlyRentCalculated']

                        # Store-Farbe finden
                        store_config = next((s for s in active_stores if s['name'].lower() in store_name.lower()), None)
                        color = store_config['color'] if store_config else '#ffffff'

                        rent_data.append({
                            'Filiale': store_name,
                            'Fläche (m²)': f"{size:,.0f}",
                            'Miete/m²': f"{rent_m2:,.2f} €",
                            'Nebenkosten/m²': f"{neben_m2:,.2f} €",
                            'Gesamt/m²': f"{total_m2:,.2f} €",
                            'Monatliche Miete': f"{monthly_rent:,.2f} €",
                            '_color': color
                        })

                    # Als styled Cards anzeigen
                    rent_cols = st.columns(len(rent_data))
                    for idx, rent_info in enumerate(rent_data):
                        with rent_cols[idx]:
                            st.markdown(f"""
                            <div class="hover-card" style="background: rgba(255,255,255,0.05); border: 1px solid {rent_info['_color']};
                                        border-radius: 15px; padding: 20px;">
                                <div style="font-size: 1.1em; font-weight: bold; color: {rent_info['_color']}; margin-bottom: 15px; text-align: center;">
                                    {rent_info['Filiale']}
                                </div>
                                <div style="display: grid; gap: 8px; font-size: 0.85em;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: #aaa;">Fläche:</span>
                                        <span style="color: white;">{rent_info['Fläche (m²)']} m²</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: #aaa;">Miete/m²:</span>
                                        <span style="color: white;">{rent_info['Miete/m²']}</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: #aaa;">Nebenkosten/m²:</span>
                                        <span style="color: white;">{rent_info['Nebenkosten/m²']}</span>
                                    </div>
                                    <div style="border-top: 1px solid rgba(255,255,255,0.2); margin: 5px 0;"></div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: #aaa;">Gesamt/m²:</span>
                                        <span style="color: #ffd93d; font-weight: bold;">{rent_info['Gesamt/m²']}</span>
                                    </div>
                                </div>
                                <div style="background: linear-gradient(135deg, rgba(0,255,136,0.2), rgba(0,212,255,0.1));
                                            border-radius: 10px; padding: 12px; margin-top: 15px; text-align: center;">
                                    <div style="font-size: 0.75em; color: #aaa;">MONATLICHE MIETE</div>
                                    <div style="font-size: 1.4em; font-weight: bold; color: #00ff88;">{rent_info['Monatliche Miete']}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    # Berechnungsformel als Info-Box
                    st.markdown("""
                    <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                                border-radius: 10px; padding: 15px; margin-top: 20px;">
                        <div style="color: #00d4ff; font-weight: bold; margin-bottom: 10px;">📐 Berechnungsformel:</div>
                        <div style="font-family: monospace; color: white; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px;">
                            Monatliche Miete = Fläche (m²) × (Miete EUR/m² + Nebenkosten EUR/m²)
                        </div>
                        <div style="color: #aaa; font-size: 0.85em; margin-top: 10px;">
                            <strong>Beispiel Freiburg:</strong> 1.240 m² × (14,50 € + 4,00 €) = 1.240 × 18,50 € = <strong style="color: #00ff88;">22.940,00 €</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("T_Location Daten konnten nicht geladen werden.")

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

                        # Durchschnittspreis
                        if 'Durchschnittspreis' in selected_cat_sections and price_col:
                            st.markdown(chart_header(
                                "💵 Durchschnittspreis nach Kategorie",
                                "<strong>Mittlerer Verkaufspreis (EUR)</strong><br>Durchschnittlicher Preis pro Kategorie. Preisunterschiede zwischen Filialen können auf unterschiedliche Produktmix oder Rabattstrategien hinweisen."
                            ), unsafe_allow_html=True)

                            fig = go.Figure()

                            for store in active_stores:
                                store_cat_data = filter_by_store(df_filtered_cat, store)
                                cat_avg = store_cat_data.groupby(cat_col)[price_col].mean()

                                fig.add_trace(go.Bar(
                                    name=store['name'],
                                    x=cat_avg.index,
                                    y=cat_avg.values,
                                    marker_color=store['color']
                                ))

                            fig.update_layout(
                                barmode='group',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                xaxis_title="Kategorie",
                                yaxis_title="Ø Preis (€)",
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
