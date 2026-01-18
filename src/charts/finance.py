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
