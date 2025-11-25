-- ============================================================================
-- BENCHMARKING SYSTEM - ACTION PLAN & DISCOVERY QUERIES
-- ============================================================================
-- Project: Rosenheim & Freiburg Branch Benchmarking
-- Group: 18 (Marco, Harun, Duy)
-- Date: 2025-11-25
-- Purpose: Execute these queries to gather information needed for implementation
-- ============================================================================

-- ============================================================================
-- SECTION 1: DATA DISCOVERY QUERIES
-- Run these first to understand the actual data in the database
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1.1: Identify Store IDs for Rosenheim and Freiburg
-- ----------------------------------------------------------------------------
SELECT
    SALESORG_ID,
    STORE_LOCATION,
    INHABITANTS,
    MARKETSHARE
FROM dbo.T_SALESORG
WHERE STORE_LOCATION IN ('Rosenheim', 'Freiburg')
ORDER BY STORE_LOCATION;

-- Expected: 2 rows showing the ID and details for each branch
-- Action: Note the SALESORG_ID values for use in filtering


-- ----------------------------------------------------------------------------
-- 1.2: Discover Cost Categories
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    COST_CATEGORY,
    COUNT(*) as record_count
FROM dbo.T_COST_RECORD
GROUP BY COST_CATEGORY
ORDER BY COST_CATEGORY;

-- Purpose: Identify actual cost category names for mapping to:
--   - Betriebskosten (Operating Costs)
--   - Personalkosten (Personnel Costs)
--   - Zusätzliche Beschaffungskosten (Procurement Costs)
-- Action: Create mapping based on results


-- ----------------------------------------------------------------------------
-- 1.3: Check Available Months in Sales Data
-- ----------------------------------------------------------------------------
SELECT
    YEAR(ID_CALMONTH) as year,
    MONTH(ID_CALMONTH) as month,
    ID_STORE,
    so.STORE_LOCATION,
    COUNT(*) as transaction_count,
    SUM(REVENUE) as total_revenue
FROM dbo.T_ETL_MONTHLY_SALES s
LEFT JOIN dbo.T_SALESORG so ON so.SALESORG_ID = s.ID_STORE
WHERE YEAR(ID_CALMONTH) = 2026
GROUP BY
    YEAR(ID_CALMONTH),
    MONTH(ID_CALMONTH),
    ID_STORE,
    so.STORE_LOCATION
ORDER BY
    year, month, STORE_LOCATION;

-- Expected: 24 rows (12 months × 2 stores)
-- Action: Verify complete data for Jan-Dec 2026 (Acceptance Criterion SPC03)


-- ----------------------------------------------------------------------------
-- 1.4: Check Product Categories
-- ----------------------------------------------------------------------------
SELECT
    pc.ID_CATEGORY,
    pc.CATEGORY,
    pc.PRODUCT_LINE,
    COUNT(DISTINCT m.ID_MAT) as material_count
FROM dbo.T_PRODUCT_CATEGORY pc
LEFT JOIN dbo.T_MATERIAL m ON m.ID_CATEGORY = pc.ID_CATEGORY
GROUP BY
    pc.ID_CATEGORY,
    pc.CATEGORY,
    pc.PRODUCT_LINE
ORDER BY
    pc.CATEGORY;

-- Purpose: Understand category structure for mapping to benchmark categories
-- Action: Define mapping to E-Bike, MTB, City/Trekking, Kinder, Sonstige


-- ----------------------------------------------------------------------------
-- 1.5: Analyze Employee Distribution
-- ----------------------------------------------------------------------------
SELECT
    e.ID_SALESORG,
    so.STORE_LOCATION,
    COUNT(*) as employee_count,
    AVG(e.EMP_SALARY_OFFERED) as avg_salary,
    AVG(e.EMP_COMMISSION) as avg_commission_pct
FROM dbo.T_EMPLOYEE e
LEFT JOIN dbo.T_SALESORG so ON so.SALESORG_ID = e.ID_SALESORG
WHERE e.DELETE_YN = 0
GROUP BY
    e.ID_SALESORG,
    so.STORE_LOCATION
ORDER BY
    so.STORE_LOCATION;

-- Purpose: Understand current employee headcount per branch
-- Action: Decide on headcount calculation strategy


-- ----------------------------------------------------------------------------
-- 1.6: Check Social Cost Percentages
-- ----------------------------------------------------------------------------
SELECT
    EMP_SOCIALCOSTS_PCT,
    COUNT(*) as applicant_count
