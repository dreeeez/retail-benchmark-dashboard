"""
Benchmark Dashboard - Gruppe 18
Hilfsfunktionen
"""


def format_currency(value):
    """Formatiert Werte als Währung (Euro)"""
    if value >= 1000000:
        return f"{value/1000000:.1f} Mio €"
    elif value >= 1000:
        return f"{value/1000:.0f} Tsd €"
    else:
        return f"{value:,.0f} €"


def format_percent(value):
    """Formatiert Werte als Prozent"""
    return f"{value:.1f}%"


def safe_sum(df, col_pattern):
    """Sichere Summe einer Spalte (case-insensitive Suche)"""
    col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
    return df[col].sum() if col else 0


def safe_mean(df, col_pattern):
    """Sicherer Durchschnitt einer Spalte (case-insensitive Suche)"""
    col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
    return df[col].mean() if col else 0


def get_trend_arrow(trend_val):
    """Gibt Trend-Pfeil und Farbe basierend auf Trend-Wert zurück"""
    if trend_val > 3:
        return "↗️", "#00ff88"
    elif trend_val < -3:
        return "↘️", "#ff4757"
    else:
        return "➡️", "#ffd93d"
