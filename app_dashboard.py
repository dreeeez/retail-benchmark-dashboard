"""
Benchmark Dashboard - Gruppe 18
Streamlit-basiertes Web-Dashboard für den Filialvergleich Rosenheim vs. Freiburg
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

# Seiten-Konfiguration
st.set_page_config(
    page_title="Gruppe 18 - Benchmark Dashboard",
    page_icon="📊",
    layout="wide"
)

# Dark Theme CSS (wie HTML-Dashboard)
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

    .chart-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .month-indicator {
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        color: white;
        display: inline-block;
    }

    /* Tabelle Styling */
    .dataframe {
        background: rgba(255, 255, 255, 0.05) !important;
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
    """Lädt Daten aus der View V_LIST_G18_BENCHMARK_EXPORT_MONTHLY"""
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT * FROM list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
        """, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Datenbankverbindung fehlgeschlagen: {e}")
        return None

# Hilfsfunktionen für Formatierung
def format_currency(value):
    """Formatiert Währung auf Deutsch"""
    if value >= 1000000:
        return f"{value/1000000:.1f} Mio €"
    elif value >= 1000:
        return f"{value/1000:.0f} Tsd €"
    else:
        return f"{value:,.0f} €"

def format_percent(value):
    """Formatiert Prozent"""
    return f"{value:.1f}%"

# Daten laden
df = load_data()

