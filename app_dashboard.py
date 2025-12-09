"""
Benchmark Dashboard - Gruppe 18
Streamlit-basiertes Web-Dashboard für den Filialvergleich Rosenheim vs. Freiburg
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db_connect import get_connection

# Farben wie im HTML-Dashboard
COLORS = {
    'rosenheim': '#00d4ff',
    'rosenheim_bg': 'rgba(0, 212, 255, 0.2)',
    'freiburg': '#7b2cbf',
    'freiburg_bg': 'rgba(123, 44, 191, 0.2)',
    'positive': '#00ff88',
    'negative': '#ff4757'
}

# Kategorien-Farben
CAT_COLORS = {
    'E-Bike': '#00d4ff',
    'MTB': '#7b2cbf',
    'City/Trekking': '#00ff88',
    'Kinder': '#ff6b6b',
    'Sonstige': '#ffd93d'
}

# Seiten-Konfiguration
st.set_page_config(
    page_title="Gruppe 18 - Benchmark Dashboard",
    page_icon="📊",
    layout="wide"
)

# Dark Theme CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .main-header {
        text-align: center;
        padding: 20px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        margin-bottom: 5px;
    }
    .main-header p {
        color: #aaa;
    }
    .kpi-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .kpi-title {
        font-size: 0.85em;
        color: #aaa;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .kpi-value-rosenheim {
        font-size: 1.8em;
        font-weight: bold;
        color: #00d4ff;
    }
    .kpi-value-freiburg {
        font-size: 1.8em;
        font-weight: bold;
        color: #7b2cbf;
    }
    .kpi-comparison-positive {
        background: rgba(0, 255, 136, 0.2);
        color: #00ff88;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
    }
    .kpi-comparison-negative {
        background: rgba(255, 71, 87, 0.2);
        color: #ff4757;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
    }
    .kpi-comparison-neutral {
        background: rgba(255, 255, 255, 0.1);
        color: #aaa;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
    }
    .month-indicator {
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        color: white;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>Benchmark Dashboard</h1>
    <p>Gruppe 18 | Rosenheim vs. Freiburg/Karlsruhe</p>
</div>
""", unsafe_allow_html=True)

# Monatsnamen
MONTH_NAMES = {
    'all': 'Gesamtjahr 2024',
    '2024-01': 'Januar 2024', '2024-02': 'Februar 2024', '2024-03': 'März 2024',
    '2024-04': 'April 2024', '2024-05': 'Mai 2024', '2024-06': 'Juni 2024',
    '2024-07': 'Juli 2024', '2024-08': 'August 2024', '2024-09': 'September 2024',
    '2024-10': 'Oktober 2024', '2024-11': 'November 2024', '2024-12': 'Dezember 2024'
}

# Daten laden
@st.cache_data(ttl=300)
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

# Hilfsfunktionen
def format_currency(value):
    if value >= 1000000:
        return f"{value/1000000:.1f} Mio €"
    elif value >= 1000:
        return f"{value/1000:.0f} Tsd €"
    else:
        return f"{value:,.0f} €"

def format_percent(value):
    return f"{value:.1f}%"

def safe_sum(df, col_pattern):
    col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
    return df[col].sum() if col else 0

def safe_mean(df, col_pattern):
    col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
    return df[col].mean() if col else 0

# Daten laden
df = load_data()

