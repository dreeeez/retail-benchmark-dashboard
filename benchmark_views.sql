-- ============================================================
-- BENCHMARK VIEWS - Systemkonzept Phase 4
-- Gruppe 18: Marco, Harun, Duy
-- Benchmarking-System für Filialen Rosenheim & Freiburg/Karlsruhe
-- ============================================================

-- ============================================================
-- 4.1 STANDARDISIERUNGS- UND BEREINIGUNGS-VIEWS
-- ============================================================

-- 4.1.1 View V_BENCHMARK_SALES_STD
-- Diese View vereinheitlicht das Monatsformat, reichert Filialstammdaten an
-- und weist Artikel Benchmark-Kategorien zu.
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_SALES_STD', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_SALES_STD;
GO

CREATE VIEW dbo.V_BENCHMARK_SALES_STD AS
SELECT
    s.ID_STORE,
    so.STORE_LOCATION AS STORE_NAME,
    s.ID_CALMONTH,
    FORMAT(s.ID_CALMONTH, 'yyyy-MM') AS ID_CALMONTH_STD,
    s.ID_MATERIAL,
    m.MAT_NR,
    m.MAT_DESCR,
    s.ID_CATEGORY,
    pc.CATEGORY,
    pc.PRODUCT_LINE,
    -- Benchmark-Kategorie Zuordnung
    CASE
        WHEN pc.PRODUCT_LINE = 'E-Bike' AND pc.CATEGORY = 'Mountainbike' THEN 'E-MTB'
        WHEN pc.PRODUCT_LINE = 'E-Bike' AND pc.CATEGORY = 'Citybike' THEN 'E-City'
        WHEN pc.PRODUCT_LINE = 'E-Bike' AND pc.CATEGORY = 'Trekkingrad' THEN 'E-Trekking'
        WHEN pc.PRODUCT_LINE = 'BioBike' AND pc.CATEGORY = 'Mountainbike' THEN 'MTB'
        WHEN pc.PRODUCT_LINE = 'BioBike' AND pc.CATEGORY = 'Citybike' THEN 'City'
        WHEN pc.PRODUCT_LINE = 'BioBike' AND pc.CATEGORY = 'Trekkingrad' THEN 'Trekking'
        WHEN pc.CATEGORY = 'Kinderrad' THEN 'Kinder'
        WHEN pc.CATEGORY = 'Rennrad' THEN 'Rennrad'
        ELSE 'Sonstige'
    END AS BENCHMARK_CATEGORY,
    s.ID_SEGMENT,
    ps.SEGMENT AS PRICE_SEGMENT,
    s.ID_EMPLOYEE,
    s.ID_CAMPAIGN,
    s.SALES_AMOUNT,
    s.TRANSFER_PRICE_EUR,
    s.SALES_PRICE_EUR,
    s.DISCOUNT_PCT,
    s.REVENUE,
    s.DISCOUNT_IN_EUR,
    s.GROSS_PROFIT_EUR
FROM dbo.T_ETL_MONTHLY_SALES s
INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
INNER JOIN dbo.T_MATERIAL m ON s.ID_MATERIAL = m.ID_MAT
INNER JOIN dbo.T_PRODUCT_CATEGORY pc ON s.ID_CATEGORY = pc.ID_CATEGORY
INNER JOIN dbo.T_PRICE_SEGMENT ps ON s.ID_SEGMENT = ps.ID_SEGMENT
WHERE so.STORE_LOCATION IN ('Rosenheim', 'Freiburg', 'Karlsruhe', 'Freiburg/Karlsruhe');
GO

-- 4.1.2 View V_BENCHMARK_SALES_ERRORS (optional)
-- Zeigt Datensätze mit fehlerhaften Werten
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_SALES_ERRORS', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_SALES_ERRORS;
GO

CREATE VIEW dbo.V_BENCHMARK_SALES_ERRORS AS
SELECT
    s.*,
    CASE
        WHEN s.REVENUE <= 0 THEN 'Umsatz <= 0'
        WHEN s.GROSS_PROFIT_EUR < 0 THEN 'Negativer Bruttogewinn'
        WHEN s.SALES_AMOUNT <= 0 THEN 'Verkaufsmenge <= 0'
        ELSE 'Unbekannter Fehler'
    END AS ERROR_TYPE
