# 4. Views und Schichten (inkl. SQL-Definitionen)

Alle fachlichen Anforderungen aus dem Fachkonzept werden über SQL-Views umgesetzt. Tabellen werden nicht verändert.

Die Views sind in Schichten gegliedert:

- Standardisierungs- und Bereinigungs-Views
- Aggregations-Views
- KPI-/Benchmark-Views
- Marketing-Views
- Export-Views

---

## 4.1 Standardisierungs- und Bereinigungs-Views

### 4.1.1 View V_LIST_G18_BENCHMARK_SALES_DETAIL

Diese View vereinheitlicht das Monatsformat, reichert Filialstammdaten an und weist Artikel Benchmark-Kategorien zu.

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_DETAIL (
    IdCalmonthStd, IdStore, StoreName, IdMaterial, MaterialDescription,
    BenchmarkCategory, Preissegment, DiscountEur, RevenueEur,
    GrossProfitEur, TransferCostEur, SalesPriceEur, Quantity
)
AS
SELECT
    FORMAT(s.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
    s.ID_STORE AS IdStore,
    s.StoreName AS StoreName,
    s.ID_MATERIAL AS IdMaterial,
    s.ProduktBeschreibung AS MaterialDescription,

    -- Benchmark-Kategorie zuweisen (6 Kategorien)
    CASE
        WHEN s.ProduktBeschreibung LIKE '%Grace%' THEN 'E-Trekking'
        WHEN s.ProduktBeschreibung LIKE '%JMS e-Bike%' THEN 'E-Trekking'
        WHEN s.ProduktBeschreibung LIKE '%Puky%' THEN 'Kid Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Cubie%' THEN 'Kid Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Copperhead%' THEN 'Mountain Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Reaction%' THEN 'Mountain Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Diesel%' THEN 'Race Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Cervelo%' THEN 'Race Bikes'
        WHEN s.ProduktBeschreibung LIKE '%Rixe%' THEN 'Trekking Bikes'
        WHEN s.ProduktBeschreibung LIKE '%KATHMANDU%' THEN 'Trekking Bikes'
        ELSE 'City Bikes'
    END AS BenchmarkCategory,

    s.ProduktPreisSegment AS Preissegment,
    s.DiscountEUR AS DiscountEur,
    (s.RevenueEUR - s.DiscountEUR) AS RevenueEur,
    ((s.RevenueEUR - s.DiscountEUR) - s.TransferPriceEUR) AS GrossProfitEur,
    s.TransferPriceEUR AS TransferCostEur,
    s.SalesPriceEUR AS SalesPriceEur,
    s.SalesAmount AS Quantity
FROM dbo.V_LIST_MONTHLY_SALES s;
```

---

## 4.2 Aggregations-Views

### 4.2.1 View V_LIST_G18_BENCHMARK_SALES_AGG

Aggregation der Verkaufsdaten je Monat, Filiale und Kategorie.

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_SALES_AGG (
    IdCalmonthStd, IdStore, StoreName, BenchmarkCategory,
    TotalDiscountEur, TotalRevenueEur, TotalGrossProfitEur,
    TotalTransferCostEur, AvgSalesPriceEur, TotalQuantity
)
AS
SELECT
    IdCalmonthStd, IdStore, StoreName, BenchmarkCategory,
    SUM(DiscountEur) AS TotalDiscountEur,
    SUM(RevenueEur) AS TotalRevenueEur,
    SUM(GrossProfitEur) AS TotalGrossProfitEur,
    SUM(TransferCostEur) AS TotalTransferCostEur,
    AVG(SalesPriceEur) AS AvgSalesPriceEur,
    SUM(Quantity) AS TotalQuantity
FROM list_views.V_LIST_G18_BENCHMARK_SALES_DETAIL
GROUP BY IdCalmonthStd, IdStore, StoreName, BenchmarkCategory;
```

### 4.2.2 View V_LIST_G18_BENCHMARK_COSTS_AGG

Aggregation der Kosten je Monat und Filiale nach Business-Kategorien (Human Resources, Facility Management, Logistics, Marketing).

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_COSTS_AGG (
    IdCalmonthStd, IdStore, StoreName, TotalCostsEur,
    HumanResourcesEur, FacilityManagementEur, LogisticsEur, MarketingEur
)
AS
SELECT
    FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
    c.ID_STORE AS IdStore,
    c.StoreName AS StoreName,
    SUM(c.WertEUR) AS TotalCostsEur,

    -- HumanResources (Gehälter + Sozialkosten)
    SUM(CASE WHEN c.Kostenkategorie IN ('Monthly Salary', 'Monthly Social Costs')
        THEN c.WertEUR ELSE 0 END) AS HumanResourcesEur,

    -- Facility Management (Miete)
    SUM(CASE WHEN c.Kostenkategorie = 'Monthly Rent'
        THEN c.WertEUR ELSE 0 END) AS FacilityManagementEur,

    -- Logistics (Beschaffungskosten)
    SUM(CASE WHEN c.Kostenkategorie LIKE 'Additional Procurement Costs%'
        THEN c.WertEUR ELSE 0 END) AS LogisticsEur,

    -- Marketing
    SUM(CASE WHEN c.Kostenkategorie = 'Marketing Campaign'
        THEN c.WertEUR ELSE 0 END) AS MarketingEur

FROM dbo.V_LIST_MONTHLY_COSTS c
GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE, c.StoreName;
```

---

## 4.3 KPI-/Benchmark-View

### 4.3.1 View V_LIST_G18_BENCHMARK_KPI

Zentrale View für das Datenobjekt „Filialkennzahlen". Berechnet Nettogewinn, Bruttogewinn-Marge und Nettogewinn-Marge.

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_KPI (
    IdCalmonthStd, IdStore, StoreName,
    TotalDiscountEur, TotalRevenueEur, TotalGrossProfitEur, TotalCostsEur,
    HumanResourcesEur, FacilityManagementEur, LogisticsEur, MarketingEur,
    NetProfitEur, GrossProfitMarginPct, NetProfitMarginPct
)
AS
SELECT
    s.IdCalmonthStd, s.IdStore, s.StoreName,
    SUM(s.TotalDiscountEur) AS TotalDiscountEur,
    SUM(s.TotalRevenueEur) AS TotalRevenueEur,
    SUM(s.TotalGrossProfitEur) AS TotalGrossProfitEur,
    c.TotalCostsEur,
    c.HumanResourcesEur, c.FacilityManagementEur, c.LogisticsEur, c.MarketingEur,

    -- Nettogewinn = Bruttogewinn - Gesamtkosten
    SUM(s.TotalGrossProfitEur) - c.TotalCostsEur AS NetProfitEur,

    -- Bruttogewinn-Marge (%) = Bruttogewinn / Umsatz * 100
    CASE WHEN SUM(s.TotalRevenueEur) > 0
        THEN (SUM(s.TotalGrossProfitEur) / SUM(s.TotalRevenueEur)) * 100
        ELSE NULL
    END AS GrossProfitMarginPct,

    -- Nettogewinn-Marge (%) = Nettogewinn / Umsatz * 100
    CASE WHEN SUM(s.TotalRevenueEur) > 0
        THEN ((SUM(s.TotalGrossProfitEur) - c.TotalCostsEur) / SUM(s.TotalRevenueEur)) * 100
        ELSE NULL
    END AS NetProfitMarginPct

FROM list_views.V_LIST_G18_BENCHMARK_SALES_AGG s
INNER JOIN list_views.V_LIST_G18_BENCHMARK_COSTS_AGG c
    ON s.IdCalmonthStd = c.IdCalmonthStd AND s.IdStore = c.IdStore
GROUP BY s.IdCalmonthStd, s.IdStore, s.StoreName,
         c.TotalCostsEur, c.HumanResourcesEur, c.FacilityManagementEur,
         c.LogisticsEur, c.MarketingEur;
```

---

## 4.4 Marketing-Views

### 4.4.1 View V_LIST_G18_MARKETING_KPI_MONTHLY

View für monatliche Marketing-Kennzahlen: ROAS (Return on Advertising Spend), CPA (Cost per Acquisition) und Marketing-Quote pro Store.

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_MARKETING_KPI_MONTHLY (
    IdCalmonthStd, IdStore, StoreName,
    MarketingCostEur, MarketingAttributedRevenueEur, TotalRevenueEur,
    ROAS, CPA, MarketingQuotePct
)
AS
SELECT
    sales.IdCalmonthStd, sales.IdStore, sales.StoreName,
    ISNULL(costs.MarketingCostEur, 0) AS MarketingCostEur,
    sales.RevenueWithCampaignEur AS MarketingAttributedRevenueEur,
    sales.TotalRevenueEur,

    -- ROAS = Marketing-attributierter Umsatz / Marketing-Kosten
    CASE WHEN ISNULL(costs.MarketingCostEur, 0) > 0
        THEN sales.RevenueWithCampaignEur / costs.MarketingCostEur
        ELSE NULL
    END AS ROAS,

    -- CPA = Marketing-Kosten / Stück
    CASE WHEN sales.QuantityWithCampaign > 0
        THEN ISNULL(costs.MarketingCostEur, 0) / sales.QuantityWithCampaign
        ELSE NULL
    END AS CPA,

    -- Marketing-Quote = Marketing-Kosten / Gesamtumsatz * 100
    CASE WHEN sales.TotalRevenueEur > 0
        THEN (ISNULL(costs.MarketingCostEur, 0) / sales.TotalRevenueEur) * 100
        ELSE NULL
    END AS MarketingQuotePct
FROM (
    SELECT
        FORMAT(s.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
        s.ID_STORE AS IdStore, s.StoreName,
        SUM(CASE WHEN s.ID_CAMPAIGN IS NOT NULL AND s.ID_CAMPAIGN != 0
            THEN s.RevenueEUR ELSE 0 END) AS RevenueWithCampaignEur,
        SUM(s.RevenueEUR) AS TotalRevenueEur,
        SUM(CASE WHEN s.ID_CAMPAIGN IS NOT NULL AND s.ID_CAMPAIGN != 0
            THEN s.SalesAmount ELSE 0 END) AS QuantityWithCampaign
    FROM dbo.V_LIST_MONTHLY_SALES s
    GROUP BY FORMAT(s.ID_CALMONTH, 'yyyy-MM'), s.ID_STORE, s.StoreName
) sales
LEFT JOIN (
    SELECT FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd, c.ID_STORE,
           SUM(c.WertEUR) AS MarketingCostEur
    FROM dbo.V_LIST_MONTHLY_COSTS c
    WHERE c.Kostenkategorie = 'Marketing Campaign'
    GROUP BY FORMAT(c.ID_CALMONTH, 'yyyy-MM'), c.ID_STORE
) costs ON sales.IdCalmonthStd = costs.IdCalmonthStd
       AND sales.IdStore = costs.IdStore;
```

### 4.4.2 View V_LIST_G18_MARKETING_BY_CAMPAIGN

ROAS und Kampagnen-Profit pro einzelner Kampagne (mit Monatsauflösung). Ermöglicht die Bewertung von Verkaufsaktionen und Rabattwirkungen (F06).

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_MARKETING_BY_CAMPAIGN (
    IdCalmonthStd, IdStore, StoreName, IdCampaign, CampaignName,
    CampaignType, RevenueEur, CostEur, DiscountEur, Quantity, ROAS, CampaignProfit
)
AS
WITH SalesAgg AS (
    SELECT
        FORMAT(ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd,
        ID_STORE, StoreName, ID_CAMPAIGN, Kampagne, KampagneTyp,
        SUM(RevenueEUR) AS RevenueEur,
        SUM(DiscountEUR) AS DiscountEur,
        SUM(SalesAmount) AS Quantity
    FROM dbo.V_LIST_MONTHLY_SALES
    WHERE ID_CAMPAIGN != 0
    GROUP BY FORMAT(ID_CALMONTH, 'yyyy-MM'), ID_STORE, StoreName,
             ID_CAMPAIGN, Kampagne, KampagneTyp
),
CostsAgg AS (
    SELECT
        FORMAT(ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd, ID_STORE,
        CAST(SUBSTRING(Beschreibung, CHARINDEX('[', Beschreibung) + 1,
            CHARINDEX(']', Beschreibung) - CHARINDEX('[', Beschreibung) - 1
        ) AS INT) AS ID_CAMPAIGN,
        SUM(WertEUR) AS CostEur
    FROM dbo.V_LIST_MONTHLY_COSTS
    WHERE Kostenkategorie = 'Marketing Campaign'
      AND CHARINDEX('[', Beschreibung) > 0
    GROUP BY FORMAT(ID_CALMONTH, 'yyyy-MM'), ID_STORE,
        SUBSTRING(Beschreibung, CHARINDEX('[', Beschreibung) + 1,
            CHARINDEX(']', Beschreibung) - CHARINDEX('[', Beschreibung) - 1)
)
SELECT
    s.IdCalmonthStd, s.ID_STORE AS IdStore, s.StoreName,
    s.ID_CAMPAIGN AS IdCampaign, s.Kampagne AS CampaignName,
    s.KampagneTyp AS CampaignType, s.RevenueEur,
    ISNULL(c.CostEur, 0) AS CostEur, s.DiscountEur, s.Quantity,
    -- ROAS = Umsatz / Kosten
    CASE WHEN ISNULL(c.CostEur, 0) > 0
        THEN s.RevenueEur / c.CostEur ELSE NULL
    END AS ROAS,
    -- Campaign Profit = Umsatz - Kosten - Discount
    (s.RevenueEur - ISNULL(c.CostEur, 0) - s.DiscountEur) AS CampaignProfit
FROM SalesAgg s
LEFT JOIN CostsAgg c ON s.IdCalmonthStd = c.IdCalmonthStd
    AND s.ID_STORE = c.ID_STORE AND s.ID_CAMPAIGN = c.ID_CAMPAIGN;
```

---

## 4.5 Export- und Reporting-View

### 4.5.1 View V_LIST_G18_BENCHMARK_EXPORT_MONTHLY

Standardisierte Export-Sicht für Reporting und Dashboards. Enthält alle relevanten KPIs inkl. EBIT für den monatlichen Filialvergleich.

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY (
    Monat, Filialgruppe, IdStore, UmsatzEur, BruttogewinnEur, WareneinsatzEur,
    GesamtkostenEur, HumanResourcesEur, FacilityManagementEur, LogisticsEur,
    MarketingEur, EbitEur, NettogewinnEur, BruttogewinnMargeProzent,
    NettogewinnMargeProzent
)
AS
SELECT
    k.IdCalmonthStd AS Monat,
    k.StoreName AS Filialgruppe,
    k.IdStore,
    ROUND(k.TotalRevenueEur, 2) AS UmsatzEur,
    ROUND(k.TotalGrossProfitEur, 2) AS BruttogewinnEur,
    ROUND(k.TotalRevenueEur - k.TotalGrossProfitEur, 2) AS WareneinsatzEur,
    ROUND(k.TotalCostsEur, 2) AS GesamtkostenEur,
    ROUND(k.HumanResourcesEur, 2) AS HumanResourcesEur,
    ROUND(k.FacilityManagementEur, 2) AS FacilityManagementEur,
    ROUND(k.LogisticsEur, 2) AS LogisticsEur,
    ROUND(k.MarketingEur, 2) AS MarketingEur,
    -- EBIT = Bruttogewinn - OPEX (F12: EBIT-Marge)
    ROUND(k.TotalGrossProfitEur - k.TotalCostsEur, 2) AS EbitEur,
    ROUND(k.NetProfitEur, 2) AS NettogewinnEur,
    ROUND(k.GrossProfitMarginPct, 2) AS BruttogewinnMargeProzent,
    ROUND(k.NetProfitMarginPct, 2) AS NettogewinnMargeProzent
FROM list_views.V_LIST_G18_BENCHMARK_KPI k;
```

---

## 4.6 Store Details View (Flächenproduktivität)

### 4.6.1 View V_LIST_G18_STORE_DETAILS

Store-Stammdaten mit Fläche (m²), Mietkosten und Umsatz-Effizienz. Berechnet die Flächenproduktivität (Umsatz pro m²) gemäß Anforderung F08.

**SQL-Definition:**

```sql
CREATE OR ALTER VIEW list_views.V_LIST_G18_STORE_DETAILS (
    IdCalmonthStd, IdStore, StoreName, StoreM2, Mietkosten,
    TotalDiscount, Umsatz, UmsatzProM2
)
AS
WITH SalesAgg AS (
    SELECT
        FORMAT(ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd, ID_STORE,
        MAX(StoreName) AS StoreName, MAX(StoreM2) AS StoreM2,
        SUM(DiscountEUR) AS TotalDiscount,
        SUM(RevenueEUR - DiscountEUR) AS Umsatz
    FROM dbo.V_LIST_MONTHLY_SALES
    GROUP BY FORMAT(ID_CALMONTH, 'yyyy-MM'), ID_STORE
),
CostsAgg AS (
    SELECT
        FORMAT(ID_CALMONTH, 'yyyy-MM') AS IdCalmonthStd, ID_STORE,
        SUM(WertEUR) AS Mietkosten
    FROM dbo.V_LIST_MONTHLY_COSTS
    WHERE Kostenkategorie = 'Monthly Rent'
    GROUP BY FORMAT(ID_CALMONTH, 'yyyy-MM'), ID_STORE
)
SELECT
    s.IdCalmonthStd, s.ID_STORE AS IdStore, s.StoreName, s.StoreM2,
    ISNULL(c.Mietkosten, 0) AS Mietkosten, s.TotalDiscount, s.Umsatz,
    CASE WHEN s.StoreM2 > 0 THEN s.Umsatz / s.StoreM2 ELSE 0 END AS UmsatzProM2
FROM SalesAgg s
LEFT JOIN CostsAgg c ON s.IdCalmonthStd = c.IdCalmonthStd
    AND s.ID_STORE = c.ID_STORE;
```

---

## View-Übersicht

| Layer | View-Name | Zweck | Fachkonzept |
|-------|-----------|-------|-------------|
| 1 - Standardisierung | V_LIST_G18_BENCHMARK_SALES_DETAIL | Monatsformat, Kategorie-Mapping | - |
| 2 - Aggregation | V_LIST_G18_BENCHMARK_SALES_AGG | Verkaufs-Aggregation | F01, F05 |
| 2 - Aggregation | V_LIST_G18_BENCHMARK_COSTS_AGG | Kosten-Aggregation | F02 |
| 3 - KPI | V_LIST_G18_BENCHMARK_KPI | Marge, Gewinn | F03, F09 |
| 3 - Marketing | V_LIST_G18_MARKETING_KPI_MONTHLY | ROAS, CPA | F06 |
| 3 - Marketing | V_LIST_G18_MARKETING_BY_CAMPAIGN | Kampagnen-Analyse | F06 |
| 4 - Export | V_LIST_G18_BENCHMARK_EXPORT_MONTHLY | Dashboard-Export, EBIT | F04, F07, F12 |
| 4 - Details | V_LIST_G18_STORE_DETAILS | Flächenproduktivität | F08 |

---

## Hinweis zur Filterung (F13)

Die Views enthalten **keine hardcodierten Store-Filter**. Die Filterung erfolgt dynamisch in der Applikation via:

```sql
WHERE IdStore IN (51003003, 51005005, 51014014)
```

Dies ermöglicht:
- Flexible Auswahl der Filialen im Dashboard
- Einfache Erweiterung um weitere Standorte
- Konsistente Datengrundlage in der Datenbank
