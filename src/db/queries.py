"""
Benchmark Dashboard - Gruppe 18
SQL Queries

Alle SQL-Queries zentral definiert.
Store-IDs werden dynamisch über {store_ids} eingefügt.
Monatsfilter werden dynamisch über {month_filter} eingefügt.
"""


def build_month_filter(month: str, month_column: str = 'IdCalmonthStd') -> str:
    """Baut SQL WHERE-Klausel für Monatsfilter

    Args:
        month: 'all' für alle Monate, sonst z.B. '2024-01'
        month_column: Name der Monatsspalte in der View

    Returns:
        Leerer String oder "AND {month_column} = '{month}'"
    """
    if month == 'all':
        return ''
    return f"AND {month_column} = '{month}'"


# =============================================================================
# VIEW-BASIERTE QUERIES
# =============================================================================

# Tab 1: Finanzperformance
SQL_EXPORT_MONTHLY = """
SELECT * FROM list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
WHERE IdStore IN ({store_ids})
{month_filter}
"""

SQL_KPI = """
SELECT * FROM list_views.V_LIST_G18_BENCHMARK_KPI
WHERE IdStore IN ({store_ids})
{month_filter}
"""

# Tab 2: Marketing
SQL_MARKETING_KPI = """
SELECT * FROM list_views.V_LIST_G18_MARKETING_KPI_MONTHLY
WHERE IdStore IN ({store_ids})
{month_filter}
"""

SQL_MARKETING_BY_CAMPAIGN = """
SELECT * FROM list_views.V_LIST_G18_MARKETING_BY_CAMPAIGN
WHERE IdStore IN ({store_ids})
"""

# Tab 3: Kostenanalyse
SQL_COSTS_AGG = """
SELECT * FROM list_views.V_LIST_G18_BENCHMARK_COSTS_AGG
WHERE IdStore IN ({store_ids})
{month_filter}
"""

SQL_COSTS_DETAIL = """
SELECT * FROM list_views.V_LIST_G18_BENCHMARK_COSTS_DETAIL
WHERE IdStore IN ({store_ids})
{month_filter}
"""

SQL_STORE_DETAILS = """
SELECT * FROM list_views.V_LIST_G18_STORE_DETAILS
WHERE IdStore IN ({store_ids})
{month_filter}
"""

# Tab 4: Produktkategorien
SQL_SALES_AGG = """
SELECT * FROM list_views.V_LIST_G18_BENCHMARK_SALES_AGG
WHERE IdStore IN ({store_ids})
{month_filter}
"""

SQL_PRICE_SEGMENT = """
SELECT
    IdStore,
    StoreName,
    Preissegment,
    SUM(RevenueEur) AS Umsatz,
    SUM(Quantity) AS Stueckzahl
FROM list_views.V_LIST_G18_BENCHMARK_SALES_DETAIL
WHERE IdStore IN ({store_ids})
{month_filter}
GROUP BY IdStore, StoreName, Preissegment
ORDER BY IdStore, SUM(RevenueEur) DESC
"""
