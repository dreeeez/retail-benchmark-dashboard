"""
Benchmark Dashboard - Gruppe 18
Finance Charts

Charts für Tab 1: Finanzperformance
"""

import plotly.graph_objects as go
from src.charts.base import get_base_layout, get_legend_horizontal
from src.utils.formatting import format_currency


def create_revenue_trend_chart(stores_data: dict, active_stores: list, monat_col: str) -> go.Figure:
    """Erstellt Umsatz-Trend-Chart (Liniendiagramm)

    Args:
        stores_data: Dict mit Store-Namen als Key und DataFrame als Value
        active_stores: Liste der aktiven Store-Configs
        monat_col: Name der Monatsspalte

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    for store in active_stores:
        store_df = stores_data.get(store['name'])
        if store_df is None or monat_col not in store_df.columns:
            continue

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

    fig.update_layout(**get_base_layout(
        showlegend=True,
        legend=get_legend_horizontal()
    ))

    return fig


def create_revenue_bar_chart(active_stores: list, stores_kpis: dict) -> go.Figure:
    """Erstellt Umsatz-Balkendiagramm für Einzelmonat

    Args:
        active_stores: Liste der aktiven Store-Configs
        stores_kpis: Dict mit Store-Namen als Key und KPIs als Value

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    store_names = [s['name'] for s in active_stores]
    umsatz_values = [stores_kpis[s['name']]['umsatz'] for s in active_stores]

    # Transparente Farben
    colors = []
    borders = []
    for s in active_stores:
        hex_color = s['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        colors.append(f'rgba({r},{g},{b},0.7)')
        borders.append(f'rgba({r},{g},{b},0.9)')

    fig.add_trace(go.Bar(
        x=store_names,
        y=umsatz_values,
        marker=dict(
            color=colors,
            line=dict(color=borders, width=1)
        ),
        text=[format_currency(v) for v in umsatz_values],
        textposition='outside'
    ))

    fig.update_layout(**get_base_layout(showlegend=False))

    return fig


def create_ebit_chart(stores_data: dict, active_stores: list, monat_col: str) -> go.Figure:
    """Erstellt EBIT-Chart (Balkendiagramm)

    Args:
        stores_data: Dict mit Store-DataFrames
        active_stores: Liste der aktiven Store-Configs
        monat_col: Name der Monatsspalte

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    for store in active_stores:
        store_df = stores_data.get(store['name'])
        if store_df is None or monat_col not in store_df.columns:
            continue

        ebit_col = next((c for c in store_df.columns if 'ebit' in c.lower()), None)

        # Transparente Farbe
        hex_color = store['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        transparent_color = f'rgba({r},{g},{b},0.7)'
        border_color = f'rgba({r},{g},{b},0.9)'

        if ebit_col:
            monthly = store_df.groupby(monat_col)[ebit_col].sum().reset_index()
            fig.add_trace(go.Bar(
                x=monthly[monat_col],
                y=monthly[ebit_col],
                name=store['name'],
                marker=dict(
                    color=transparent_color,
                    line=dict(color=border_color, width=1)
                )
            ))
        else:
            # Fallback: EBIT berechnen
            bruttogewinn_col = next((c for c in store_df.columns
                                     if 'bruttogewinn' in c.lower()
                                     and 'marge' not in c.lower()
                                     and 'prozent' not in c.lower()), None)
            kosten_col = next((c for c in store_df.columns if 'gesamtkosten' in c.lower()), None)

            if bruttogewinn_col and kosten_col:
                store_df['EBIT_calc'] = store_df[bruttogewinn_col] - store_df[kosten_col]
                monthly = store_df.groupby(monat_col)['EBIT_calc'].sum().reset_index()
                fig.add_trace(go.Bar(
                    x=monthly[monat_col],
                    y=monthly['EBIT_calc'],
                    name=store['name'],
                    marker=dict(
                        color=transparent_color,
                        line=dict(color=border_color, width=1)
                    )
                ))

    fig.update_layout(**get_base_layout(
        barmode='group',
        showlegend=True,
        legend=get_legend_horizontal()
    ))

    return fig


def create_margin_chart(active_stores: list, stores_kpis: dict, margin_type: str = 'brutto') -> go.Figure:
    """Erstellt Margen-Vergleich-Chart

    Args:
        active_stores: Liste der Store-Configs
        stores_kpis: Dict mit KPIs
        margin_type: 'brutto' oder 'ebit'

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    store_names = [s['name'] for s in active_stores]

    if margin_type == 'brutto':
        margins = [
            (stores_kpis[s['name']]['bruttogewinn'] / stores_kpis[s['name']]['umsatz'] * 100)
            if stores_kpis[s['name']]['umsatz'] > 0 else 0
            for s in active_stores
        ]
        y_title = "Bruttomarge (%)"
    else:  # ebit
        margins = [
            (stores_kpis[s['name']]['nettogewinn'] / stores_kpis[s['name']]['umsatz'] * 100)
            if stores_kpis[s['name']]['umsatz'] > 0 else 0
            for s in active_stores
        ]
        y_title = "EBIT-Marge (%)"

    # Transparente Farben
    colors = []
    borders = []
    for s in active_stores:
        hex_color = s['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        colors.append(f'rgba({r},{g},{b},0.7)')
        borders.append(f'rgba({r},{g},{b},0.9)')

    fig.add_trace(go.Bar(
        x=store_names,
        y=margins,
        marker=dict(
            color=colors,
            line=dict(color=borders, width=1)
        ),
        text=[f"{m:.1f}%" for m in margins],
        textposition='outside'
    ))

    fig.update_layout(**get_base_layout(yaxis_title=y_title))

    return fig


def create_cost_ratio_chart(active_stores: list, stores_kpis: dict) -> go.Figure:
    """Erstellt Kostenquoten-Vergleich-Chart

    Args:
        active_stores: Liste der Store-Configs
        stores_kpis: Dict mit KPIs

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    store_names = [s['name'] for s in active_stores]
    ratios = [
        (stores_kpis[s['name']]['kosten'] / stores_kpis[s['name']]['umsatz'] * 100)
        if stores_kpis[s['name']]['umsatz'] > 0 else 0
        for s in active_stores
    ]

    # Transparente Farben
    colors = []
    borders = []
    for s in active_stores:
        hex_color = s['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        colors.append(f'rgba({r},{g},{b},0.7)')
        borders.append(f'rgba({r},{g},{b},0.9)')

    fig.add_trace(go.Bar(
        name='Kostenquote',
        x=store_names,
        y=ratios,
        marker=dict(
            color=colors,
            line=dict(color=borders, width=1)
        ),
        text=[f"{v:.1f}%" for v in ratios],
        textposition='outside'
    ))

    fig.update_layout(**get_base_layout(yaxis_title="Kostenquote (%)"))

    return fig


def create_cost_treemap(stores_kpis: dict, active_stores: list) -> go.Figure:
    """Erstellt Treemap für Kostenstruktur-Analyse

    Zeigt hierarchisch: Store -> Kostenkategorie -> Größe nach Betrag
    Verwendet die gleichen 5 Hauptkategorien wie die Kostenstruktur-Tabelle.

    Args:
        stores_kpis: Dict mit KPIs pro Store (aus get_kpis_from_view)
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure mit Treemap
    """
    import plotly.express as px
    import pandas as pd

    # Erstelle DataFrame mit den 5 Hauptkategorien
    data_rows = []
    for store in active_stores:
        kpis = stores_kpis.get(store['name'], {})

        # Die 5 Hauptkategorien wie in der Tabelle
        categories = [
            ('Wareneinsatz', abs(kpis.get('wareneinsatz', 0))),
            ('Personal', abs(kpis.get('personalkosten', 0))),
            ('Miete', abs(kpis.get('betriebskosten', 0))),
            ('Logistik', abs(kpis.get('beschaffungskosten', 0))),
            ('Marketing', abs(kpis.get('marketingkosten', 0)))
        ]

        for kategorie, betrag in categories:
            if betrag > 0:  # Nur Kategorien mit Werten
                data_rows.append({
                    'StoreName': store['name'],
                    'Kategorie': kategorie,
                    'Betrag': betrag
                })

    if not data_rows:
        fig = go.Figure()
        fig.update_layout(**get_base_layout(height=500))
        return fig

    agg_df = pd.DataFrame(data_rows)

    # Berechne Prozentanteil innerhalb jedes Stores
    store_totals = agg_df.groupby('StoreName')['Betrag'].transform('sum')
    agg_df['Prozent'] = (agg_df['Betrag'] / store_totals * 100).round(1)

    # Berechne Durchschnitt pro Kategorie (über alle Stores) für Benchmark
    category_avg = agg_df.groupby('Kategorie')['Betrag'].mean().to_dict()
    agg_df['Benchmark'] = agg_df['Kategorie'].map(category_avg)
    agg_df['AbweichungPct'] = ((agg_df['Betrag'] - agg_df['Benchmark']) / agg_df['Benchmark'] * 100).round(1)

    fig = px.treemap(
        agg_df,
        path=['StoreName', 'Kategorie'],
        values='Betrag',
        color='AbweichungPct',
        color_continuous_scale=[
            'rgba(0, 255, 136, 0.7)',    # Grün - unter Durchschnitt
            'rgba(244, 208, 63, 0.7)',   # Gelb - im Durchschnitt
            'rgba(255, 107, 107, 0.7)'   # Rot - über Durchschnitt
        ],
        color_continuous_midpoint=0,
        custom_data=['Betrag', 'Prozent', 'AbweichungPct', 'Benchmark']
    )

    fig.update_traces(
        textinfo='label+value',
        textfont=dict(size=12, color='white'),
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Betrag: %{customdata[0]:,.0f} €<br>'
            'Anteil: %{customdata[1]:.1f}%<br>'
            'Benchmark: %{customdata[3]:,.0f} €<br>'
            'Abweichung: %{customdata[2]:+.1f}%'
            '<extra></extra>'
        ),
        marker=dict(
            line=dict(width=1, color='rgba(255,255,255,0.3)'),
            cornerradius=5
        ),
        opacity=0.85
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        coloraxis_colorbar=dict(
            title=dict(text="Abweichung<br>vom Ø", font=dict(color='white')),
            ticksuffix="%",
            tickfont=dict(color='white'),
            bgcolor='rgba(0,0,0,0.3)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        )
    )

    return fig


def create_productivity_chart(store_details_df, active_stores: list) -> go.Figure:
    """Erstellt Flächenproduktivitäts-Chart (Umsatz pro m²)

    Args:
        store_details_df: DataFrame aus load_store_details()
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure mit horizontalem Balkendiagramm
    """
    fig = go.Figure()

    if store_details_df is None or store_details_df.empty:
        fig.update_layout(**get_base_layout(height=350))
        return fig

    # Nur aktive Stores
    active_store_ids = [store['id'] for store in active_stores]
    df = store_details_df[store_details_df['IdStore'].isin(active_store_ids)].copy()

    if df.empty:
        fig.update_layout(**get_base_layout(height=350))
        return fig

    # Sortiere nach Umsatz pro m² (höchste zuerst für horizontale Darstellung)
    df = df.sort_values('UmsatzProM2', ascending=True)

    # Benchmark = Durchschnitt aller Stores
    benchmark = df['UmsatzProM2'].mean()

    # Farben basierend auf Performance vs. Benchmark
    colors = []
    for _, row in df.iterrows():
        store_config = next((s for s in active_stores if s['id'] == row['IdStore']), None)
        if store_config:
            colors.append(store_config['color'])
        else:
            colors.append('#00d4ff')

    fig.add_trace(go.Bar(
        y=df['StoreName'],
        x=df['UmsatzProM2'],
        orientation='h',
        marker=dict(color=colors, opacity=0.8),
        text=[f"{v:,.0f} €/m²".replace(",", ".") for v in df['UmsatzProM2']],
        textposition='outside',
        textfont=dict(size=11, color='white'),
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Umsatz/m²: %{x:,.0f} €<br>'
            f'Benchmark: {benchmark:,.0f} €/m²'
            '<extra></extra>'
        )
    ))

    # Benchmark-Linie
    fig.add_vline(
        x=benchmark,
        line=dict(color='rgba(255,255,255,0.5)', width=2, dash='dash'),
        annotation_text=f"Ø {benchmark:,.0f} €/m²".replace(",", "."),
        annotation_position="top",
        annotation_font=dict(color='white', size=10)
    )

    fig.update_layout(**get_base_layout(
        xaxis_title="Umsatz pro m² (€)",
        yaxis_title="",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=80, t=30, b=40)
    ))

    fig.update_xaxes(tickformat=",.0f", ticksuffix=" €")

    return fig
