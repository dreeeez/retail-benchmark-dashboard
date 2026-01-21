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
    """Erstellt Range-Bar Chart mit Dots für Bruttomarge nach Kategorie

    Management-taugliches Chart:
    - Range-Bar (Min-Max) pro Kategorie
    - Dots für jeden Standort
    - Sortiert nach Ø-Marge (absteigend)

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
    # Berechne Margen pro Store und Kategorie
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

    # Berechne Min, Max, Avg für jede Kategorie
    category_stats = {}
    for cat in sorted_categories:
        margins = all_margins[cat]
        category_stats[cat] = {
            'min': min(margins),
            'max': max(margins),
            'avg': sum(margins) / len(margins)
        }

    fig = go.Figure()

    # 1. Range-Bars (Min-Max)
    for cat in sorted_categories:
        stats = category_stats[cat]
        range_width = stats['max'] - stats['min']

        # Farbcodierung basierend auf Kategorie (gedämpft)
        base_color = get_category_color(cat)
        hex_color = base_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        fig.add_trace(go.Bar(
            name=cat,
            y=[cat],
            x=[range_width],
            base=stats['min'],
            orientation='h',
            marker=dict(
                color=f'rgba({r},{g},{b},0.15)',
                line=dict(color=f'rgba({r},{g},{b},0.4)', width=1)
            ),
            showlegend=False,
            hovertemplate=f'<b>{cat}</b><br>Min: {stats["min"]:.1f}%<br>Max: {stats["max"]:.1f}%<br>Ø: {stats["avg"]:.1f}%<extra></extra>'
        ))

    # 2. Dots für jeden Standort
    store_colors = {
        'Heidelberg': '#00d4ff',
        'Karlsruhe': '#7b2cbf',
        'Rosenheim': '#00ff88',
        'Freiburg': '#ff4757'
    }

    for store in active_stores:
        cat_margin = store_margins[store['name']]

        y_values = []
        x_values = []
        hover_texts = []

        for cat in sorted_categories:
            margin = cat_margin.get(cat, 0)
            y_values.append(cat)
            x_values.append(margin)
            hover_texts.append(f'<b>{store["name"]}</b><br>{cat}: {margin:.1f}%')

        fig.add_trace(go.Scatter(
            name=store['name'],
            y=y_values,
            x=x_values,
            mode='markers',
            marker=dict(
                size=10,
                color=store_colors.get(store['name'], '#999'),
                line=dict(color='rgba(255,255,255,0.4)', width=1)
            ),
            hovertemplate='%{text}<extra></extra>',
            text=hover_texts
        ))

    fig.update_layout(**get_base_layout(
        xaxis_title="Bruttomarge (%)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        height=max(350, len(sorted_categories) * 35),
        margin=dict(l=120, r=40, t=60, b=60),
        yaxis=dict(categoryorder='array', categoryarray=sorted_categories[::-1])
    ))

    return fig


def create_profit_distribution_chart(df_filtered, active_stores: list,
                                      cat_col: str, profit_col: str,
                                      filter_by_store) -> go.Figure:
    """Erstellt 100% gestapeltes horizontales Balkendiagramm für Bruttogewinn-Anteil

    Management-taugliches Chart:
    - Ein Balken pro Standort
    - Segmente = Produktkategorien
    - Nur Top-1 und Top-2 beschriftet, Rest per Tooltip
    - Sortierung nach Bruttogewinn-Anteil (absteigend)
    - Transparente Farben passend zum Bruttomarge-Chart

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
    store_profit_abs = {}
    total_profit_by_cat = {}

    for store in active_stores:
        store_cat_data = filter_by_store(df_filtered, store)
        cat_profit = store_cat_data.groupby(cat_col)[profit_col].sum()
        total_profit = cat_profit.sum()
        cat_pct = (cat_profit / total_profit * 100) if total_profit > 0 else cat_profit * 0
        store_profit_pct[store['name']] = cat_pct
        store_profit_abs[store['name']] = cat_profit

        for cat in cat_pct.index:
            if cat not in total_profit_by_cat:
                total_profit_by_cat[cat] = 0
            total_profit_by_cat[cat] += cat_pct[cat]

    # Sortiere Kategorien nach Gesamtgewinn-Anteil
    sorted_categories = sorted(total_profit_by_cat.keys(),
                               key=lambda x: total_profit_by_cat[x], reverse=True)

    fig = go.Figure()

    for i, cat in enumerate(sorted_categories):
        values = []
        texts = []
        hover_texts = []

        # Transparente Farbe wie beim Bruttomarge-Chart
        base_color = get_category_color(cat)
        hex_color = base_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        transparent_color = f'rgba({r},{g},{b},0.7)'  # Leicht transparent für modernen Look
        border_color = f'rgba({r},{g},{b},0.9)'

        for store in active_stores:
            pct = store_profit_pct[store['name']].get(cat, 0)
            abs_profit = store_profit_abs[store['name']].get(cat, 0)
            values.append(pct)

            # Alle Kategorien mit Prozentangabe beschriften (wenn genug Platz)
            if pct >= 2:  # Nur anzeigen wenn >= 2% für Lesbarkeit
                texts.append(f"{pct:.1f}%")
            else:
                texts.append("")

            hover_texts.append(f'<b>{cat}</b><br>{store["name"]}: {pct:.1f}% ({abs_profit:,.0f} €)')

        fig.add_trace(go.Bar(
            name=cat,
            y=[s['name'] for s in active_stores],
            x=values,
            orientation='h',
            marker=dict(
                color=transparent_color,
                line=dict(color=border_color, width=1)
            ),
            text=texts,
            textposition='inside',
            textfont=dict(size=11, color='white'),
            insidetextanchor='middle',
            hovertemplate='%{text}<extra></extra>',
            hovertext=hover_texts
        ))

    fig.update_layout(**get_base_layout(
        barmode='stack',
        xaxis_title="Anteil am Bruttogewinn (%)",
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        height=300,
        margin=dict(l=120, r=20, t=60, b=40)
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
        store_data = price_segment_data[price_segment_data['IdStore'] == store['id']]
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

        # Transparente Farbe wie bei den anderen Charts
        base_color = segment_colors.get(segment, '#666')
        hex_color = base_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        transparent_color = f'rgba({r},{g},{b},0.7)'
        border_color = f'rgba({r},{g},{b},0.9)'

        fig.add_trace(go.Bar(
            name=segment,
            y=[s['name'] for s in active_stores],
            x=values,
            orientation='h',
            marker=dict(
                color=transparent_color,
                line=dict(color=border_color, width=1)
            ),
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
