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
-- Zweck: Aggregation der Kosten je Monat und Filiale
-- Beschaffungskosten werden nur in den Monaten angezeigt, in denen sie tatsächlich anfallen
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

    -- Personalkosten (Gehalt + Sozialkosten + Kommission/Provision)
    SUM(CASE
        WHEN c.Kostenkategorie IN ('Monthly Salary', 'Monthly Social Costs', 'Commission')
        THEN c.WertEUR
        ELSE 0
    END) AS PersonnelCostsEur,

    -- Betriebskosten (Miete + Marketing)
    SUM(CASE
        WHEN c.Kostenkategorie IN ('Monthly Rent', 'Marketing Campaign')
        THEN c.WertEUR
        ELSE 0
    END) AS OperatingCostsEur,

    -- Zusätzliche Beschaffungskosten (alle "Additional Procurement Costs for ...")
    SUM(CASE
        WHEN c.Kostenkategorie LIKE 'Additional Procurement Costs%'
        THEN c.WertEUR
        ELSE 0
    END) AS AdditionalProcurementCostsEur

FROM dbo.V_LIST_MONTHLY_COSTS c
WHERE c.ID_STORE IN (3, 5, 14)  -- Benchmark-Filialen
GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE, c.StoreName;
GO


-- =============================================
-- LAYER 3: KPI-BERECHNUNG
-- =============================================

-- View 4: list_views.V_LIST_G18_BENCHMARK_KPI
-- Zweck: Zentrale KPI-View für Filialkennzahlen
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
-- LAYER 4: EXPORT - EINZELNE STORES (NEU!)
-- =============================================

-- View 5: list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
-- ÄNDERUNG: Jetzt mit einzelnen Stores statt kombiniert
-- Das erlaubt modularen Vergleich beliebiger Stores
-- NEU: Gesamtkosten = Wareneinsatz + Betriebskosten + Personalkosten + Beschaffungskosten
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY (
    Monat,
    Filialgruppe,
    IdStore,
    UmsatzEur,
    BruttogewinnEur,
    WareneinsatzEur,
    GesamtkostenEur,
    PersonalkostenEur,
    BetriebskostenEur,
    BeschaffungskostenEur,
    NettogewinnEur,
    BruttogewinnMargeProzent,
    BetriebskostenQuoteProzent,
    PersonalkostenAnteilProzent,
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
    -- NEUE FORMEL: Gesamtkosten = Wareneinsatz + Betriebskosten + Personalkosten + Beschaffungskosten
    ROUND(
        (k.TotalRevenueEur - k.TotalGrossProfitEur)  -- Wareneinsatz
        + k.OperatingCostsEur                         -- Betriebskosten (Miete, Marketing, Kommission)
        + k.PersonnelCostsEur                         -- Personalkosten
        + c.AdditionalProcurementCostsEur             -- zusätzliche Beschaffungskosten
    , 2) AS GesamtkostenEur,
    ROUND(k.PersonnelCostsEur, 2) AS PersonalkostenEur,
    ROUND(k.OperatingCostsEur, 2) AS BetriebskostenEur,
    ROUND(c.AdditionalProcurementCostsEur, 2) AS BeschaffungskostenEur,
    ROUND(k.NetProfitEur, 2) AS NettogewinnEur,
    ROUND(k.GrossProfitMarginPct, 2) AS BruttogewinnMargeProzent,
    ROUND(k.OperatingCostRatioPct, 2) AS BetriebskostenQuoteProzent,
    ROUND(k.PersonnelCostRatioPct, 2) AS PersonalkostenAnteilProzent,
    ROUND(k.NetProfitMarginPct, 2) AS NettogewinnMargeProzent
FROM list_views.V_LIST_G18_BENCHMARK_KPI k
INNER JOIN list_views.V_LIST_G18_BENCHMARK_COSTS_AGG c
    ON k.IdCalmonthStd = c.IdCalmonthStd AND k.IdStore = c.IdStore;
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
-- Zweck: Daten für Waterfall-Chart (Umsatz -> Kosten -> Gewinn)
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_WATERFALL (
    IdCalmonthStd,
    IdStore,
    StoreName,
    UmsatzEur,
    WareneinsatzEur,
    BruttogewinnEur,
    PersonalkostenEur,
    MieteEur,
    MarketingEur,
    KommissionEur,
    BeschaffungskostenEur,
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
    -- Einzelne Kostenpositionen aus COSTS_AGG
    c.PersonnelCostsEur AS PersonalkostenEur,
    -- Miete separat (aus Detail-Aggregation)
    ISNULL((SELECT SUM(WertEUR) FROM dbo.V_LIST_MONTHLY_COSTS
            WHERE ID_STORE = k.IdStore
            AND FORMAT(ID_CALMONTH, 'yyyy-MM') = k.IdCalmonthStd
            AND Kostenkategorie = 'Monthly Rent'), 0) AS MieteEur,
    -- Marketing
    ISNULL((SELECT SUM(WertEUR) FROM dbo.V_LIST_MONTHLY_COSTS
            WHERE ID_STORE = k.IdStore
            AND FORMAT(ID_CALMONTH, 'yyyy-MM') = k.IdCalmonthStd
            AND Kostenkategorie = 'Marketing Campaign'), 0) AS MarketingEur,
    -- Kommission
    ISNULL((SELECT SUM(WertEUR) FROM dbo.V_LIST_MONTHLY_COSTS
            WHERE ID_STORE = k.IdStore
            AND FORMAT(ID_CALMONTH, 'yyyy-MM') = k.IdCalmonthStd
            AND Kostenkategorie = 'Commission'), 0) AS KommissionEur,
    -- Beschaffungskosten
    c.AdditionalProcurementCostsEur AS BeschaffungskostenEur,
    k.NetProfitEur AS NettogewinnEur
FROM list_views.V_LIST_G18_BENCHMARK_KPI k
INNER JOIN list_views.V_LIST_G18_BENCHMARK_COSTS_AGG c
    ON k.IdCalmonthStd = c.IdCalmonthStd AND k.IdStore = c.IdStore;
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