FROM dbo.V_BENCHMARK_SALES_STD s
WHERE s.REVENUE <= 0
   OR s.GROSS_PROFIT_EUR < 0
   OR s.SALES_AMOUNT <= 0;
GO

-- ============================================================
-- 4.2 AGGREGATIONS-VIEWS
-- ============================================================

-- 4.2.1 View V_BENCHMARK_SALES_AGG
-- Aggregation der Verkaufsdaten je Monat, Filiale, Kategorie
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_SALES_AGG', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_SALES_AGG;
GO

CREATE VIEW dbo.V_BENCHMARK_SALES_AGG AS
SELECT
    ID_STORE,
    STORE_NAME,
    ID_CALMONTH,
    ID_CALMONTH_STD,
    BENCHMARK_CATEGORY,
    COUNT(*) AS TRANSACTION_COUNT,
    SUM(SALES_AMOUNT) AS TOTAL_SALES_AMOUNT,
    SUM(REVENUE) AS TOTAL_REVENUE_EUR,
    SUM(GROSS_PROFIT_EUR) AS TOTAL_GROSS_PROFIT_EUR,
    SUM(TRANSFER_PRICE_EUR * SALES_AMOUNT) AS TOTAL_TRANSFER_COST_EUR,
    SUM(DISCOUNT_IN_EUR) AS TOTAL_DISCOUNT_EUR,
    AVG(SALES_PRICE_EUR) AS AVG_SALES_PRICE_EUR,
    AVG(DISCOUNT_PCT) AS AVG_DISCOUNT_PCT
FROM dbo.V_BENCHMARK_SALES_STD
GROUP BY
    ID_STORE,
    STORE_NAME,
    ID_CALMONTH,
    ID_CALMONTH_STD,
    BENCHMARK_CATEGORY;
GO

-- 4.2.2 View V_BENCHMARK_COSTS_AGG
-- Aggregation der Kosten je Monat, Filiale und Kostenart
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_COSTS_AGG', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_COSTS_AGG;
GO

CREATE VIEW dbo.V_BENCHMARK_COSTS_AGG AS
SELECT
    c.ID_STORE,
    so.STORE_LOCATION AS STORE_NAME,
    c.ID_CALMONTH,
    FORMAT(c.ID_CALMONTH, 'yyyy-MM') AS ID_CALMONTH_STD,
    cr.COST_CATEGORY,
    SUM(c.VALUE) AS TOTAL_COST_EUR
FROM dbo.T_ETL_MONTHLY_COSTS c
INNER JOIN dbo.T_COST_RECORD cr
    ON c.ID_GAME = cr.ID_GAME
    AND c.ID_STORE = cr.ID_STORE
    AND c.ID_COST_RECORD = cr.ID_COST_RECORD
INNER JOIN dbo.T_SALESORG so ON c.ID_STORE = so.SALESORG_ID
WHERE so.STORE_LOCATION IN ('Rosenheim', 'Freiburg', 'Karlsruhe', 'Freiburg/Karlsruhe')
GROUP BY
    c.ID_STORE,
    so.STORE_LOCATION,
    c.ID_CALMONTH,
    cr.COST_CATEGORY;
GO

-- 4.2.3 View V_BENCHMARK_COSTS_TOTAL
-- Gesamtkosten je Monat und Filiale
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_COSTS_TOTAL', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_COSTS_TOTAL;
GO

