"""
Benchmark Dashboard - Gruppe 18
Streamlit-basiertes Web-Dashboard für den Filialvergleich

VERSION 3: Modulare Architektur
- Config: src/config/
- DB: src/db/
- Domain: src/domain/
- UI: src/ui/
- Charts: src/charts/
- Services: src/services/
- Utils: src/utils/
"""

import streamlit as st

# Auth
from src.auth.login_ui import render_login_screen

# Config
from src.config.stores import get_stores
from src.config.settings import MONTH_NAMES

# DB
from src.db.repository import (
    load_data,
    load_kpi,
    load_marketing_kpi,
    load_marketing_by_campaign,
    load_sales_agg,
    load_rent_and_revenue_per_m2,
    load_price_segment_data,
    load_deckungsbeitrag,
)

# Domain
from src.domain.metrics import get_kpis_from_view, calculate_kpis

# UI
from src.ui.layout import setup_page, render_header
from src.ui.styles import DASHBOARD_CSS
from src.ui.components import chart_header, render_store_kpi_card, render_cost_card
from src.ui.sidebar import render_sidebar

# Charts
from src.charts.finance import (
    create_revenue_trend_chart,
    create_revenue_bar_chart,
    create_ebit_chart,
    create_margin_chart,
    create_cost_ratio_chart,
)
from src.charts.marketing import (
    create_marketing_trend_chart,
    create_marketing_bar_chart,
    create_marketing_quote_chart,
    create_top_campaigns_overall_chart,
    create_top_campaigns_per_store_chart,
    create_campaign_profit_chart,
)
from src.charts.categories import (
    create_margin_by_category_chart,
    create_profit_distribution_chart,
    create_price_segment_chart,
)

# Services
from src.services.aggregations import aggregate_marketing_kpis, aggregate_romi, calculate_cost_percentages
from src.services.filters import create_store_filter

# Utils
from src.utils.formatting import format_currency

# =============================================================================
# SEITEN-KONFIGURATION
# =============================================================================
setup_page()

# =============================================================================
# AUTHENTIFIZIERUNG
# =============================================================================
if not render_login_screen():
    # User ist nicht eingeloggt - Login-Screen wird angezeigt
    st.stop()

# User ist eingeloggt - Dashboard anzeigen
render_header()

# =============================================================================
# SIDEBAR - FILTER & USER INFO
# =============================================================================
df = load_data()