FROM dbo.T_APPLICANTS
GROUP BY EMP_SOCIALCOSTS_PCT
ORDER BY EMP_SOCIALCOSTS_PCT;

-- Purpose: Identify social cost factors for personnel cost calculations
-- Action: Determine if all employees have same social cost % or varies


-- ----------------------------------------------------------------------------
-- 1.7: Verify Material Descriptions for Category Mapping
-- ----------------------------------------------------------------------------
SELECT TOP 50
    m.ID_MAT,
    m.MAT_NR,
    m.MAT_DESCR,
    pc.CATEGORY,
    ps.SEGMENT
FROM dbo.T_MATERIAL m
LEFT JOIN dbo.T_PRODUCT_CATEGORY pc ON pc.ID_CATEGORY = m.ID_CATEGORY
LEFT JOIN dbo.T_PRICE_SEGMENT ps ON ps.ID_SEGMENT = m.ID_SEGMENT
ORDER BY
    pc.CATEGORY,
    m.MAT_DESCR;

-- Purpose: Verify material descriptions for LIKE pattern matching
-- Action: Refine CASE statement patterns for benchmark category assignment


-- ============================================================================
-- SECTION 2: DATA QUALITY CHECKS (Before Implementation)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1: Check for Missing Store References
-- ----------------------------------------------------------------------------
SELECT
    'Sales with missing store' as issue_type,
    COUNT(*) as issue_count
FROM dbo.T_ETL_MONTHLY_SALES
WHERE ID_STORE NOT IN (SELECT SALESORG_ID FROM dbo.T_SALESORG)

UNION ALL

SELECT
    'Costs with missing store' as issue_type,
    COUNT(*) as issue_count
FROM dbo.T_ETL_MONTHLY_COSTS
WHERE ID_STORE NOT IN (SELECT SALESORG_ID FROM dbo.T_SALESORG);

-- Expected: 0 issues
-- Action: Escalate to data provider if issues found


-- ----------------------------------------------------------------------------
-- 2.2: Identify Negative or Zero Revenue Records (TF03)
-- ----------------------------------------------------------------------------
SELECT
    ID_STORE,
    so.STORE_LOCATION,
    ID_CALMONTH,
    ID_MATERIAL,
    REVENUE,
    GROSS_PROFIT_EUR,
    CASE
        WHEN REVENUE <= 0 THEN 'Zero/Negative Revenue'
        WHEN GROSS_PROFIT_EUR < 0 THEN 'Negative Gross Profit'
        ELSE 'Other Issue'
    END as issue_type
FROM dbo.T_ETL_MONTHLY_SALES s
LEFT JOIN dbo.T_SALESORG so ON so.SALESORG_ID = s.ID_STORE
WHERE REVENUE <= 0 OR GROSS_PROFIT_EUR < 0
ORDER BY
    ID_CALMONTH,
    STORE_LOCATION;

-- Purpose: Identify data quality issues for V_BENCHMARK_SALES_ERRORS
-- Action: Document findings, decide on handling strategy


-- ----------------------------------------------------------------------------
-- 2.3: Check for Missing Material Data
-- ----------------------------------------------------------------------------
SELECT
    'Sales records missing material' as issue_type,
    COUNT(*) as issue_count
FROM dbo.T_ETL_MONTHLY_SALES
WHERE ID_MATERIAL NOT IN (SELECT ID_MAT FROM dbo.T_MATERIAL);

-- Expected: 0 or low count
-- Action: Handle in views with LEFT JOIN


-- ----------------------------------------------------------------------------
-- 2.4: Verify Monthly Data Completeness (SPC03)
-- ----------------------------------------------------------------------------
WITH expected_months AS (
    SELECT 1 as month_num UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL
    SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
    SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
),
expected_stores AS (
    SELECT SALESORG_ID FROM T_SALESORG WHERE STORE_LOCATION IN ('Rosenheim', 'Freiburg')
),
expected_combinations AS (
    SELECT
        s.SALESORG_ID as ID_STORE,
        m.month_num
    FROM expected_stores s
    CROSS JOIN expected_months m
),
actual_data AS (
    SELECT DISTINCT
        ID_STORE,
        MONTH(ID_CALMONTH) as month_num
    FROM T_ETL_MONTHLY_SALES
    WHERE YEAR(ID_CALMONTH) = 2026
)
SELECT
    exp.ID_STORE,
    so.STORE_LOCATION,
    exp.month_num as missing_month
FROM expected_combinations exp
LEFT JOIN actual_data act
    ON act.ID_STORE = exp.ID_STORE
    AND act.month_num = exp.month_num
