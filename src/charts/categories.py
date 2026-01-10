"""
Benchmark Dashboard - Gruppe 18
Categories Charts

Charts für Tab 4: Produktkategorien
"""

import plotly.graph_objects as go
from src.charts.base import get_base_layout, get_legend_horizontal_centered
from src.config.categories import get_category_color


def create_revenue_distribution_chart(df_filtered, active_stores: list,
                                       cat_col: str, revenue_col: str,
                                       filter_by_store) -> go.Figure:
    """Erstellt 100% gestapeltes Umsatzverteilungs-Chart

    Args:
        df_filtered: Gefilterter DataFrame
        active_stores: Liste der Store-Configs
        cat_col: Name der Kategorie-Spalte
        revenue_col: Name der Umsatz-Spalte
        filter_by_store: Funktion zum Filtern nach Store

    Returns:
        Plotly Figure
    """
    all_categories = sorted(df_filtered[cat_col].unique())

    # Daten pro Store und Kategorie berechnen
    store_cat_pct = {}
    for store in active_stores:
        store_cat_data = filter_by_store(df_filtered, store)
        cat_sums = store_cat_data.groupby(cat_col)[revenue_col].sum()
        total = cat_sums.sum()
        cat_pct = (cat_sums / total * 100) if total > 0 else cat_sums * 0
        store_cat_pct[store['name']] = cat_pct

    fig = go.Figure()

    for cat in all_categories:
        values = [store_cat_pct[store['name']].get(cat, 0) for store in active_stores]

        fig.add_trace(go.Bar(
            name=cat,
            y=[s['name'] for s in active_stores],
            x=values,
            orientation='h',
            marker_color=get_category_color(cat),
            text=[f"{v:.1f}%" for v in values],
            textposition='inside',
            insidetextanchor='middle'
        ))

    fig.update_layout(**get_base_layout(
        barmode='stack',
        xaxis_title="Umsatzanteil (%)",
        xaxis=dict(range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.25, xanchor="center", x=0.5),
        height=320,
        margin=dict(l=120, r=20, t=100, b=40)
    ))

    return fig


def create_quantity_heatmap(df_filtered, active_stores: list,
                            cat_col: str, quantity_col: str,
                            filter_by_store) -> go.Figure:
    """Erstellt Stückzahl-Heatmap

    Args:
        df_filtered: Gefilterter DataFrame
        active_stores: Liste der Store-Configs
        cat_col: Name der Kategorie-Spalte
        quantity_col: Name der Stückzahl-Spalte
        filter_by_store: Funktion zum Filtern nach Store

    Returns:
        Plotly Figure
    """
    all_cats = sorted(df_filtered[cat_col].unique())
    store_names = [s['name'] for s in active_stores]

    z_values = []
    text_values = []

    for cat in all_cats:
        row_values = []
        row_text = []
        for store in active_stores:
            store_cat_data = filter_by_store(df_filtered, store)
            cat_sums = store_cat_data.groupby(cat_col)[quantity_col].sum()
            total_qty = cat_sums.sum()
            pct = (cat_sums.get(cat, 0) / total_qty * 100) if total_qty > 0 else 0
            row_values.append(pct)
            row_text.append(f"{pct:.1f}%")
        z_values.append(row_values)
        text_values.append(row_text)

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=store_names,
        y=all_cats,
        text=text_values,
        texttemplate="%{text}",
        textfont={"size": 14, "color": "white"},
        colorscale=[
            [0, '#1a1a2e'],
            [0.25, '#2d2d44'],
            [0.5, '#4a3f6b'],
            [0.75, '#7c3aed'],
            [1, '#a855f7']
        ],
        showscale=True,
        colorbar=dict(
            title=dict(text="Anteil (%)", font=dict(color='white')),
            tickfont=dict(color='white')
        ),
        hovertemplate='%{y}<br>%{x}: %{text}<extra></extra>'
    ))

    fig.update_layout(**get_base_layout(
        xaxis=dict(side='top', tickfont=dict(size=12)),
        yaxis=dict(tickfont=dict(size=11)),
        height=350,
        margin=dict(l=100, r=80, t=40, b=20)
    ))

    return fig


