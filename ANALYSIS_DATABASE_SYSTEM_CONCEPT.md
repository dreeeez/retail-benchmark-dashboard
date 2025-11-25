# Benchmarking System - Database Structure & System Concept Analysis

**Project:** Benchmarking System for Branches Rosenheim & Freiburg
**Group:** 18 (Marco, Harun, Duy)
**Analysis Date:** 2025-11-25

---

## Executive Summary

This document provides a comprehensive analysis of the database structure in relation to the system concept requirements for benchmarking two bicycle retail branches (Rosenheim and Freiburg). The analysis identifies existing data foundations, gaps, required implementations, and provides actionable recommendations.

---

## 1. System Concept Overview

### 1.1 Project Scope
- **Branches:** Rosenheim and Freiburg
- **Focus:** Stationary bicycle retail (B2C)
- **Granularity:** Monthly analysis (ID_CALMONTH)
- **Period:** January - December 2026
- **Approach:** Read-only analysis using SQL Views

### 1.2 Key Requirements

The system concept defines implementation across 5 view layers:

1. **Standardization & Cleansing Views** - Data quality and format standardization
2. **Aggregation Views** - Monthly summaries per branch and category
3. **KPI/Benchmark Views** - Calculated metrics
4. **Comparison Views** - Branch-to-branch comparisons
5. **Export/Reporting Views** - Final reporting interface

---

## 2. Database Structure Analysis

### 2.1 Core Data Tables (Existing)

#### T_ETL_MONTHLY_SALES
**Purpose:** Monthly sales data from ERP
**Columns:**
- `ID_CAMPAIGN` (int, NULL) - Marketing campaign
- `ID_GAME` (int, NOT NULL) - Game/simulation identifier
- `ID_STORE` (int, NULL) - Branch identifier
- `ID_MATERIAL` (int, NULL) - Product/material ID
- `ID_CALMONTH` (date, NOT NULL) - Calendar month
- `ID_EMPLOYEE` (int, NULL) - Employee who made the sale
- `ID_CATEGORY` (int, NOT NULL) - Product category
- `ID_SEGMENT` (int, NOT NULL) - Price segment
- `SALES_AMOUNT` (int, NULL) - Quantity sold
- `TRANSFER_PRICE_EUR` (money, NULL) - Internal transfer price
- `SALES_PRICE_EUR` (money, NULL) - Actual sales price
- `DISCOUNT_PCT` (float, NULL) - Discount percentage
- `REVENUE` (money, NULL) - Total revenue
- `DISCOUNT_IN_EUR` (float, NULL) - Discount in EUR
- `GROSS_PROFIT_EUR` (float, NULL) - Gross profit

**Assessment:** ✅ **Complete and ready** - Contains all required sales metrics

#### T_ETL_MONTHLY_COSTS
**Purpose:** Monthly cost data from ERP
**Columns:**
- `ID_GAME` (int, NOT NULL)
- `ID_STORE` (int, NOT NULL)
- `ID_COST_RECORD` (bigint, NOT NULL)
- `ID_CALMONTH` (date, NOT NULL)
- `VALUE` (float, NULL) - Cost value
- `ODS_USERNAME` (nvarchar, NOT NULL)
- `COST_CENTER` (int, NOT NULL)

**Assessment:** ✅ **Available but needs enrichment** - Link to T_COST_RECORD needed for cost categorization

#### T_COST_RECORD
**Purpose:** Cost category master data
**Columns:**
- `ID_GAME` (int, NOT NULL)
- `ID_STORE` (int, NOT NULL)
- `ID_COST_RECORD` (int, NULL)
- `ID_COST_CATEGORY` (int, NOT NULL)
- `COST_CATEGORY` (nvarchar, NULL) - Category name (e.g., "Betriebskosten", "Personalkosten")
- `COMMENT` (nvarchar, NULL)
- `ODS_USERNAME` (nvarchar, NOT NULL)

**Assessment:** ✅ **Critical for cost breakdown** - Enables separation of operating costs, personnel costs, etc.