LEFT JOIN T_SALESORG so ON so.SALESORG_ID = exp.ID_STORE
WHERE act.ID_STORE IS NULL
ORDER BY
    exp.ID_STORE,
    exp.month_num;

-- Expected: 0 rows (all months present)
-- Action: If missing months found, critical blocker - escalate


-- ============================================================================
-- SECTION 3: VALIDATION OF EXISTING VIEW
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1: Test V_BENCHMARK_SALES_AGG (Already Exists)
-- ----------------------------------------------------------------------------
SELECT
    ID_CALMONTH,
    ID_STORE,
    STORE_NAME,
    ID_CATEGORY,
    SALES_AMOUNT,
    REVENUE_EUR,
    GROSS_PROFIT_EUR,
    TRANSFER_COST_EUR,
    AVG_SALES_PRICE_EUR
FROM list_views.V_BENCHMARK_SALES_AGG
WHERE YEAR(ID_CALMONTH) = 2026
    AND STORE_NAME IN ('Rosenheim', 'Freiburg')
ORDER BY
    ID_CALMONTH,
    STORE_NAME,
    ID_CATEGORY;

-- Purpose: Verify existing aggregation view works correctly
-- Expected: Monthly aggregated data per store and category
-- Action: If issues found, may need to recreate view


-- ----------------------------------------------------------------------------
-- 3.2: Validate Aggregation Logic (TF01)
-- ----------------------------------------------------------------------------
-- Compare aggregated revenue with sum of detail records
SELECT
    'Detail Sum' as source,
    ID_STORE,
    ID_CALMONTH,
    ID_CATEGORY,
    SUM(REVENUE) as total_revenue
FROM dbo.T_ETL_MONTHLY_SALES
WHERE YEAR(ID_CALMONTH) = 2026
    AND ID_STORE IN (SELECT SALESORG_ID FROM T_SALESORG WHERE STORE_LOCATION IN ('Rosenheim', 'Freiburg'))
GROUP BY
    ID_STORE,
    ID_CALMONTH,
    ID_CATEGORY

UNION ALL

SELECT
    'Aggregated' as source,
    ID_STORE,
    ID_CALMONTH,
    ID_CATEGORY,
    REVENUE_EUR as total_revenue
FROM list_views.V_BENCHMARK_SALES_AGG
WHERE YEAR(ID_CALMONTH) = 2026

ORDER BY
    ID_STORE,
    ID_CALMONTH,
    ID_CATEGORY,
    source;

-- Purpose: Test Case TF01 - Verify aggregation correctness
-- Expected: Detail Sum = Aggregated for each month/store/category
-- Action: Investigate discrepancies if found


-- ============================================================================
-- SECTION 4: COST ANALYSIS QUERIES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1: Analyze Cost Distribution by Category
-- ----------------------------------------------------------------------------
SELECT
    c.ID_STORE,
    so.STORE_LOCATION,
    cr.COST_CATEGORY,
    COUNT(*) as cost_record_count,
    SUM(c.VALUE) as total_cost_eur
FROM dbo.T_ETL_MONTHLY_COSTS c
LEFT JOIN dbo.T_COST_RECORD cr
    ON cr.ID_COST_RECORD = c.ID_COST_RECORD
    AND cr.ID_STORE = c.ID_STORE
LEFT JOIN dbo.T_SALESORG so ON so.SALESORG_ID = c.ID_STORE
WHERE YEAR(c.ID_CALMONTH) = 2026
GROUP BY
    c.ID_STORE,
    so.STORE_LOCATION,
    cr.COST_CATEGORY
ORDER BY
    so.STORE_LOCATION,
    cr.COST_CATEGORY;

-- Purpose: Understand cost structure for mapping
-- Action: Create mapping for V_BENCHMARK_COSTS_AGG


-- ----------------------------------------------------------------------------
-- 4.2: Check if Personnel Costs are in Cost Table or Need Calculation
-- ----------------------------------------------------------------------------
SELECT
    'Personnel Costs in T_ETL_MONTHLY_COSTS' as check_type,
    COUNT(*) as record_count
FROM dbo.T_ETL_MONTHLY_COSTS c
LEFT JOIN dbo.T_COST_RECORD cr ON cr.ID_COST_RECORD = c.ID_COST_RECORD AND cr.ID_STORE = c.ID_STORE
WHERE cr.COST_CATEGORY LIKE '%personal%'
   OR cr.COST_CATEGORY LIKE '%gehalt%'
   OR cr.COST_CATEGORY LIKE '%lohn%';