CREATE VIEW dbo.V_BENCHMARK_COSTS_TOTAL AS
SELECT
    ID_STORE,
    STORE_NAME,
    ID_CALMONTH,
    ID_CALMONTH_STD,
    SUM(CASE WHEN COST_CATEGORY LIKE '%Personal%' OR COST_CATEGORY LIKE '%Gehalt%' OR COST_CATEGORY LIKE '%Lohn%'
        THEN TOTAL_COST_EUR ELSE 0 END) AS PERSONNEL_COSTS_EUR,
    SUM(CASE WHEN COST_CATEGORY LIKE '%Betrieb%' OR COST_CATEGORY LIKE '%Miete%' OR COST_CATEGORY LIKE '%Energie%'
        THEN TOTAL_COST_EUR ELSE 0 END) AS OPERATING_COSTS_EUR,
    SUM(CASE WHEN COST_CATEGORY LIKE '%Marketing%' OR COST_CATEGORY LIKE '%Werbung%'
        THEN TOTAL_COST_EUR ELSE 0 END) AS MARKETING_COSTS_EUR,
    SUM(TOTAL_COST_EUR) AS TOTAL_COSTS_EUR
FROM dbo.V_BENCHMARK_COSTS_AGG
GROUP BY
    ID_STORE,
    STORE_NAME,
    ID_CALMONTH,
    ID_CALMONTH_STD;
GO

-- 4.2.4 View V_BENCHMARK_HEADCOUNT
-- Mitarbeiteranzahl je Filiale
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_HEADCOUNT', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_HEADCOUNT;
GO

CREATE VIEW dbo.V_BENCHMARK_HEADCOUNT AS
SELECT
    e.ID_SALESORG AS ID_STORE,
    so.STORE_LOCATION AS STORE_NAME,
    COUNT(e.ID_EMP) AS EMPLOYEE_COUNT
FROM dbo.T_EMPLOYEE e
INNER JOIN dbo.T_SALESORG so ON e.ID_SALESORG = so.SALESORG_ID
WHERE e.DELETE_YN = 0
  AND so.STORE_LOCATION IN ('Rosenheim', 'Freiburg', 'Karlsruhe', 'Freiburg/Karlsruhe')
GROUP BY
    e.ID_SALESORG,
    so.STORE_LOCATION;
GO

-- ============================================================
-- 4.3 KPI-/BENCHMARK-VIEW
-- ============================================================

-- 4.3.1 View V_BENCHMARK_KPI
-- Zentrale View für das Datenobjekt "Filialkennzahlen"
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_KPI', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_KPI;
GO

CREATE VIEW dbo.V_BENCHMARK_KPI AS
SELECT
    sa.ID_STORE,
    sa.STORE_NAME,
    sa.ID_CALMONTH,
    sa.ID_CALMONTH_STD,
    sa.BENCHMARK_CATEGORY,

    -- Basisgroessen
    sa.TOTAL_SALES_AMOUNT,
    sa.TOTAL_REVENUE_EUR AS REVENUE_EUR,
    sa.TOTAL_GROSS_PROFIT_EUR AS GROSS_PROFIT_EUR,
    sa.TOTAL_TRANSFER_COST_EUR AS TRANSFER_COST_EUR,
    sa.TOTAL_DISCOUNT_EUR AS DISCOUNT_EUR,
    sa.AVG_SALES_PRICE_EUR,

    -- Kosten (auf Monat/Filiale-Ebene, anteilig auf Kategorie verteilt)
    ISNULL(ct.PERSONNEL_COSTS_EUR, 0) AS PERSONNEL_COSTS_EUR,
    ISNULL(ct.OPERATING_COSTS_EUR, 0) AS OPERATING_COSTS_EUR,
    ISNULL(ct.MARKETING_COSTS_EUR, 0) AS MARKETING_COSTS_EUR,
    ISNULL(ct.TOTAL_COSTS_EUR, 0) AS TOTAL_COSTS_EUR,

    -- Gesamtkosten inkl. Wareneinsatz
    sa.TOTAL_TRANSFER_COST_EUR + ISNULL(ct.TOTAL_COSTS_EUR, 0) AS TOTAL_EXPENSES_EUR,

    -- Nettogewinn
    sa.TOTAL_GROSS_PROFIT_EUR - ISNULL(ct.TOTAL_COSTS_EUR, 0) AS NET_PROFIT_EUR,

    -- Mitarbeiter
    ISNULL(hc.EMPLOYEE_COUNT, 0) AS EMPLOYEE_COUNT,

    -- ============================================================
    -- KENNZAHLEN (KPIs)
    -- ============================================================

    -- Bruttogewinn-Marge (%)
    CASE
        WHEN sa.TOTAL_REVENUE_EUR > 0
        THEN ROUND((sa.TOTAL_GROSS_PROFIT_EUR / sa.TOTAL_REVENUE_EUR) * 100, 2)
        ELSE NULL
    END AS GROSS_MARGIN_PCT,

    -- Nettogewinn-Marge (%)
    CASE
        WHEN sa.TOTAL_REVENUE_EUR > 0
        THEN ROUND(((sa.TOTAL_GROSS_PROFIT_EUR - ISNULL(ct.TOTAL_COSTS_EUR, 0)) / sa.TOTAL_REVENUE_EUR) * 100, 2)
        ELSE NULL
    END AS NET_MARGIN_PCT,

    -- Betriebskosten-Quote (%)
    CASE
        WHEN sa.TOTAL_REVENUE_EUR > 0
        THEN ROUND((ISNULL(ct.OPERATING_COSTS_EUR, 0) / sa.TOTAL_REVENUE_EUR) * 100, 2)
        ELSE NULL
    END AS OPERATING_COST_RATIO_PCT,

    -- Personalkosten-Anteil (%)
    CASE
        WHEN sa.TOTAL_REVENUE_EUR > 0
        THEN ROUND((ISNULL(ct.PERSONNEL_COSTS_EUR, 0) / sa.TOTAL_REVENUE_EUR) * 100, 2)
        ELSE NULL
    END AS PERSONNEL_COST_RATIO_PCT,

    -- Umsatz pro Mitarbeiter
    CASE
        WHEN ISNULL(hc.EMPLOYEE_COUNT, 0) > 0
        THEN ROUND(sa.TOTAL_REVENUE_EUR / hc.EMPLOYEE_COUNT, 2)
        ELSE NULL
    END AS REVENUE_PER_EMPLOYEE,

    -- Durchschnittlicher Rabatt (%)
    sa.AVG_DISCOUNT_PCT AS AVG_DISCOUNT_PCT

