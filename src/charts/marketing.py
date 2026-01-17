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
        marker_color='rgba(0, 212, 255, 0.7)',
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


def create_top_campaigns_per_store_chart(campaign_df, active_stores: list) -> go.Figure:
    """Erstellt Top 3 Kampagnen pro Store (horizontal, gruppiert)

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure mit horizontalem gruppierten Balkendiagramm
    """
    fig = go.Figure()

    # Sammle alle Top 3 Kampagnen aller Stores für konsistente Y-Achse
    all_campaign_names = set()
    store_data = {}

    for store in active_stores:
        store_campaigns = campaign_df[campaign_df['IdStore'] == store['id']].copy()
        if not store_campaigns.empty:
            top3 = store_campaigns.nlargest(3, 'RevenueEur')
            store_data[store['name']] = top3
            all_campaign_names.update(top3['CampaignName'].tolist())

    # Sortiere Kampagnennamen alphabetisch für konsistente Reihenfolge
    sorted_campaigns = sorted(all_campaign_names)

    for store in active_stores:
        if store['name'] in store_data:
            top3 = store_data[store['name']]

            # Erstelle dict für schnellen Zugriff
            campaign_revenue = dict(zip(top3['CampaignName'], top3['RevenueEur']))

            # Baue Arrays für alle Kampagnen (0 wenn nicht in Top 3)
            y_values = sorted_campaigns
            x_values = [campaign_revenue.get(name, 0) for name in sorted_campaigns]
            text_values = [_format_revenue_short(val) if val > 0 else "" for val in x_values]

            fig.add_trace(go.Bar(
                name=store['name'],
                y=y_values,
                x=x_values,
                orientation='h',
                marker_color=f"rgba({int(store['color'][1:3], 16)}, {int(store['color'][3:5], 16)}, {int(store['color'][5:7], 16)}, 0.7)",
                text=text_values,
                textposition='outside',
                textfont=dict(size=10, color='white'),
                hovertemplate='<b>%{y}</b><br>%{x:,.0f} €<extra></extra>'
            ))

    fig.update_layout(**get_base_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=350,
        barmode='group',
        margin=dict(l=20, r=20, t=40, b=10),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(tickfont=dict(size=11))
    ))

    return fig


def create_campaign_profit_chart(campaign_df, active_stores: list) -> go.Figure:
    """Erstellt Top 3 Profit-Kampagnen pro Store (horizontal, gruppiert)

    Profit = RevenueEur - CostEur - DiscountEur

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure mit horizontalem gruppierten Balkendiagramm
    """
    fig = go.Figure()

    # Sammle alle Top 3 Profit-Kampagnen aller Stores
    all_campaign_names = set()
    store_data = {}

    for store in active_stores:
        store_campaigns = campaign_df[campaign_df['IdStore'] == store['id']].copy()
        if not store_campaigns.empty:
            # Top 3 nach CampaignProfit sortieren
            top3 = store_campaigns.nlargest(3, 'CampaignProfit')
            store_data[store['name']] = top3
            all_campaign_names.update(top3['CampaignName'].tolist())

    # Sortiere Kampagnennamen alphabetisch für konsistente Reihenfolge
    sorted_campaigns = sorted(all_campaign_names)

    for store in active_stores:
        if store['name'] in store_data:
            top3 = store_data[store['name']]

            # Erstelle dict für schnellen Zugriff
            campaign_profit = dict(zip(top3['CampaignName'], top3['CampaignProfit']))

            # Baue Arrays für alle Kampagnen (0 wenn nicht in Top 3)
            y_values = sorted_campaigns
            x_values = [campaign_profit.get(name, 0) for name in sorted_campaigns]
            text_values = [_format_revenue_short(val) if val > 0 else "" for val in x_values]

            fig.add_trace(go.Bar(
                name=store['name'],
                y=y_values,
                x=x_values,
                orientation='h',
                marker_color=f"rgba({int(store['color'][1:3], 16)}, {int(store['color'][3:5], 16)}, {int(store['color'][5:7], 16)}, 0.7)",
                text=text_values,
                textposition='outside',
                textfont=dict(size=10, color='white'),
                hovertemplate='<b>%{y}</b><br>Profit: %{x:,.0f} EUR<extra></extra>'
            ))

    fig.update_layout(**get_base_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=350,
        barmode='group',
        margin=dict(l=20, r=20, t=40, b=10),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=True, zerolinecolor='rgba(255,255,255,0.3)'),
        yaxis=dict(tickfont=dict(size=11))
    ))

    return fig
