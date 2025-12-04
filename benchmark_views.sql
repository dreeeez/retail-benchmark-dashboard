-- ============================================================================
-- BENCHMARK VIEWS für Filialvergleich Rosenheim (ID=14) vs. Freiburg (ID=5)
-- Phase 4 - Systemkonzept Benchmarking
-- Gruppe 18: Marco, Harun, Duy
--
-- Namenskonventionen gemäß Vorgaben Datenbankentwicklung:
-- - Schema: list_views für Anzeige-Views
-- - View-Namen: V_LIST_ (Anzeige), GROSSBUCHSTABEN, Snake_Case
-- - Spaltennamen in Views: CamelCase (z.B. RevenueEur)
-- - Tabellen-Spaltennamen: GROSSBUCHSTABEN
-- ============================================================================

-- ============================================================================
-- 4.1.1 V_LIST_G18_BENCHMARK_SALES_STD - Standardisierungs- und Bereinigungs-View
-- Vereinheitlicht Monatsformat, reichert Filialstammdaten an,
-- weist Artikel Benchmark-Kategorien zu
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_STD AS
SELECT
    s.ID_STORE                                          AS IdStore,
    s.ID_CALMONTH                                       AS IdCalmonth,
    FORMAT(s.ID_CALMONTH, 'yyyy-MM')                    AS IdCalmonthStd,
    YEAR(s.ID_CALMONTH)                                 AS Jahr,
    MONTH(s.ID_CALMONTH)                                AS Monat,
    so.STORE_LOCATION                                   AS StoreName,
    loc.LOC_SIZE_M2                                     AS StoreM2,
    s.ID_MATERIAL                                       AS IdMaterial,
    m.MAT_NR                                            AS MatNr,
    m.MAT_DESCR                                         AS MatDescr,
    s.ID_CATEGORY                                       AS IdCategory,
    pc.CATEGORY                                         AS Category,
    pc.PRODUCT_LINE                                     AS ProductLine,
    CASE
        WHEN pc.PRODUCT_LINE = 'E-Bike' THEN 'E-Bike'
        WHEN pc.CATEGORY = 'Mountain Bikes' THEN 'MTB'
        WHEN pc.CATEGORY IN ('City Bikes', 'Trekking Bikes') THEN 'City/Trekking'
        WHEN pc.CATEGORY = 'Kid Bikes' THEN 'Kinder'
        WHEN pc.CATEGORY = 'Race Bikes' THEN 'Rennrad'
        ELSE 'Sonstige'
    END                                                 AS BenchmarkCategory,
    s.ID_EMPLOYEE                                       AS IdEmployee,
    s.ID_CAMPAIGN                                       AS IdCampaign,
    s.SALES_AMOUNT                                      AS SalesAmount,
    s.TRANSFER_PRICE_EUR                                AS TransferPriceEur,
    s.SALES_PRICE_EUR                                   AS SalesPriceEur,
    s.DISCOUNT_PCT                                      AS DiscountPct,
    s.DISCOUNT_IN_EUR                                   AS DiscountEur,
    s.REVENUE                                           AS RevenueEur,
    s.GROSS_PROFIT_EUR                                  AS GrossProfitEur,
    CASE
        WHEN s.SALES_AMOUNT > 0 THEN s.REVENUE / s.SALES_AMOUNT
        ELSE NULL
    END                                                 AS AvgSalesPriceEur
FROM dbo.T_ETL_MONTHLY_SALES s
INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
LEFT JOIN dbo.T_LOCATION loc ON s.ID_STORE = loc.ID_STORE
LEFT JOIN dbo.T_MATERIAL m ON s.ID_MATERIAL = m.ID_MAT
LEFT JOIN dbo.T_PRODUCT_CATEGORY pc ON s.ID_CATEGORY = pc.ID_CATEGORY
WHERE s.ID_STORE IN (5, 14);
GO