#### T_SALESORG
**Purpose:** Branch master data
**Columns:**
- `SALESORG_ID` (int, NOT NULL) - Primary key
- `STORE_LOCATION` (nvarchar, NOT NULL) - Branch name (e.g., "Rosenheim", "Freiburg")
- `KFZ` (nchar, NULL)
- `INHABITANTS` (int, NOT NULL)
- `STORE_LOC` (nchar, NOT NULL)
- `MARKETSHARE` (int, NULL)
- Various demand factors (F_EMB, F_ECB, etc.)
- Monthly factors (F_JAN through F_DEC)
- `LATITUDE`, `LONGITUDE` (float, NULL)
- `INS_DATE` (datetime, NOT NULL)

**Assessment:** ✅ **Complete** - Contains branch identification data

#### T_EMPLOYEE
**Purpose:** Employee assignments and compensation
**Columns:**
- `ID_EMP` (int, NOT NULL)
- `ID_SALESORG` (int, NOT NULL) - Links employee to branch
- `DELETE_YN` (tinyint, NOT NULL)
- `EMP_SALARY_OFFERED` (money, NOT NULL) - Salary
- `EMP_COMMISSION` (int, NOT NULL) - Commission percentage
- `INS_DATE`, `UPD_DATE` (datetime, NOT NULL)
- `INS_USER`, `UPD_USER` (nvarchar, NOT NULL)

**Assessment:** ✅ **Available** - Can be used for personnel cost calculations

#### T_APPLICANTS
**Purpose:** Master data for potential employees
**Columns:**
- `ID_EMP` (int, NOT NULL)
- `EMP_NAME` (nvarchar, NOT NULL)
- `EMP_AGE` (int, NOT NULL)
- `EMP_IMAGE` (nvarchar, NOT NULL)
- `EMP_CV` (text, NOT NULL)
- `EMP_JOBPOSITION` (int, NOT NULL)
- `EMP_SALARY_EUR` (money, NOT NULL)
- `EMP_COMMISSION_PCT` (int, NOT NULL)
- `EMP_SOCIALCOSTS_PCT` (int, NOT NULL) - Social costs percentage
- `GAME_FACTOR` (float, NOT NULL)
- `INS_DATE` (datetime, NOT NULL)

**Assessment:** ✅ **Contains social cost factor** - Critical for calculating total personnel costs

#### T_MATERIAL
**Purpose:** Product master data
**Columns:**
- `ID_MAT` (int, NOT NULL)
- `MAT_NR` (nvarchar, NOT NULL) - Material number
- `MAT_DESCR` (nvarchar, NOT NULL) - Material description
- `ID_SEGMENT` (int, NOT NULL) - Price segment
- `ID_CATEGORY` (int, NOT NULL) - Product category
- `TRANSFER_PRICE` (money, NOT NULL)
- `SALES_PRICE` (money, NOT NULL)
- `SALES_PRICE_STORE` (money, NOT NULL)
- Additional fields for inventory, delivery, etc.

**Assessment:** ✅ **Complete** - Enables category mapping

#### T_PRODUCT_CATEGORY
**Purpose:** Product category definitions
**Columns:**
- `ID_CATEGORY` (int, NOT NULL)
- `CATEGORY` (nvarchar, NOT NULL) - Category name (e.g., "E-Bike", "MTB", "City/Trekking")
- `PRODUCT_LINE` (nvarchar, NOT NULL)

**Assessment:** ✅ **Ready for benchmark categorization**

#### T_PRICE_SEGMENT
**Purpose:** Price segment definitions
**Columns:**
- `ID_SEGMENT` (int, NOT NULL)
- `SEGMENT` (nvarchar, NOT NULL) - Segment name

**Assessment:** ✅ **Available**

---

### 2.2 Existing Views

#### V_LIST_MONTHLY_SALES
**Purpose:** Readable view of monthly sales
**Columns:**
- ID_STORE, ID_CALMONTH, ID_MATERIAL
- MAT_NR, MAT_DESCR
- SALES_AMOUNT, REVENUE
- TRANSFER_PRICE_EUR, SALES_PRICE_EUR
- DISCOUNT_PCT, DISCOUNT_IN_EUR
- GROSS_PROFIT_EUR
- ID_EMPLOYEE, ID_CAMPAIGN
- CAMP_NAME, CAMP_TYPE, CAMP_DESCR