FROM dbo.V_BENCHMARK_SALES_AGG sa
LEFT JOIN dbo.V_BENCHMARK_COSTS_TOTAL ct
    ON sa.ID_STORE = ct.ID_STORE
    AND sa.ID_CALMONTH = ct.ID_CALMONTH
LEFT JOIN dbo.V_BENCHMARK_HEADCOUNT hc
    ON sa.ID_STORE = hc.ID_STORE;
GO

-- ============================================================
-- 4.4 VERGLEICHS-VIEW (FILIAL-BENCHMARKING)
-- ============================================================

-- 4.4.1 View V_BENCHMARK_STORE_COMPARISON
-- Vergleich der Filialen Freiburg/Karlsruhe und Rosenheim je Monat und Kategorie
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_STORE_COMPARISON', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_STORE_COMPARISON;
GO

CREATE VIEW dbo.V_BENCHMARK_STORE_COMPARISON AS
WITH RosenheimData AS (
    SELECT
        ID_CALMONTH,
        ID_CALMONTH_STD,
        BENCHMARK_CATEGORY,
        REVENUE_EUR AS ROS_REVENUE_EUR,
        GROSS_PROFIT_EUR AS ROS_GROSS_PROFIT_EUR,
        NET_PROFIT_EUR AS ROS_NET_PROFIT_EUR,
        TOTAL_SALES_AMOUNT AS ROS_SALES_AMOUNT,
        GROSS_MARGIN_PCT AS ROS_GROSS_MARGIN_PCT,
        NET_MARGIN_PCT AS ROS_NET_MARGIN_PCT,
        OPERATING_COST_RATIO_PCT AS ROS_OPERATING_COST_RATIO_PCT,
        PERSONNEL_COST_RATIO_PCT AS ROS_PERSONNEL_COST_RATIO_PCT,
        REVENUE_PER_EMPLOYEE AS ROS_REVENUE_PER_EMPLOYEE
    FROM dbo.V_BENCHMARK_KPI
    WHERE STORE_NAME = 'Rosenheim'
),
FreiburgData AS (
    SELECT
        ID_CALMONTH,
        ID_CALMONTH_STD,
        BENCHMARK_CATEGORY,
        REVENUE_EUR AS FRK_REVENUE_EUR,
        GROSS_PROFIT_EUR AS FRK_GROSS_PROFIT_EUR,
        NET_PROFIT_EUR AS FRK_NET_PROFIT_EUR,
        TOTAL_SALES_AMOUNT AS FRK_SALES_AMOUNT,
        GROSS_MARGIN_PCT AS FRK_GROSS_MARGIN_PCT,
        NET_MARGIN_PCT AS FRK_NET_MARGIN_PCT,
        OPERATING_COST_RATIO_PCT AS FRK_OPERATING_COST_RATIO_PCT,
        PERSONNEL_COST_RATIO_PCT AS FRK_PERSONNEL_COST_RATIO_PCT,
        REVENUE_PER_EMPLOYEE AS FRK_REVENUE_PER_EMPLOYEE
    FROM dbo.V_BENCHMARK_KPI
    WHERE STORE_NAME IN ('Freiburg', 'Karlsruhe', 'Freiburg/Karlsruhe')
)
SELECT
    COALESCE(r.ID_CALMONTH, f.ID_CALMONTH) AS ID_CALMONTH,
    COALESCE(r.ID_CALMONTH_STD, f.ID_CALMONTH_STD) AS ID_CALMONTH_STD,
    COALESCE(r.BENCHMARK_CATEGORY, f.BENCHMARK_CATEGORY) AS BENCHMARK_CATEGORY,

    -- Rosenheim Werte
    ISNULL(r.ROS_REVENUE_EUR, 0) AS ROS_REVENUE_EUR,
    ISNULL(r.ROS_GROSS_PROFIT_EUR, 0) AS ROS_GROSS_PROFIT_EUR,
    ISNULL(r.ROS_NET_PROFIT_EUR, 0) AS ROS_NET_PROFIT_EUR,
    ISNULL(r.ROS_SALES_AMOUNT, 0) AS ROS_SALES_AMOUNT,
    r.ROS_GROSS_MARGIN_PCT,
    r.ROS_NET_MARGIN_PCT,

    -- Freiburg/Karlsruhe Werte
    ISNULL(f.FRK_REVENUE_EUR, 0) AS FRK_REVENUE_EUR,
    ISNULL(f.FRK_GROSS_PROFIT_EUR, 0) AS FRK_GROSS_PROFIT_EUR,
    ISNULL(f.FRK_NET_PROFIT_EUR, 0) AS FRK_NET_PROFIT_EUR,
    ISNULL(f.FRK_SALES_AMOUNT, 0) AS FRK_SALES_AMOUNT,
    f.FRK_GROSS_MARGIN_PCT,
    f.FRK_NET_MARGIN_PCT,

    -- Differenzen (Rosenheim - Freiburg/Karlsruhe)
    ISNULL(r.ROS_REVENUE_EUR, 0) - ISNULL(f.FRK_REVENUE_EUR, 0) AS DIFF_REVENUE_EUR,
    ISNULL(r.ROS_GROSS_PROFIT_EUR, 0) - ISNULL(f.FRK_GROSS_PROFIT_EUR, 0) AS DIFF_GROSS_PROFIT_EUR,
    ISNULL(r.ROS_NET_PROFIT_EUR, 0) - ISNULL(f.FRK_NET_PROFIT_EUR, 0) AS DIFF_NET_PROFIT_EUR,
    ISNULL(r.ROS_SALES_AMOUNT, 0) - ISNULL(f.FRK_SALES_AMOUNT, 0) AS DIFF_SALES_AMOUNT,
    ISNULL(r.ROS_GROSS_MARGIN_PCT, 0) - ISNULL(f.FRK_GROSS_MARGIN_PCT, 0) AS DIFF_GROSS_MARGIN_PCT,
    ISNULL(r.ROS_NET_MARGIN_PCT, 0) - ISNULL(f.FRK_NET_MARGIN_PCT, 0) AS DIFF_NET_MARGIN_PCT,

    -- Prozentuale Abweichung Umsatz
    CASE
        WHEN ISNULL(f.FRK_REVENUE_EUR, 0) > 0
        THEN ROUND(((ISNULL(r.ROS_REVENUE_EUR, 0) - ISNULL(f.FRK_REVENUE_EUR, 0)) / f.FRK_REVENUE_EUR) * 100, 2)
        ELSE NULL
    END AS REVENUE_DIFF_PCT