def create_margin_by_category_chart(df_filtered, active_stores: list,
                                     cat_col: str, profit_col: str, revenue_col: str,
                                     filter_by_store) -> go.Figure:
    """Erstellt Bruttomarge nach Kategorie Chart

    Args:
        df_filtered: Gefilterter DataFrame
        active_stores: Liste der Store-Configs
        cat_col: Name der Kategorie-Spalte
        profit_col: Name der Gewinn-Spalte
        revenue_col: Name der Umsatz-Spalte
        filter_by_store: Funktion zum Filtern nach Store

    Returns:
        Plotly Figure
    """
    # Berechne durchschnittliche Marge pro Kategorie für Sortierung
    all_margins = {}
    store_margins = {}

    for store in active_stores:
        store_cat_data = filter_by_store(df_filtered, store)
        cat_profit = store_cat_data.groupby(cat_col)[profit_col].sum()
        cat_revenue = store_cat_data.groupby(cat_col)[revenue_col].sum()
        cat_margin = (cat_profit / cat_revenue * 100).fillna(0)
        store_margins[store['name']] = cat_margin

        for cat in cat_margin.index:
            if cat not in all_margins:
                all_margins[cat] = []
            all_margins[cat].append(cat_margin[cat])

    # Sortiere nach Durchschnittsmarge
    avg_margins = {cat: sum(vals) / len(vals) for cat, vals in all_margins.items()}
    sorted_categories = sorted(avg_margins.keys(), key=lambda x: avg_margins[x], reverse=True)

    # Opazität pro Store
    store_styles = {}
    for i, store in enumerate(active_stores):
        if i == 0:
            store_styles[store['name']] = {'opacity': 1.0, 'line_width': 0}
        elif i == 1:
            store_styles[store['name']] = {'opacity': 0.55, 'line_width': 2}
        else:
            store_styles[store['name']] = {'opacity': 0.25, 'line_width': 3}

    fig = go.Figure()

    for store in active_stores:
        cat_margin = store_margins[store['name']]
        sorted_values = [cat_margin.get(cat, 0) for cat in sorted_categories]

        bar_colors = []
        line_colors = []
        style = store_styles.get(store['name'], {'opacity': 0.5, 'line_width': 1})

        for cat in sorted_categories:
            base_color = get_category_color(cat)
            hex_color = base_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
            bar_colors.append(f'rgba({r},{g},{b},{style["opacity"]})')
            line_colors.append(f'rgba({r},{g},{b},1)')

        fig.add_trace(go.Bar(
            name=store['name'],
            y=sorted_categories,
            x=sorted_values,
            marker=dict(
                color=bar_colors,
                line=dict(color=line_colors, width=style['line_width'])
            ),
            text=[f"{v:.1f}%" for v in sorted_values],
            textposition='outside',
            orientation='h'
        ))

    fig.update_layout(**get_base_layout(
        barmode='group',
        xaxis_title="Bruttomarge (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.12),
        height=420,
        margin=dict(t=60),
        yaxis=dict(categoryorder='array', categoryarray=sorted_categories[::-1])
    ))

    return fig


def create_profit_distribution_chart(df_filtered, active_stores: list,
                                      cat_col: str, profit_col: str,
                                      filter_by_store) -> go.Figure:
    """Erstellt Bruttogewinn-Verteilung Chart

    Args:
        df_filtered: Gefilterter DataFrame
        active_stores: Liste der Store-Configs
        cat_col: Name der Kategorie-Spalte
        profit_col: Name der Gewinn-Spalte
        filter_by_store: Funktion zum Filtern nach Store

    Returns:
        Plotly Figure
    """
    store_profit_pct = {}
    total_profit_by_cat = {}

    for store in active_stores:
        store_cat_data = filter_by_store(df_filtered, store)
        cat_profit = store_cat_data.groupby(cat_col)[profit_col].sum()
        total_profit = cat_profit.sum()
        cat_pct = (cat_profit / total_profit * 100) if total_profit > 0 else cat_profit * 0
        store_profit_pct[store['name']] = cat_pct

        for cat in cat_pct.index:
            if cat not in total_profit_by_cat:
                total_profit_by_cat[cat] = 0
            total_profit_by_cat[cat] += cat_pct[cat]

    sorted_categories = sorted(total_profit_by_cat.keys(),
                               key=lambda x: total_profit_by_cat[x], reverse=True)

    fig = go.Figure()

    for cat in sorted_categories:
        values = [store_profit_pct[store['name']].get(cat, 0) for store in active_stores]

        fig.add_trace(go.Bar(
            name=cat,
            y=[s['name'] for s in active_stores],
            x=values,
            orientation='h',
            marker_color=get_category_color(cat),
            text=[f"{v:.1f}%" for v in values],
            textposition='inside',
            insidetextanchor='middle'
        ))

    fig.update_layout(**get_base_layout(
        barmode='stack',
        xaxis_title="Anteil am Bruttogewinn (%)",
        xaxis=dict(range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5),
        height=320,
        margin=dict(l=120, r=20, t=80, b=40)
    ))

    return fig


def create_price_segment_chart(price_segment_data, active_stores: list) -> go.Figure:
    """Erstellt Preissegment-Verteilung Chart

    Args:
        price_segment_data: DataFrame aus load_price_segment_data()
        active_stores: Liste der Store-Configs

    Returns:
        Plotly Figure
    """
    store_segment_pct = {}

    for store in active_stores:
        store_data = price_segment_data[price_segment_data['ID_STORE'] == store['id']]
        total_umsatz = store_data['Umsatz'].sum()
        segment_pct = {}
        for _, row in store_data.iterrows():
            pct = (row['Umsatz'] / total_umsatz * 100) if total_umsatz > 0 else 0
            segment_pct[row['Preissegment']] = pct
        store_segment_pct[store['name']] = segment_pct

    segment_order = ['Budget', 'Mid-Low', 'Mid-Up', 'Premium']
    segment_colors = {
        'Budget': '#8ecae6',
        'Mid-Low': '#58a4b0',
        'Mid-Up': '#3d5a80',
        'Premium': '#1d3557'
    }

    available_segments = [
        s for s in segment_order
        if any(s in store_segment_pct[store['name']] for store in active_stores)
    ]

    fig = go.Figure()

    for segment in available_segments:
        values = [store_segment_pct[store['name']].get(segment, 0) for store in active_stores]

        fig.add_trace(go.Bar(
            name=segment,
            y=[s['name'] for s in active_stores],
            x=values,
            orientation='h',
            marker_color=segment_colors.get(segment, '#666'),
            text=[f"{v:.1f}%" for v in values],
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color='white')
        ))

    fig.update_layout(**get_base_layout(
        barmode='stack',
        xaxis_title="Umsatzanteil (%)",
        xaxis=dict(range=[0, 100]),
        legend=get_legend_horizontal_centered(),
        height=250,
        margin=dict(l=120, r=20, t=40, b=40)
    ))

    return fig
