-- =============================================
-- Benchmarking System - Gruppe 18
-- VERSION 2: Modulares Multi-Store System
-- Mit korrekten Produktkategorien
-- =============================================

-- =============================================
-- LAYER 1: STANDARDISIERUNG
-- =============================================

-- View 1: list_views.V_LIST_G18_BENCHMARK_SALES_STD
-- Zweck: Standardisierung der Verkaufsdaten
-- ÄNDERUNG: Neue Produktkategorien
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

    -- Benchmark-Kategorie zuweisen (6 Kategorien basierend auf Produktnamen)
    CASE
        -- E-Trekking: Grace, JMS e-Bike
        WHEN s.ProduktBeschreibung LIKE '%Grace%' THEN 'E-Trekking'
        WHEN s.ProduktBeschreibung LIKE '%JMS e-Bike%' THEN 'E-Trekking'
        WHEN s.ProduktBeschreibung LIKE '%S-Pedelec%' THEN 'E-Trekking'
        WHEN s.ProduktBeschreibung LIKE '%Pedelec%' THEN 'E-Trekking'

        -- Kid Bikes: Puky, Cubie, Mini Racer
        WHEN s.ProduktBeschreibung LIKE '%Puky%' THEN 'Kid Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Cubie%' THEN 'Kid Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Mini Racer%' THEN 'Kid Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Leo%' THEN 'Kid Bikes'

        -- Mountain Bikes: Copperhead, Aim, Reaction, Genius
        WHEN s.ProduktBeschreibung LIKE '%Copperhead%' THEN 'Mountain Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Aim Disc%' THEN 'Mountain Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Reaction%' THEN 'Mountain Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Genius%' THEN 'Mountain Bikes'

        -- Race Bikes: Diesel, Night Falcon, Vulture, Cervelo
        WHEN s.ProduktBeschreibung LIKE '%Diesel%' THEN 'Race Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Night Falcon%' THEN 'Race Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Vulture%' THEN 'Race Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Cervelo%' THEN 'Race Bikes'

        -- Trekking Bikes: Rixe, Avenza, KATHMANDU, Cube Trekking
        WHEN s.ProduktBeschreibung LIKE '%Rixe%' THEN 'Trekking Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Avenza%' THEN 'Trekking Bikes'
        WHEN s.ProduktBeschreibung LIKE '%KATHMANDU%' THEN 'Trekking Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Trekking%' THEN 'Trekking Bikes'

        -- City Bikes: Corona, PEGASUS, Town Lite, Travel City (und Rest)
        WHEN s.ProduktBeschreibung LIKE '%Corona%' THEN 'City Bikes'
        WHEN s.ProduktBeschreibung LIKE '%PEGASUS%' THEN 'City Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Town Lite%' THEN 'City Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Travel City%' THEN 'City Bikes'

        ELSE 'City Bikes'  -- Fallback
    END AS BenchmarkCategory,

    s.RevenueEUR AS RevenueEur,
    (s.RevenueEUR - s.TransferPriceEUR) AS GrossProfitEur,
    s.TransferPriceEUR AS TransferCostEur,
    s.SalesPriceEUR AS SalesPriceEur,
    s.SalesAmount AS Quantity

FROM dbo.V_LIST_MONTHLY_SALES s
INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
WHERE s.ID_STORE IN (3, 5, 14);  -- Benchmark-Filialen (konfigurierbar)
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
-- Zweck: Aggregation der Kosten je Monat und Filiale nach Business-Kategorien
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_COSTS_AGG (
    IdCalmonthStd,
    IdStore,
    StoreName,
    TotalCostsEur,
    HumanResourcesEur,
    FacilityManagementEur,
    LogisticsEur,
    MarketingEur
)
AS
SELECT
    FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
    c.ID_STORE AS IdStore,
    c.StoreName AS StoreName,

    -- Gesamtkosten (Summe aller Kategorien)
    SUM(c.WertEUR) AS TotalCostsEur,

    -- HumanResources (Monthly Salary + Monthly Social Costs)
    SUM(CASE
        WHEN c.Kostenkategorie IN ('Monthly Salary', 'Monthly Social Costs')
        THEN c.WertEUR
        ELSE 0
    END) AS HumanResourcesEur,

    -- Facility Management (Monthly Rent)
    SUM(CASE
        WHEN c.Kostenkategorie = 'Monthly Rent'
        THEN c.WertEUR
        ELSE 0
    END) AS FacilityManagementEur,

    -- Logistics (Additional Procurement Costs)
    SUM(CASE
        WHEN c.Kostenkategorie LIKE 'Additional Procurement Costs%'
        THEN c.WertEUR
        ELSE 0
    END) AS LogisticsEur,

    -- Marketing (Marketing Campaign)
    SUM(CASE
        WHEN c.Kostenkategorie = 'Marketing Campaign'
        THEN c.WertEUR
        ELSE 0
    END) AS MarketingEur

FROM dbo.V_LIST_MONTHLY_COSTS c
WHERE c.ID_STORE IN (3, 5, 14)  -- Benchmark-Filialen
GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE, c.StoreName;
GO


-- =============================================
-- LAYER 3: KPI-BERECHNUNG
-- =============================================

