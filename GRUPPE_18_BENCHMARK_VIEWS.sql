-- =============================================
-- Benchmarking System - Gruppe 18
-- Alle Views in einer Datei
-- Rosenheim vs. Freiburg/Karlsruhe
-- =============================================

-- =============================================
-- LAYER 1: STANDARDISIERUNG
-- =============================================

-- View 1: list_views.V_LIST_G18_BENCHMARK_SALES_STD
-- Zweck: Standardisierung der Verkaufsdaten
-- - Monatsformat vereinheitlichen (YYYY-MM)
-- - Filialstammdaten anreichern
-- - Benchmark-Kategorien zuweisen
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_STD (
    IdCalmonthStd,
    IdStore,
    StoreName,
    IdMaterial,
    MaterialDescription,
    BenchmarkCategory,
    RevenueEur,
    GrossProfitEur,
    TransferCostEur,
    SalesPriceEur,
    Quantity
)
AS
SELECT
    -- Monatsformat standardisieren zu YYYY-MM
    FORMAT(s.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,

    s.ID_STORE AS IdStore,

    -- Filialname aus Stammdaten
    so.STORE_LOCATION AS StoreName,

    s.ID_MATERIAL AS IdMaterial,
    s.ProduktBeschreibung AS MaterialDescription,

    -- Benchmark-Kategorie zuweisen
    CASE
        WHEN s.ProduktBeschreibung LIKE '%E-Bike%' OR s.ProduktBeschreibung LIKE '%E-Trekking%' THEN 'E-Bike'
        WHEN s.ProduktBeschreibung LIKE '%MTB%' OR s.ProduktBeschreibung LIKE '%Mountain%' THEN 'MTB'
        WHEN s.ProduktBeschreibung LIKE '%City%' OR s.ProduktBeschreibung LIKE '%Trekking%' THEN 'City/Trekking'
        WHEN s.ProduktBeschreibung LIKE '%Kid%' OR s.ProduktBeschreibung LIKE '%Kinder%' THEN 'Kinder'
        ELSE 'Sonstige'
    END AS BenchmarkCategory,

    s.RevenueEUR AS RevenueEur,
    (s.RevenueEUR - s.TransferPriceEUR) AS GrossProfitEur,
    s.TransferPriceEUR AS TransferCostEur,
    s.SalesPriceEUR AS SalesPriceEur,
    s.SalesAmount AS Quantity

FROM dbo.V_LIST_MONTHLY_SALES s
INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
WHERE s.ID_STORE IN (3, 5, 14);  -- Nur Benchmark-Filialen
GO


-- =============================================
-- LAYER 2: AGGREGATION
-- =============================================

-- View 2: list_views.V_LIST_G18_BENCHMARK_SALES_AGG
-- Zweck: Aggregation der Verkaufsdaten je Monat, Filiale, Kategorie
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_AGG (
    IdCalmonthStd,
    IdStore,
    StoreName,
    BenchmarkCategory,
    TotalRevenueEur,
    TotalGrossProfitEur,
    TotalTransferCostEur,
    AvgSalesPriceEur,
    TotalQuantity
)
AS
SELECT
    IdCalmonthStd,
    IdStore,
    StoreName,
    BenchmarkCategory,

    SUM(RevenueEur) AS TotalRevenueEur,
    SUM(GrossProfitEur) AS TotalGrossProfitEur,
    SUM(TransferCostEur) AS TotalTransferCostEur,
    AVG(SalesPriceEur) AS AvgSalesPriceEur,
    SUM(Quantity) AS TotalQuantity

FROM list_views.V_LIST_G18_BENCHMARK_SALES_STD
GROUP BY IdCalmonthStd, IdStore, StoreName, BenchmarkCategory;
GO


-- View 3: list_views.V_LIST_G18_BENCHMARK_COSTS_AGG
-- Zweck: Aggregation der Kosten je Monat und Filiale
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_COSTS_AGG (
    IdCalmonthStd,
    IdStore,
    StoreName,
    TotalCostsEur,
    PersonnelCostsEur,
    OperatingCostsEur,
    AdditionalProcurementCostsEur
)
AS
SELECT
    FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
    c.ID_STORE AS IdStore,
    c.StoreName AS StoreName,

    -- Gesamtkosten
    SUM(c.WertEUR) AS TotalCostsEur,

    -- Personalkosten (Gehalt + Sozialkosten)
    SUM(CASE
        WHEN c.Kostenkategorie = 'Monthly Salary' OR c.Kostenkategorie = 'Monthly Social Costs'
        THEN c.WertEUR
        ELSE 0
    END) AS PersonnelCostsEur,

    -- Betriebskosten (Miete + Marketing + Kommission)
    SUM(CASE
        WHEN c.Kostenkategorie IN ('Monthly Rent', 'Marketing Campaign', 'Commission')
        THEN c.WertEUR
        ELSE 0
    END) AS OperatingCostsEur,

    -- Zusätzliche Beschaffungskosten
    SUM(CASE
        WHEN c.Kostenkategorie = 'Additional Procurement Costs'
        THEN c.WertEUR
        ELSE 0
    END) AS AdditionalProcurementCostsEur

FROM dbo.V_LIST_MONTHLY_COSTS c
WHERE c.ID_STORE IN (3, 5, 14)  -- Nur Benchmark-Filialen
GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE, c.StoreName;
GO


-- =============================================
-- LAYER 3: KPI-BERECHNUNG
-- =============================================

-- View 4: list_views.V_LIST_G18_BENCHMARK_KPI
-- Zweck: Zentrale KPI-View für Filialkennzahlen
-- KPIs: Bruttogewinn-Marge, Betriebskosten-Quote, Personalkosten-Anteil
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_KPI (
    IdCalmonthStd,
    IdStore,
    StoreName,
    TotalRevenueEur,
    TotalGrossProfitEur,
    TotalCostsEur,
    PersonnelCostsEur,
    OperatingCostsEur,
    NetProfitEur,
    GrossProfitMarginPct,
    OperatingCostRatioPct,
    PersonnelCostRatioPct,
    NetProfitMarginPct
)
AS
SELECT
    s.IdCalmonthStd,
    s.IdStore,
    s.StoreName,

    -- Summierte Basisgrößen (über alle Kategorien)
    SUM(s.TotalRevenueEur) AS TotalRevenueEur,
    SUM(s.TotalGrossProfitEur) AS TotalGrossProfitEur,
    c.TotalCostsEur,
    c.PersonnelCostsEur,
    c.OperatingCostsEur,

    -- Nettogewinn = Bruttogewinn - Gesamtkosten
    SUM(s.TotalGrossProfitEur) - c.TotalCostsEur AS NetProfitEur,

    -- KPI 1: Bruttogewinn-Marge (%) = Bruttogewinn / Umsatz * 100
    CASE
        WHEN SUM(s.TotalRevenueEur) > 0
        THEN (SUM(s.TotalGrossProfitEur) / SUM(s.TotalRevenueEur)) * 100
        ELSE NULL
    END AS GrossProfitMarginPct,

    -- KPI 2: Betriebskosten-Quote (%) = Betriebskosten / Umsatz * 100
    CASE
        WHEN SUM(s.TotalRevenueEur) > 0
        THEN (c.OperatingCostsEur / SUM(s.TotalRevenueEur)) * 100
        ELSE NULL
    END AS OperatingCostRatioPct,

    -- KPI 3: Personalkosten-Anteil (%) = Personalkosten / Gesamtkosten * 100
    CASE
        WHEN c.TotalCostsEur > 0
        THEN (c.PersonnelCostsEur / c.TotalCostsEur) * 100
        ELSE NULL
    END AS PersonnelCostRatioPct,

    -- Nettogewinn-Marge (%) = Nettogewinn / Umsatz * 100
    CASE
        WHEN SUM(s.TotalRevenueEur) > 0
        THEN ((SUM(s.TotalGrossProfitEur) - c.TotalCostsEur) / SUM(s.TotalRevenueEur)) * 100
        ELSE NULL
    END AS NetProfitMarginPct

FROM list_views.V_LIST_G18_BENCHMARK_SALES_AGG s
INNER JOIN list_views.V_LIST_G18_BENCHMARK_COSTS_AGG c
    ON s.IdCalmonthStd = c.IdCalmonthStd
    AND s.IdStore = c.IdStore
GROUP BY s.IdCalmonthStd, s.IdStore, s.StoreName,
         c.TotalCostsEur, c.PersonnelCostsEur, c.OperatingCostsEur;
GO


-- =============================================
-- LAYER 4: VERGLEICH (UNION)
-- =============================================

-- View 5: list_views.V_LIST_G18_BENCHMARK_STORE_COMPARISON
-- Zweck: Vergleich Freiburg/Karlsruhe (kombiniert) vs. Rosenheim
-- Feature: UNION für Side-by-Side Vergleich
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_STORE_COMPARISON (
    IdCalmonthStd,
    StoreGroup,
    TotalRevenueEur,
    TotalGrossProfitEur,
    TotalCostsEur,
    PersonnelCostsEur,
    OperatingCostsEur,
    NetProfitEur,
    GrossProfitMarginPct,
    OperatingCostRatioPct,
    PersonnelCostRatioPct,
    NetProfitMarginPct
)
AS
-- Rosenheim (ID_STORE = 14)
SELECT
    IdCalmonthStd,
    'Rosenheim' AS StoreGroup,
    TotalRevenueEur,
    TotalGrossProfitEur,
    TotalCostsEur,
    PersonnelCostsEur,
    OperatingCostsEur,
    NetProfitEur,
    GrossProfitMarginPct,
    OperatingCostRatioPct,
    PersonnelCostRatioPct,
    NetProfitMarginPct
FROM list_views.V_LIST_G18_BENCHMARK_KPI
WHERE IdStore = 14

UNION ALL

-- Freiburg/Karlsruhe kombiniert (ID_STORE = 3, 5)
SELECT
    IdCalmonthStd,
    'Freiburg/Karlsruhe' AS StoreGroup,
    SUM(TotalRevenueEur) AS TotalRevenueEur,
    SUM(TotalGrossProfitEur) AS TotalGrossProfitEur,
    SUM(TotalCostsEur) AS TotalCostsEur,
    SUM(PersonnelCostsEur) AS PersonnelCostsEur,
    SUM(OperatingCostsEur) AS OperatingCostsEur,
    SUM(NetProfitEur) AS NetProfitEur,

    -- Neu berechnen für kombinierte Gruppe
    CASE
        WHEN SUM(TotalRevenueEur) > 0
        THEN (SUM(TotalGrossProfitEur) / SUM(TotalRevenueEur)) * 100
        ELSE NULL
    END AS GrossProfitMarginPct,

    CASE
        WHEN SUM(TotalRevenueEur) > 0
        THEN (SUM(OperatingCostsEur) / SUM(TotalRevenueEur)) * 100
        ELSE NULL
    END AS OperatingCostRatioPct,

    CASE
        WHEN SUM(TotalCostsEur) > 0
        THEN (SUM(PersonnelCostsEur) / SUM(TotalCostsEur)) * 100
        ELSE NULL
    END AS PersonnelCostRatioPct,

    CASE
        WHEN SUM(TotalRevenueEur) > 0
        THEN (SUM(NetProfitEur) / SUM(TotalRevenueEur)) * 100
        ELSE NULL
    END AS NetProfitMarginPct

FROM list_views.V_LIST_G18_BENCHMARK_KPI
WHERE IdStore IN (3, 5)
GROUP BY IdCalmonthStd;
GO


-- =============================================
-- LAYER 5: EXPORT
-- =============================================

-- View 6: list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
-- Zweck: Export-View für Reporting und Dashboards
-- Format: Alle KPIs in einer Zeile pro Monat und Filialgruppe
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY (
    Monat,
    Filialgruppe,
    UmsatzEur,
    BruttogewinnEur,
    GesamtkostenEur,
    PersonalkostenEur,
    BetriebskostenEur,
    NettogewinnEur,
    BruttogewinnMargeProzent,
    BetriebskostenQuoteProzent,
    PersonalkostenAnteilProzent,
    NettogewinnMargeProzent
)
AS
SELECT
    IdCalmonthStd AS Monat,
    StoreGroup AS Filialgruppe,
    ROUND(TotalRevenueEur, 2) AS UmsatzEur,
    ROUND(TotalGrossProfitEur, 2) AS BruttogewinnEur,
    ROUND(TotalCostsEur, 2) AS GesamtkostenEur,
    ROUND(PersonnelCostsEur, 2) AS PersonalkostenEur,
    ROUND(OperatingCostsEur, 2) AS BetriebskostenEur,
    ROUND(NetProfitEur, 2) AS NettogewinnEur,
    ROUND(GrossProfitMarginPct, 2) AS BruttogewinnMargeProzent,
    ROUND(OperatingCostRatioPct, 2) AS BetriebskostenQuoteProzent,
    ROUND(PersonnelCostRatioPct, 2) AS PersonalkostenAnteilProzent,
    ROUND(NetProfitMarginPct, 2) AS NettogewinnMargeProzent
FROM list_views.V_LIST_G18_BENCHMARK_STORE_COMPARISON;
GO


-- =============================================
-- DEPLOYMENT ABGESCHLOSSEN
-- =============================================

PRINT '============================================='
PRINT 'Gruppe 18 - Benchmark Views erstellt!'
PRINT '============================================='
PRINT ''
PRINT '6 Views erfolgreich erstellt:'
PRINT '  1. list_views.V_LIST_G18_BENCHMARK_SALES_STD'
PRINT '  2. list_views.V_LIST_G18_BENCHMARK_SALES_AGG'
PRINT '  3. list_views.V_LIST_G18_BENCHMARK_COSTS_AGG'
PRINT '  4. list_views.V_LIST_G18_BENCHMARK_KPI'
PRINT '  5. list_views.V_LIST_G18_BENCHMARK_STORE_COMPARISON'
PRINT '  6. list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY'
PRINT ''
PRINT '============================================='
GO

-- Verifizierung
SELECT
    TABLE_SCHEMA AS [Schema],
    TABLE_NAME AS Viewname,
    'Gruppe 18' AS Projekt
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'VIEW'
  AND TABLE_SCHEMA = 'list_views'
  AND TABLE_NAME LIKE 'V_LIST_G18_BENCHMARK%'
ORDER BY TABLE_NAME;
GO
