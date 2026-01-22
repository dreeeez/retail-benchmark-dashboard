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


def create_campaign_efficiency_scatter(campaign_df, store: dict) -> go.Figure:
    """Erstellt gruppierten Bar Chart für Top 8 Kampagnen (Kosten vs. Umsatz) einer Filiale

    Zeigt die Top 8 Kampagnen nach Umsatz mit zwei Balken pro Kampagne:
    - Marketing-Kosten (CostEur)
    - Generierter Umsatz (RevenueEur)

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        store: Store-Config Dictionary mit id, name, color

    Returns:
        Plotly Figure mit gruppiertem Bar Chart
    """
    fig = go.Figure()

    if campaign_df is None or campaign_df.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    # Nur Kampagnen dieser Filiale
    store_campaigns = campaign_df[campaign_df['IdStore'] == store['id']].copy()

    if store_campaigns.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    # Aggregiere pro Kampagne (über alle Monate)
    campaign_totals = store_campaigns.groupby('CampaignName').agg({
        'CostEur': 'sum',
        'RevenueEur': 'sum'
    }).reset_index()

    # Top 8 nach Umsatz
    top_campaigns = campaign_totals.nlargest(8, 'RevenueEur')

    if top_campaigns.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    campaign_names = top_campaigns['CampaignName'].tolist()
    costs = top_campaigns['CostEur'].tolist()
    revenues = top_campaigns['RevenueEur'].tolist()

    # Balken für Kosten
    fig.add_trace(go.Bar(
        x=campaign_names,
        y=costs,
        name='Marketing-Kosten',
        marker=dict(
            color='rgba(255, 71, 87, 0.8)',
            line=dict(color='rgba(255, 71, 87, 1)', width=2)
        ),
        hovertemplate='<b>%{x}</b><br>Kosten: %{y:,.0f} €<extra></extra>'
    ))

    # Balken für Umsatz
    fig.add_trace(go.Bar(
        x=campaign_names,
        y=revenues,
        name='Generierter Umsatz',
        marker=dict(
            color='rgba(0, 255, 136, 0.8)',
            line=dict(color='rgba(0, 255, 136, 1)', width=2)
        ),
        hovertemplate='<b>%{x}</b><br>Umsatz: %{y:,.0f} €<extra></extra>'
    ))

    fig.update_layout(**get_base_layout(
        xaxis_title="Kampagne",
        yaxis_title="Betrag (€)",
        showlegend=True,
        legend=get_legend_horizontal(),
        barmode='group',
        height=500,
        margin=dict(l=70, r=30, t=40, b=100)
    ))

    # Achsen-Formatierung
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.1)',
        showgrid=False,
        tickangle=-45
    )
    fig.update_yaxes(
        tickformat=",.0f",
        ticksuffix=" €",
        gridcolor='rgba(255,255,255,0.1)',
        showgrid=True
    )

    return fig


