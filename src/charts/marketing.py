"""
Benchmark Dashboard - Gruppe 18
Marketing Charts

Charts für Tab 2: Marketing
"""

import plotly.graph_objects as go
from src.charts.base import get_base_layout, get_legend_horizontal


def create_marketing_trend_chart(marketing_df, active_stores: list) -> go.Figure:
    """Erstellt Marketing-Trend-Chart als Balkendiagramm

    Args:
        marketing_df: DataFrame aus load_marketing_kpi('all')
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure (gruppiertes Balkendiagramm)
    """
    fig = go.Figure()

    for store in active_stores:
        store_mkt = marketing_df[marketing_df['IdStore'] == store['id']]
        if not store_mkt.empty:
            store_mkt = store_mkt.sort_values('IdCalmonthStd')
            # Transparente Farbe für Balken
            hex_color = store['color'].lstrip('#')
            r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

            fig.add_trace(go.Bar(
                x=store_mkt['IdCalmonthStd'],
                y=store_mkt['MarketingCostEur'],
                name=store['name'],
                marker=dict(
                    color=f'rgba({r},{g},{b},0.7)',
                    line=dict(color=f'rgba({r},{g},{b},0.9)', width=1)
                ),
                hovertemplate='<b>%{x}</b><br>%{y:,.0f} €<extra>' + store['name'] + '</extra>'
            ))

    fig.update_layout(**get_base_layout(
        yaxis_title="Marketing (€)",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=400,
        barmode='group'
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


def create_marketing_revenue_share_chart(active_stores: list, marketing_kpis: dict) -> go.Figure:
    """Erstellt 100% Stacked Bar Chart: Marketing-attributierter vs. unabhängiger Umsatz

    Zeigt für jeden Store, wie viel Prozent des Gesamtumsatzes durch Marketing generiert wurde.

    Args:
        active_stores: Liste der Store-Configs
        marketing_kpis: Dict mit Marketing-KPIs pro Store

    Returns:
        Plotly Figure (100% Stacked Bar)
    """
    store_names = []
    marketing_revenue = []
    organic_revenue = []
    marketing_pct = []
    organic_pct = []

    for store in active_stores:
        mkpi = marketing_kpis.get(store['name'], {})
        umsatz_marketing = mkpi.get('umsatz_mit_marketing', 0)
        umsatz_organisch = mkpi.get('umsatz_ohne_marketing', 0)
        umsatz_gesamt = mkpi.get('umsatz_gesamt', 0)

        store_names.append(store['name'])
        marketing_revenue.append(umsatz_marketing)
        organic_revenue.append(umsatz_organisch)

        if umsatz_gesamt > 0:
            marketing_pct.append(umsatz_marketing / umsatz_gesamt * 100)
            organic_pct.append(umsatz_organisch / umsatz_gesamt * 100)
        else:
            marketing_pct.append(0)
            organic_pct.append(0)

    fig = go.Figure()

    # Marketing-attributierter Umsatz (grün)
    fig.add_trace(go.Bar(
        name='Marketing-Umsatz',
        x=store_names,
        y=marketing_pct,
        marker=dict(
            color='rgba(0, 255, 136, 0.7)',
            line=dict(color='rgba(0, 255, 136, 0.9)', width=1)
        ),
        text=[f"{pct:.1f}%" for pct in marketing_pct],
        textposition='inside',
        textfont=dict(color='white', size=12),
        hovertemplate='<b>%{x}</b><br>Marketing-Umsatz: %{customdata:,.0f} €<br>Anteil: %{y:.1f}%<extra></extra>',
        customdata=marketing_revenue
    ))

    # Organischer Umsatz (grau)
    fig.add_trace(go.Bar(
        name='Organischer Umsatz',
        x=store_names,
        y=organic_pct,
        marker=dict(
            color='rgba(150, 150, 150, 0.5)',
            line=dict(color='rgba(150, 150, 150, 0.7)', width=1)
        ),
        text=[f"{pct:.1f}%" for pct in organic_pct],
        textposition='inside',
        textfont=dict(color='white', size=12),
        hovertemplate='<b>%{x}</b><br>Organischer Umsatz: %{customdata:,.0f} €<br>Anteil: %{y:.1f}%<extra></extra>',
        customdata=organic_revenue
    ))

    fig.update_layout(**get_base_layout(
        yaxis_title="Anteil am Gesamtumsatz (%)",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=400,
        barmode='stack',
        yaxis=dict(range=[0, 100], ticksuffix='%')
    ))

    return fig


def create_roas_monthly_chart(marketing_df, active_stores: list) -> go.Figure:
    """Erstellt ROAS-Balkendiagramm pro Monat

    Zeigt für jeden Store den Return on Advertising Spend (ROAS) pro Monat.
    ROAS = Marketing-attributierter Umsatz / Marketing-Kosten

    Args:
        marketing_df: DataFrame aus load_marketing_kpi('all') mit ROAS-Spalte
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure (gruppiertes Balkendiagramm)
    """
    fig = go.Figure()

    for store in active_stores:
        store_data = marketing_df[marketing_df['IdStore'] == store['id']]
        if not store_data.empty:
            store_data = store_data.sort_values('IdCalmonthStd')
            # Transparente Farbe für Balken
            hex_color = store['color'].lstrip('#')
            r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

            # ROAS-Werte (None/NaN durch 0 ersetzen für Anzeige)
            roas_values = store_data['ROAS'].fillna(0).tolist()

            fig.add_trace(go.Bar(
                x=store_data['IdCalmonthStd'],
                y=roas_values,
                name=store['name'],
                marker=dict(
                    color=f'rgba({r},{g},{b},0.7)',
                    line=dict(color=f'rgba({r},{g},{b},0.9)', width=1)
                ),
                text=[f"{v:.1f}x" if v > 0 else "" for v in roas_values],
                textposition='outside',
                textfont=dict(size=10),
                hovertemplate='<b>%{x}</b><br>ROAS: %{y:.2f}x<extra>' + store['name'] + '</extra>'
            ))

    # Referenzlinie bei ROAS = 1 (Break-even)
    fig.add_hline(y=1, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  annotation_text="Break-even", annotation_position="right")

    fig.update_layout(**get_base_layout(
        yaxis_title="ROAS (Return on Ad Spend)",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=400,
        barmode='group'
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


def create_campaign_efficiency_scatter(campaign_df, active_stores: list) -> go.Figure:
    """Erstellt Scatter Plot für Kampagnen-Effizienz (Kosten vs. Umsatz)

    X-Achse: Marketing-Kosten (CostEur)
    Y-Achse: Generierter Umsatz (RevenueEur)

    Interpretation:
    - Oben links = "Perlen" (wenig Kosten, viel Umsatz) = hoher ROAS
    - Unten rechts = "Geldverbrenner" (hohe Kosten, wenig Umsatz) = niedriger ROAS
    - Diagonale = Break-even (ROAS = 1)

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure mit Scatter Plot
    """
    fig = go.Figure()

    # Nur Kampagnen der aktiven Stores
    active_store_ids = [store['id'] for store in active_stores]
    filtered_df = campaign_df[campaign_df['IdStore'].isin(active_store_ids)].copy()

    if filtered_df.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    # Für jeden Store eine eigene Trace (Farbe)
    for store in active_stores:
        store_data = filtered_df[filtered_df['IdStore'] == store['id']]
        if store_data.empty:
            continue

        hex_color = store['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        fig.add_trace(go.Scatter(
            x=store_data['CostEur'],
            y=store_data['RevenueEur'],
            mode='markers+text',
            name=store['name'],
            marker=dict(
                size=12,
                color=f'rgba({r},{g},{b},0.7)',
                line=dict(color=f'rgba({r},{g},{b},1)', width=1)
            ),
            text=store_data['CampaignName'],
            textposition='top center',
            textfont=dict(size=9, color='white'),
            hovertemplate=(
                '<b>%{text}</b><br>'
                'Kosten: %{x:,.0f} €<br>'
                'Umsatz: %{y:,.0f} €<br>'
                'ROAS: %{customdata:.1f}x'
                '<extra>' + store['name'] + '</extra>'
            ),
            customdata=store_data['ROAS'].fillna(0)
        ))

    # Diagonale Linie für ROAS = 1 (Break-even)
    if not filtered_df.empty:
        max_val = max(filtered_df['CostEur'].max(), filtered_df['RevenueEur'].max()) * 1.1
        fig.add_trace(go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            name='ROAS = 1 (Break-even)',
            line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dash'),
            hoverinfo='skip'
        ))

    fig.update_layout(**get_base_layout(
        xaxis_title="Marketing-Kosten (€)",
        yaxis_title="Generierter Umsatz (€)",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=450,
        margin=dict(l=60, r=20, t=20, b=60)
    ))

    # Annotationen für Quadranten
    fig.add_annotation(
        x=0.02, y=0.98, xref="paper", yref="paper",
        text="⭐ Perlen<br>(effizient)",
        showarrow=False,
        font=dict(size=10, color='#00ff88'),
        align='left'
    )
    fig.add_annotation(
        x=0.98, y=0.02, xref="paper", yref="paper",
        text="⚠️ Geldverbrenner<br>(ineffizient)",
        showarrow=False,
        font=dict(size=10, color='#ff6b6b'),
        align='right'
    )

    return fig
