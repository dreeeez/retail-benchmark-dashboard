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
        hex_color = store['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        cost_data.append({
            'name': store['name'],
            'cost': mkpi.get('marketing', 0),
            'color': f'rgba({r},{g},{b},0.7)',
            'border': f'rgba({r},{g},{b},0.9)'
        })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[d['name'] for d in cost_data],
        y=[d['cost'] for d in cost_data],
        marker=dict(
            color=[d['color'] for d in cost_data],
            line=dict(color=[d['border'] for d in cost_data], width=1)
        ),
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
        hex_color = store['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        quote_data.append({
            'name': store['name'],
            'quote': mkpi.get('marketing_quote', 0),
            'color': f'rgba({r},{g},{b},0.7)',
            'border': f'rgba({r},{g},{b},0.9)'
        })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[d['name'] for d in quote_data],
        y=[d['quote'] for d in quote_data],
        marker=dict(
            color=[d['color'] for d in quote_data],
            line=dict(color=[d['border'] for d in quote_data], width=1)
        ),
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


def _format_revenue_short(value: float) -> str:
    """Formatiert Umsatzwerte kompakt (1.2M, 450K, etc.)"""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M €"
    elif value >= 1_000:
        return f"{value / 1_000:.0f}K €"
    else:
        return f"{value:.0f} €"


def create_top_campaigns_overall_chart(campaign_df, active_stores: list) -> go.Figure:
    """Erstellt Top 5 Kampagnen Chart nach Gesamtumsatz (horizontal)

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure mit horizontalem Balkendiagramm
    """
    # Nur Kampagnen der aktiven Stores berücksichtigen
    active_store_ids = [store['id'] for store in active_stores]
    filtered_campaigns = campaign_df[campaign_df['IdStore'].isin(active_store_ids)].copy()

    # Gruppiere nach Kampagnenname und summiere RevenueEur über alle Stores
    campaign_totals = filtered_campaigns.groupby('CampaignName', as_index=False)['RevenueEur'].sum()

    # Top 5 nach Gesamtumsatz, sortiert für horizontale Darstellung (niedrigste oben)
    top5_overall = campaign_totals.nlargest(5, 'RevenueEur').sort_values('RevenueEur', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top5_overall['CampaignName'],
        x=top5_overall['RevenueEur'],
        orientation='h',
        marker=dict(
            color='rgba(0, 212, 255, 0.7)',
            line=dict(color='rgba(0, 212, 255, 0.9)', width=1)
        ),
        text=[_format_revenue_short(val) for val in top5_overall['RevenueEur']],
        textposition='outside',
        textfont=dict(size=11, color='white'),
        hovertemplate='<b>%{y}</b><br>Umsatz: %{x:,.0f} €<extra></extra>'
    ))

    fig.update_layout(**get_base_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        height=350,
        margin=dict(l=20, r=20, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(tickfont=dict(size=11))
    ))

    return fig


def create_top_campaigns_per_store_chart(campaign_df, store: dict) -> go.Figure:
    """Erstellt Top 5 Kampagnen Chart für einen einzelnen Store (horizontal)

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        store: Store-Config Dictionary mit id, name, color

    Returns:
        Plotly Figure mit horizontalem Balkendiagramm
    """
    fig = go.Figure()

    store_campaigns = campaign_df[campaign_df['IdStore'] == store['id']].copy()

    if store_campaigns.empty:
        # Leerer Chart wenn keine Daten
        fig.update_layout(**get_base_layout(
            height=300,
            margin=dict(l=20, r=20, t=10, b=10)
        ))
        return fig

    # Top 5 nach Umsatz, sortiert für horizontale Darstellung (niedrigste oben)
    top5 = store_campaigns.nlargest(5, 'RevenueEur').sort_values('RevenueEur', ascending=True)

    # Transparente Farbe aus Store-Farbe
    hex_color = store['color'].lstrip('#')
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    fig.add_trace(go.Bar(
        y=top5['CampaignName'],
        x=top5['RevenueEur'],
        orientation='h',
        marker=dict(
            color=f'rgba({r},{g},{b},0.7)',
            line=dict(color=f'rgba({r},{g},{b},0.9)', width=1)
        ),
        text=[_format_revenue_short(val) for val in top5['RevenueEur']],
        textposition='outside',
        textfont=dict(size=11, color='white'),
        hovertemplate='<b>%{y}</b><br>Umsatz: %{x:,.0f} €<extra></extra>'
    ))

    fig.update_layout(**get_base_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=80, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(tickfont=dict(size=11))
    ))

    return fig


def create_campaign_profit_chart(campaign_df, store: dict) -> go.Figure:
    """Erstellt Top 5 Profit-Kampagnen Chart für einen einzelnen Store (horizontal)

    Profit = RevenueEur - CostEur - DiscountEur

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        store: Store-Config Dictionary mit id, name, color

    Returns:
        Plotly Figure mit horizontalem Balkendiagramm
    """
    fig = go.Figure()

    store_campaigns = campaign_df[campaign_df['IdStore'] == store['id']].copy()

    if store_campaigns.empty:
        # Leerer Chart wenn keine Daten
        fig.update_layout(**get_base_layout(
            height=300,
            margin=dict(l=20, r=20, t=10, b=10)
        ))
        return fig

    # Top 5 nach Profit, sortiert für horizontale Darstellung (niedrigste oben)
    top5 = store_campaigns.nlargest(5, 'CampaignProfit').sort_values('CampaignProfit', ascending=True)

    # Transparente Farbe aus Store-Farbe
    hex_color = store['color'].lstrip('#')
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    fig.add_trace(go.Bar(
        y=top5['CampaignName'],
        x=top5['CampaignProfit'],
        orientation='h',
        marker=dict(
            color=f'rgba({r},{g},{b},0.7)',
            line=dict(color=f'rgba({r},{g},{b},0.9)', width=1)
        ),
        text=[_format_revenue_short(val) for val in top5['CampaignProfit']],
        textposition='outside',
        textfont=dict(size=11, color='white'),
        hovertemplate='<b>%{y}</b><br>Profit: %{x:,.0f} €<extra></extra>'
    ))

    fig.update_layout(**get_base_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=80, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=True, zerolinecolor='rgba(255,255,255,0.3)', autorange=True),
        yaxis=dict(tickfont=dict(size=11))
    ))

    return fig