-- ============================================================================
-- 4.1.2 V_LIST_G18_BENCHMARK_SALES_ERRORS - Fehler-View (optional)
-- Zeigt Datensätze mit Umsatz <= 0 oder negativem Bruttogewinn
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_ERRORS AS
SELECT
    IdStore,
    IdCalmonth,
    IdCalmonthStd,
    StoreName,
    IdMaterial,
    MatNr,
    MatDescr,
    BenchmarkCategory,
    SalesAmount,
    RevenueEur,
    GrossProfitEur,
    CASE
        WHEN RevenueEur <= 0 THEN 'Umsatz <= 0'
        WHEN GrossProfitEur < 0 THEN 'Negativer Bruttogewinn'
        ELSE 'Unbekannter Fehler'
    END                                                 AS ErrorType
FROM list_views.V_LIST_G18_BENCHMARK_SALES_STD
WHERE RevenueEur <= 0 OR GrossProfitEur < 0;
GO

-- ============================================================================
-- 4.2.1 V_LIST_G18_BENCHMARK_SALES_AGG - Aggregation der Verkaufsdaten
-- Aggregation je Monat, Filiale, Kategorie
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_AGG AS
SELECT
    IdStore,
    IdCalmonth,
    IdCalmonthStd,
    Jahr,
    Monat,
    StoreName,
    StoreM2,
    BenchmarkCategory,
    SUM(SalesAmount)                                    AS TotalSalesAmount,
    SUM(RevenueEur)                                     AS RevenueEur,
    SUM(GrossProfitEur)                                 AS GrossProfitEur,
    SUM(TransferPriceEur * SalesAmount)                 AS TransferCostEur,
    SUM(DiscountEur)                                    AS TotalDiscountEur,
    CASE
        WHEN SUM(SalesAmount) > 0 THEN SUM(RevenueEur) / SUM(SalesAmount)
        ELSE NULL
    END                                                 AS AvgSalesPriceEur,
    COUNT(*)                                            AS TransactionCount
FROM list_views.V_LIST_G18_BENCHMARK_SALES_STD
GROUP BY
    IdStore,
    IdCalmonth,
    IdCalmonthStd,
    Jahr,
    Monat,
    StoreName,
    StoreM2,
    BenchmarkCategory;
GO

-- ============================================================================
-- 4.2.2 V_LIST_G18_BENCHMARK_COSTS_AGG - Aggregation der Kosten
-- Aggregation je Monat, Filiale und Kostenkategorie
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_COSTS_AGG AS
SELECT
    c.ID_STORE                                          AS IdStore,
    c.ID_CALMONTH                                       AS IdCalmonth,
    FORMAT(c.ID_CALMONTH, 'yyyy-MM')                    AS IdCalmonthStd,
    YEAR(c.ID_CALMONTH)                                 AS Jahr,
    MONTH(c.ID_CALMONTH)                                AS Monat,
    so.STORE_LOCATION                                   AS StoreName,
    SUM(CASE WHEN cr.ID_COST_CATEGORY IN (1, 2, 11) THEN c.VALUE ELSE 0 END)
                                                        AS PersonnelCostsEur,
    SUM(CASE WHEN cr.ID_COST_CATEGORY = 3 THEN c.VALUE ELSE 0 END)
                                                        AS RentCostsEur,
    SUM(CASE WHEN cr.ID_COST_CATEGORY = 10 THEN c.VALUE ELSE 0 END)
                                                        AS MarketingCostsEur,
    SUM(CASE WHEN cr.ID_COST_CATEGORY = 12 THEN c.VALUE ELSE 0 END)
                                                        AS AdditionalProcurementEur,
    SUM(CASE WHEN cr.ID_COST_CATEGORY = 4 THEN c.VALUE ELSE 0 END)
                                                        AS TransferCostsEur,
    SUM(CASE WHEN cr.ID_COST_CATEGORY IN (3, 10) THEN c.VALUE ELSE 0 END)
                                                        AS OperatingCostsEur,
    SUM(c.VALUE)                                        AS TotalCostsEur