FROM RosenheimData r
FULL OUTER JOIN FreiburgData f
    ON r.ID_CALMONTH = f.ID_CALMONTH
    AND r.BENCHMARK_CATEGORY = f.BENCHMARK_CATEGORY;
GO

-- ============================================================
-- 4.5 EXPORT- UND REPORTING-VIEW
-- ============================================================

-- 4.5.1 View V_BENCHMARK_EXPORT_MONTHLY
-- Standardisierte Export-Sicht für Reporting und Dashboards
-- ============================================================
IF OBJECT_ID('dbo.V_BENCHMARK_EXPORT_MONTHLY', 'V') IS NOT NULL
    DROP VIEW dbo.V_BENCHMARK_EXPORT_MONTHLY;
GO

CREATE VIEW dbo.V_BENCHMARK_EXPORT_MONTHLY AS
SELECT
    -- Dimensionen
    ID_STORE,
    STORE_NAME,
    ID_CALMONTH,
    ID_CALMONTH_STD,
    YEAR(ID_CALMONTH) AS YEAR,
    MONTH(ID_CALMONTH) AS MONTH,
    DATENAME(MONTH, ID_CALMONTH) AS MONTH_NAME,
    BENCHMARK_CATEGORY,

    -- Basisgroessen
    TOTAL_SALES_AMOUNT,
    REVENUE_EUR,
    GROSS_PROFIT_EUR,
    TRANSFER_COST_EUR,
    DISCOUNT_EUR,
    AVG_SALES_PRICE_EUR,

    -- Kosten
    PERSONNEL_COSTS_EUR,
    OPERATING_COSTS_EUR,
    MARKETING_COSTS_EUR,
    TOTAL_COSTS_EUR,
    TOTAL_EXPENSES_EUR,

    -- Gewinn
    NET_PROFIT_EUR,

    -- Mitarbeiter
    EMPLOYEE_COUNT,

    -- KPIs
    GROSS_MARGIN_PCT,
    NET_MARGIN_PCT,
    OPERATING_COST_RATIO_PCT,
    PERSONNEL_COST_RATIO_PCT,
    REVENUE_PER_EMPLOYEE,
    AVG_DISCOUNT_PCT,

    -- Metadaten
    GETDATE() AS EXPORT_DATE