**Assessment:** ✅ **Useful as base view** - Already enriched with material and campaign info

#### V_LIST_MONTHLY_COSTS
**Purpose:** Readable view of monthly costs
**Columns:**
- ID_STORE
- ID_CALMONTH
- COST_CATEGORY
- COMMENT
- VALUE

**Assessment:** ✅ **Perfect for cost analysis** - Already includes cost category names

#### V_BENCHMARK_SALES_AGG (list_views schema)
**Purpose:** Aggregated sales by month, store, category
**Columns:**
- ID_CALMONTH (date)
- ID_STORE (int)
- STORE_NAME (nvarchar)
- ID_CATEGORY (int)
- SALES_AMOUNT (int)
- REVENUE_EUR (money)
- GROSS_PROFIT_EUR (float)
- TRANSFER_COST_EUR (float)
- AVG_SALES_PRICE_EUR (numeric)

**Status:** ✅ **ALREADY IMPLEMENTED!**
This is the first aggregation view from the system concept (Section 4.2.1)

---

### 2.3 Missing Components

#### ❌ T_STORE_HEADCOUNT
**Required by:** System concept Section 2.1, 3.1, 4.2.3
**Purpose:** Employee count per branch per month
**Required Columns:**
- ID_CALMONTH
- ID_STORE
- EMPLOYEE_COUNT

**Impact:** HIGH - Required for "Revenue per Employee" KPI

**Solution Options:**
1. Create table from T_EMPLOYEE aggregation
2. Use dynamic calculation from T_EMPLOYEE
3. Request data from ETL process

#### ❌ Views V_ETL_MONTHLY_SALES and V_ETL_MONTHLY_COSTS
**Note:** System concept references these views, but:
- The actual base tables are T_ETL_MONTHLY_SALES and T_ETL_MONTHLY_COSTS
- The readable views are V_LIST_MONTHLY_SALES and V_LIST_MONTHLY_COSTS
- **Recommendation:** Use existing V_LIST_* views or create aliases

---

## 3. Implementation Gap Analysis

### 3.1 Views to Implement (from System Concept Section 4)

#### ✅ COMPLETED
1. **V_BENCHMARK_SALES_AGG** (Section 4.2.1) - Already exists in list_views schema

#### ⚠️ IN PROGRESS / NEEDS ADJUSTMENT
2. **V_BENCHMARK_SALES_STD** (Section 4.1.1)
   - Status: NOT FOUND in database
   - Purpose: Standardize month format, enrich branch data, map to benchmark categories
   - Dependency: None - should use T_ETL_MONTHLY_SALES + T_SALESORG + T_MATERIAL
   - **Action Required:** Create this view

3. **V_BENCHMARK_SALES_ERRORS** (Section 4.1.2)
   - Status: NOT FOUND
   - Purpose: Data quality view for suspicious records
   - **Action Required:** Create this view

#### ❌ NOT IMPLEMENTED
4. **V_BENCHMARK_COSTS_AGG** (Section 4.2.2)
   - Purpose: Aggregate costs by month, branch, category
   - Required fields: OPERATING_COST_EUR, PERSONNEL_COST_EUR, PROCUREMENT_EXTRA_EUR, OTHER_COST_TOTAL_EUR
   - **Action Required:** Create this view using V_LIST_MONTHLY_COSTS + cost category filtering

5. **V_BENCHMARK_HEADCOUNT** (Section 4.2.3)
   - Purpose: Aggregate employee count by month and branch
   - **Blocker:** No T_STORE_HEADCOUNT table exists
   - **Action Required:**
     - Create headcount calculation from T_EMPLOYEE
     - Or create T_STORE_HEADCOUNT table

6. **V_BENCHMARK_KPI** (Section 4.3.1)
   - Purpose: Central KPI view with all calculated metrics
   - Required calculations:
     - BRUTTOGEWINN_MARGE_PROZ
     - BETRIEBSKOSTEN_QUOTE_PROZ
     - PERSONALKOSTEN_ANTEIL_PROZ
     - UMSATZ_PRO_MA_EUR
   - **Action Required:** Create this comprehensive view