if df is not None and len(df) > 0:
    cols = df.columns.tolist()

    # Spaltennamen finden
    monat_col = next((c for c in cols if 'monat' in c.lower() or 'month' in c.lower()), None)
    filiale_col = next((c for c in cols if 'filial' in c.lower() or 'store' in c.lower() or 'gruppe' in c.lower()), None)

    if monat_col and filiale_col:
        # Filter Section - kompakter
        col_filter, col_indicator, col_spacer = st.columns([1, 1, 2])

        with col_filter:
            available_months = ['all'] + sorted(df[monat_col].unique().tolist())
            month_options = {m: MONTH_NAMES.get(m, m) for m in available_months}
            selected_month = st.selectbox("Zeitraum:", options=list(month_options.keys()),
                                          format_func=lambda x: month_options[x])

        with col_indicator:
            st.markdown("<br>", unsafe_allow_html=True)  # Vertikale Ausrichtung
            st.markdown(f'<div class="month-indicator">{month_options[selected_month]}</div>', unsafe_allow_html=True)

        # Daten filtern
        filtered_df = df if selected_month == 'all' else df[df[monat_col] == selected_month]

        # Filialen identifizieren
        filialen = filtered_df[filiale_col].unique().tolist()
        rosenheim_name = next((f for f in filialen if 'rosen' in f.lower()), filialen[0] if filialen else None)
        freiburg_name = next((f for f in filialen if 'frei' in f.lower() or 'karlsruhe' in f.lower()), filialen[1] if len(filialen) > 1 else None)

        # =============================================
        # TABS OBEN
        # =============================================
        tab_main, tab_categories, tab_data = st.tabs(["📊 Dashboard", "🚲 Produktkategorien", "📋 Rohdaten"])

        if rosenheim_name and freiburg_name:
            df_rosenheim = filtered_df[filtered_df[filiale_col] == rosenheim_name]
            df_freiburg = filtered_df[filtered_df[filiale_col] == freiburg_name]

            # =============================================
            # TAB 1: DASHBOARD
            # =============================================
            with tab_main:
                # KPIs berechnen
                umsatz_ros = safe_sum(df_rosenheim, 'umsatz')
                umsatz_fre = safe_sum(df_freiburg, 'umsatz')
                nettogewinn_ros = safe_sum(df_rosenheim, 'nettogewinn')
                nettogewinn_fre = safe_sum(df_freiburg, 'nettogewinn')
                marge_ros = safe_mean(df_rosenheim, 'nettogewinnmarge')
                marge_fre = safe_mean(df_freiburg, 'nettogewinnmarge')

                umsatz_diff = ((umsatz_ros / umsatz_fre) - 1) * 100 if umsatz_fre > 0 else 0
                marge_diff = marge_ros - marge_fre
                gewinn_diff = ((nettogewinn_ros / nettogewinn_fre) - 1) * 100 if nettogewinn_fre > 0 else 0

                # KPI Cards
                col1, col2, col3, col4, col5, col6 = st.columns(6)

                with col1:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-title">Umsatz Rosenheim</div>
                        <div class="kpi-value-rosenheim">{format_currency(umsatz_ros)}</div>
                        <span class="{'kpi-comparison-positive' if umsatz_diff >= 0 else 'kpi-comparison-negative'}">{'+' if umsatz_diff >= 0 else ''}{umsatz_diff:.1f}% vs FK</span>
                    </div>""", unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-title">Umsatz Freiburg/K.</div>
                        <div class="kpi-value-freiburg">{format_currency(umsatz_fre)}</div>
                        <span class="kpi-comparison-neutral">Benchmark</span>
                    </div>""", unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-title">Nettomarge Rosenheim</div>
                        <div class="kpi-value-rosenheim">{format_percent(marge_ros)}</div>
                        <span class="{'kpi-comparison-positive' if marge_diff >= 0 else 'kpi-comparison-negative'}">{'+' if marge_diff >= 0 else ''}{marge_diff:.1f}pp</span>
                    </div>""", unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-title">Nettomarge Freiburg/K.</div>
                        <div class="kpi-value-freiburg">{format_percent(marge_fre)}</div>
                        <span class="kpi-comparison-neutral">Benchmark</span>
                    </div>""", unsafe_allow_html=True)

                with col5:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-title">Gewinn Rosenheim</div>
                        <div class="kpi-value-rosenheim">{format_currency(nettogewinn_ros)}</div>
                        <span class="{'kpi-comparison-positive' if gewinn_diff >= 0 else 'kpi-comparison-negative'}">{'+' if gewinn_diff >= 0 else ''}{gewinn_diff:.1f}%</span>
                    </div>""", unsafe_allow_html=True)

                with col6:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-title">Gewinn Freiburg/K.</div>
                        <div class="kpi-value-freiburg">{format_currency(nettogewinn_fre)}</div>
                        <span class="kpi-comparison-neutral">Benchmark</span>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # Charts
                is_single_month = selected_month != 'all'
                col_chart1, col_chart2 = st.columns(2)

                # Spaltennamen finden
                umsatz_col_name = next((c for c in df.columns if 'umsatz' in c.lower() and 'eur' in c.lower()), None)
                gewinn_col_name = next((c for c in df.columns if 'nettogewinn' in c.lower() and 'marge' not in c.lower() and 'prozent' not in c.lower()), None)

                with col_chart1:
                    st.subheader("Umsatz-Vergleich" if is_single_month else "Umsatzentwicklung")
                    if is_single_month:
                        fig = go.Figure(data=[go.Bar(y=['Rosenheim', 'Freiburg/Karlsruhe'], x=[umsatz_ros, umsatz_fre],
                                                     orientation='h', marker_color=[COLORS['rosenheim'], COLORS['freiburg']])])
                    else:
                        fig = go.Figure()
                        if umsatz_col_name:
                            fig.add_trace(go.Scatter(x=df_rosenheim[monat_col], y=df_rosenheim[umsatz_col_name],
                                                     name='Rosenheim', line=dict(color=COLORS['rosenheim']),
                                                     fill='tozeroy', fillcolor=COLORS['rosenheim_bg']))
                            fig.add_trace(go.Scatter(x=df_freiburg[monat_col], y=df_freiburg[umsatz_col_name],
                                                     name='Freiburg/Karlsruhe', line=dict(color=COLORS['freiburg']),
                                                     fill='tozeroy', fillcolor=COLORS['freiburg_bg']))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
                    st.plotly_chart(fig, use_container_width=True)

                with col_chart2:
                    st.subheader("Nettogewinn-Vergleich" if is_single_month else "Nettogewinn-Entwicklung")
                    if is_single_month:
                        fig = go.Figure(data=[go.Bar(y=['Rosenheim', 'Freiburg/Karlsruhe'], x=[nettogewinn_ros, nettogewinn_fre],
                                                     orientation='h', marker_color=[COLORS['rosenheim'], COLORS['freiburg']])])
                    else:
                        fig = go.Figure()
                        if gewinn_col_name:
                            fig.add_trace(go.Bar(x=df_rosenheim[monat_col], y=df_rosenheim[gewinn_col_name],
                                                 name='Rosenheim', marker_color=COLORS['rosenheim']))
                            fig.add_trace(go.Bar(x=df_freiburg[monat_col], y=df_freiburg[gewinn_col_name],
                                                 name='Freiburg/Karlsruhe', marker_color=COLORS['freiburg']))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', barmode='group')
                    st.plotly_chart(fig, use_container_width=True)

                # Zweite Reihe
                col_chart3, col_chart4 = st.columns(2)
                brutto_col = next((c for c in df.columns if 'brutto' in c.lower() and 'marge' in c.lower()), None)
                netto_col = next((c for c in df.columns if 'netto' in c.lower() and 'marge' in c.lower()), None)

                with col_chart3:
                    st.subheader("Margen-Vergleich (%)")
                    fig = go.Figure()
                    if brutto_col and netto_col:
                        if is_single_month:
                            fig.add_trace(go.Bar(x=['Bruttomarge', 'Nettomarge'],
                                                 y=[df_rosenheim[brutto_col].mean(), df_rosenheim[netto_col].mean()],
                                                 name='Rosenheim', marker_color=COLORS['rosenheim']))
                            fig.add_trace(go.Bar(x=['Bruttomarge', 'Nettomarge'],
                                                 y=[df_freiburg[brutto_col].mean(), df_freiburg[netto_col].mean()],
                                                 name='Freiburg/Karlsruhe', marker_color=COLORS['freiburg']))
                        else:
                            fig.add_trace(go.Scatter(x=df_rosenheim[monat_col], y=df_rosenheim[brutto_col],
                                                     name='Bruttomarge RO', line=dict(color=COLORS['rosenheim'])))
                            fig.add_trace(go.Scatter(x=df_freiburg[monat_col], y=df_freiburg[brutto_col],
                                                     name='Bruttomarge FK', line=dict(color=COLORS['freiburg'])))
                            fig.add_trace(go.Scatter(x=df_rosenheim[monat_col], y=df_rosenheim[netto_col],
                                                     name='Nettomarge RO', line=dict(color=COLORS['rosenheim'], dash='dash')))
                            fig.add_trace(go.Scatter(x=df_freiburg[monat_col], y=df_freiburg[netto_col],
                                                     name='Nettomarge FK', line=dict(color=COLORS['freiburg'], dash='dash')))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', barmode='group')
                    st.plotly_chart(fig, use_container_width=True)

                with col_chart4:
                    st.subheader("Kostenstruktur")
                    personal_col = next((c for c in df.columns if 'personal' in c.lower() and 'eur' in c.lower()), None)
                    betriebs_col = next((c for c in df.columns if 'betrieb' in c.lower() and 'eur' in c.lower()), None)
                    if personal_col and betriebs_col:
                        fig = go.Figure()
                        fig.add_trace(go.Bar(x=['Rosenheim', 'Freiburg/Karlsruhe'],
                                             y=[df_rosenheim[personal_col].sum(), df_freiburg[personal_col].sum()],
                                             name='Personalkosten', marker_color=[COLORS['rosenheim'], COLORS['freiburg']]))
                        fig.add_trace(go.Bar(x=['Rosenheim', 'Freiburg/Karlsruhe'],
                                             y=[df_rosenheim[betriebs_col].sum(), df_freiburg[betriebs_col].sum()],
                                             name='Betriebskosten', marker_color=[COLORS['rosenheim_bg'], COLORS['freiburg_bg']]))
                        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', barmode='stack')
                        st.plotly_chart(fig, use_container_width=True)

                # Radar Chart
                st.markdown("---")
                st.subheader("KPI-Vergleich")

                betriebs_quote_col = next((c for c in df.columns if 'betrieb' in c.lower() and 'quote' in c.lower()), None)
                personal_anteil_col = next((c for c in df.columns if 'personal' in c.lower() and 'anteil' in c.lower()), None)

                if brutto_col and netto_col:
                    categories = ['Bruttomarge', 'Nettomarge', 'Betriebseffizienz', 'Personalkosteneffizienz']
                    ros_values = [
                        df_rosenheim[brutto_col].mean() if brutto_col else 0,
                        df_rosenheim[netto_col].mean() if netto_col else 0,
                        20 - df_rosenheim[betriebs_quote_col].mean() if betriebs_quote_col else 10,
                        100 - df_rosenheim[personal_anteil_col].mean() if personal_anteil_col else 50
                    ]
                    fre_values = [
                        df_freiburg[brutto_col].mean() if brutto_col else 0,
                        df_freiburg[netto_col].mean() if netto_col else 0,
                        20 - df_freiburg[betriebs_quote_col].mean() if betriebs_quote_col else 10,
                        100 - df_freiburg[personal_anteil_col].mean() if personal_anteil_col else 50
                    ]

                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=ros_values, theta=categories, fill='toself', name='Rosenheim',
                                                  fillcolor=COLORS['rosenheim_bg'], line_color=COLORS['rosenheim']))
                    fig.add_trace(go.Scatterpolar(r=fre_values, theta=categories, fill='toself', name='Freiburg/Karlsruhe',
                                                  fillcolor=COLORS['freiburg_bg'], line_color=COLORS['freiburg']))
                    fig.update_layout(
                        polar=dict(
                            bgcolor='rgba(0,0,0,0)',
                            radialaxis=dict(visible=True, color='white', gridcolor='rgba(255,255,255,0.2)'),
                            angularaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Datentabelle
                st.markdown("---")
                st.subheader("Detaillierte Daten")
                display_cols = [c for c in df.columns if any(x in c.lower() for x in ['monat', 'filial', 'umsatz', 'gewinn', 'marge'])]
                st.dataframe(filtered_df[display_cols] if display_cols else filtered_df, use_container_width=True, hide_index=True)

                csv = filtered_df.to_csv(index=False)
                st.download_button("📥 Daten als CSV herunterladen", csv, f"benchmark_export_{selected_month}.csv", "text/csv")

            # =============================================
            # TAB 2: PRODUKTKATEGORIEN
            # =============================================
            with tab_categories:
                st.subheader("🚲 Produktkategorien-Analyse")
                st.markdown("Umsatz und Performance nach Fahrrad-Kategorie")

                df_sales_agg = load_sales_agg_data()

                if df_sales_agg is not None and len(df_sales_agg) > 0:
                    cat_col = next((c for c in df_sales_agg.columns if 'category' in c.lower()), None)
                    store_col = next((c for c in df_sales_agg.columns if 'store' in c.lower() and 'id' not in c.lower()), None)
                    month_col_agg = next((c for c in df_sales_agg.columns if 'month' in c.lower() or 'calmonth' in c.lower()), None)
                    revenue_col = next((c for c in df_sales_agg.columns if 'revenue' in c.lower()), None)
                    quantity_col = next((c for c in df_sales_agg.columns if 'quantity' in c.lower()), None)
                    profit_col = next((c for c in df_sales_agg.columns if 'profit' in c.lower()), None)
                    price_col = next((c for c in df_sales_agg.columns if 'price' in c.lower() or 'preis' in c.lower()), None)

                    if cat_col and store_col and revenue_col:
                        # Filtern nach Monat
                        if selected_month != 'all' and month_col_agg:
                            df_cat = df_sales_agg[df_sales_agg[month_col_agg] == selected_month]
                        else:
                            df_cat = df_sales_agg

                        stores = df_cat[store_col].unique().tolist()
                        ros_store = next((s for s in stores if 'rosen' in s.lower()), None)
                        fk_stores = [s for s in stores if 'frei' in s.lower() or 'karl' in s.lower()]

                        df_ros_cat = df_cat[df_cat[store_col] == ros_store].groupby(cat_col)[revenue_col].sum().reset_index() if ros_store else pd.DataFrame()
                        df_fk_cat = df_cat[df_cat[store_col].isin(fk_stores)].groupby(cat_col)[revenue_col].sum().reset_index() if fk_stores else pd.DataFrame()

                        # === UMSATZ DONUT CHARTS ===
                        st.markdown("### 💰 Umsatzverteilung")
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("#### Rosenheim")
                            if len(df_ros_cat) > 0:
                                fig = go.Figure(data=[go.Pie(labels=df_ros_cat[cat_col], values=df_ros_cat[revenue_col],
                                                             marker_colors=[CAT_COLORS.get(c, '#888') for c in df_ros_cat[cat_col]], hole=0.4)])
                                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                                st.plotly_chart(fig, use_container_width=True)

                        with col2:
                            st.markdown("#### Freiburg/Karlsruhe")
                            if len(df_fk_cat) > 0:
                                fig = go.Figure(data=[go.Pie(labels=df_fk_cat[cat_col], values=df_fk_cat[revenue_col],
                                                             marker_colors=[CAT_COLORS.get(c, '#888') for c in df_fk_cat[cat_col]], hole=0.4)])
                                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                                st.plotly_chart(fig, use_container_width=True)

                        # === UMSATZ BALKENVERGLEICH ===
                        st.markdown("---")
                        st.markdown("### 📊 Kategorien-Vergleich: Umsatz")
                        all_cats = sorted(set(list(df_ros_cat[cat_col].unique() if len(df_ros_cat) > 0 else []) +
                                             list(df_fk_cat[cat_col].unique() if len(df_fk_cat) > 0 else [])))

                        ros_vals = [df_ros_cat[df_ros_cat[cat_col] == c][revenue_col].sum() if len(df_ros_cat) > 0 else 0 for c in all_cats]
                        fk_vals = [df_fk_cat[df_fk_cat[cat_col] == c][revenue_col].sum() if len(df_fk_cat) > 0 else 0 for c in all_cats]

                        fig = go.Figure()
                        fig.add_trace(go.Bar(name='Rosenheim', x=all_cats, y=ros_vals, marker_color=COLORS['rosenheim']))
                        fig.add_trace(go.Bar(name='Freiburg/Karlsruhe', x=all_cats, y=fk_vals, marker_color=COLORS['freiburg']))
                        fig.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                          font_color='white', xaxis_title='Kategorie', yaxis_title='Umsatz (EUR)')
                        st.plotly_chart(fig, use_container_width=True)

                        # === STÜCKZAHLEN VERGLEICH ===
                        if quantity_col:
                            st.markdown("---")
                            st.markdown("### 📦 Verkaufte Stückzahlen")

                            df_ros_qty = df_cat[df_cat[store_col] == ros_store].groupby(cat_col)[quantity_col].sum().reset_index() if ros_store else pd.DataFrame()
                            df_fk_qty = df_cat[df_cat[store_col].isin(fk_stores)].groupby(cat_col)[quantity_col].sum().reset_index() if fk_stores else pd.DataFrame()

                            ros_qty = [df_ros_qty[df_ros_qty[cat_col] == c][quantity_col].sum() if len(df_ros_qty) > 0 else 0 for c in all_cats]
                            fk_qty = [df_fk_qty[df_fk_qty[cat_col] == c][quantity_col].sum() if len(df_fk_qty) > 0 else 0 for c in all_cats]

                            fig = go.Figure()
                            fig.add_trace(go.Bar(name='Rosenheim', x=all_cats, y=ros_qty, marker_color=COLORS['rosenheim']))
                            fig.add_trace(go.Bar(name='Freiburg/Karlsruhe', x=all_cats, y=fk_qty, marker_color=COLORS['freiburg']))
                            fig.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                              font_color='white', xaxis_title='Kategorie', yaxis_title='Stückzahl')
                            st.plotly_chart(fig, use_container_width=True)

                        # === DURCHSCHNITTSPREIS VERGLEICH ===
                        if price_col:
                            st.markdown("---")
                            st.markdown("### 💵 Durchschnittlicher Verkaufspreis")

                            df_ros_price = df_cat[df_cat[store_col] == ros_store].groupby(cat_col)[price_col].mean().reset_index() if ros_store else pd.DataFrame()
                            df_fk_price = df_cat[df_cat[store_col].isin(fk_stores)].groupby(cat_col)[price_col].mean().reset_index() if fk_stores else pd.DataFrame()

                            ros_price = [df_ros_price[df_ros_price[cat_col] == c][price_col].mean() if len(df_ros_price) > 0 and c in df_ros_price[cat_col].values else 0 for c in all_cats]
                            fk_price = [df_fk_price[df_fk_price[cat_col] == c][price_col].mean() if len(df_fk_price) > 0 and c in df_fk_price[cat_col].values else 0 for c in all_cats]

                            fig = go.Figure()
                            fig.add_trace(go.Bar(name='Rosenheim', x=all_cats, y=ros_price, marker_color=COLORS['rosenheim']))
                            fig.add_trace(go.Bar(name='Freiburg/Karlsruhe', x=all_cats, y=fk_price, marker_color=COLORS['freiburg']))
                            fig.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                              font_color='white', xaxis_title='Kategorie', yaxis_title='Ø Preis (EUR)')
                            st.plotly_chart(fig, use_container_width=True)

                        # === BRUTTOGEWINN VERGLEICH ===
                        if profit_col:
                            st.markdown("---")
                            st.markdown("### 📈 Bruttogewinn nach Kategorie")

                            df_ros_profit = df_cat[df_cat[store_col] == ros_store].groupby(cat_col)[profit_col].sum().reset_index() if ros_store else pd.DataFrame()
                            df_fk_profit = df_cat[df_cat[store_col].isin(fk_stores)].groupby(cat_col)[profit_col].sum().reset_index() if fk_stores else pd.DataFrame()

                            ros_profit = [df_ros_profit[df_ros_profit[cat_col] == c][profit_col].sum() if len(df_ros_profit) > 0 else 0 for c in all_cats]
                            fk_profit = [df_fk_profit[df_fk_profit[cat_col] == c][profit_col].sum() if len(df_fk_profit) > 0 else 0 for c in all_cats]

                            fig = go.Figure()
                            fig.add_trace(go.Bar(name='Rosenheim', x=all_cats, y=ros_profit, marker_color=COLORS['rosenheim']))
                            fig.add_trace(go.Bar(name='Freiburg/Karlsruhe', x=all_cats, y=fk_profit, marker_color=COLORS['freiburg']))
                            fig.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                              font_color='white', xaxis_title='Kategorie', yaxis_title='Bruttogewinn (EUR)')
                            st.plotly_chart(fig, use_container_width=True)

                        # === ZEITLICHER TREND ===
                        if month_col_agg and selected_month == 'all':
                            st.markdown("---")
                            st.markdown("### 📅 Umsatz-Trend über Zeit")

                            # Kategorie-Auswahl
                            selected_cat = st.selectbox("Kategorie auswählen:", all_cats)

                            df_ros_trend = df_sales_agg[(df_sales_agg[store_col] == ros_store) & (df_sales_agg[cat_col] == selected_cat)] if ros_store else pd.DataFrame()
                            df_fk_trend = df_sales_agg[(df_sales_agg[store_col].isin(fk_stores)) & (df_sales_agg[cat_col] == selected_cat)] if fk_stores else pd.DataFrame()

                            # Aggregiere FK nach Monat
                            if len(df_fk_trend) > 0:
                                df_fk_trend = df_fk_trend.groupby(month_col_agg)[revenue_col].sum().reset_index()

                            fig = go.Figure()
                            if len(df_ros_trend) > 0:
                                fig.add_trace(go.Scatter(x=df_ros_trend[month_col_agg], y=df_ros_trend[revenue_col],
                                                         name='Rosenheim', line=dict(color=COLORS['rosenheim']),
                                                         fill='tozeroy', fillcolor=COLORS['rosenheim_bg']))
                            if len(df_fk_trend) > 0:
                                fig.add_trace(go.Scatter(x=df_fk_trend[month_col_agg], y=df_fk_trend[revenue_col],
                                                         name='Freiburg/Karlsruhe', line=dict(color=COLORS['freiburg']),
                                                         fill='tozeroy', fillcolor=COLORS['freiburg_bg']))

                            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                              font_color='white', xaxis_title='Monat', yaxis_title='Umsatz (EUR)',
                                              title=f'Umsatzentwicklung: {selected_cat}')
                            st.plotly_chart(fig, use_container_width=True)

                        # === ROHDATEN ===
                        st.markdown("---")
                        st.markdown("### 📋 Detaildaten")
                        st.dataframe(df_cat, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Kategorien-Spalten nicht gefunden")
                else:
                    st.error("Produktkategorien-Daten nicht verfügbar")

            # =============================================
            # TAB 3: ROHDATEN
            # =============================================
            with tab_data:
                st.subheader("📋 Alle Rohdaten")

                st.markdown("#### Export Monthly View")
                st.dataframe(df, use_container_width=True, hide_index=True)

                df_sales_full = load_sales_agg_data()
                if df_sales_full is not None:
                    st.markdown("#### Sales Aggregation View")
                    st.dataframe(df_sales_full, use_container_width=True, hide_index=True)

        else:
            st.error("Filialen nicht identifiziert: " + str(filialen))
    else:
        st.error("Spalten nicht gefunden")
else:
    st.error("❌ Keine Daten verfügbar")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Benchmark Dashboard v2.0 | Gruppe 18 | Hochschule der Medien</small>
</div>
""", unsafe_allow_html=True)