-- Purpose: Determine if personnel costs need separate calculation from T_EMPLOYEE
-- Action: If count = 0, must calculate from T_EMPLOYEE + T_APPLICANTS


-- ============================================================================
-- SECTION 5: TEST QUERIES FOR KPI CALCULATIONS (TF02)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 5.1: Manual KPI Calculation for Validation
-- Sample calculation for one month/store for testing
-- ----------------------------------------------------------------------------
DECLARE @test_month DATE = '2026-01-01';
DECLARE @test_store INT = (SELECT TOP 1 SALESORG_ID FROM T_SALESORG WHERE STORE_LOCATION = 'Rosenheim');

SELECT
    'Manual Calculation' as calculation_type,
    @test_month as test_month,
    @test_store as test_store,

    -- Base values
    SUM(REVENUE) as revenue_eur,
    SUM(GROSS_PROFIT_EUR) as gross_profit_eur,

    -- Calculated KPIs
    CASE WHEN SUM(REVENUE) = 0 THEN NULL
         ELSE SUM(GROSS_PROFIT_EUR) * 100.0 / SUM(REVENUE)
    END as gross_margin_pct,

    CASE WHEN SUM(SALES_AMOUNT) = 0 THEN NULL
         ELSE SUM(REVENUE) * 1.0 / SUM(SALES_AMOUNT)
    END as avg_sales_price_eur

FROM dbo.T_ETL_MONTHLY_SALES
WHERE ID_CALMONTH = @test_month
  AND ID_STORE = @test_store;

-- Purpose: Manual calculation for Test Case TF02
-- Action: Compare with values from V_BENCHMARK_KPI once created


-- ============================================================================
-- SECTION 6: HEADCOUNT STRATEGY QUERIES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 6.1: Option A - Calculate Headcount from T_EMPLOYEE per Month
-- ----------------------------------------------------------------------------
SELECT
    e.ID_SALESORG as ID_STORE,
    so.STORE_LOCATION,
    c.ID_CALMONTH,
    COUNT(DISTINCT e.ID_EMP) as employee_count
FROM dbo.T_EMPLOYEE e
LEFT JOIN dbo.T_SALESORG so ON so.SALESORG_ID = e.ID_SALESORG
CROSS JOIN (
    SELECT DISTINCT ID_CALMONTH
    FROM dbo.T_ETL_MONTHLY_SALES
    WHERE YEAR(ID_CALMONTH) = 2026
) c
WHERE e.DELETE_YN = 0
GROUP BY
    e.ID_SALESORG,
    so.STORE_LOCATION,
    c.ID_CALMONTH
ORDER BY
    so.STORE_LOCATION,
    c.ID_CALMONTH;

-- Purpose: Test headcount calculation approach
-- Limitation: Assumes all active employees worked all months
-- Action: Decide if this approach is acceptable or if fixed counts needed


-- ----------------------------------------------------------------------------
-- 6.2: Option C - Proposed Fixed Headcount Table (if needed)
-- ----------------------------------------------------------------------------
-- Example: Create and populate a simple headcount table

/*
CREATE TABLE dbo.T_STORE_HEADCOUNT (
    ID_STORE INT NOT NULL,
    ID_CALMONTH DATE NOT NULL,
    EMPLOYEE_COUNT INT NOT NULL,
    INS_DATE DATETIME NOT NULL DEFAULT GETDATE(),
    INS_USER NVARCHAR(50) NOT NULL DEFAULT SUSER_SNAME(),
    PRIMARY KEY (ID_STORE, ID_CALMONTH)
);

-- Populate with example data (adjust counts as needed)
DECLARE @rosenheim_id INT = (SELECT SALESORG_ID FROM T_SALESORG WHERE STORE_LOCATION = 'Rosenheim');
DECLARE @freiburg_id INT = (SELECT SALESORG_ID FROM T_SALESORG WHERE STORE_LOCATION = 'Freiburg');

WITH months AS (
    SELECT DISTINCT ID_CALMONTH FROM T_ETL_MONTHLY_SALES WHERE YEAR(ID_CALMONTH) = 2026
)
INSERT INTO T_STORE_HEADCOUNT (ID_STORE, ID_CALMONTH, EMPLOYEE_COUNT, INS_USER)
SELECT @rosenheim_id, ID_CALMONTH, 10, 'SYSTEM' FROM months  -- Adjust count
UNION ALL
SELECT @freiburg_id, ID_CALMONTH, 8, 'SYSTEM' FROM months;   -- Adjust count
*/