7. **V_BENCHMARK_STORE_COMPARISON** (Section 4.4.1)
   - Purpose: Direct comparison Freiburg vs. Rosenheim
   - **Action Required:** Create pivot view from V_BENCHMARK_KPI

8. **V_BENCHMARK_EXPORT_MONTHLY** (Section 4.5.1)
   - Purpose: Final export/reporting view
   - **Action Required:** Create subset of V_BENCHMARK_KPI

---

## 4. Data Flow Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│                         SOURCE DATA                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│T_ETL_MONTHLY_    │    │T_ETL_MONTHLY_    │    │  T_EMPLOYEE      │
│    SALES         │    │    COSTS         │    │  T_APPLICANTS    │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                        │
        │                       │                        │
        ▼                       ▼                        │
┌──────────────────┐    ┌──────────────────┐            │
│V_LIST_MONTHLY_   │    │V_LIST_MONTHLY_   │            │
│    SALES         │    │    COSTS         │            │
└──────────────────┘    └──────────────────┘            │
        │                       │                        │
        ▼                       │                        │
┌──────────────────┐            │                        │
│V_BENCHMARK_      │            │                        │
│  SALES_STD       │            │                        │
│ [TO CREATE]      │            │                        │
└──────────────────┘            │                        │
        │                       │                        │
        ▼                       ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│V_BENCHMARK_      │    │V_BENCHMARK_      │    │V_BENCHMARK_      │
│  SALES_AGG       │    │  COSTS_AGG       │    │  HEADCOUNT       │
│  [✅ EXISTS]     │    │  [TO CREATE]     │    │  [TO CREATE]     │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                        │
        └───────────────────────┴────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  V_BENCHMARK_KPI │
                    │   [TO CREATE]    │
                    └──────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌────────────────────────┐  ┌────────────────────────┐
    │V_BENCHMARK_STORE_      │  │V_BENCHMARK_EXPORT_     │
    │   COMPARISON           │  │   MONTHLY              │
    │   [TO CREATE]          │  │   [TO CREATE]          │
    └────────────────────────┘  └────────────────────────┘
```

---

## 5. KPI Calculations - Data Availability

### 5.1 Required KPIs (from Section 3.3)

| KPI | Formula | Data Availability | Status |
|-----|---------|-------------------|--------|
| **Bruttogewinn-Marge (%)** | GROSS_PROFIT_EUR / REVENUE * 100 | ✅ Both in T_ETL_MONTHLY_SALES | Ready |
| **Betriebskosten-Quote (%)** | OPERATING_COST_EUR / REVENUE * 100 | ✅ REVENUE available; Operating costs need filtering from V_LIST_MONTHLY_COSTS | Needs cost type filter |
| **Personalkosten-Anteil (%)** | PERSONNEL_COST_EUR / GROSS_PROFIT_EUR * 100 | ⚠️ Personnel costs need calculation or filtering | Needs implementation |
| **Umsatz pro Mitarbeiter** | REVENUE / EMPLOYEE_COUNT | ⚠️ Need employee count per month/branch | Missing headcount data |
| **Durchschnittlicher Verkaufspreis** | REVENUE / SALES_AMOUNT | ✅ Both available | Ready |
| **Gesamtkosten** | Transfer + Operating + Personnel + Procurement | ⚠️ Need to aggregate from cost categories | Needs aggregation |

---

### 5.2 Cost Category Mapping

The system concept (Section 3.2) defines these cost types:
- **Betriebskosten_EUR** (Operating Costs)
- **Personalkosten_EUR** (Personnel Costs)
- **Zusätzliche Beschaffungskosten_EUR** (Additional Procurement Costs)

**Data Source:** T_COST_RECORD.COST_CATEGORY
**Action Required:** Identify actual cost category names in database and map to these types

---

## 6. Personnel Cost Calculation Strategy

### 6.1 Current Situation
- **T_EMPLOYEE** contains: EMP_SALARY_OFFERED, EMP_COMMISSION
- **T_APPLICANTS** contains: EMP_SOCIALCOSTS_PCT
- **System Concept requires:** Total personnel costs including social costs

### 6.2 Recommended Approach

```sql
-- Personnel Cost per Employee per Month
Total_Personnel_Cost =
    (EMP_SALARY_OFFERED + (Revenue * EMP_COMMISSION / 100))
    * (1 + EMP_SOCIALCOSTS_PCT / 100)
