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


def create_cost_treemap(costs_detail_df, active_stores: list) -> go.Figure:
    """Erstellt Treemap für Kostenstruktur-Analyse

    Zeigt hierarchisch: Store -> Kostenkategorie -> Größe nach Betrag
    Ermöglicht visuellen Vergleich der Kostenverteilung zwischen Filialen.

    Args:
        costs_detail_df: DataFrame aus load_costs_detail() mit Spalten:
                        IdStore, StoreName, Kostenkategorie, KostenEur
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure mit Treemap
    """
    import plotly.express as px

    # Nur aktive Stores
    active_store_ids = [store['id'] for store in active_stores]
    filtered_df = costs_detail_df[costs_detail_df['IdStore'].isin(active_store_ids)].copy()

    if filtered_df.empty:
        fig = go.Figure()
        fig.update_layout(**get_base_layout(height=500))
        return fig

    # Aggregiere über alle Monate (falls Monatsfilter 'all')
    agg_df = filtered_df.groupby(['StoreName', 'Kostenkategorie'], as_index=False)['KostenEur'].sum()

    # Absolute Werte für Treemap (Kosten sind negativ in DB)
    agg_df['KostenAbs'] = agg_df['KostenEur'].abs()

    # Berechne Prozentanteil innerhalb jedes Stores
    store_totals = agg_df.groupby('StoreName')['KostenAbs'].transform('sum')
    agg_df['Prozent'] = (agg_df['KostenAbs'] / store_totals * 100).round(1)

    # Berechne Durchschnitt pro Kategorie (über alle Stores) für Benchmark
    category_avg = agg_df.groupby('Kostenkategorie')['KostenAbs'].mean().to_dict()
    agg_df['Benchmark'] = agg_df['Kostenkategorie'].map(category_avg)
    agg_df['AbweichungPct'] = ((agg_df['KostenAbs'] - agg_df['Benchmark']) / agg_df['Benchmark'] * 100).round(1)

    # Farbe basierend auf Abweichung vom Durchschnitt
    # Grün = unter Durchschnitt (gut), Rot = über Durchschnitt (schlecht)
    def get_color(abw):
        if abw <= -20:
            return '#00ff88'  # Deutlich unter Durchschnitt - grün
        elif abw <= -5:
            return '#7dcea0'  # Leicht unter Durchschnitt
        elif abw <= 5:
            return '#f4d03f'  # Im Durchschnitt - gelb
        elif abw <= 20:
            return '#e59866'  # Leicht über Durchschnitt
        else:
            return '#ff6b6b'  # Deutlich über Durchschnitt - rot

    agg_df['Farbe'] = agg_df['AbweichungPct'].apply(get_color)

    # Kategorien auf Deutsch übersetzen
    kategorie_labels = {
        'Monthly Salary': 'Gehälter',
        'Monthly Social Costs': 'Sozialkosten',
        'Monthly Rent': 'Miete',
        'Additional Procurement Costs': 'Logistik',
        'Marketing Campaign': 'Marketing',
        'Commission': 'Provisionen'
    }
    agg_df['KategorieLabel'] = agg_df['Kostenkategorie'].map(kategorie_labels).fillna(agg_df['Kostenkategorie'])

    # Custom Text für Hover und Labels
    agg_df['Label'] = agg_df.apply(
        lambda row: f"{row['KategorieLabel']}<br>{row['KostenAbs']:,.0f} €<br>({row['Prozent']:.0f}%)",
        axis=1
    )

    fig = px.treemap(
        agg_df,
        path=['StoreName', 'KategorieLabel'],
        values='KostenAbs',
        color='AbweichungPct',
        color_continuous_scale=['#00ff88', '#f4d03f', '#ff6b6b'],
        color_continuous_midpoint=0,
        custom_data=['KostenAbs', 'Prozent', 'AbweichungPct', 'Benchmark']
    )

    fig.update_traces(
        textinfo='label+value',
        textfont=dict(size=12),
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Kosten: %{customdata[0]:,.0f} €<br>'
            'Anteil: %{customdata[1]:.1f}%<br>'
            'Benchmark: %{customdata[3]:,.0f} €<br>'
            'Abweichung: %{customdata[2]:+.1f}%'
            '<extra></extra>'
        ),
        marker=dict(
            line=dict(width=2, color='#1a1a2e')
        )
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
            tickfont=dict(color='white')
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
