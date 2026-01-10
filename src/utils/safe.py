"""
Benchmark Dashboard - Gruppe 18
Sichere Aggregations-Funktionen
"""

import pandas as pd
from typing import Tuple


def safe_sum(df: pd.DataFrame, col_pattern: str) -> float:
    """Sichere Summe einer Spalte (case-insensitive Suche)

    Args:
        df: DataFrame
        col_pattern: Pattern zum Suchen der Spalte

    Returns:
        Summe oder 0 falls Spalte nicht gefunden
    """
    col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
    return df[col].sum() if col else 0


def safe_mean(df: pd.DataFrame, col_pattern: str) -> float:
    """Sicherer Durchschnitt einer Spalte (case-insensitive Suche)

    Args:
        df: DataFrame
        col_pattern: Pattern zum Suchen der Spalte

    Returns:
        Durchschnitt oder 0 falls Spalte nicht gefunden
    """
    col = next((c for c in df.columns if col_pattern.lower() in c.lower()), None)
    return df[col].mean() if col else 0


def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Sichere Division mit Default bei Division durch 0

    Args:
        numerator: Zähler
        denominator: Nenner
        default: Rückgabewert bei Division durch 0

    Returns:
        Ergebnis oder default
    """
    return numerator / denominator if denominator != 0 else default


def get_trend_arrow(trend_val: float) -> Tuple[str, str]:
    """Gibt Trend-Pfeil und Farbe basierend auf Trend-Wert zurück

    Args:
        trend_val: Trend-Wert (positiv = Wachstum)

    Returns:
        Tuple (Pfeil-Emoji, Farbe)
    """
    if trend_val > 3:
        return "↗️", "#00ff88"
    elif trend_val < -3:
        return "↘️", "#ff4757"
    else:
        return "➡️", "#ffd93d"