```

**Components:**
1. Base salary from T_EMPLOYEE.EMP_SALARY_OFFERED
2. Commission from T_EMPLOYEE.EMP_COMMISSION applied to revenue
3. Social costs factor from T_APPLICANTS.EMP_SOCIALCOSTS_PCT (via JOIN on ID_EMP)

---

## 7. Headcount Data Strategy

### 7.1 Problem
System concept references T_STORE_HEADCOUNT which doesn't exist.

### 7.2 Solution Options

#### Option A: Create from T_EMPLOYEE (Recommended)
```sql
-- Count active employees per store per month
SELECT
    ID_SALESORG as ID_STORE,
    ID_CALMONTH, -- Need to generate or cross-join with calendar
    COUNT(*) as EMPLOYEE_COUNT
FROM T_EMPLOYEE
WHERE DELETE_YN = 0
GROUP BY ID_SALESORG, ID_CALMONTH
```

**Pros:** Uses existing data
**Cons:** Need to determine employee active periods (hire/termination dates not visible)

#### Option B: Manual Table Creation
Create T_STORE_HEADCOUNT and populate with known employee counts for the analysis period.

**Pros:** Simple, controlled
**Cons:** Requires manual data entry or ETL process

#### Option C: Use Fixed Headcount
For Phase 4 implementation, use a fixed employee count per branch.

**Pros:** Quickest implementation
**Cons:** Less accurate, not dynamic

---

## 8. Implementation Recommendations

### 8.1 Priority 1 (Critical Path)

1. **Create V_BENCHMARK_SALES_STD**
   - Base: T_ETL_MONTHLY_SALES
   - Enrich with T_SALESORG (STORE_LOCATION)
   - Enrich with T_MATERIAL (MAT_NR, MAT_DESCR)
   - Enrich with T_PRODUCT_CATEGORY (CATEGORY)
   - Map to benchmark categories (E-Bike, MTB, City/Trekking, Kinder, Sonstige)

2. **Solve Headcount Issue**
   - Decision needed on Option A, B, or C
   - Create V_BENCHMARK_HEADCOUNT or equivalent

3. **Create V_BENCHMARK_COSTS_AGG**
   - Analyze T_COST_RECORD.COST_CATEGORY values
   - Map to: OPERATING_COST_EUR, PERSONNEL_COST_EUR, PROCUREMENT_EXTRA_EUR
   - Aggregate by month, store, category

### 8.2 Priority 2 (Core KPIs)

4. **Create V_BENCHMARK_KPI**
   - Join V_BENCHMARK_SALES_AGG + V_BENCHMARK_COSTS_AGG + V_BENCHMARK_HEADCOUNT
   - Implement all KPI calculations
   - Handle NULL/zero division cases

### 8.3 Priority 3 (Reporting)

5. **Create V_BENCHMARK_STORE_COMPARISON**
   - Pivot V_BENCHMARK_KPI for Freiburg vs. Rosenheim

6. **Create V_BENCHMARK_EXPORT_MONTHLY**
   - Final reporting view with selected columns

7. **Create V_BENCHMARK_SALES_ERRORS** (Data Quality)
   - Identify data quality issues

---

## 9. SQL Implementation Templates

### 9.1 V_BENCHMARK_SALES_STD (Template)

```sql
CREATE OR ALTER VIEW list_views.V_BENCHMARK_SALES_STD AS
SELECT
    -- Standardized month format
    CONVERT(char(7), s.ID_CALMONTH, 126) AS ID_CALMONTH_STD,
    s.ID_CALMONTH,

    -- Store information
    s.ID_STORE,
    so.STORE_LOCATION AS STORE_NAME,

    -- Material information
    s.ID_MATERIAL,
    m.MAT_NR,
    m.MAT_DESCR,

    -- Benchmark category mapping
    CASE
        WHEN pc.CATEGORY LIKE '%E-Bike%' THEN 'E-Bike'
        WHEN pc.CATEGORY LIKE '%MTB%' THEN 'MTB'
        WHEN pc.CATEGORY LIKE '%City%' OR pc.CATEGORY LIKE '%Trekking%' THEN 'City/Trekking'
        WHEN pc.CATEGORY LIKE '%Kinder%' THEN 'Kinder'
        ELSE 'Sonstige'
    END AS BENCHMARK_CATEGORY,

    -- Sales metrics
    s.SALES_AMOUNT,
    s.REVENUE,
    s.GROSS_PROFIT_EUR