FROM dbo.T_ETL_MONTHLY_COSTS c
INNER JOIN dbo.T_COST_RECORD cr
    ON c.ID_COST_RECORD = cr.ID_COST_RECORD
    AND c.ID_STORE = cr.ID_STORE
    AND c.ID_GAME = cr.ID_GAME
INNER JOIN dbo.T_SALESORG so ON c.ID_STORE = so.SALESORG_ID
WHERE c.ID_STORE IN (5, 14)
GROUP BY
    c.ID_STORE,
    c.ID_CALMONTH,
    so.STORE_LOCATION;
GO

-- ============================================================================
-- 4.2.3 V_LIST_G18_BENCHMARK_HEADCOUNT - Mitarbeiteranzahl je Filiale
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_HEADCOUNT AS
SELECT
    e.ID_SALESORG                                       AS IdStore,
    so.STORE_LOCATION                                   AS StoreName,
    COUNT(DISTINCT e.ID_EMP)                            AS EmployeeCount,
    SUM(e.EMP_SALARY_OFFERED)                           AS TotalSalaryOffered
FROM dbo.T_EMPLOYEE e
INNER JOIN dbo.T_SALESORG so ON e.ID_SALESORG = so.SALESORG_ID
WHERE e.ID_SALESORG IN (5, 14)
  AND e.DELETE_YN = 0
GROUP BY
    e.ID_SALESORG,
    so.STORE_LOCATION;
GO

-- ============================================================================
-- 4.3.1 V_LIST_G18_BENCHMARK_KPI - Zentrale KPI-View für Filialkennzahlen
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_KPI AS
SELECT
    s.IdStore,
    s.IdCalmonth,
    s.IdCalmonthStd,
    s.Jahr,
    s.Monat,
    s.StoreName,
    s.StoreM2,
    s.BenchmarkCategory,

    -- Basisgroessen Umsatz
    s.TotalSalesAmount,
    s.RevenueEur,
    s.GrossProfitEur,
    s.TransferCostEur,
    s.TotalDiscountEur,
    s.AvgSalesPriceEur,

    -- Kosten
    c.PersonnelCostsEur,
    c.RentCostsEur,
    c.MarketingCostsEur,
    c.AdditionalProcurementEur,
    c.OperatingCostsEur,
    c.TotalCostsEur,

    -- Gesamtkosten inkl. Wareneinsatz
    ISNULL(s.TransferCostEur, 0) + ISNULL(c.OperatingCostsEur, 0) +
    ISNULL(c.PersonnelCostsEur, 0) + ISNULL(c.AdditionalProcurementEur, 0)
                                                        AS TotalCostsFullEur,

    -- Nettogewinn
    s.GrossProfitEur - ISNULL(c.OperatingCostsEur, 0) -
    ISNULL(c.PersonnelCostsEur, 0) - ISNULL(c.AdditionalProcurementEur, 0)
                                                        AS NetProfitEur,

    -- Mitarbeiter
    h.EmployeeCount,

    -- Bruttogewinn-Marge (%)
    CASE
        WHEN s.RevenueEur > 0 THEN (s.GrossProfitEur / s.RevenueEur) * 100
        ELSE NULL
    END                                                 AS GrossProfitMarginPct,

    -- Nettogewinn-Marge (%)
    CASE
        WHEN s.RevenueEur > 0 THEN
            ((s.GrossProfitEur - ISNULL(c.OperatingCostsEur, 0) -
              ISNULL(c.PersonnelCostsEur, 0) - ISNULL(c.AdditionalProcurementEur, 0))
             / s.RevenueEur) * 100
        ELSE NULL
    END                                                 AS NetProfitMarginPct,

    -- Betriebskosten-Quote (%)
    CASE
        WHEN s.RevenueEur > 0 THEN (ISNULL(c.OperatingCostsEur, 0) / s.RevenueEur) * 100
        ELSE NULL
    END                                                 AS OperatingCostRatioPct,

    -- Personalkosten-Anteil (%)
    CASE
        WHEN s.RevenueEur > 0 THEN (ISNULL(c.PersonnelCostsEur, 0) / s.RevenueEur) * 100
        ELSE NULL
    END                                                 AS PersonnelCostRatioPct,

    -- Umsatz pro Mitarbeiter
    CASE
        WHEN ISNULL(h.EmployeeCount, 0) > 0 THEN s.RevenueEur / h.EmployeeCount
        ELSE NULL
    END                                                 AS RevenuePerEmployee,

    -- Umsatz pro Quadratmeter
    CASE
        WHEN ISNULL(s.StoreM2, 0) > 0 THEN s.RevenueEur / s.StoreM2
        ELSE NULL
    END                                                 AS RevenuePerM2,

    -- Brutto-Marketingbeitrag
    s.RevenueEur - ISNULL(c.MarketingCostsEur, 0)       AS GrossMarketingContribution