def create_cpa_monthly_chart(campaign_df, store: dict) -> go.Figure:
    """Erstellt CPA-Chart pro Kampagne und Monat für eine Filiale (gruppiertes Balkendiagramm)

    Berechnet CPA = CostEur / Quantity pro Kampagne pro Monat.
    Nur bezahlte Kampagnen werden einbezogen (CostEur > 0).

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign() mit IdCalmonthStd
        store: Store-Config Dictionary mit id, name, color

    Returns:
        Plotly Figure (gruppiertes Balkendiagramm)
    """
    fig = go.Figure()

    if campaign_df is None or campaign_df.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    # Nur diese Filiale und bezahlte Kampagnen (CostEur > 0)
    paid_campaigns = campaign_df[
        (campaign_df['IdStore'] == store['id']) &
        (campaign_df['CostEur'] > 0) &
        (campaign_df['Quantity'] > 0)
    ].copy()

    if paid_campaigns.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    # CPA berechnen pro Kampagne pro Monat
    paid_campaigns['CPA'] = paid_campaigns['CostEur'] / paid_campaigns['Quantity']

    # Durchschnittlichen CPA pro Kampagne berechnen (über alle Monate)
    avg_cpa_per_campaign = paid_campaigns.groupby('CampaignName')['CPA'].mean().sort_values()

    # Top 5 Kampagnen mit niedrigstem durchschnittlichen CPA
    top_5_campaigns = avg_cpa_per_campaign.head(5).index.tolist()

    # Nur Daten dieser Top 5 Kampagnen
    top_campaigns_data = paid_campaigns[paid_campaigns['CampaignName'].isin(top_5_campaigns)].copy()

    # Sortiere nach Monat
    top_campaigns_data = top_campaigns_data.sort_values('IdCalmonthStd')

    if top_campaigns_data.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    # Farbpalette für Kampagnen
    campaign_colors = [
        '#00d4ff', '#00ff88', '#ff6b6b', '#ffd93d', '#c56cf0',
        '#ff9f43', '#54a0ff', '#5f27cd', '#01a3a4', '#f368e0'
    ]

    for idx, campaign in enumerate(top_5_campaigns):
        campaign_data = top_campaigns_data[top_campaigns_data['CampaignName'] == campaign]

        # Farbe aus Palette (zyklisch)
        color = campaign_colors[idx % len(campaign_colors)]
        hex_color = color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        fig.add_trace(go.Bar(
            x=campaign_data['IdCalmonthStd'],
            y=campaign_data['CPA'],
            name=campaign,
            marker=dict(
                color=f'rgba({r},{g},{b},0.7)',
                line=dict(color=f'rgba({r},{g},{b},0.9)', width=1)
            ),
            text=[f"{cpa:.2f} €" for cpa in campaign_data['CPA']],
            textposition='outside',
            textfont=dict(size=9),
            hovertemplate=(
                '<b>%{x}</b><br>'
                f'<b>{campaign}</b><br>'
                'CPA: %{y:.2f} €<br>'
                '<extra></extra>'
            )
        ))

    fig.update_layout(**get_base_layout(
        yaxis_title="CPA (€ pro Stück)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=9)
        ),
        height=450,
        barmode='group'
    ))

    # Y-Achse bei 0 starten
    fig.update_yaxes(
        tickformat=".2f",
        ticksuffix=" €",
        rangemode='tozero'
    )

    return fig


def create_cpa_top5_per_store_chart(campaign_df, store: dict) -> go.Figure:
    """Erstellt Top 5 Kampagnen Chart nach Effizienz für einen Store (horizontal)

    - Bezahlte Kampagnen: CPA = CostEur / Quantity (niedriger = besser)
    - Rabatt-Aktionen (CostEur = 0): Sortiert nach Quantity (höher = besser)

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign()
        store: Store-Config Dictionary mit id, name, color

    Returns:
        Plotly Figure mit horizontalem Balkendiagramm
    """
    fig = go.Figure()

    if campaign_df is None or campaign_df.empty:
        fig.update_layout(**get_base_layout(height=350))
        return fig

    # Alle Kampagnen dieses Stores mit Verkäufen
    store_campaigns = campaign_df[
        (campaign_df['IdStore'] == store['id']) &
        (campaign_df['Quantity'] > 0)
    ].copy()

    if store_campaigns.empty:
        fig.update_layout(**get_base_layout(height=350))
        return fig

    # Aggregiere pro Kampagne (über alle Monate)
    campaign_agg = store_campaigns.groupby('CampaignName').agg({
        'CostEur': 'sum',
        'Quantity': 'sum'
    }).reset_index()

    # Teile in bezahlte und Rabatt-Aktionen
    paid = campaign_agg[campaign_agg['CostEur'] > 0].copy()
    discounts = campaign_agg[campaign_agg['CostEur'] == 0].copy()

    # Bezahlte: CPA berechnen, Top 5 nach niedrigstem CPA
    if not paid.empty:
        paid['CPA'] = paid['CostEur'] / paid['Quantity']
        paid['Label'] = paid['CPA'].apply(lambda x: f"{x:.2f} € CPA")
        paid['Typ'] = 'Bezahlt'
        paid_top5 = paid.nsmallest(5, 'CPA')
    else:
        paid_top5 = paid

    # Rabatt-Aktionen: Top 5 nach höchster Quantity
    if not discounts.empty:
        discounts['CPA'] = 0  # Für Sortierung
        discounts['Label'] = discounts['Quantity'].apply(lambda x: f"{int(x):,} Stück".replace(",", "."))
        discounts['Typ'] = 'Rabatt'
        discount_top5 = discounts.nlargest(5, 'Quantity')
    else:
        discount_top5 = discounts

    # Transparente Farbe aus Store-Farbe
    hex_color = store['color'].lstrip('#')
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    # Bezahlte Kampagnen (Store-Farbe)
    if not paid_top5.empty:
        paid_sorted = paid_top5.sort_values('CPA', ascending=False)
        fig.add_trace(go.Bar(
            y=paid_sorted['CampaignName'],
            x=paid_sorted['Quantity'],
            orientation='h',
            name='Bezahlte Kampagnen',
            marker=dict(
                color=f'rgba({r},{g},{b},0.7)',
                line=dict(color=f'rgba({r},{g},{b},0.9)', width=1)
            ),
            text=paid_sorted['Label'],
            textposition='outside',
            textfont=dict(size=10, color='white'),
            hovertemplate='<b>%{y}</b><br>Verkäufe: %{x:,}<br>%{text}<extra>Bezahlt</extra>'
        ))

    # Rabatt-Aktionen (Grün)
    if not discount_top5.empty:
        discount_sorted = discount_top5.sort_values('Quantity', ascending=True)
        fig.add_trace(go.Bar(
            y=discount_sorted['CampaignName'],
            x=discount_sorted['Quantity'],
            orientation='h',
            name='Rabatt-Aktionen',
            marker=dict(
                color='rgba(0, 255, 136, 0.7)',
                line=dict(color='rgba(0, 255, 136, 0.9)', width=1)
            ),
            text=discount_sorted['Label'],
            textposition='outside',
            textfont=dict(size=10, color='white'),
            hovertemplate='<b>%{y}</b><br>Verkäufe: %{x:,}<extra>Rabatt-Aktion</extra>'
        ))

    fig.update_layout(**get_base_layout(
        xaxis_title="Verkäufe (Stück)",
        yaxis_title="",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=9)
        ),
        height=400,
        margin=dict(l=20, r=100, t=40, b=40),
        yaxis=dict(tickfont=dict(size=10))
    ))

    return fig