FROM dbo.T_ETL_MONTHLY_SALES s
LEFT JOIN dbo.T_SALESORG so ON so.SALESORG_ID = s.ID_STORE
LEFT JOIN dbo.T_MATERIAL m ON m.ID_MAT = s.ID_MATERIAL
LEFT JOIN dbo.T_PRODUCT_CATEGORY pc ON pc.ID_CATEGORY = m.ID_CATEGORY
WHERE s.REVENUE > 0; -- Data cleansing
```

### 9.2 V_BENCHMARK_HEADCOUNT (Option A: From T_EMPLOYEE)

```sql
CREATE OR ALTER VIEW list_views.V_BENCHMARK_HEADCOUNT AS
SELECT
    e.ID_SALESORG AS ID_STORE,
    c.ID_CALMONTH,
    CONVERT(char(7), c.ID_CALMONTH, 126) AS ID_CALMONTH_STD,
    COUNT(DISTINCT e.ID_EMP) AS EMPLOYEE_COUNT
FROM dbo.T_EMPLOYEE e
CROSS JOIN (
    SELECT DISTINCT ID_CALMONTH
    FROM dbo.T_ETL_MONTHLY_SALES
) c
WHERE e.DELETE_YN = 0
GROUP BY e.ID_SALESORG, c.ID_CALMONTH;
```

**Note:** This assumes all active employees were active during all analysis months. Refinement needed based on actual hire/termination tracking.

### 9.3 V_BENCHMARK_COSTS_AGG (Template - requires cost category mapping)

```sql
CREATE OR ALTER VIEW list_views.V_BENCHMARK_COSTS_AGG AS
SELECT
    c.ID_CALMONTH,
    CONVERT(char(7), c.ID_CALMONTH, 126) AS ID_CALMONTH_STD,
    c.ID_STORE,

    -- Operating costs
    SUM(CASE
        WHEN cr.COST_CATEGORY IN ('Betriebskosten', 'Miete', 'Strom', 'Marketing')
        THEN c.VALUE ELSE 0
    END) AS OPERATING_COST_EUR,

    -- Personnel costs (if tracked separately)
    SUM(CASE
        WHEN cr.COST_CATEGORY IN ('Personalkosten', 'Gehälter', 'Sozialkosten')
        THEN c.VALUE ELSE 0
    END) AS PERSONNEL_COST_EUR,

    -- Procurement costs
    SUM(CASE
        WHEN cr.COST_CATEGORY IN ('Beschaffungskosten', 'Zusatzkosten')
        THEN c.VALUE ELSE 0
    END) AS PROCUREMENT_EXTRA_EUR,

    -- Total other costs
    SUM(c.VALUE) AS OTHER_COST_TOTAL_EUR

FROM dbo.T_ETL_MONTHLY_COSTS c
LEFT JOIN dbo.T_COST_RECORD cr
    ON cr.ID_COST_RECORD = c.ID_COST_RECORD
    AND cr.ID_STORE = c.ID_STORE
GROUP BY
    c.ID_CALMONTH,
    c.ID_STORE;
```

**Action Required:** Query T_COST_RECORD to identify actual COST_CATEGORY values and update the CASE statements.

---

## 10. Data Quality Checks Needed

### 10.1 Critical Validations

```sql
-- 1. Check for missing store data
SELECT DISTINCT ID_STORE
FROM T_ETL_MONTHLY_SALES
WHERE ID_STORE NOT IN (SELECT SALESORG_ID FROM T_SALESORG);

-- 2. Check for negative revenues or gross profits
SELECT COUNT(*) as error_count
FROM T_ETL_MONTHLY_SALES
WHERE REVENUE <= 0 OR GROSS_PROFIT_EUR < 0;