-- Action: Uncomment and execute if fixed headcount approach is chosen


-- ============================================================================
-- SECTION 7: PERFORMANCE BASELINE (N02)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 7.1: Test Query Performance on Base Tables
-- ----------------------------------------------------------------------------
SET STATISTICS TIME ON;
SET STATISTICS IO ON;

SELECT
    s.ID_STORE,
    so.STORE_LOCATION,
    s.ID_CALMONTH,
    COUNT(*) as record_count,
    SUM(s.REVENUE) as total_revenue
FROM dbo.T_ETL_MONTHLY_SALES s
LEFT JOIN dbo.T_SALESORG so ON so.SALESORG_ID = s.ID_STORE
WHERE YEAR(s.ID_CALMONTH) = 2026
  AND so.STORE_LOCATION IN ('Rosenheim', 'Freiburg')
GROUP BY
    s.ID_STORE,
    so.STORE_LOCATION,
    s.ID_CALMONTH
ORDER BY
    s.ID_CALMONTH,
    so.STORE_LOCATION;

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;

-- Purpose: Baseline performance measurement
-- Target: Should complete in < 5 seconds (N02)
-- Action: If slow, recommend indexes on ID_CALMONTH, ID_STORE


-- ----------------------------------------------------------------------------
-- 7.2: Check Existing Indexes
-- ----------------------------------------------------------------------------
SELECT
    OBJECT_SCHEMA_NAME(i.object_id) as schema_name,
    OBJECT_NAME(i.object_id) as table_name,
    i.name as index_name,
    i.type_desc,
    STRING_AGG(c.name, ', ') as indexed_columns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE OBJECT_NAME(i.object_id) IN ('T_ETL_MONTHLY_SALES', 'T_ETL_MONTHLY_COSTS', 'T_SALESORG', 'T_EMPLOYEE')
GROUP BY
    i.object_id,
    i.name,
    i.type_desc
ORDER BY
    schema_name,
    table_name,
    index_name;

-- Purpose: Identify existing indexes
-- Action: Recommend additional indexes if needed:
--   - T_ETL_MONTHLY_SALES: (ID_CALMONTH, ID_STORE, ID_CATEGORY)
--   - T_ETL_MONTHLY_COSTS: (ID_CALMONTH, ID_STORE, ID_COST_RECORD)


-- ============================================================================
-- SECTION 8: SUMMARY REPORT QUERY
-- Generate a summary of findings to share with team
-- ============================================================================

SELECT 'DATABASE READINESS SUMMARY' as report_section, '' as detail
UNION ALL
SELECT '================================', ''
UNION ALL
SELECT 'Stores Found:', CAST(COUNT(DISTINCT SALESORG_ID) as VARCHAR)
FROM T_SALESORG WHERE STORE_LOCATION IN ('Rosenheim', 'Freiburg')
UNION ALL
SELECT 'Months in 2026:', CAST(COUNT(DISTINCT ID_CALMONTH) as VARCHAR)
FROM T_ETL_MONTHLY_SALES WHERE YEAR(ID_CALMONTH) = 2026
UNION ALL
SELECT 'Total Sales Records (2026):', CAST(COUNT(*) as VARCHAR)
FROM T_ETL_MONTHLY_SALES WHERE YEAR(ID_CALMONTH) = 2026
UNION ALL
SELECT 'Total Cost Records (2026):', CAST(COUNT(*) as VARCHAR)
FROM T_ETL_MONTHLY_COSTS WHERE YEAR(ID_CALMONTH) = 2026
UNION ALL
SELECT 'Active Employees:', CAST(COUNT(*) as VARCHAR)
FROM T_EMPLOYEE WHERE DELETE_YN = 0
UNION ALL
SELECT 'Product Categories:', CAST(COUNT(*) as VARCHAR)
FROM T_PRODUCT_CATEGORY
UNION ALL
SELECT 'Existing Benchmark Views:', CAST(COUNT(*) as VARCHAR)
FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME LIKE '%BENCHMARK%';


-- ============================================================================
-- END OF ACTION PLAN QUERIES
-- ============================================================================

-- NEXT STEPS:
-- 1. Execute Section 1 (Data Discovery) queries and document results
-- 2. Execute Section 2 (Data Quality) queries and address any issues
-- 3. Validate Section 3 (Existing View) works correctly
-- 4. Analyze Section 4 (Cost Analysis) to create cost category mapping
-- 5. Decide on headcount strategy from Section 6
-- 6. Use findings to implement missing views from System Concept Section 4
-- ============================================================================