def create_romi_monthly_chart(campaign_df, active_stores: list) -> go.Figure:
    """Erstellt ROMI-Zeitverlauf-Chart (Return on Marketing Investment pro Monat)

    Berechnet ROMI = SUM(CampaignProfit) / SUM(CostEur) pro Monat und Store.
    Nur bezahlte Kampagnen werden einbezogen (CostEur > 0).

    Args:
        campaign_df: DataFrame aus load_marketing_by_campaign() mit IdCalmonthStd
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure (gruppiertes Balkendiagramm)
    """
    fig = go.Figure()

    if campaign_df is None or campaign_df.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    # Nur aktive Stores und bezahlte Kampagnen (CostEur > 0)
    active_store_ids = [store['id'] for store in active_stores]
    paid_campaigns = campaign_df[
        (campaign_df['IdStore'].isin(active_store_ids)) &
        (campaign_df['CostEur'] > 0)
    ].copy()

    if paid_campaigns.empty:
        fig.update_layout(**get_base_layout(height=400))
        return fig

    for store in active_stores:
        store_data = paid_campaigns[paid_campaigns['IdStore'] == store['id']]
        if store_data.empty:
            continue

        # Aggregiere pro Monat: ROMI = SUM(CampaignProfit) / SUM(CostEur)
        monthly_agg = store_data.groupby('IdCalmonthStd').agg({
            'CampaignProfit': 'sum',
            'CostEur': 'sum'
        }).reset_index()

        # ROMI berechnen (nur wenn CostEur > 0)
        monthly_agg['ROMI'] = monthly_agg.apply(
            lambda row: row['CampaignProfit'] / row['CostEur'] if row['CostEur'] > 0 else 0,
            axis=1
        )

        monthly_agg = monthly_agg.sort_values('IdCalmonthStd')

        # Transparente Farbe
        hex_color = store['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        fig.add_trace(go.Bar(
            x=monthly_agg['IdCalmonthStd'],
            y=monthly_agg['ROMI'],
            name=store['name'],
            marker=dict(
                color=f'rgba({r},{g},{b},0.7)',
                line=dict(color=f'rgba({r},{g},{b},0.9)', width=1)
            ),
            text=[f"{romi:.1f}x" if romi != 0 else "" for romi in monthly_agg['ROMI']],
            textposition='outside',
            textfont=dict(size=10),
            hovertemplate=(
                '<b>%{x}</b><br>'
                'ROMI: %{y:.2f}x<br>'
                '<extra>' + store['name'] + '</extra>'
            )
        ))

    # Referenzlinie bei ROMI = 0 (Break-even)
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  annotation_text="Break-even", annotation_position="right")

    fig.update_layout(**get_base_layout(
        yaxis_title="ROMI (Return on Marketing Investment)",
        showlegend=True,
        legend=get_legend_horizontal(),
        height=400,
        barmode='group'
    ))

    return fig