-- 3. Verify all 12 months exist for both stores
SELECT
    ID_STORE,
    COUNT(DISTINCT ID_CALMONTH) as month_count
FROM T_ETL_MONTHLY_SALES
WHERE YEAR(ID_CALMONTH) = 2026
GROUP BY ID_STORE;

-- 4. Check cost category coverage
SELECT DISTINCT COST_CATEGORY
FROM T_COST_RECORD
ORDER BY COST_CATEGORY;

-- 5. Verify employee-store assignments
SELECT
    ID_SALESORG,
    COUNT(*) as employee_count
FROM T_EMPLOYEE
WHERE DELETE_YN = 0
GROUP BY ID_SALESORG;
```

---

## 11. Next Steps - Action Items

### Immediate Actions

1. **Query Cost Categories**
   ```sql
   SELECT DISTINCT COST_CATEGORY, COUNT(*) as count
   FROM T_COST_RECORD
   GROUP BY COST_CATEGORY
   ORDER BY COST_CATEGORY;
   ```
   **Purpose:** Identify actual cost category names for mapping

2. **Determine Headcount Strategy**
   - Decide on Option A, B, or C
   - Create appropriate view or table

3. **Verify Store IDs**
   ```sql
   SELECT SALESORG_ID, STORE_LOCATION
   FROM T_SALESORG
   WHERE STORE_LOCATION IN ('Rosenheim', 'Freiburg');
   ```
   **Purpose:** Confirm store identifiers for filtering

### Implementation Sequence

**Phase 1: Foundation (Week 1)**
- ✅ Verify data availability (COMPLETE - this document)
- ⬜ Query cost categories and create mapping
- ⬜ Decide and implement headcount solution
- ⬜ Create V_BENCHMARK_SALES_STD

**Phase 2: Aggregation (Week 2)**
- ⬜ Create V_BENCHMARK_COSTS_AGG
- ⬜ Create V_BENCHMARK_HEADCOUNT
- ⬜ Validate V_BENCHMARK_SALES_AGG (already exists)

**Phase 3: KPI Calculation (Week 3)**
- ⬜ Create V_BENCHMARK_KPI with all metrics
- ⬜ Test NULL handling and edge cases
- ⬜ Validate calculations against manual computations (TF02)

**Phase 4: Reporting (Week 4)**
- ⬜ Create V_BENCHMARK_STORE_COMPARISON
- ⬜ Create V_BENCHMARK_EXPORT_MONTHLY
- ⬜ Create V_BENCHMARK_SALES_ERRORS (data quality)
- ⬜ Performance testing (< 5 seconds, N02)

**Phase 5: Acceptance (Week 5)**
- ⬜ Execute all test cases (TF01-TF05)
- ⬜ Verify acceptance criteria (SPC01-SPC05)
- ⬜ Documentation and handover

---

## 12. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **T_STORE_HEADCOUNT missing** | HIGH | Implement Option A (from T_EMPLOYEE) or use fixed counts |
| **Cost categories don't match concept** | MEDIUM | Query actual categories, adapt V_BENCHMARK_COSTS_AGG |
| **Incomplete monthly data (SPC03)** | HIGH | Run data quality check, escalate to data provider |
| **Personnel costs not in cost table** | MEDIUM | Calculate from T_EMPLOYEE + T_APPLICANTS separately |
| **Performance issues with complex views** | LOW | Add indexes on ID_CALMONTH, ID_STORE, ID_CATEGORY |
| **Social cost percentages unavailable** | MEDIUM | Use standard percentage or exclude from calculation |

---

## 13. Appendix: Key System Concept References

- **Section 2.1:** Architecture - Base Tables
- **Section 3.2:** Basisgrößen (Base Metrics)
- **Section 3.3:** Kennzahlen (KPIs)
- **Section 4.1:** Standardization Views
- **Section 4.2:** Aggregation Views
- **Section 4.3:** KPI Views
- **Section 4.4:** Comparison Views
- **Section 4.5:** Export Views
- **Section 9.1:** Test Cases
- **Section 9.2:** Acceptance Criteria

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-25 | Claude AI | Initial comprehensive analysis based on db_structure.xlsx and system concept PDF |

---

**END OF ANALYSIS DOCUMENT**