FROM list_views.V_LIST_G18_BENCHMARK_SALES_AGG s
LEFT JOIN list_views.V_LIST_G18_BENCHMARK_COSTS_AGG c
    ON s.IdStore = c.IdStore
    AND s.IdCalmonth = c.IdCalmonth
LEFT JOIN list_views.V_LIST_G18_BENCHMARK_HEADCOUNT h
    ON s.IdStore = h.IdStore;
GO

-- ============================================================================
-- 4.4.1 V_LIST_G18_BENCHMARK_STORE_COMPARISON - Filialvergleich
-- Vergleich Freiburg (ID=5) vs. Rosenheim (ID=14) je Monat und Kategorie
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_STORE_COMPARISON AS
SELECT
    COALESCE(f.IdCalmonth, r.IdCalmonth)                AS IdCalmonth,
    COALESCE(f.IdCalmonthStd, r.IdCalmonthStd)          AS IdCalmonthStd,
    COALESCE(f.Jahr, r.Jahr)                            AS Jahr,
    COALESCE(f.Monat, r.Monat)                          AS Monat,
    COALESCE(f.BenchmarkCategory, r.BenchmarkCategory)  AS BenchmarkCategory,

    -- Freiburg Kennzahlen
    f.RevenueEur                                        AS FreiburgRevenueEur,
    f.GrossProfitEur                                    AS FreiburgGrossProfitEur,
    f.TotalSalesAmount                                  AS FreiburgSalesAmount,
    f.GrossProfitMarginPct                              AS FreiburgMarginPct,
    f.RevenuePerEmployee                                AS FreiburgRevPerEmployee,
    f.RevenuePerM2                                      AS FreiburgRevPerM2,

    -- Rosenheim Kennzahlen
    r.RevenueEur                                        AS RosenheimRevenueEur,
    r.GrossProfitEur                                    AS RosenheimGrossProfitEur,
    r.TotalSalesAmount                                  AS RosenheimSalesAmount,
    r.GrossProfitMarginPct                              AS RosenheimMarginPct,
    r.RevenuePerEmployee                                AS RosenheimRevPerEmployee,
    r.RevenuePerM2                                      AS RosenheimRevPerM2,

    -- Differenzen (Rosenheim - Freiburg)
    ISNULL(r.RevenueEur, 0) - ISNULL(f.RevenueEur, 0)   AS DiffRevenueEur,
    ISNULL(r.GrossProfitEur, 0) - ISNULL(f.GrossProfitEur, 0)
                                                        AS DiffGrossProfitEur,
    ISNULL(r.TotalSalesAmount, 0) - ISNULL(f.TotalSalesAmount, 0)
                                                        AS DiffSalesAmount,
    ISNULL(r.GrossProfitMarginPct, 0) - ISNULL(f.GrossProfitMarginPct, 0)
                                                        AS DiffMarginPct,

    -- Prozentuale Abweichung Umsatz
    CASE
        WHEN ISNULL(f.RevenueEur, 0) > 0
        THEN ((ISNULL(r.RevenueEur, 0) - f.RevenueEur) / f.RevenueEur) * 100
        ELSE NULL
    END                                                 AS DiffRevenuePct