-- View 4: list_views.V_LIST_G18_BENCHMARK_KPI
-- Zweck: Zentrale KPI-View für Filialkennzahlen mit Business-Kategorien
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_KPI (
    IdCalmonthStd,
    IdStore,
    StoreName,
    TotalRevenueEur,
    TotalGrossProfitEur,
    TotalCostsEur,
    HumanResourcesEur,
    FacilityManagementEur,
    LogisticsEur,
    MarketingEur,
    NetProfitEur,
    GrossProfitMarginPct,
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
    c.HumanResourcesEur,
    c.FacilityManagementEur,
    c.LogisticsEur,
    c.MarketingEur,

    -- Nettogewinn = Bruttogewinn - Gesamtkosten
    SUM(s.TotalGrossProfitEur) - c.TotalCostsEur AS NetProfitEur,

    -- KPI 1: Bruttogewinn-Marge (%) = Bruttogewinn / Umsatz * 100
    CASE
        WHEN SUM(s.TotalRevenueEur) > 0
        THEN (SUM(s.TotalGrossProfitEur) / SUM(s.TotalRevenueEur)) * 100
        ELSE NULL
    END AS GrossProfitMarginPct,

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
         c.TotalCostsEur, c.HumanResourcesEur, c.FacilityManagementEur,
         c.LogisticsEur, c.MarketingEur;
GO


-- =============================================
-- LAYER 4: EXPORT - EINZELNE STORES (NEU!)
-- =============================================

-- View 5: list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
-- Zweck: Export-View mit Business-Kategorien für Dashboard
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY (
    Monat,
    Filialgruppe,
    IdStore,
    UmsatzEur,
    BruttogewinnEur,
    WareneinsatzEur,
    GesamtkostenEur,
    HumanResourcesEur,
    FacilityManagementEur,
    LogisticsEur,
    MarketingEur,
    EbitEur,
    NettogewinnEur,
    BruttogewinnMargeProzent,
    NettogewinnMargeProzent
)
AS
SELECT
    k.IdCalmonthStd AS Monat,
    k.StoreName AS Filialgruppe,
    k.IdStore,
    ROUND(k.TotalRevenueEur, 2) AS UmsatzEur,
    ROUND(k.TotalGrossProfitEur, 2) AS BruttogewinnEur,
    -- Wareneinsatz = Umsatz - Bruttogewinn
    ROUND(k.TotalRevenueEur - k.TotalGrossProfitEur, 2) AS WareneinsatzEur,
    -- Gesamtkosten aus COSTS_AGG (ohne Wareneinsatz) = OPEX
    ROUND(k.TotalCostsEur, 2) AS GesamtkostenEur,
    -- Business-Kategorien (OPEX)
    ROUND(k.HumanResourcesEur, 2) AS HumanResourcesEur,
    ROUND(k.FacilityManagementEur, 2) AS FacilityManagementEur,
    ROUND(k.LogisticsEur, 2) AS LogisticsEur,
    ROUND(k.MarketingEur, 2) AS MarketingEur,
    -- EBIT = Revenue - TransferPrice - OPEX = Bruttogewinn - OPEX
    ROUND(k.TotalGrossProfitEur - k.TotalCostsEur, 2) AS EbitEur,
    ROUND(k.NetProfitEur, 2) AS NettogewinnEur,
    ROUND(k.GrossProfitMarginPct, 2) AS BruttogewinnMargeProzent,
    ROUND(k.NetProfitMarginPct, 2) AS NettogewinnMargeProzent
FROM list_views.V_LIST_G18_BENCHMARK_KPI k;
GO


-- =============================================
-- LAYER 5: DETAILLIERTE KOSTENANALYSE
-- =============================================

-- View 6: list_views.V_LIST_G18_BENCHMARK_COSTS_DETAIL
-- Zweck: Detaillierte Kostenaufstellung nach Kategorie für Waterfall-Charts
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_COSTS_DETAIL (
    IdCalmonthStd,
    IdStore,
    StoreName,
    Kostenkategorie,
    KostenEur
)
AS
SELECT
    FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
    c.ID_STORE AS IdStore,
    c.StoreName AS StoreName,
    c.Kostenkategorie,
    SUM(c.WertEUR) AS KostenEur
FROM dbo.V_LIST_MONTHLY_COSTS c
WHERE c.ID_STORE IN (3, 5, 14)  -- Benchmark-Filialen
GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE, c.StoreName, c.Kostenkategorie;
GO


-- View 7: list_views.V_LIST_G18_BENCHMARK_WATERFALL
-- Zweck: Daten für Waterfall-Chart mit Business-Kategorien
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_WATERFALL (
    IdCalmonthStd,
    IdStore,
    StoreName,
    UmsatzEur,
    WareneinsatzEur,
    BruttogewinnEur,
    HumanResourcesEur,
    FacilityManagementEur,
    LogisticsEur,
    MarketingEur,
    TotalCostsEur,
    NettogewinnEur
)
AS
SELECT
    k.IdCalmonthStd,
    k.IdStore,
    k.StoreName,
    k.TotalRevenueEur AS UmsatzEur,
    -- Wareneinsatz = Umsatz - Bruttogewinn
    (k.TotalRevenueEur - k.TotalGrossProfitEur) AS WareneinsatzEur,
    k.TotalGrossProfitEur AS BruttogewinnEur,
    -- Business-Kategorien
    k.HumanResourcesEur,
    k.FacilityManagementEur,
    k.LogisticsEur,
    k.MarketingEur,
    k.TotalCostsEur,
    k.NetProfitEur AS NettogewinnEur
FROM list_views.V_LIST_G18_BENCHMARK_KPI k;
GO


-- =============================================
-- DEPLOYMENT ABGESCHLOSSEN
-- =============================================

PRINT '============================================='
PRINT 'Gruppe 18 - Benchmark Views V2.1 erstellt!'
PRINT '============================================='
PRINT ''
PRINT 'Änderungen in V2:'
PRINT '  - 6 Produktkategorien: City Bikes, E-Trekking, Kid Bikes,'
PRINT '    Mountain Bikes, Race Bikes, Trekking Bikes'
PRINT '  - Einzelne Stores statt kombinierte Gruppen'
PRINT '  - Modulares System für beliebige Store-Anzahl'
PRINT ''
PRINT '============================================='
GO
