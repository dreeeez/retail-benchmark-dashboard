"""
Benchmark Dashboard - Gruppe 18
Marketing Charts

Charts für Tab 2: Marketing
"""

import plotly.graph_objects as go
from src.charts.base import get_base_layout, get_legend_horizontal


def create_marketing_trend_chart(marketing_df, active_stores: list) -> go.Figure:
    """Erstellt Marketing-Trend-Chart

    Args:
        marketing_df: DataFrame aus load_marketing_kpi('all')
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    for store in active_stores:
        store_mkt = marketing_df[marketing_df['IdStore'] == store['id']]
        if not store_mkt.empty:
            store_mkt = store_mkt.sort_values('IdCalmonthStd')
            fig.add_trace(go.Scatter(
                x=store_mkt['IdCalmonthStd'],
                y=store_mkt['MarketingCostEur'],
                name=store['name'],
                line=dict(color=store['color'], width=3),
                mode='lines+markers'
            ))

    fig.update_layout(**get_base_layout(
        yaxis_title="Marketing (€)",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=400
    ))

    return fig


def create_marketing_bar_chart(active_stores: list, marketing_kpis: dict) -> go.Figure:
    """Erstellt Marketing-Kosten-Balkendiagramm für einzelnen Monat

    Args:
        active_stores: Liste der Store-Configs
        marketing_kpis: Dict mit Marketing-KPIs pro Store

    Returns:
        Plotly Figure
    """
    cost_data = []
    for store in active_stores:
        mkpi = marketing_kpis.get(store['name'], {})
        cost_data.append({
            'name': store['name'],
            'cost': mkpi.get('marketing', 0),
            'color': store['color']
        })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[d['name'] for d in cost_data],
        y=[d['cost'] for d in cost_data],
        marker_color=[d['color'] for d in cost_data],
        text=[f"{d['cost']:,.0f} €".replace(",", ".") for d in cost_data],
        textposition='outside'
    ))

    max_cost = max([d['cost'] for d in cost_data]) if cost_data else 1

    fig.update_layout(**get_base_layout(
        yaxis_title="Marketing-Kosten (€)",
        showlegend=False,
        height=400,
        yaxis=dict(range=[0, max_cost * 1.3])
    ))

    return fig


def create_marketing_quote_chart(active_stores: list, marketing_kpis: dict) -> go.Figure:
    """Erstellt Marketing-Quote-Chart

    Args:
        active_stores: Liste der Store-Configs
        marketing_kpis: Dict mit Marketing-KPIs pro Store

    Returns:
        Plotly Figure
    """
    quote_data = []
    for store in active_stores:
        mkpi = marketing_kpis.get(store['name'], {})
        quote_data.append({
            'name': store['name'],
            'quote': mkpi.get('marketing_quote', 0),
            'color': store['color']
        })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[d['name'] for d in quote_data],
        y=[d['quote'] for d in quote_data],
        marker_color=[d['color'] for d in quote_data],
        text=[f"{d['quote']:.2f}%" for d in quote_data],
        textposition='outside'
    ))

    max_quote = max([d['quote'] for d in quote_data]) if quote_data else 1

    fig.update_layout(**get_base_layout(
        yaxis_title="Marketing-Quote (%)",
        showlegend=False,
        height=400,
        yaxis=dict(range=[0, max_quote * 1.3])
    ))

    return fig
