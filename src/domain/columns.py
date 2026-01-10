"""
Benchmark Dashboard - Gruppe 18
Spalten-Definitionen und Finder

Zentrale Definition aller erwarteten Spalten und
Helper-Funktion zum Finden von Spalten (case-insensitive).
"""

from typing import Optional, List

# =============================================================================
# SPALTEN-PATTERNS
# =============================================================================
# Definiert wie Spalten in verschiedenen Views heißen können

COLUMN_PATTERNS = {
    # Identifikatoren
    'month': ['monat', 'month', 'idcalmonthstd'],
    'store': ['filial', 'store', 'gruppe', 'storename'],
    'store_id': ['idstore', 'id_store'],
    'category': ['category', 'kategorie', 'productcategory'],

    # Finanz-Metriken
    'revenue': ['umsatz', 'revenue', 'umsatzeur', 'revenueeur'],
    'gross_profit': ['bruttogewinn', 'grossprofit', 'grossprofiteur'],
    'net_profit': ['nettogewinn', 'netprofit', 'netprofiteur', 'ebit'],
    'quantity': ['quantity', 'menge', 'stueckzahl', 'salesamount'],
    'price': ['price', 'preis', 'avgprice'],

    # Kosten
    'costs_total': ['gesamtkosten', 'totalcosts', 'totalcostseur'],
    'hr_costs': ['humanresources', 'personalkosten'],
    'facility_costs': ['facilitymanagement', 'betriebskosten', 'miete'],
    'logistics_costs': ['logistics', 'logistik', 'beschaffungskosten'],
    'marketing_costs': ['marketing', 'marketingkosten', 'marketingeur'],
}


def find_column(df, pattern_key: str) -> Optional[str]:
    """Findet Spaltenname im DataFrame basierend auf Pattern

    Args:
        df: DataFrame
        pattern_key: Key aus COLUMN_PATTERNS (z.B. 'revenue', 'month')

    Returns:
        Gefundener Spaltenname oder None
    """
    patterns = COLUMN_PATTERNS.get(pattern_key, [pattern_key])

    # Falls pattern_key nicht in COLUMN_PATTERNS, als direktes Pattern verwenden
    if isinstance(patterns, str):
        patterns = [patterns]

    for col in df.columns:
        col_lower = col.lower()
        for pattern in patterns:
            if pattern in col_lower:
                return col
    return None


def find_columns(df, pattern_keys: List[str]) -> dict:
    """Findet mehrere Spalten auf einmal

    Args:
        df: DataFrame
        pattern_keys: Liste von Keys aus COLUMN_PATTERNS

    Returns:
        Dict mit {pattern_key: column_name}
    """
    return {key: find_column(df, key) for key in pattern_keys}