if df is not None and len(df) > 0:
    # Spaltennamen ermitteln (können CamelCase oder anders sein)
    cols = df.columns.tolist()
    st.sidebar.write("Verfügbare Spalten:", cols)

    # Versuche die richtigen Spaltennamen zu finden
    # Suche nach Monat-Spalte
    monat_col = next((c for c in cols if 'monat' in c.lower() or 'month' in c.lower() or 'calmonth' in c.lower()), None)
    filiale_col = next((c for c in cols if 'filial' in c.lower() or 'store' in c.lower() or 'gruppe' in c.lower()), None)
    umsatz_col = next((c for c in cols if 'umsatz' in c.lower() or 'revenue' in c.lower()), None)

    if monat_col and filiale_col:
        # Filter Section
        col_filter, col_indicator = st.columns([3, 1])

        with col_filter:
            # Verfügbare Monate aus den Daten
            available_months = ['all'] + sorted(df[monat_col].unique().tolist())
            month_options = {m: MONTH_NAMES.get(m, m) for m in available_months}

            selected_month = st.selectbox(
                "Zeitraum:",
                options=list(month_options.keys()),
                format_func=lambda x: month_options[x],
                key="month_filter"
            )

        with col_indicator:
            st.markdown(f'<div class="month-indicator">{month_options[selected_month]}</div>', unsafe_allow_html=True)

        # Daten filtern
        if selected_month == 'all':
            filtered_df = df
        else:
            filtered_df = df[df[monat_col] == selected_month]

        # Daten nach Filialgruppe trennen
        filialen = filtered_df[filiale_col].unique().tolist()

        # Versuche Rosenheim und Freiburg zu identifizieren
        rosenheim_name = next((f for f in filialen if 'rosen' in f.lower()), filialen[0] if len(filialen) > 0 else None)
        freiburg_name = next((f for f in filialen if 'frei' in f.lower() or 'karlsruhe' in f.lower()), filialen[1] if len(filialen) > 1 else None)

        if rosenheim_name and freiburg_name:
            df_rosenheim = filtered_df[filtered_df[filiale_col] == rosenheim_name]
            df_freiburg = filtered_df[filtered_df[filiale_col] == freiburg_name]

            # Numerische Spalten finden
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()

            # KPI Cards
            st.markdown("---")

            # Berechne Summen/Durchschnitte
            def safe_sum(df, col_pattern):
                """Findet Spalte und summiert"""
                col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
                if col:
                    return df[col].sum()
                return 0

            def safe_mean(df, col_pattern):
                """Findet Spalte und mittelt"""
                col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
                if col:
                    return df[col].mean()
                return 0

            # KPIs berechnen
            umsatz_ros = safe_sum(df_rosenheim, 'umsatz')
            umsatz_fre = safe_sum(df_freiburg, 'umsatz')

            nettogewinn_ros = safe_sum(df_rosenheim, 'nettogewinn') if safe_sum(df_rosenheim, 'nettogewinn') != 0 else safe_sum(df_rosenheim, 'gewinn')
            nettogewinn_fre = safe_sum(df_freiburg, 'nettogewinn') if safe_sum(df_freiburg, 'nettogewinn') != 0 else safe_sum(df_freiburg, 'gewinn')

            marge_ros = safe_mean(df_rosenheim, 'nettogewinnmarge') if safe_mean(df_rosenheim, 'nettogewinnmarge') != 0 else safe_mean(df_rosenheim, 'marge')
            marge_fre = safe_mean(df_freiburg, 'nettogewinnmarge') if safe_mean(df_freiburg, 'nettogewinnmarge') != 0 else safe_mean(df_freiburg, 'marge')

            # Differenzen berechnen
            umsatz_diff = ((umsatz_ros / umsatz_fre) - 1) * 100 if umsatz_fre > 0 else 0
            marge_diff = marge_ros - marge_fre
            gewinn_diff = ((nettogewinn_ros / nettogewinn_fre) - 1) * 100 if nettogewinn_fre > 0 else 0

            # KPI Cards anzeigen (6 Karten in 2 Reihen)
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Umsatz Rosenheim</div>
                    <div class="kpi-value-rosenheim">{format_currency(umsatz_ros)}</div>
                    <span class="{'kpi-comparison-positive' if umsatz_diff >= 0 else 'kpi-comparison-negative'}">
                        {'+' if umsatz_diff >= 0 else ''}{umsatz_diff:.1f}% vs FK
                    </span>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Umsatz Freiburg/K.</div>
                    <div class="kpi-value-freiburg">{format_currency(umsatz_fre)}</div>
                    <span class="kpi-comparison-neutral">Benchmark</span>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Nettomarge Rosenheim</div>
                    <div class="kpi-value-rosenheim">{format_percent(marge_ros)}</div>
                    <span class="{'kpi-comparison-positive' if marge_diff >= 0 else 'kpi-comparison-negative'}">
                        {'+' if marge_diff >= 0 else ''}{marge_diff:.1f}pp
                    </span>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Nettomarge Freiburg/K.</div>
                    <div class="kpi-value-freiburg">{format_percent(marge_fre)}</div>
                    <span class="kpi-comparison-neutral">Benchmark</span>
                </div>
                """, unsafe_allow_html=True)

            with col5:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Gewinn Rosenheim</div>
                    <div class="kpi-value-rosenheim">{format_currency(nettogewinn_ros)}</div>
                    <span class="{'kpi-comparison-positive' if gewinn_diff >= 0 else 'kpi-comparison-negative'}">
                        {'+' if gewinn_diff >= 0 else ''}{gewinn_diff:.1f}%
                    </span>
                </div>
                """, unsafe_allow_html=True)

            with col6:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Gewinn Freiburg/K.</div>
                    <div class="kpi-value-freiburg">{format_currency(nettogewinn_fre)}</div>
                    <span class="kpi-comparison-neutral">Benchmark</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Charts - 2x2 Grid
            is_single_month = selected_month != 'all'

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("Umsatzentwicklung" if not is_single_month else "Umsatz-Vergleich")

                umsatz_col_name = next((c for c in df.columns if 'umsatz' in c.lower()), None)

                if is_single_month:
                    # Balkenvergleich für einzelnen Monat
                    fig_umsatz = go.Figure(data=[
                        go.Bar(
                            y=['Rosenheim', 'Freiburg/Karlsruhe'],
                            x=[umsatz_ros, umsatz_fre],
                            orientation='h',
                            marker_color=[COLORS['rosenheim'], COLORS['freiburg']]
                        )
                    ])
                else:
                    # Liniendiagramm für alle Monate
                    fig_umsatz = go.Figure()
                    if umsatz_col_name:
                        fig_umsatz.add_trace(go.Scatter(
                            x=df_rosenheim[monat_col],
                            y=df_rosenheim[umsatz_col_name],
                            name='Rosenheim',
                            line=dict(color=COLORS['rosenheim']),
                            fill='tozeroy',
                            fillcolor=COLORS['rosenheim_bg']
                        ))
                        fig_umsatz.add_trace(go.Scatter(
                            x=df_freiburg[monat_col],
                            y=df_freiburg[umsatz_col_name],
                            name='Freiburg/Karlsruhe',
                            line=dict(color=COLORS['freiburg']),
                            fill='tozeroy',
                            fillcolor=COLORS['freiburg_bg']
                        ))

                fig_umsatz.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    showlegend=not is_single_month
                )
                st.plotly_chart(fig_umsatz, use_container_width=True)

            with col_chart2:
                st.subheader("Nettogewinn-Entwicklung" if not is_single_month else "Nettogewinn-Vergleich")

                gewinn_col_name = next((c for c in df.columns if 'nettogewinn' in c.lower() and 'marge' not in c.lower() and 'prozent' not in c.lower()), None)

                if is_single_month:
                    fig_gewinn = go.Figure(data=[
                        go.Bar(
                            y=['Rosenheim', 'Freiburg/Karlsruhe'],
                            x=[nettogewinn_ros, nettogewinn_fre],
                            orientation='h',
                            marker_color=[COLORS['rosenheim'], COLORS['freiburg']]
                        )
                    ])
                else:
                    fig_gewinn = go.Figure()
                    if gewinn_col_name:
                        fig_gewinn.add_trace(go.Bar(
                            x=df_rosenheim[monat_col],
                            y=df_rosenheim[gewinn_col_name],
                            name='Rosenheim',
                            marker_color=COLORS['rosenheim']
                        ))
                        fig_gewinn.add_trace(go.Bar(
                            x=df_freiburg[monat_col],
                            y=df_freiburg[gewinn_col_name],
                            name='Freiburg/Karlsruhe',
                            marker_color=COLORS['freiburg']
                        ))

                fig_gewinn.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    barmode='group'
                )
                st.plotly_chart(fig_gewinn, use_container_width=True)

            # Zweite Reihe Charts
            col_chart3, col_chart4 = st.columns(2)

            with col_chart3:
                st.subheader("Margen-Vergleich (%)")

                brutto_col = next((c for c in df.columns if 'brutto' in c.lower() and 'marge' in c.lower()), None)
                netto_col = next((c for c in df.columns if 'netto' in c.lower() and 'marge' in c.lower()), None)

                if is_single_month and brutto_col and netto_col:
                    fig_marge = go.Figure()
                    fig_marge.add_trace(go.Bar(
                        x=['Bruttomarge', 'Nettomarge'],
                        y=[df_rosenheim[brutto_col].mean(), df_rosenheim[netto_col].mean()],
                        name='Rosenheim',
                        marker_color=COLORS['rosenheim']
                    ))
                    fig_marge.add_trace(go.Bar(
                        x=['Bruttomarge', 'Nettomarge'],
                        y=[df_freiburg[brutto_col].mean(), df_freiburg[netto_col].mean()],
                        name='Freiburg/Karlsruhe',
                        marker_color=COLORS['freiburg']
                    ))
                elif brutto_col and netto_col:
                    fig_marge = go.Figure()
                    fig_marge.add_trace(go.Scatter(
                        x=df_rosenheim[monat_col], y=df_rosenheim[brutto_col],
                        name='Bruttomarge Rosenheim', line=dict(color=COLORS['rosenheim'])
                    ))
                    fig_marge.add_trace(go.Scatter(
                        x=df_freiburg[monat_col], y=df_freiburg[brutto_col],
                        name='Bruttomarge FK', line=dict(color=COLORS['freiburg'])
                    ))
                    fig_marge.add_trace(go.Scatter(
                        x=df_rosenheim[monat_col], y=df_rosenheim[netto_col],
                        name='Nettomarge Rosenheim', line=dict(color=COLORS['rosenheim'], dash='dash')
                    ))
                    fig_marge.add_trace(go.Scatter(
                        x=df_freiburg[monat_col], y=df_freiburg[netto_col],
                        name='Nettomarge FK', line=dict(color=COLORS['freiburg'], dash='dash')
                    ))
                else:
                    fig_marge = go.Figure()

                fig_marge.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    barmode='group'
                )
                st.plotly_chart(fig_marge, use_container_width=True)

            with col_chart4:
                st.subheader("Kostenstruktur")

                personal_col = next((c for c in df.columns if 'personal' in c.lower() and 'eur' in c.lower()), None)
                betriebs_col = next((c for c in df.columns if 'betrieb' in c.lower() and 'eur' in c.lower()), None)

                if personal_col and betriebs_col:
                    personal_ros = df_rosenheim[personal_col].sum()
                    personal_fre = df_freiburg[personal_col].sum()
                    betriebs_ros = df_rosenheim[betriebs_col].sum()
                    betriebs_fre = df_freiburg[betriebs_col].sum()

                    fig_kosten = go.Figure()
                    fig_kosten.add_trace(go.Bar(
                        x=['Rosenheim', 'Freiburg/Karlsruhe'],
                        y=[personal_ros, personal_fre],
                        name='Personalkosten',
                        marker_color=[COLORS['rosenheim'], COLORS['freiburg']]
                    ))
                    fig_kosten.add_trace(go.Bar(
                        x=['Rosenheim', 'Freiburg/Karlsruhe'],
                        y=[betriebs_ros, betriebs_fre],
                        name='Betriebskosten',
                        marker_color=[COLORS['rosenheim_bg'], COLORS['freiburg_bg']]
                    ))

                    fig_kosten.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        barmode='stack'
                    )
                    st.plotly_chart(fig_kosten, use_container_width=True)
                else:
                    st.info("Kostendaten nicht verfügbar")

            # KPI Radar Chart (volle Breite)
            st.markdown("---")
            st.subheader("KPI-Vergleich")

            brutto_marge_col = next((c for c in df.columns if 'brutto' in c.lower() and 'marge' in c.lower()), None)
            netto_marge_col = next((c for c in df.columns if 'netto' in c.lower() and 'marge' in c.lower()), None)
            betriebs_quote_col = next((c for c in df.columns if 'betrieb' in c.lower() and 'quote' in c.lower()), None)
            personal_anteil_col = next((c for c in df.columns if 'personal' in c.lower() and 'anteil' in c.lower()), None)

            if brutto_marge_col and netto_marge_col:
                categories = ['Bruttomarge', 'Nettomarge', 'Betriebseffizienz', 'Personalkosteneffizienz']

                # Berechne Werte (höher = besser)
                ros_values = [
                    df_rosenheim[brutto_marge_col].mean() if brutto_marge_col else 0,
                    df_rosenheim[netto_marge_col].mean() if netto_marge_col else 0,
                    20 - df_rosenheim[betriebs_quote_col].mean() if betriebs_quote_col else 10,
                    100 - df_rosenheim[personal_anteil_col].mean() if personal_anteil_col else 50
                ]

                fre_values = [
                    df_freiburg[brutto_marge_col].mean() if brutto_marge_col else 0,
                    df_freiburg[netto_marge_col].mean() if netto_marge_col else 0,
                    20 - df_freiburg[betriebs_quote_col].mean() if betriebs_quote_col else 10,
                    100 - df_freiburg[personal_anteil_col].mean() if personal_anteil_col else 50
                ]

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=ros_values,
                    theta=categories,
                    fill='toself',
                    name='Rosenheim',
                    fillcolor=COLORS['rosenheim_bg'],
                    line_color=COLORS['rosenheim']
                ))
                fig_radar.add_trace(go.Scatterpolar(
                    r=fre_values,
                    theta=categories,
                    fill='toself',
                    name='Freiburg/Karlsruhe',
                    fillcolor=COLORS['freiburg_bg'],
                    line_color=COLORS['freiburg']
                ))

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, color='white'),
                        angularaxis=dict(color='white')
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    showlegend=True
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # Detaillierte Daten Tabelle
            st.markdown("---")
            st.subheader("Detaillierte Daten")

            # Tabelle mit den wichtigsten Spalten
            display_cols = [c for c in df.columns if any(x in c.lower() for x in ['monat', 'filial', 'umsatz', 'gewinn', 'marge', 'brutto', 'netto'])]
            if display_cols:
                st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)
            else:
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            # Download Button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Daten als CSV herunterladen",
                data=csv,
                file_name=f"benchmark_export_{selected_month}.csv",
                mime="text/csv"
            )

        else:
            st.error("Konnte Filialen nicht identifizieren. Verfügbare Filialen: " + str(filialen))
    else:
        st.error(f"Konnte Spalten nicht identifizieren. Verfügbare Spalten: {cols}")
        st.dataframe(df)

else:
    st.error("❌ Keine Daten verfügbar. Bitte Datenbankverbindung prüfen.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Benchmark Dashboard v2.0 | Gruppe 18 | Hochschule Rosenheim</small>
</div>
""", unsafe_allow_html=True)