FROM (SELECT * FROM list_views.V_LIST_G18_BENCHMARK_KPI WHERE IdStore = 5) f
FULL OUTER JOIN (SELECT * FROM list_views.V_LIST_G18_BENCHMARK_KPI WHERE IdStore = 14) r
    ON f.IdCalmonth = r.IdCalmonth
    AND f.BenchmarkCategory = r.BenchmarkCategory;
GO

-- ============================================================================
-- 4.5.1 V_LIST_G18_BENCHMARK_EXPORT_MONTHLY - Export-View für Reporting
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY AS
SELECT
    IdStore,
    IdCalmonth,
    IdCalmonthStd,
    Jahr,
    Monat,
    StoreName,
    StoreM2,
    BenchmarkCategory,
    TotalSalesAmount,
    RevenueEur,
    GrossProfitEur,
    TransferCostEur,
    TotalDiscountEur,
    AvgSalesPriceEur,
    PersonnelCostsEur,
    RentCostsEur,
    MarketingCostsEur,
    AdditionalProcurementEur,
    OperatingCostsEur,
    TotalCostsEur,
    TotalCostsFullEur,
    NetProfitEur,
    EmployeeCount,
    GrossProfitMarginPct,
    NetProfitMarginPct,
    OperatingCostRatioPct,
    PersonnelCostRatioPct,
    RevenuePerEmployee,
    RevenuePerM2,
    GrossMarketingContribution,
    GETDATE()                                           AS ExportTimestamp
FROM list_views.V_LIST_G18_BENCHMARK_KPI;
GO

-- ============================================================================
-- V_LIST_G18_BENCHMARK_MONTHLY_TOTALS - Aggregation ohne Kategorie
-- ============================================================================
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_MONTHLY_TOTALS AS
SELECT
    IdStore,
    IdCalmonth,
    IdCalmonthStd,
    Jahr,
    Monat,
    StoreName,
    MAX(StoreM2)                                        AS StoreM2,
    SUM(TotalSalesAmount)                               AS TotalSalesAmount,
    SUM(RevenueEur)                                     AS RevenueEur,
    SUM(GrossProfitEur)                                 AS GrossProfitEur,
    SUM(TransferCostEur)                                AS TransferCostEur,
    SUM(TotalDiscountEur)                               AS TotalDiscountEur,
    MAX(PersonnelCostsEur)                              AS PersonnelCostsEur,
    MAX(OperatingCostsEur)                              AS OperatingCostsEur,
    MAX(TotalCostsEur)                                  AS TotalCostsEur,
    MAX(EmployeeCount)                                  AS EmployeeCount,
    CASE
        WHEN SUM(RevenueEur) > 0 THEN (SUM(GrossProfitEur) / SUM(RevenueEur)) * 100
        ELSE NULL
    END                                                 AS GrossProfitMarginPct,
    CASE
        WHEN MAX(EmployeeCount) > 0 THEN SUM(RevenueEur) / MAX(EmployeeCount)
        ELSE NULL
    END                                                 AS RevenuePerEmployee,
    CASE
        WHEN MAX(StoreM2) > 0 THEN SUM(RevenueEur) / MAX(StoreM2)
        ELSE NULL
    END                                                 AS RevenuePerM2
FROM list_views.V_LIST_G18_BENCHMARK_KPI
GROUP BY
    IdStore,
    IdCalmonth,
    IdCalmonthStd,
    Jahr,
    Monat,
    StoreName;
GO

PRINT 'Alle Benchmark Views wurden erfolgreich erstellt.';
GO