if df is not None and len(df) > 0:
    cols = df.columns.tolist()

    # Spaltennamen finden
    monat_col = next((c for c in cols if 'monat' in c.lower() or 'month' in c.lower()), None)
    filiale_col = next((c for c in cols if 'filial' in c.lower() or 'store' in c.lower() or 'gruppe' in c.lower()), None)

    if monat_col and filiale_col:
        # Sidebar mit Filtern rendern
        selected_stores, selected_month = render_sidebar(df, monat_col)

        # Alle verfügbaren Sections definieren
        dashboard_all_sections = ['KPI-Karten', 'Margen-Vergleich', 'Kostenstruktur']
        cat_all_sections = ['Bruttogewinn-Anteil (%)', 'Bruttomarge (%)', 'Umsatz-Trend']

        # Session State für Multiselects initialisieren
        if 'dashboard_multiselect' not in st.session_state:
            st.session_state['dashboard_multiselect'] = dashboard_all_sections.copy()
        if 'cat_multiselect' not in st.session_state:
            st.session_state['cat_multiselect'] = cat_all_sections.copy()

        # =================================================================
        # DATEN LADEN MIT SQL-FILTER
        # =================================================================
        kpi_df = load_kpi(selected_month)
        filtered_df = df if selected_month == 'all' else df[df[monat_col] == selected_month]

        # =================================================================
        # STORES DYNAMISCH ERKENNEN
        # =================================================================
        available_stores = filtered_df[filiale_col].unique().tolist()

        # Store-Daten und KPIs für alle Stores
        stores_data = {}
        stores_kpis = {}

        for store in get_stores():
            matching_name = next((s for s in available_stores if store['name'].lower() in s.lower()), None)
            if matching_name:
                stores_data[store['name']] = filtered_df[filtered_df[filiale_col] == matching_name]
                if kpi_df is not None and not kpi_df.empty:
                    stores_kpis[store['name']] = get_kpis_from_view(kpi_df, store['id'])
                else:
                    stores_kpis[store['name']] = calculate_kpis(stores_data[store['name']])

        active_stores = [s for s in get_stores() if s['name'] in stores_data and s['name'] in selected_stores]

        # =================================================================
        # TABS
        # =================================================================
        tab_main, tab_marketing, tab_costs, tab_categories, tab_db, tab_data = st.tabs([
            "📊 Finanzperformance", "📢 Marketing", "💸 Kostenanalyse", "🚲 Produktkategorien", "📈 Deckungsbeitrag", "📋 Export"
        ])

        if len(active_stores) >= 1:
            # =============================================================
            # TAB 1: FINANZPERFORMANCE
            # =============================================================
            with tab_main:
                col_dash_space, col_dash_settings = st.columns([15, 1])
                with col_dash_settings:
                    with st.popover("⚙️"):
                        st.markdown("**Anzeigeoptionen**")
                        if st.button("Alle anzeigen", key="reset_dashboard"):
                            st.session_state['dashboard_multiselect'] = dashboard_all_sections.copy()
                            st.rerun()
                        st.multiselect("Bereiche:", options=dashboard_all_sections,
                                       key="dashboard_multiselect", label_visibility="collapsed")

                selected_sections = st.session_state.get('dashboard_multiselect', dashboard_all_sections)

                if 'KPI-Karten' in selected_sections:
                    st.subheader("📈 Vergleich Umsatz & Operativer Gewinn")
                    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

                    # Responsive Grid: Max 3 Stores pro Zeile
                    num_stores = len(active_stores)
                    stores_per_row = min(3, num_stores)  # Max 3 pro Zeile

                    # Zeilen berechnen
                    for row_start in range(0, num_stores, stores_per_row):
                        row_stores = active_stores[row_start:row_start + stores_per_row]
                        kpi_cols = st.columns(len(row_stores))

                        for idx, store in enumerate(row_stores):
                            with kpi_cols[idx]:
                                st.markdown(render_store_kpi_card(store, stores_kpis[store['name']]), unsafe_allow_html=True)

                        if row_start + stores_per_row < num_stores:  # Abstand zwischen Zeilen
                            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    col_chart1, col_chart2 = st.columns(2)

                    with col_chart1:
                        if selected_month == 'all':
                            st.markdown(chart_header("💰 Umsatzentwicklung",
                                "<strong>Berechnung:</strong> Summe aller Verkaufserlöse pro Monat<br><br>"
                                "<strong>Nutzen:</strong> Zeigt Umsatztrends und Saisonalität. Ermöglicht Vergleich der Filialperformance und Erkennung von Wachstums- oder Rückgangsphasen."), unsafe_allow_html=True)
                            fig = create_revenue_trend_chart(stores_data, active_stores, monat_col)
                        else:
                            month_name = MONTH_NAMES.get(selected_month, selected_month)
                            st.markdown(chart_header(f"💰 Umsatzvergleich {month_name}",
                                "<strong>Berechnung:</strong> Summe aller Verkaufserlöse im Monat<br><br>"
                                "<strong>Nutzen:</strong> Direkter Filialvergleich für den gewählten Zeitraum. Zeigt welche Filiale am umsatzstärksten ist."), unsafe_allow_html=True)
                            fig = create_revenue_bar_chart(active_stores, stores_kpis)
                        st.plotly_chart(fig, use_container_width=True)

                    with col_chart2:
                        if selected_month == 'all':
                            st.markdown(chart_header("📊 Operativer Gewinn (EBIT) - Entwicklung",
                                "<strong>Berechnung:</strong> EBIT = Umsatz - Wareneinsatz - Betriebskosten (Personal, Miete, Logistik, Marketing)<br><br>"
                                "<strong>Nutzen:</strong> Zeigt die tatsächliche operative Profitabilität. Ein negativer EBIT bedeutet Verlust im Kerngeschäft - unabhängig von Finanzierung und Steuern."), unsafe_allow_html=True)
                        else:
                            month_name = MONTH_NAMES.get(selected_month, selected_month)
                            st.markdown(chart_header(f"📊 Operativer Gewinn (EBIT) - Vergleich {month_name}",
                                "<strong>Berechnung:</strong> EBIT = Umsatz - Wareneinsatz - Betriebskosten (Personal, Miete, Logistik, Marketing)<br><br>"
                                "<strong>Nutzen:</strong> Zeigt die tatsächliche operative Profitabilität. Ein negativer EBIT bedeutet Verlust im Kerngeschäft - unabhängig von Finanzierung und Steuern."), unsafe_allow_html=True)
                        fig = create_ebit_chart(stores_data, active_stores, monat_col)
                        st.plotly_chart(fig, use_container_width=True)

                    if 'Margen-Vergleich' in selected_sections:
                        col_brutto, col_ebit = st.columns(2)

                        with col_brutto:
                            st.markdown(chart_header("📊 Bruttomarge im Vergleich",
                                "<strong>Berechnung:</strong> (Umsatz - Wareneinsatz) / Umsatz × 100<br><br>"
                                "<strong>Nutzen:</strong> Zeigt die Handelsspanne nach Abzug der Warenkosten. Höhere Bruttomarge = mehr Spielraum für Betriebskosten. Niedrige Werte deuten auf Preisdruck oder hohe Einkaufskosten hin."), unsafe_allow_html=True)
                            fig = create_margin_chart(active_stores, stores_kpis, 'brutto')
                            st.plotly_chart(fig, use_container_width=True)

                        with col_ebit:
                            st.markdown(chart_header("📈 EBIT-Marge im Vergleich",
                                "<strong>Berechnung:</strong> EBIT / Umsatz × 100<br><br>"
                                "<strong>Nutzen:</strong> Zeigt wie viel vom Umsatz als operativer Gewinn übrig bleibt. Benchmark für operative Effizienz. Negative Werte = Filiale arbeitet nicht kostendeckend."), unsafe_allow_html=True)
                            fig = create_margin_chart(active_stores, stores_kpis, 'ebit')
                            st.plotly_chart(fig, use_container_width=True)

                        st.markdown(chart_header("📊 Kostenquote im Vergleich",
                            "<strong>Berechnung:</strong> Gesamtkosten / Umsatz × 100<br><br>"
                            "<strong>Nutzen:</strong> Zeigt den Kostenanteil am Umsatz. Werte über 100% bedeuten Verlust. Ermöglicht Identifikation von Filialen mit Kostenoptimierungspotenzial."), unsafe_allow_html=True)
                        fig = create_cost_ratio_chart(active_stores, stores_kpis)
                        st.plotly_chart(fig, use_container_width=True)

            # =============================================================
            # TAB 2: MARKETING
            # =============================================================
            with tab_marketing:
                st.subheader("📢 Marketing-Effizienz Analyse")
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

                marketing_filtered = load_marketing_kpi(selected_month)
                marketing_all_months = load_marketing_kpi('all')

                if marketing_filtered is not None and not marketing_filtered.empty:
                    marketing_kpis = {}
                    for store in active_stores:
                        marketing_kpis[store['name']] = aggregate_marketing_kpis(marketing_filtered, store['id'])

                    # Marketing-KPI Cards (wie im alten Design)
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
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Marketing-attributierter Umsatz</div>
                                        <div style="color: #00ff88; font-size: 1em; font-weight: bold;">{format_currency(mkpi['umsatz_mit_marketing'])}</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Marketing-unabhängiger Umsatz</div>
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
                        if selected_month == 'all':
                            st.markdown(chart_header("📈 Marketing-Ausgaben im Zeitverlauf",
                                "<strong>Berechnung:</strong> Summe aller Marketing-Kosten pro Monat<br><br>"
                                "<strong>Nutzen:</strong> Zeigt Investitionsmuster und Kampagnen-Intensität. Hilft bei Budget-Planung und Identifikation von Marketing-Hochphasen."), unsafe_allow_html=True)
                            fig = create_marketing_trend_chart(marketing_all_months, active_stores)
                        else:
                            month_name = MONTH_NAMES.get(selected_month, selected_month)
                            st.markdown(chart_header(f"📊 Marketing-Kosten {month_name}",
                                "<strong>Berechnung:</strong> Summe aller Marketing-Kosten im Monat<br><br>"
                                "<strong>Nutzen:</strong> Direkter Vergleich der Marketing-Investitionen zwischen Filialen."), unsafe_allow_html=True)
                            fig = create_marketing_bar_chart(active_stores, marketing_kpis)
                        st.plotly_chart(fig, use_container_width=True)

                    with col_quote:
                        st.markdown(chart_header("📊 Marketing-Quote",
                            "<strong>Berechnung:</strong> Marketing-Kosten / Gesamtumsatz × 100<br><br>"
                            "<strong>Nutzen:</strong> Zeigt den Anteil des Umsatzes, der in Marketing fließt. Hilft bei der Bewertung der Marketing-Intensität. Branchenüblich im Einzelhandel: 3-8%."), unsafe_allow_html=True)
                        fig = create_marketing_quote_chart(active_stores, marketing_kpis)
                        st.plotly_chart(fig, use_container_width=True)

                    # CPA - Cost per Acquisition (wie im alten Design)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(chart_header("💰 CPA - Cost per Acquisition",
                        "<strong>Berechnung:</strong> Marketing-Kosten / Verkaufte Stückzahl (bei Kampagnen)<br><br>"
                        "<strong>Nutzen:</strong> Zeigt die Akquisekosten pro verkauftem Artikel. Niedriger CPA = effizienteres Marketing. Ermöglicht ROI-Bewertung einzelner Kampagnen."), unsafe_allow_html=True)
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
                            """.replace(",", "."), unsafe_allow_html=True)

                    # ROMI - Return on Marketing Investment
                    st.markdown("<br>", unsafe_allow_html=True)
                    campaign_data = load_marketing_by_campaign()
                    if campaign_data is not None and not campaign_data.empty:
                        st.markdown(chart_header("📈 ROMI - Return on Marketing Investment",
                            "<strong>Berechnung:</strong> Summe(Kampagnen-Profit) / Summe(Marketing-Kosten)<br><br>"
                            "<strong>Nutzen:</strong> Zeigt die Rendite der Marketing-Investitionen. ROMI > 1 bedeutet profitables Marketing. Höherer ROMI = effizientere Marketing-Strategie."), unsafe_allow_html=True)
                        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

                        romi_cols = st.columns(len(active_stores))
                        for idx, store in enumerate(active_stores):
                            romi_data = aggregate_romi(campaign_data, store['id'])
                            with romi_cols[idx]:
                                # Farbe basierend auf ROMI-Wert
                                romi_color = '#00ff88' if romi_data['romi'] > 1 else '#ff6b6b'
                                st.markdown(f"""
                                <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                            border-radius: 12px; padding: 20px; text-align: center;">
                                    <div style="color: {store['color']}; font-weight: bold; margin-bottom: 10px;">{store['name']}</div>
                                    <div style="font-size: 2em; font-weight: bold; color: {romi_color};">{romi_data['romi']:.2f}x</div>
                                    <div style="color: #aaa; font-size: 0.8em;">Return on Marketing</div>
                                    <div style="color: #aaa; font-size: 0.75em; margin-top: 8px;">
                                        Profit: {format_currency(romi_data['total_profit'])} |
                                        Kosten: {format_currency(romi_data['total_cost'])}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Top Kampagnen nach Profit
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(chart_header("💰 Top 5 Kampagnen nach Profit je Filiale",
                            "<strong>Berechnung:</strong> Kampagnenumsatz - Kampagnenkosten - Rabatte<br><br>"
                            "<strong>Nutzen:</strong> Zeigt die profitabelsten Kampagnen nach Abzug aller Kosten und Rabatte. Ermöglicht Identifikation der wirklich rentablen Marketing-Initiativen."), unsafe_allow_html=True)

                        # Tabs für jeden Store
                        profit_tabs = st.tabs([s['name'] for s in active_stores])
                        for idx, store in enumerate(active_stores):
                            with profit_tabs[idx]:
                                fig = create_campaign_profit_chart(campaign_data, store)
                                st.plotly_chart(fig, use_container_width=True, config={'autosizable': True, 'responsive': True})

                else:
                    st.info("Keine Marketing-Daten verfügbar.")

            # =============================================================
            # TAB 3: KOSTENANALYSE
            # =============================================================
            with tab_costs:
                st.markdown(chart_header("💰 Gesamtkosten je Filiale",
                    "<strong>Berechnung:</strong> Wareneinsatz + Personal + Miete + Logistik + Marketing<br><br>"
                    "<strong>Nutzen:</strong> Zeigt die absolute Kostenbelastung jeder Filiale. Basis für Kostenoptimierung und Budgetplanung."), unsafe_allow_html=True)

                cost_cols = st.columns(len(active_stores))
                for idx, store in enumerate(active_stores):
                    with cost_cols[idx]:
                        st.markdown(render_cost_card(store, stores_kpis[store['name']]['kosten']), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(chart_header("📊 Kostenstruktur (in % vom Umsatz)",
                    "<strong>Berechnung:</strong> Jeweilige Kostenart / Umsatz × 100<br><br>"
                    "<strong>Nutzen:</strong> Zeigt wo das Geld hingeht. Ermöglicht Identifikation von Kostentreibern und Benchmarking zwischen Filialen. Hohe Werte in einzelnen Kategorien signalisieren Optimierungspotenzial."), unsafe_allow_html=True)

                # Kostenstruktur-Tabelle
                table_html = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
                table_html += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'
                table_html += '<th style="padding: 12px; text-align: left;">Filiale</th>'
                for header in ['Wareneinsatz', 'Personal', 'Miete', 'Logistik', 'Marketing', 'Gesamt']:
                    table_html += f'<th style="padding: 12px; text-align: center;">{header}</th>'
                table_html += '</tr></thead><tbody>'

                for store in active_stores:
                    cost_pct = calculate_cost_percentages(stores_kpis[store['name']])
                    table_html += f'<tr style="background: {store["color_bg"]}; border-left: 4px solid {store["color"]};">'
                    table_html += f'<td style="padding: 15px; font-weight: bold; color: {store["color"]};">{store["name"]}</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{cost_pct["wareneinsatz_pct"]:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{cost_pct["personal_pct"]:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{cost_pct["miete_pct"]:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{cost_pct["logistik_pct"]:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: white;">{cost_pct["marketing_pct"]:.1f}%</td>'
                    table_html += f'<td style="padding: 15px; text-align: center; color: {store["color"]}; font-weight: bold;">{cost_pct["gesamt_pct"]:.1f}%</td>'
                    table_html += '</tr>'
                table_html += '</tbody></table>'
                st.markdown(table_html, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                rent_m2_data = load_rent_and_revenue_per_m2(selected_month)
                if rent_m2_data is not None and not rent_m2_data.empty:
                    period_label = "Gesamt" if selected_month == 'all' else MONTH_NAMES.get(selected_month, selected_month)
                    st.markdown(chart_header(f"📋 Filialdetails (Fläche & Effizienz) - {period_label}",
                        "<strong>Berechnung:</strong> Umsatz/m² = Umsatz / Verkaufsfläche<br><br>"
                        "<strong>Nutzen:</strong> Zeigt die Flächenproduktivität. Höherer Umsatz/m² = effizientere Flächennutzung. Ermöglicht Vergleich trotz unterschiedlicher Filialgrößen."), unsafe_allow_html=True)

                    detail_html = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
                    detail_html += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'
                    for header in ['Filiale', 'Fläche (m²)', 'Mietkosten', 'Umsatz', 'Umsatz/m²']:
                        detail_html += f'<th style="padding: 12px; text-align: center;">{header}</th>'
                    detail_html += '</tr></thead><tbody>'

                    for store in active_stores:
                        store_data = rent_m2_data[rent_m2_data['IdStore'] == store['id']]
                        if not store_data.empty:
                            row = store_data.iloc[0]
                            detail_html += f'<tr style="background: {store["color_bg"]}; border-left: 4px solid {store["color"]};">'
                            detail_html += f'<td style="padding: 15px; font-weight: bold; color: {store["color"]};">{store["name"]}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{int(row["StoreM2"]):,} m²</td>'.replace(",", ".")
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{format_currency(row["Mietkosten"])}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{format_currency(row["Umsatz"])}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: {store["color"]}; font-weight: bold;">{row["UmsatzProM2"]:,.0f} €/m²</td>'.replace(",", ".")
                            detail_html += '</tr>'

                    detail_html += '</tbody></table>'
                    st.markdown(detail_html, unsafe_allow_html=True)

            # =============================================================
            # TAB 4: PRODUKTKATEGORIEN
            # =============================================================
            with tab_categories:
                col_cat_space, col_cat_settings = st.columns([15, 1])
                with col_cat_settings:
                    with st.popover("⚙️"):
                        st.markdown("**Anzeigeoptionen**")
                        if st.button("Alle anzeigen", key="reset_cat"):
                            st.session_state['cat_multiselect'] = cat_all_sections.copy()
                            st.rerun()
                        st.multiselect("Bereiche:", options=cat_all_sections,
                                       key="cat_multiselect", label_visibility="collapsed")

                selected_cat_sections = st.session_state.get('cat_multiselect', cat_all_sections)
                df_sales_agg = load_sales_agg(selected_month)

                if df_sales_agg is not None and len(df_sales_agg) > 0:
                    cat_col = next((c for c in df_sales_agg.columns if 'category' in c.lower() or 'kategorie' in c.lower()), None)
                    store_name_col = next((c for c in df_sales_agg.columns if 'storename' in c.lower().replace('_', '')), None)
                    store_id_col = next((c for c in df_sales_agg.columns if c.lower() in ['idstore', 'id_store']), None)
                    revenue_col = next((c for c in df_sales_agg.columns if 'revenue' in c.lower() or 'umsatz' in c.lower()), None)
                    quantity_col = next((c for c in df_sales_agg.columns if 'quantity' in c.lower() or 'menge' in c.lower()), None)
                    profit_col = next((c for c in df_sales_agg.columns if 'profit' in c.lower() or 'gewinn' in c.lower()), None)

                    filter_by_store = create_store_filter(df_sales_agg)

                    if cat_col and revenue_col:
                        df_filtered_cat = df_sales_agg.copy()

                        if quantity_col:
                            st.markdown(chart_header("🛒 Gesamtverkäufe (Stückzahl)",
                                "<strong>Berechnung:</strong> Summe aller verkauften Artikel<br><br>"
                                "<strong>Nutzen:</strong> Zeigt das Absatzvolumen unabhängig vom Preis. Hohe Stückzahl bei niedrigem Umsatz deutet auf günstige Produkte hin. Wichtig für Lager- und Bestellplanung."), unsafe_allow_html=True)

                            sales_cols = st.columns(len(active_stores))
                            for idx, store in enumerate(active_stores):
                                store_cat_data = filter_by_store(df_filtered_cat, store)
                                total_qty = store_cat_data[quantity_col].sum()
                                with sales_cols[idx]:
                                    st.markdown(f"""
                                    <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                                border-radius: 15px; padding: 25px; text-align: center;">
                                        <div style="color: {store['color']}; font-size: 0.9em;">{store['name']}</div>
                                        <div style="color: {store['color']}; font-size: 2em; font-weight: bold;">{int(total_qty):,}</div>
                                        <div style="color: #aaa; font-size: 0.8em;">Stück verkauft</div>
                                    </div>
                                    """.replace(",", "."), unsafe_allow_html=True)

                            st.markdown("<br>", unsafe_allow_html=True)

                        if 'Bruttogewinn-Anteil (%)' in selected_cat_sections and profit_col:
                            st.markdown(chart_header("💰 Bruttogewinn-Anteil je Kategorie (%)",
                                "<strong>Berechnung:</strong> Bruttogewinn je Kategorie / Gesamtbruttogewinn × 100<br><br>"
                                "<strong>Nutzen:</strong> Zeigt welche Kategorien am meisten zum Gewinn beitragen. Kombiniert Umsatzvolumen und Marge zu einer Gesamtbewertung."), unsafe_allow_html=True)
                            fig = create_profit_distribution_chart(df_filtered_cat, active_stores, cat_col, profit_col, filter_by_store)
                            st.plotly_chart(fig, use_container_width=True)

                        if 'Bruttomarge (%)' in selected_cat_sections and profit_col:
                            st.markdown(chart_header("📈 Bruttomarge nach Kategorie (%)",
                                "<strong>Berechnung:</strong> (Umsatz - Wareneinsatz) / Umsatz × 100 je Kategorie<br><br>"
                                "<strong>Nutzen:</strong> Zeigt welche Kategorien am profitabelsten sind. Hohe Marge = mehr Gewinn pro Euro Umsatz. Basis für Preisstrategien und Sortimentsentscheidungen."), unsafe_allow_html=True)
                            fig = create_margin_by_category_chart(df_filtered_cat, active_stores, cat_col, profit_col, revenue_col, filter_by_store)
                            st.plotly_chart(fig, use_container_width=True)

                        st.markdown(chart_header("💎 Umsatzverteilung nach Preissegment (%)",
                            "<strong>Berechnung:</strong> Umsatz je Preissegment / Gesamtumsatz × 100<br><br>"
                            "<strong>Nutzen:</strong> Zeigt die Positionierung im Markt. Hoher Premium-Anteil = hochwertige Kundschaft. Hilft bei Sortiments- und Preisstrategie."), unsafe_allow_html=True)
                        price_segment_data = load_price_segment_data(selected_month)
                        if price_segment_data is not None and not price_segment_data.empty:
                            fig = create_price_segment_chart(price_segment_data, active_stores)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Keine Preissegment-Daten verfügbar.")
                else:
                    st.warning("Keine Kategoriedaten verfügbar.")

            # =============================================================
            # TAB 5: DECKUNGSBEITRAG
            # =============================================================
            with tab_db:
                # Titel und optionaler Quartalsfilter
                # Zeige aktuellen Zeitraum aus Sidebar-Filter
                period_label = MONTH_NAMES.get(selected_month, selected_month)
                st.subheader(f"📈 Deckungsbeitragsrechnung - {period_label}")

                # Zusätzlicher Quartalsfilter als horizontale Radio-Buttons (nur wenn Sidebar auf "Gesamt" steht)
                if selected_month == 'all':
                    db_quarter_options = ['Gesamtjahr', 'Q1', 'Q2', 'Q3', 'Q4']
                    db_quarter_map = {'Gesamtjahr': 'all', 'Q1': 'Q1', 'Q2': 'Q2', 'Q3': 'Q3', 'Q4': 'Q4'}

                    selected_db_quarter_label = st.radio(
                        "Zeitraum:",
                        options=db_quarter_options,
                        index=0,
                        key="db_quarter_filter",
                        horizontal=True
                    )
                    selected_db_period = db_quarter_map[selected_db_quarter_label]
                else:
                    # Nutze den Sidebar-Monatsfilter direkt
                    selected_db_period = selected_month

                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

                store_names_tuple = tuple(s['name'] for s in active_stores)
                db_data = load_deckungsbeitrag(selected_db_period, store_names_tuple)
                if db_data is not None and not db_data.empty:
                    # Berechne Deckungsbeiträge für jeden Store
                    for store in active_stores:
                        store_db = db_data[db_data['StoreName'] == store['name']]
                        if store_db.empty:
                            continue

                        # Pivot: Kenngröße -> Wert
                        values = {}
                        for _, row in store_db.iterrows():
                            values[row['Kenngröße']] = row['Wert']

                        # Berechne DB-Stufen
                        umsatz = values.get('UmsatzEUR', 0)
                        wareneinsatz = abs(values.get('TransferPriceEUR', 0))
                        db1 = umsatz - wareneinsatz

                        rabatt_material = abs(values.get('DiscountAufMaterialEUR', 0))
                        rabatt_kategorie = abs(values.get('DiscountAufMaterialKategorieEUR', 0))
                        rabatte_gesamt = rabatt_material + rabatt_kategorie
                        db2 = db1 - rabatte_gesamt

                        personal = abs(values.get('Monthly Salary', 0)) + abs(values.get('Monthly Social Costs', 0))
                        miete = abs(values.get('Monthly Rent', 0))
                        logistik = abs(values.get('Additional Procurement Costs', 0))
                        marketing = abs(values.get('Marketing Campaign', 0))
                        commission = abs(values.get('Commission', 0))
                        betriebskosten = personal + miete + logistik + marketing + commission
                        db3 = db2 - betriebskosten

                        # DB-Margen in Prozent
                        db1_pct = (db1 / umsatz * 100) if umsatz > 0 else 0
                        db2_pct = (db2 / umsatz * 100) if umsatz > 0 else 0
                        db3_pct = (db3 / umsatz * 100) if umsatz > 0 else 0

                        # Anzeige als Card
                        st.markdown(f"""
                        <div style="background: {store['color_bg']}; border: 1px solid {store['color']};
                                    border-radius: 15px; padding: 20px; margin-bottom: 20px;">
                            <h3 style="color: {store['color']}; margin-bottom: 20px; text-align: center;">{store['name']}</h3>
                            <table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: white;">Umsatz</td>
                                    <td style="padding: 10px; text-align: right; color: #00ff88; font-weight: bold;">{format_currency(umsatz)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;">100%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: #aaa;">- Wareneinsatz</td>
                                    <td style="padding: 10px; text-align: right; color: #ff6b6b;">{format_currency(wareneinsatz)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;"></td>
                                </tr>
                                <tr style="border-bottom: 2px solid {store['color']}; background: rgba(255,255,255,0.05);">
                                    <td style="padding: 10px; color: white; font-weight: bold;">= DB I (Rohertrag)</td>
                                    <td style="padding: 10px; text-align: right; color: {'#00ff88' if db1 > 0 else '#ff6b6b'}; font-weight: bold;">{format_currency(db1)}</td>
                                    <td style="padding: 10px; text-align: right; color: {store['color']}; font-weight: bold;">{db1_pct:.1f}%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: #aaa;">- Rabatte</td>
                                    <td style="padding: 10px; text-align: right; color: #ff6b6b;">{format_currency(rabatte_gesamt)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;"></td>
                                </tr>
                                <tr style="border-bottom: 2px solid {store['color']}; background: rgba(255,255,255,0.05);">
                                    <td style="padding: 10px; color: white; font-weight: bold;">= DB II</td>
                                    <td style="padding: 10px; text-align: right; color: {'#00ff88' if db2 > 0 else '#ff6b6b'}; font-weight: bold;">{format_currency(db2)}</td>
                                    <td style="padding: 10px; text-align: right; color: {store['color']}; font-weight: bold;">{db2_pct:.1f}%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: #aaa;">- Personal</td>
                                    <td style="padding: 10px; text-align: right; color: #ff6b6b;">{format_currency(personal)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;"></td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: #aaa;">- Miete</td>
                                    <td style="padding: 10px; text-align: right; color: #ff6b6b;">{format_currency(miete)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;"></td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: #aaa;">- Logistik</td>
                                    <td style="padding: 10px; text-align: right; color: #ff6b6b;">{format_currency(logistik)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;"></td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: #aaa;">- Marketing</td>
                                    <td style="padding: 10px; text-align: right; color: #ff6b6b;">{format_currency(marketing)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;"></td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <td style="padding: 10px; color: #aaa;">- Provisionen</td>
                                    <td style="padding: 10px; text-align: right; color: #ff6b6b;">{format_currency(commission)}</td>
                                    <td style="padding: 10px; text-align: right; color: #aaa;"></td>
                                </tr>
                                <tr style="background: rgba(255,255,255,0.1);">
                                    <td style="padding: 15px; color: white; font-weight: bold; font-size: 1.2em;">= DB III (Betriebsergebnis)</td>
                                    <td style="padding: 15px; text-align: right; color: {'#00ff88' if db3 > 0 else '#ff6b6b'}; font-weight: bold; font-size: 1.2em;">{format_currency(db3)}</td>
                                    <td style="padding: 15px; text-align: right; color: {store['color']}; font-weight: bold; font-size: 1.2em;">{db3_pct:.1f}%</td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Keine Deckungsbeitragsdaten verfügbar.")

            # =============================================================
            # TAB 6: EXPORT
            # =============================================================
            with tab_data:
                st.subheader("📋 Rohdaten-Export")
                st.markdown("Alle verfügbaren Daten aus der Datenbank")
                st.dataframe(filtered_df, use_container_width=True)

                csv = filtered_df.to_csv(index=False)
                st.download_button("📥 Daten als CSV herunterladen", csv,
                                   f"benchmark_export_{selected_month}.csv", "text/csv")

        else:
            st.warning("Bitte mindestens eine Filiale auswählen.")

    else:
        st.error("Spalten 'Monat' oder 'Filialgruppe' nicht gefunden.")

else:
    st.error("Keine Daten verfügbar. Bitte Datenbankverbindung prüfen.")