FROM dbo.V_BENCHMARK_KPI;
GO

-- ============================================================
-- ROLLEN UND BERECHTIGUNGEN
-- ============================================================

-- Hinweis: Die folgenden Befehle muessen mit entsprechenden Rechten ausgefuehrt werden

-- Rolle: Management
-- GRANT SELECT ON dbo.V_BENCHMARK_KPI TO [Management_Role];
-- GRANT SELECT ON dbo.V_BENCHMARK_STORE_COMPARISON TO [Management_Role];
-- GRANT SELECT ON dbo.V_BENCHMARK_EXPORT_MONTHLY TO [Management_Role];

-- Rolle: Controlling
-- GRANT SELECT ON dbo.V_BENCHMARK_KPI TO [Controlling_Role];
-- GRANT SELECT ON dbo.V_BENCHMARK_STORE_COMPARISON TO [Controlling_Role];
-- GRANT SELECT ON dbo.V_BENCHMARK_EXPORT_MONTHLY TO [Controlling_Role];
-- GRANT SELECT ON dbo.V_BENCHMARK_SALES_AGG TO [Controlling_Role];
-- GRANT SELECT ON dbo.V_BENCHMARK_COSTS_AGG TO [Controlling_Role];
-- GRANT SELECT ON dbo.V_BENCHMARK_SALES_ERRORS TO [Controlling_Role];

-- Rolle: Vertrieb
-- GRANT SELECT ON dbo.V_BENCHMARK_KPI TO [Vertrieb_Role];

PRINT 'Alle Benchmark-Views wurden erfolgreich erstellt.';
GO
