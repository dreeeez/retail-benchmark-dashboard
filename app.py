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

# Config
from src.config.stores import STORES
from src.config.settings import MONTH_NAMES

# DB
from src.db.repository import (
    load_data,
    load_kpi,
    load_marketing_kpi,
    load_sales_agg_data,
    load_rent_and_revenue_per_m2,
    load_price_segment_data,
)

# Domain
from src.domain.metrics import get_kpis_from_view, calculate_kpis

# UI
from src.ui.layout import setup_page, render_header
from src.ui.styles import DASHBOARD_CSS
from src.ui.components import chart_header, render_store_kpi_card, render_cost_card

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
    create_marketing_quote_chart,
)
from src.charts.categories import (
    create_revenue_distribution_chart,
    create_quantity_heatmap,
    create_margin_by_category_chart,
    create_profit_distribution_chart,
    create_price_segment_chart,
)

# Services
from src.services.aggregations import aggregate_marketing_kpis, calculate_cost_percentages
from src.services.filters import create_store_filter

# Utils
from src.utils.formatting import format_currency

# =============================================================================
# SEITEN-KONFIGURATION
# =============================================================================
setup_page()
render_header()

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

        for store in STORES:
            matching_name = next((s for s in available_stores if store['name'].lower() in s.lower()), None)
            if matching_name:
                stores_data[store['name']] = filtered_df[filtered_df[filiale_col] == matching_name]
                if kpi_df is not None and not kpi_df.empty:
                    stores_kpis[store['name']] = get_kpis_from_view(kpi_df, store['id'])
                else:
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

                    kpi_cols = st.columns(len(active_stores))
                    for idx, store in enumerate(active_stores):
                        with kpi_cols[idx]:
                            st.markdown(render_store_kpi_card(store, stores_kpis[store['name']]), unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    col_chart1, col_chart2 = st.columns(2)

                    with col_chart1:
                        if selected_month == 'all':
                            st.markdown(chart_header("💰 Umsatzentwicklung",
                                "<strong>Umsatz pro Monat</strong><br>Zeigt den Gesamtumsatz jeder Filiale im Zeitverlauf."), unsafe_allow_html=True)
                            fig = create_revenue_trend_chart(stores_data, active_stores, monat_col)
                        else:
                            month_name = MONTH_NAMES.get(selected_month, selected_month)
                            st.markdown(chart_header(f"💰 Umsatzvergleich {month_name}",
                                "<strong>Umsatz im ausgewählten Monat</strong>"), unsafe_allow_html=True)
                            fig = create_revenue_bar_chart(active_stores, stores_kpis)
                        st.plotly_chart(fig, use_container_width=True)

                    with col_chart2:
                        if selected_month == 'all':
                            st.markdown(chart_header("📊 Operativer Gewinn (EBIT) - Entwicklung",
                                "<strong>EBIT = Umsatz - Wareneinsatz - OPEX</strong>"), unsafe_allow_html=True)
                        else:
                            month_name = MONTH_NAMES.get(selected_month, selected_month)
                            st.markdown(chart_header(f"📊 Operativer Gewinn (EBIT) - Vergleich {month_name}",
                                "<strong>EBIT = Umsatz - Wareneinsatz - OPEX</strong>"), unsafe_allow_html=True)
                        fig = create_ebit_chart(stores_data, active_stores, monat_col)
                        st.plotly_chart(fig, use_container_width=True)

                    if 'Margen-Vergleich' in selected_sections:
                        col_brutto, col_ebit = st.columns(2)

                        with col_brutto:
                            st.markdown(chart_header("📊 Bruttomarge im Vergleich",
                                "<strong>Bruttomarge = Bruttogewinn / Umsatz × 100</strong>"), unsafe_allow_html=True)
                            fig = create_margin_chart(active_stores, stores_kpis, 'brutto')
                            st.plotly_chart(fig, use_container_width=True)

                        with col_ebit:
                            st.markdown(chart_header("📈 EBIT Margen-Vergleich",
                                "<strong>EBIT-Marge = EBIT / Umsatz × 100</strong>"), unsafe_allow_html=True)
                            fig = create_margin_chart(active_stores, stores_kpis, 'ebit')
                            st.plotly_chart(fig, use_container_width=True)

                        st.markdown(chart_header("📊 Kostenquote im Vergleich",
                            "<strong>Kostenquote (%) = Gesamtkosten / Umsatz × 100</strong>"), unsafe_allow_html=True)
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
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Umsatz direkt zurechenbar zu Marketing</div>
                                        <div style="color: #00ff88; font-size: 1em; font-weight: bold;">{format_currency(mkpi['umsatz_mit_marketing'])}</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="color: #aaa; font-size: 0.65em; text-transform: uppercase;">Umsatz nicht direkt dem Marketing zurechenbar</div>
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
                        st.markdown(chart_header("📈 Marketing-Ausgaben im Zeitverlauf",
                            "<strong>Monatliche Marketing-Investitionen</strong><br>Zeigt wie sich die Marketing-Ausgaben über die Monate entwickelt haben."), unsafe_allow_html=True)
                        fig = create_marketing_trend_chart(marketing_all_months, active_stores)
                        st.plotly_chart(fig, use_container_width=True)

                    with col_quote:
                        st.markdown(chart_header("📊 Marketing-Quote",
                            "<strong>Marketing-Kosten / Gesamtumsatz × 100</strong><br>Zeigt wie viel Prozent vom Umsatz für Marketing ausgegeben wird."), unsafe_allow_html=True)
                        fig = create_marketing_quote_chart(active_stores, marketing_kpis)
                        st.plotly_chart(fig, use_container_width=True)

                    # CPA - Cost per Acquisition (wie im alten Design)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(chart_header("💰 CPA - Cost per Acquisition",
                        "<strong>Marketing-Kosten / Verkaufte Stück</strong><br>Was kostet ein verkaufter Artikel an Werbung?"), unsafe_allow_html=True)
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

                else:
                    st.info("Keine Marketing-Daten verfügbar.")

            # =============================================================
            # TAB 3: KOSTENANALYSE
            # =============================================================
            with tab_costs:
                st.markdown(chart_header("💰 Gesamtkosten je Filiale",
                    "<strong>Gesamtkosten = Wareneinsatz + OPEX</strong>"), unsafe_allow_html=True)

                cost_cols = st.columns(len(active_stores))
                for idx, store in enumerate(active_stores):
                    with cost_cols[idx]:
                        st.markdown(render_cost_card(store, stores_kpis[store['name']]['kosten']), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(chart_header("📊 Kostenstruktur (in % vom Umsatz)",
                    "<strong>Jede Kostenstelle als Anteil vom Umsatz</strong>"), unsafe_allow_html=True)

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

                rent_m2_data = load_rent_and_revenue_per_m2()
                if rent_m2_data is not None and not rent_m2_data.empty:
                    st.markdown(chart_header("📋 Filialdetails (Fläche & Effizienz)",
                        "<strong>Übersicht Fläche, Miete und Umsatzeffizienz</strong>"), unsafe_allow_html=True)

                    detail_html = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
                    detail_html += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'
                    for header in ['Filiale', 'Fläche (m²)', 'Mietkosten', 'Umsatz', 'Umsatz/m²']:
                        detail_html += f'<th style="padding: 12px; text-align: center;">{header}</th>'
                    detail_html += '</tr></thead><tbody>'

                    for store in active_stores:
                        store_data = rent_m2_data[rent_m2_data['ID_STORE'] == store['id']]
                        if not store_data.empty:
                            row = store_data.iloc[0]
                            detail_html += f'<tr style="background: {store["color_bg"]}; border-left: 4px solid {store["color"]};">'
                            detail_html += f'<td style="padding: 15px; font-weight: bold; color: {store["color"]};">{store["name"]}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{int(row["StoreM2"]):,} m²</td>'.replace(",", ".")
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{format_currency(row["MietkostenGesamt"])}</td>'
                            detail_html += f'<td style="padding: 15px; text-align: center; color: white;">{format_currency(row["UmsatzGesamt"])}</td>'
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
                df_sales_agg = load_sales_agg_data()

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
                                "<strong>Absolute Anzahl verkaufter Einheiten</strong>"), unsafe_allow_html=True)

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

                        if 'Umsatzverteilung (Donut)' in selected_cat_sections:
                            st.markdown(chart_header("📊 Umsatzverteilung nach Kategorie",
                                "<strong>Anteil jeder Kategorie am Gesamtumsatz</strong>"), unsafe_allow_html=True)
                            fig = create_revenue_distribution_chart(df_filtered_cat, active_stores, cat_col, revenue_col, filter_by_store)
                            st.plotly_chart(fig, use_container_width=True)

                        if 'Stückzahl-Anteil (%)' in selected_cat_sections and quantity_col:
                            st.markdown(chart_header("📦 Anteil an Gesamtstückzahl je Kategorie (%)",
                                "<strong>Prozentuale Verteilung der verkauften Einheiten</strong>"), unsafe_allow_html=True)
                            fig = create_quantity_heatmap(df_filtered_cat, active_stores, cat_col, quantity_col, filter_by_store)
                            st.plotly_chart(fig, use_container_width=True)

                        if 'Bruttomarge (%)' in selected_cat_sections and profit_col:
                            st.markdown(chart_header("📈 Bruttomarge nach Kategorie (%)",
                                "<strong>Bruttomarge = Bruttogewinn / Umsatz × 100</strong>"), unsafe_allow_html=True)
                            fig = create_margin_by_category_chart(df_filtered_cat, active_stores, cat_col, profit_col, revenue_col, filter_by_store)
                            st.plotly_chart(fig, use_container_width=True)

                        if 'Bruttogewinn-Anteil (%)' in selected_cat_sections and profit_col:
                            st.markdown(chart_header("💰 Bruttogewinn-Anteil je Kategorie (%)",
                                "<strong>Anteil am Gesamtbruttogewinn</strong>"), unsafe_allow_html=True)
                            fig = create_profit_distribution_chart(df_filtered_cat, active_stores, cat_col, profit_col, filter_by_store)
                            st.plotly_chart(fig, use_container_width=True)

                        st.markdown(chart_header("💎 Umsatzverteilung nach Preissegment (%)",
                            "<strong>Anteil der Preissegmente am Gesamtumsatz</strong>"), unsafe_allow_html=True)
                        price_segment_data = load_price_segment_data()
                        if price_segment_data is not None and not price_segment_data.empty:
                            fig = create_price_segment_chart(price_segment_data, active_stores)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Keine Preissegment-Daten verfügbar.")
                else:
                    st.warning("Keine Kategoriedaten verfügbar.")

            # =============================================================
            # TAB 5: EXPORT
            # =============================================================
            with tab_data:
                st.subheader("📋 Rohdaten-Export")
                st.markdown("Alle verfügbaren Daten aus der Datenbank")
                st.dataframe(filtered_df, use_container_width=True)

                csv = filtered_df.to_csv(index=False)
                st.download_button("📥 Daten als CSV herunterladen", csv,
                                   f"benchmark_export_{selected_month}.csv", "text/csv")

        else:
            st.warning(f"Nicht genügend Stores gefunden. Gefunden: {len(active_stores)}, Benötigt: mindestens 2")

    else:
        st.error("Spalten 'Monat' oder 'Filialgruppe' nicht gefunden.")

else:
    st.error("Keine Daten verfügbar. Bitte Datenbankverbindung prüfen.")
