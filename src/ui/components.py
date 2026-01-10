"""
Benchmark Dashboard - Gruppe 18
UI Components

Wiederverwendbare HTML-Komponenten für das Dashboard.
"""

from src.utils.formatting import format_currency


def render_kpi_card(title: str, value: str, color: str, comparison: float = None) -> str:
    """Rendert eine einfache KPI-Karte

    Args:
        title: Titel der Karte
        value: Formatierter Wert
        color: Farbe für den Wert
        comparison: Optionaler Vergleichswert (%)

    Returns:
        HTML-String
    """
    comp_html = ""
    if comparison is not None:
        if comparison > 0:
            comp_class = "kpi-comparison-positive"
            comp_text = f"+{comparison:.1f}%"
        elif comparison < 0:
            comp_class = "kpi-comparison-negative"
            comp_text = f"{comparison:.1f}%"
        else:
            comp_class = "kpi-comparison-neutral"
            comp_text = f"{comparison:.1f}%"
        comp_html = f'<div class="{comp_class}">{comp_text}</div>'

    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div style="font-size: 1.5em; font-weight: bold; color: {color}; height: 50px; line-height: 50px;">{value}</div>
        {comp_html}
    </div>
    """


def chart_header(title: str, tooltip_text: str) -> str:
    """Rendert einen Chart-Titel mit Info-Tooltip

    Args:
        title: Chart-Titel
        tooltip_text: Erklärungstext (HTML erlaubt)

    Returns:
        HTML-String
    """
    return f"""
    <div class="chart-header">
        <h3 class="chart-title">{title}</h3>
        <div class="info-tooltip">
            i
            <span class="tooltip-text">{tooltip_text}</span>
        </div>
    </div>
    """


def render_store_kpi_card(store: dict, kpis: dict) -> str:
    """Rendert eine Store-KPI-Karte mit Umsatz, Bruttogewinn, Nettogewinn

    Args:
        store: Store-Config aus STORES
        kpis: KPI-Dict aus get_kpis_from_view()

    Returns:
        HTML-String
    """
    return f"""
    <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                border-radius: 15px; padding: 20px;">
        <div style="font-size: 1.2em; font-weight: bold; color: {store['color']}; text-align: center; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
            {store['name']}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
            <div style="text-align: center;">
                <div style="color: #aaa; font-size: 0.75em; text-transform: uppercase;">Umsatz</div>
                <div style="color: white; font-size: 1.2em; font-weight: bold;">{format_currency(kpis['umsatz'])}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #aaa; font-size: 0.75em; text-transform: uppercase;">Bruttogewinn</div>
                <div style="color: #ffd93d; font-size: 1.2em; font-weight: bold;">{format_currency(kpis['bruttogewinn'])}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #aaa; font-size: 0.75em; text-transform: uppercase;">Operativer Gewinn</div>
                <div style="color: #00ff88; font-size: 1.2em; font-weight: bold;">{format_currency(kpis['nettogewinn'])}</div>
            </div>
        </div>
    </div>
    """


def render_cost_card(store: dict, kosten: float) -> str:
    """Rendert eine Kosten-Karte

    Args:
        store: Store-Config
        kosten: Gesamtkosten

    Returns:
        HTML-String
    """
    return f"""
    <div class="hover-card" style="background: {store['color_bg']}; border: 1px solid {store['color']};
                border-radius: 15px; padding: 20px; text-align: center;">
        <div style="font-size: 0.9em; color: #aaa;">{store['name']}</div>
        <div style="font-size: 2em; font-weight: bold; color: {store['color']};">{format_currency(kosten)}</div>
        <div style="font-size: 0.7em; color: #aaa; margin-top: 5px;">Gesamtkosten</div>
    </div>
    """


def render_html_table(headers: list, rows: list) -> str:
    """Rendert eine HTML-Tabelle

    Args:
        headers: Liste von Header-Strings
        rows: Liste von Row-Dicts mit 'cells' (Liste) und optional 'style'

    Returns:
        HTML-String
    """
    table_html = '<table style="width: 100%; border-collapse: collapse; font-size: 1.1em;">'
    table_html += '<thead><tr style="background: rgba(255,255,255,0.1); color: #aaa;">'

    for header in headers:
        table_html += f'<th style="padding: 12px; text-align: center;">{header}</th>'

    table_html += '</tr></thead><tbody>'

    for row in rows:
        style = row.get('style', '')
        table_html += f'<tr style="{style}">'
        for cell in row['cells']:
            table_html += f'<td style="padding: 15px; text-align: center; color: white;">{cell}</td>'
        table_html += '</tr>'

    table_html += '</tbody></table>'
    return table_html
