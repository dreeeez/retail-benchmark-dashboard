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

SQL_RENT_REVENUE_M2 = """
SELECT
    s.ID_STORE,
    MAX(s.StoreM2) AS StoreM2,
    ISNULL(SUM(c.WertEUR), 0) AS MietkostenGesamt,
    SUM(s.RevenueEUR) AS UmsatzGesamt,
    CASE
        WHEN MAX(s.StoreM2) > 0 THEN SUM(s.RevenueEUR) / MAX(s.StoreM2)
        ELSE 0
    END AS UmsatzProM2
FROM dbo.V_LIST_MONTHLY_SALES s
LEFT JOIN dbo.V_LIST_MONTHLY_COSTS c
    ON s.ID_STORE = c.ID_STORE
    AND c.Kostenkategorie = 'Monthly Rent'
WHERE s.ID_STORE IN ({store_ids})
GROUP BY s.ID_STORE
"""

# Tab 4: Produktkategorien
SQL_SALES_AGG = """
SELECT * FROM list_views.V_LIST_G18_BENCHMARK_SALES_AGG
WHERE IdStore IN ({store_ids})
{month_filter}
"""

SQL_PRICE_SEGMENT = """
SELECT
    s.ID_STORE,
    so.STORE_LOCATION AS StoreName,
    ps.SEGMENT AS Preissegment,
    SUM(s.RevenueEUR) AS Umsatz,
    SUM(s.SalesAmount) AS Stueckzahl
FROM dbo.V_LIST_MONTHLY_SALES s
INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
INNER JOIN dbo.T_MATERIAL m ON s.ID_MATERIAL = m.ID_MAT
INNER JOIN dbo.T_PRICE_SEGMENT ps ON m.ID_SEGMENT = ps.ID_SEGMENT
WHERE s.ID_STORE IN ({store_ids})
{month_filter}
GROUP BY s.ID_STORE, so.STORE_LOCATION, ps.SEGMENT
ORDER BY s.ID_STORE, SUM(s.RevenueEUR) DESC
"""
