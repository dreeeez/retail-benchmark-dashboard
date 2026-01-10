"""
Benchmark Dashboard - Gruppe 18
Formatierungs-Funktionen
"""


def format_currency(value: float) -> str:
    """Formatiert Werte als Währung (Euro)

    Args:
        value: Zahlenwert

    Returns:
        Formatierter String (z.B. "1.5 Mio €", "500 Tsd €")
    """
    if value >= 1000000:
        return f"{value / 1000000:.1f} Mio €"
    elif value >= 1000:
        return f"{value / 1000:.0f} Tsd €"
    else:
        return f"{value:,.0f} €"


def format_percent(value: float, decimals: int = 1) -> str:
    """Formatiert Werte als Prozent

    Args:
        value: Zahlenwert (z.B. 15.5 für 15.5%)
        decimals: Anzahl Nachkommastellen

    Returns:
        Formatierter String (z.B. "15.5%")
    """
    return f"{value:.{decimals}f}%"


def format_number(value: float, decimals: int = 0) -> str:
    """Formatiert Zahlen mit Tausender-Trennzeichen

    Args:
        value: Zahlenwert
        decimals: Anzahl Nachkommastellen

    Returns:
        Formatierter String (z.B. "1.234.567")
    """
    formatted = f"{value:,.{decimals}f}"
    # Deutsche Formatierung: Punkt als Tausender, Komma als Dezimal
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
