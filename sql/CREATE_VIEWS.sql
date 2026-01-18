-- =============================================
-- Benchmarking System - Gruppe 18
-- VERSION 2.3: Views OHNE hardcodierte Store-IDs
-- Filterung erfolgt dynamisch in der App via WHERE IdStore IN (...)
-- =============================================

-- =============================================
-- LAYER 1: STANDARDISIERUNG (ALLE STORES)
-- =============================================

-- View 1: list_views.V_LIST_G18_BENCHMARK_SALES_DETAIL
-- Zweck: Standardisierung der Verkaufsdaten für ALLE Stores
-- KEIN Store-Filter mehr - App filtert dynamisch!
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_DETAIL (
    IdCalmonthStd,
    IdStore,
    StoreName,
    IdMaterial,
    MaterialDescription,
    BenchmarkCategory,
    Preissegment,
    DiscountEur,
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

    -- Filialname direkt aus V_LIST_MONTHLY_SALES (kein JOIN mehr nötig)
    s.StoreName AS StoreName,

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

    -- Preissegment direkt aus Basis-View
    s.ProduktPreisSegment AS Preissegment,

    -- DiscountEur für Netto-Umsatz Berechnung
    s.DiscountEUR AS DiscountEur,

    -- RevenueEur = Brutto-Umsatz - Rabatt (Netto-Umsatz)
    (s.RevenueEUR - s.DiscountEUR) AS RevenueEur,

    -- GrossProfitEur = Netto-Umsatz - Wareneinsatz
    ((s.RevenueEUR - s.DiscountEUR) - s.TransferPriceEUR) AS GrossProfitEur,

    s.TransferPriceEUR AS TransferCostEur,
    s.SalesPriceEUR AS SalesPriceEur,
    s.SalesAmount AS Quantity

FROM dbo.V_LIST_MONTHLY_SALES s;
-- JOIN mit T_SALESORG entfernt - StoreName ist bereits in V_LIST_MONTHLY_SALES vorhanden
-- KEIN WHERE-Filter! App filtert via: WHERE IdStore IN (51003003, 51005005, 51014014)
GO


-- =============================================
-- LAYER 2: AGGREGATION (ALLE STORES)
-- =============================================

-- View 2: list_views.V_LIST_G18_BENCHMARK_SALES_AGG
-- Zweck: Aggregation der Verkaufsdaten je Monat, Filiale, Kategorie
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_AGG (
    IdCalmonthStd,
    IdStore,
    StoreName,
    BenchmarkCategory,
    TotalDiscountEur,
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

    SUM(DiscountEur) AS TotalDiscountEur,
    SUM(RevenueEur) AS TotalRevenueEur,
    SUM(GrossProfitEur) AS TotalGrossProfitEur,
    SUM(TransferCostEur) AS TotalTransferCostEur,
    AVG(SalesPriceEur) AS AvgSalesPriceEur,
    SUM(Quantity) AS TotalQuantity

FROM list_views.V_LIST_G18_BENCHMARK_SALES_DETAIL
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
GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE, c.StoreName;
-- KEIN WHERE-Filter! App filtert via: WHERE IdStore IN (51003003, 51005005, 51014014)
GO


-- =============================================
-- LAYER 3: KPI-BERECHNUNG (ALLE STORES)
-- =============================================

-- View 4: list_views.V_LIST_G18_BENCHMARK_KPI
-- Zweck: Zentrale KPI-View für Filialkennzahlen mit Business-Kategorien
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_KPI (
    IdCalmonthStd,
    IdStore,
    StoreName,
    TotalDiscountEur,
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
    SUM(s.TotalDiscountEur) AS TotalDiscountEur,
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
-- LAYER 4: EXPORT (ALLE STORES)
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
-- LAYER 5: DETAILLIERTE KOSTENANALYSE (ALLE STORES)
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
GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE, c.StoreName, c.Kostenkategorie;
GO


-- =============================================
-- LAYER 6: MARKETING-KPIs (ALLE STORES)
-- =============================================

-- View 8: list_views.V_LIST_G18_MARKETING_KPI_MONTHLY
-- Zweck: Zentrale Marketing-View - ersetzt alle Inline-Queries und Regex-Logik
-- Liefert: ROAS, CPA, Marketing-Quote pro Monat und Store
CREATE OR ALTER VIEW list_views.V_LIST_G18_MARKETING_KPI_MONTHLY (
    IdCalmonthStd,
    IdStore,
    StoreName,
    MarketingCostEur,
    MarketingAttributedRevenueEur,      -- "Marketing-attributierter Umsatz"
    MarketingIndependentRevenueEur,     -- "Marketing-unabhängiger Umsatz"
    TotalRevenueEur,
    MarketingAttributedQuantity,        -- Anzahl mit Marketing
    QuantityTotal,
    ROAS,
    CPA,
    MarketingQuotePct
)
AS
SELECT
    sales.IdCalmonthStd,
    sales.IdStore,
    sales.StoreName,
    ISNULL(costs.MarketingCostEur, 0) AS MarketingCostEur,
    sales.RevenueWithCampaignEur AS MarketingAttributedRevenueEur,
    sales.RevenueWithoutCampaignEur AS MarketingIndependentRevenueEur,
    sales.TotalRevenueEur,
    sales.QuantityWithCampaign AS MarketingAttributedQuantity,
    sales.QuantityTotal,
    -- ROAS = Marketing-attributierter Umsatz / Marketing-Kosten
    CASE
        WHEN ISNULL(costs.MarketingCostEur, 0) > 0
        THEN sales.RevenueWithCampaignEur / costs.MarketingCostEur
        ELSE NULL
    END AS ROAS,
    -- CPA = Marketing-Kosten / Stück (marketing-attributiert)
    CASE
        WHEN sales.QuantityWithCampaign > 0
        THEN ISNULL(costs.MarketingCostEur, 0) / sales.QuantityWithCampaign
        ELSE NULL
    END AS CPA,
    -- Marketing-Quote = Marketing-Kosten / Gesamtumsatz × 100
    CASE
        WHEN sales.TotalRevenueEur > 0
        THEN (ISNULL(costs.MarketingCostEur, 0) / sales.TotalRevenueEur) * 100
        ELSE NULL
    END AS MarketingQuotePct
FROM (
    -- Subquery: Sales aggregiert nach Monat/Store mit Kampagnen-Split
    SELECT
        FORMAT(s.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
        s.ID_STORE AS IdStore,
        s.StoreName AS StoreName,
        SUM(CASE WHEN s.ID_CAMPAIGN IS NOT NULL AND s.ID_CAMPAIGN != 0 THEN s.RevenueEUR ELSE 0 END) AS RevenueWithCampaignEur,
        SUM(CASE WHEN s.ID_CAMPAIGN IS NULL OR s.ID_CAMPAIGN = 0 THEN s.RevenueEUR ELSE 0 END) AS RevenueWithoutCampaignEur,
        SUM(s.RevenueEUR) AS TotalRevenueEur,
        SUM(CASE WHEN s.ID_CAMPAIGN IS NOT NULL AND s.ID_CAMPAIGN != 0 THEN s.SalesAmount ELSE 0 END) AS QuantityWithCampaign,
        SUM(s.SalesAmount) AS QuantityTotal
    FROM dbo.V_LIST_MONTHLY_SALES s
    GROUP BY FORMAT(s.ID_CALMONTH, 'yyyy-MM'), s.ID_STORE, s.StoreName
) sales
LEFT JOIN (
    -- Subquery: Marketing-Kosten pro Monat/Store
    SELECT
        FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
        c.ID_STORE AS IdStore,
        SUM(c.WertEUR) AS MarketingCostEur
    FROM dbo.V_LIST_MONTHLY_COSTS c
    WHERE c.Kostenkategorie = 'Marketing Campaign'
    GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE
) costs ON sales.IdCalmonthStd = costs.IdCalmonthStd AND sales.IdStore = costs.IdStore;
GO


-- View 9: list_views.V_LIST_G18_MARKETING_BY_CAMPAIGN
-- Zweck: ROAS und Profit pro einzelner Kampagne
CREATE OR ALTER VIEW list_views.V_LIST_G18_MARKETING_BY_CAMPAIGN (
    IdStore,
    StoreName,
    IdCampaign,
    CampaignName,
    CampaignType,
    RevenueEur,
    CostEur,
    DiscountEur,
    Quantity,
    ROAS,
    CampaignProfit
)
AS
WITH SalesAgg AS (
    -- Aggregiere Sales pro Store und Kampagne
    SELECT
        ID_STORE,
        StoreName,
        ID_CAMPAIGN,
        Kampagne,
        KampagneTyp,
        SUM(RevenueEUR) AS RevenueEur,
        SUM(DiscountEUR) AS DiscountEur,
        SUM(SalesAmount) AS Quantity
    FROM dbo.V_LIST_MONTHLY_SALES
    WHERE ID_CAMPAIGN != 0
    GROUP BY ID_STORE, StoreName, ID_CAMPAIGN, Kampagne, KampagneTyp
),
CostsAgg AS (
    -- Kosten pro Kampagne extrahieren (aus Beschreibung mit ID)
    -- Format: "Marketing Campaign [XX]: Name" -> extrahiere XX als Campaign-ID
    SELECT
        ID_STORE,
        CAST(SUBSTRING(
            Beschreibung,
            CHARINDEX('[', Beschreibung) + 1,
            CHARINDEX(']', Beschreibung) - CHARINDEX('[', Beschreibung) - 1
        ) AS INT) AS ID_CAMPAIGN,
        SUM(WertEUR) AS CostEur
    FROM dbo.V_LIST_MONTHLY_COSTS
    WHERE Kostenkategorie = 'Marketing Campaign'
    AND CHARINDEX('[', Beschreibung) > 0
    AND CHARINDEX(']', Beschreibung) > CHARINDEX('[', Beschreibung)
    GROUP BY ID_STORE, SUBSTRING(
        Beschreibung,
        CHARINDEX('[', Beschreibung) + 1,
        CHARINDEX(']', Beschreibung) - CHARINDEX('[', Beschreibung) - 1
    )
)
SELECT
    s.ID_STORE AS IdStore,
    s.StoreName AS StoreName,
    s.ID_CAMPAIGN AS IdCampaign,
    s.Kampagne AS CampaignName,
    s.KampagneTyp AS CampaignType,
    s.RevenueEur AS RevenueEur,
    ISNULL(c.CostEur, 0) AS CostEur,
    s.DiscountEur AS DiscountEur,
    s.Quantity AS Quantity,
    -- ROAS = Umsatz / Kosten
    CASE
        WHEN ISNULL(c.CostEur, 0) > 0
        THEN s.RevenueEur / c.CostEur
        ELSE NULL
    END AS ROAS,
    -- Campaign Profit = Umsatz - Kosten - Discount
    (s.RevenueEur - ISNULL(c.CostEur, 0) - s.DiscountEur) AS CampaignProfit
FROM SalesAgg s
LEFT JOIN CostsAgg c ON s.ID_STORE = c.ID_STORE AND s.ID_CAMPAIGN = c.ID_CAMPAIGN;
GO


-- =============================================
-- LAYER 7: STORE DETAILS (ALLE STORES)
-- =============================================

-- View 10: list_views.V_LIST_G18_STORE_DETAILS
-- Zweck: Store-Stammdaten mit Fläche, Mietkosten und Umsatz-Effizienz (pro Monat)
CREATE OR ALTER VIEW list_views.V_LIST_G18_STORE_DETAILS (
    IdCalmonthStd,
    IdStore,
    StoreName,
    StoreM2,
    Mietkosten,
    TotalDiscount,
    Umsatz,
    UmsatzProM2
)
AS
WITH SalesAgg AS (
    SELECT
        FORMAT(ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
        ID_STORE,
        MAX(StoreName) AS StoreName,
        MAX(StoreM2) AS StoreM2,
        SUM(DiscountEUR) AS TotalDiscount,
        SUM(RevenueEUR - DiscountEUR) AS Umsatz
    FROM dbo.V_LIST_MONTHLY_SALES
    GROUP BY FORMAT(ID_CALMONTH, 'yyyy-MM'), ID_STORE
),
CostsAgg AS (
    SELECT
        FORMAT(ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
        ID_STORE,
        SUM(WertEUR) AS Mietkosten
    FROM dbo.V_LIST_MONTHLY_COSTS
    WHERE Kostenkategorie = 'Monthly Rent'
    GROUP BY FORMAT(ID_CALMONTH, 'yyyy-MM'), ID_STORE
)
SELECT
    s.IdCalmonthStd,
    s.ID_STORE AS IdStore,
    s.StoreName AS StoreName,
    s.StoreM2,
    ISNULL(c.Mietkosten, 0) AS Mietkosten,
    s.TotalDiscount,
    s.Umsatz,
    CASE
        WHEN s.StoreM2 > 0 THEN s.Umsatz / s.StoreM2
        ELSE 0
    END AS UmsatzProM2
FROM SalesAgg s
LEFT JOIN CostsAgg c ON s.IdCalmonthStd = c.IdCalmonthStd AND s.ID_STORE = c.ID_STORE;
GO


-- =============================================
-- DEPLOYMENT ABGESCHLOSSEN
-- =============================================

PRINT '============================================='
PRINT 'Gruppe 18 - Benchmark Views V2.4 erstellt!'
PRINT '============================================='
PRINT ''
PRINT 'WICHTIG: Views enthalten KEINE Store-Filter mehr!'
PRINT 'Die App filtert dynamisch via:'
PRINT '  WHERE IdStore IN (51003003, 51005005, 51014014)'
PRINT ''
PRINT 'Vorteile:'
PRINT '  - Keine Logik-Duplikate in Views'
PRINT '  - Flexibel: Stores in App hinzufügen/entfernen'
PRINT '  - Konsistent: DB liefert Wahrheit, App filtert'
PRINT ''
PRINT 'Enthaltene Views:'
PRINT '  1. V_LIST_G18_BENCHMARK_SALES_DETAIL'
PRINT '  2. V_LIST_G18_BENCHMARK_SALES_AGG'
PRINT '  3. V_LIST_G18_BENCHMARK_COSTS_AGG'
PRINT '  4. V_LIST_G18_BENCHMARK_KPI'
PRINT '  5. V_LIST_G18_BENCHMARK_EXPORT_MONTHLY'
PRINT '  6. V_LIST_G18_BENCHMARK_COSTS_DETAIL'
PRINT '  7. V_LIST_G18_MARKETING_KPI_MONTHLY'
PRINT '  8. V_LIST_G18_MARKETING_BY_CAMPAIGN'
PRINT '  9. V_LIST_G18_STORE_DETAILS'
PRINT ''
PRINT '============================================='
GO
