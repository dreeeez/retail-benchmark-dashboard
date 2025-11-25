# Benchmarking System - Data Model & Relationships

**Project:** Rosenheim & Freiburg Branch Benchmarking
**Date:** 2025-11-25

---

## Entity Relationship Diagram (Text Format)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MASTER DATA LAYER                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐          ┌──────────────────────┐
│   T_SALESORG         │          │   T_PRODUCT_CATEGORY │
│──────────────────────│          │──────────────────────│
│ SALESORG_ID (PK)     │          │ ID_CATEGORY (PK)     │
│ STORE_LOCATION       │          │ CATEGORY             │
│ INHABITANTS          │          │ PRODUCT_LINE         │
│ MARKETSHARE          │          └──────────────────────┘
│ ...location data...  │                      │
└──────────────────────┘                      │
         │                                    │
         │                                    │
         │                    ┌───────────────┘
         │                    │
         │              ┌──────────────────────┐
         │              │   T_MATERIAL         │
         │              │──────────────────────│
         │              │ ID_MAT (PK)          │
         │              │ MAT_NR               │
         │              │ MAT_DESCR            │
         │              │ ID_CATEGORY (FK) ────┘
         │              │ ID_SEGMENT           │
         │              │ TRANSFER_PRICE       │
         │              │ SALES_PRICE          │
         │              └──────────────────────┘
         │                        │
         │                        │
         │              ┌──────────────────────┐
         │              │   T_PRICE_SEGMENT    │
         │              │──────────────────────│
         │              │ ID_SEGMENT (PK)      │
         │              │ SEGMENT              │
         │              └──────────────────────┘
         │
         │
┌──────────────────────┐
│   T_EMPLOYEE         │
│──────────────────────│
│ ID_EMP (PK)          │
│ ID_SALESORG (FK) ────┘
│ EMP_SALARY_OFFERED   │
│ EMP_COMMISSION       │
│ DELETE_YN            │
└──────────────────────┘
         │
         │ (References)
         │
┌──────────────────────┐
│   T_APPLICANTS       │
│──────────────────────│
│ ID_EMP (PK)          │
│ EMP_NAME             │
│ EMP_SALARY_EUR       │
│ EMP_COMMISSION_PCT   │
│ EMP_SOCIALCOSTS_PCT  │◄── Social cost % for personnel calculations
└──────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRANSACTIONAL DATA LAYER                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────┐
│   T_ETL_MONTHLY_SALES (Main Sales Fact)      │
│───────────────────────────────────────────────│
│ ID_GAME                                       │
│ ID_STORE (FK) ──────────► T_SALESORG         │
│ ID_MATERIAL (FK) ────────► T_MATERIAL        │
│ ID_CALMONTH (Date Key)                        │
│ ID_EMPLOYEE (FK) ────────► T_EMPLOYEE        │
│ ID_CATEGORY (FK) ────────► T_PRODUCT_CATEGORY│
│ ID_SEGMENT (FK) ─────────► T_PRICE_SEGMENT   │
│ ID_CAMPAIGN (FK)                              │
│ SALES_AMOUNT (Quantity)                       │
│ TRANSFER_PRICE_EUR                            │
│ SALES_PRICE_EUR                               │
│ DISCOUNT_PCT                                  │
│ REVENUE                   ◄─── KEY METRIC    │
│ DISCOUNT_IN_EUR                               │
│ GROSS_PROFIT_EUR          ◄─── KEY METRIC    │
└───────────────────────────────────────────────┘
                    │
                    │
                    ▼
┌───────────────────────────────────────────────┐
│   V_LIST_MONTHLY_SALES (Enriched View)       │
│───────────────────────────────────────────────│
│ ID_STORE                                      │
│ ID_CALMONTH                                   │
│ ID_MATERIAL                                   │
│ MAT_NR, MAT_DESCR     ◄─── From JOIN         │
│ SALES_AMOUNT                                  │
│ REVENUE                                       │
│ GROSS_PROFIT_EUR                              │
│ CAMP_NAME, CAMP_TYPE  ◄─── From JOIN         │
│ ...                                           │
└───────────────────────────────────────────────┘


┌───────────────────────────────────────────────┐
│   T_ETL_MONTHLY_COSTS (Main Cost Fact)       │
│───────────────────────────────────────────────│
│ ID_GAME                                       │
│ ID_STORE (FK) ──────────► T_SALESORG         │
│ ID_COST_RECORD (FK) ─────► T_COST_RECORD     │
│ ID_CALMONTH (Date Key)                        │
│ VALUE                     ◄─── Cost Amount    │
│ COST_CENTER                                   │
└───────────────────────────────────────────────┘
                    │
                    │
                    ▼
┌───────────────────────────────────────────────┐
│   T_COST_RECORD (Cost Master)                │
│───────────────────────────────────────────────│
│ ID_COST_RECORD (PK)                           │
│ ID_STORE                                      │
│ ID_COST_CATEGORY                              │
│ COST_CATEGORY         ◄─── Category Name     │
│ COMMENT                                       │
└───────────────────────────────────────────────┘
                    │
                    │
                    ▼
┌───────────────────────────────────────────────┐
│   V_LIST_MONTHLY_COSTS (Enriched View)       │
│───────────────────────────────────────────────│
│ ID_STORE                                      │
│ ID_CALMONTH                                   │
│ COST_CATEGORY         ◄─── From JOIN         │
│ COMMENT                                       │
│ VALUE                                         │
└───────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                        BENCHMARK VIEW LAYER (To Build)                       │
└─────────────────────────────────────────────────────────────────────────────┘


LAYER 1: STANDARDIZATION & CLEANSING
════════════════════════════════════════════════════════════════════

┌───────────────────────────────────────────────┐
│   V_BENCHMARK_SALES_STD [TO CREATE]           │
│───────────────────────────────────────────────│
│ Source: T_ETL_MONTHLY_SALES                   │
│         + T_SALESORG                          │
│         + T_MATERIAL                          │
│         + T_PRODUCT_CATEGORY                  │
│───────────────────────────────────────────────│
│ ID_CALMONTH_STD (YYYY-MM format)              │
│ ID_CALMONTH (original)                        │
│ ID_STORE                                      │
│ STORE_NAME                                    │
│ MAT_NR, MAT_DESCR                             │
│ BENCHMARK_CATEGORY ◄── E-Bike, MTB, City,... │
│ SALES_AMOUNT                                  │
│ REVENUE                                       │
│ GROSS_PROFIT_EUR                              │
└───────────────────────────────────────────────┘

┌───────────────────────────────────────────────┐
│   V_BENCHMARK_SALES_ERRORS [TO CREATE]        │
│───────────────────────────────────────────────│
│ Purpose: Data quality view                    │
│ Shows records with:                           │
│  - REVENUE <= 0                               │
│  - GROSS_PROFIT_EUR < 0                       │
└───────────────────────────────────────────────┘


LAYER 2: AGGREGATION
════════════════════════════════════════════════════════════════════

┌───────────────────────────────────────────────┐
│   V_BENCHMARK_SALES_AGG [✅ ALREADY EXISTS]   │
│───────────────────────────────────────────────│
│ Granularity: Month × Store × Category        │
│───────────────────────────────────────────────│
│ ID_CALMONTH                                   │
│ ID_STORE                                      │
│ STORE_NAME                                    │
│ ID_CATEGORY                                   │
│ SALES_AMOUNT                                  │
│ REVENUE_EUR                                   │
│ GROSS_PROFIT_EUR                              │
│ TRANSFER_COST_EUR                             │
│ AVG_SALES_PRICE_EUR                           │
└───────────────────────────────────────────────┘

┌───────────────────────────────────────────────┐
│   V_BENCHMARK_COSTS_AGG [TO CREATE]           │
│───────────────────────────────────────────────│
│ Source: V_LIST_MONTHLY_COSTS                  │
│         + Cost Category Mapping               │
│───────────────────────────────────────────────│
│ Granularity: Month × Store × Category        │
│───────────────────────────────────────────────│
│ ID_CALMONTH                                   │
│ ID_CALMONTH_STD                               │
│ ID_STORE                                      │
│ ID_CATEGORY                                   │
│ OPERATING_COST_EUR    ◄─── Filtered          │
│ PERSONNEL_COST_EUR    ◄─── Filtered          │
│ PROCUREMENT_EXTRA_EUR ◄─── Filtered          │
│ OTHER_COST_TOTAL_EUR  ◄─── Sum All           │
└───────────────────────────────────────────────┘

┌───────────────────────────────────────────────┐
│   V_BENCHMARK_HEADCOUNT [TO CREATE]           │
│───────────────────────────────────────────────│
│ Source: T_EMPLOYEE (Option A)                 │
│    OR: T_STORE_HEADCOUNT (Option B)           │
│    OR: Fixed Values (Option C)                │
│───────────────────────────────────────────────│
│ Granularity: Month × Store                    │
│───────────────────────────────────────────────│
│ ID_CALMONTH                                   │
│ ID_CALMONTH_STD                               │
│ ID_STORE                                      │
│ EMPLOYEE_COUNT                                │
└───────────────────────────────────────────────┘


LAYER 3: KPI CALCULATION
════════════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────┐
│   V_BENCHMARK_KPI [TO CREATE] ─── CENTRAL KPI VIEW             │
│────────────────────────────────────────────────────────────────│
│ Source: V_BENCHMARK_SALES_AGG                                  │
│       + V_BENCHMARK_COSTS_AGG                                  │
│       + V_BENCHMARK_HEADCOUNT                                  │
│────────────────────────────────────────────────────────────────│
│ Granularity: Month × Store × Category                          │
│────────────────────────────────────────────────────────────────│
│ DIMENSIONS:                                                    │
│  - ID_CALMONTH_STD                                             │
│  - ID_STORE, STORE_NAME                                        │
│  - ID_CATEGORY                                                 │
│                                                                │
│ BASE METRICS:                                                  │
│  - UMSATZ_EUR (Revenue)                                        │
│  - BRUTTOGEWINN_EUR (Gross Profit)                             │
│  - GESAMTKOSTEN_EUR (Total Costs)                              │
│  - BETRIEBSKOSTEN_EUR (Operating Costs)                        │
│  - PERSONALKOSTEN_EUR (Personnel Costs)                        │
│  - ZUSAETZL_BESCHAFFUNGSKOSTEN_EUR (Procurement)               │
│  - AVG_SALES_PRICE_EUR                                         │
│  - EMPLOYEE_COUNT                                              │
│                                                                │
│ CALCULATED KPIs:                                               │
│  - BRUTTOGEWINN_MARGE_PROZ                                     │
│    = BRUTTOGEWINN / UMSATZ × 100                               │
│                                                                │
│  - BETRIEBSKOSTEN_QUOTE_PROZ                                   │
│    = BETRIEBSKOSTEN / UMSATZ × 100                             │
│                                                                │
│  - PERSONALKOSTEN_ANTEIL_PROZ                                  │
│    = PERSONALKOSTEN / BRUTTOGEWINN × 100                       │
│                                                                │
│  - UMSATZ_PRO_MA_EUR                                           │
│    = UMSATZ / EMPLOYEE_COUNT                                   │
└────────────────────────────────────────────────────────────────┘


LAYER 4: COMPARISON
════════════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────┐
│   V_BENCHMARK_STORE_COMPARISON [TO CREATE]                     │
│────────────────────────────────────────────────────────────────│
│ Source: V_BENCHMARK_KPI (Pivoted)                              │
│────────────────────────────────────────────────────────────────│
│ Granularity: Month × Category                                  │
│────────────────────────────────────────────────────────────────│
│ ID_CALMONTH_STD                                                │
│ ID_CATEGORY                                                    │
│                                                                │
│ FREIBURG:                                                      │
│  - UMSATZ_FREIBURG_EUR                                         │
│  - BRUTTOGEWINN_FREIBURG_EUR                                   │
│                                                                │
│ ROSENHEIM:                                                     │
│  - UMSATZ_ROSENHEIM_EUR                                        │
│  - BRUTTOGEWINN_ROSENHEIM_EUR                                  │
│                                                                │
│ DIFFERENCES:                                                   │
│  - DIFF_UMSATZ_EUR (Rosenheim - Freiburg)                      │
│  - DIFF_BRUTTOGEWINN_EUR                                       │
└────────────────────────────────────────────────────────────────┘


LAYER 5: EXPORT / REPORTING
════════════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────┐
│   V_BENCHMARK_EXPORT_MONTHLY [TO CREATE]                       │
│────────────────────────────────────────────────────────────────│
│ Source: V_BENCHMARK_KPI (Selected columns)                     │
│────────────────────────────────────────────────────────────────│
│ Purpose: Standardized export for reporting tools               │
│────────────────────────────────────────────────────────────────│
│ REPORT_MONTH (ID_CALMONTH_STD)                                 │
│ ID_STORE                                                       │
│ STORE_NAME                                                     │
│ ID_CATEGORY                                                    │
│ UMSATZ_EUR                                                     │
│ BRUTTOGEWINN_EUR                                               │
│ BRUTTOGEWINN_MARGE_PROZ                                        │
│ BETRIEBSKOSTEN_EUR                                             │
│ BETRIEBSKOSTEN_QUOTE_PROZ                                      │
│ PERSONALKOSTEN_EUR                                             │
│ PERSONALKOSTEN_ANTEIL_PROZ                                     │
│ UMSATZ_PRO_MA_EUR                                              │
└────────────────────────────────────────────────────────────────┘
```

---

## Key Relationships Explained

### 1. Sales Data Flow

```
T_ETL_MONTHLY_SALES
    │
    ├──► JOIN T_SALESORG (ID_STORE) ────► Get STORE_LOCATION
    ├──► JOIN T_MATERIAL (ID_MATERIAL) ──► Get MAT_NR, MAT_DESCR
    ├──► JOIN T_PRODUCT_CATEGORY ────────► Get CATEGORY for mapping
    │
    ▼
V_BENCHMARK_SALES_STD (Standardized + Enriched)
    │
    ▼
V_BENCHMARK_SALES_AGG (Aggregated by Month × Store × Category)
```

### 2. Cost Data Flow

```
T_ETL_MONTHLY_COSTS
    │
    ├──► JOIN T_COST_RECORD ────► Get COST_CATEGORY name
    │
    ▼
V_LIST_MONTHLY_COSTS (Already exists with category names)
    │
    ├──► FILTER CASE statements:
    │    - "Betriebskosten" → OPERATING_COST_EUR
    │    - "Personalkosten" → PERSONNEL_COST_EUR
    │    - etc.
    │
    ▼
V_BENCHMARK_COSTS_AGG (Aggregated by cost type)
```

### 3. Headcount Data Flow (Option A)

```
T_EMPLOYEE (Active employees)
    │
    ├──► CROSS JOIN with distinct months from sales
    ├──► WHERE DELETE_YN = 0 (active only)
    │
    ▼
V_BENCHMARK_HEADCOUNT (Count per Store × Month)
```

### 4. KPI Calculation Flow

```
V_BENCHMARK_SALES_AGG
        +
V_BENCHMARK_COSTS_AGG
        +
V_BENCHMARK_HEADCOUNT
        │
        ▼
    LEFT JOINS on:
    - ID_CALMONTH_STD
    - ID_STORE
    - ID_CATEGORY (where applicable)
        │
        ▼
V_BENCHMARK_KPI
    │
    ├──► Calculate margins: Gross Profit / Revenue × 100
    ├──► Calculate ratios: Operating Cost / Revenue × 100
    ├──► Calculate productivity: Revenue / Employee Count
    │
    ▼
All KPIs available for reporting
```

---

## Time Dimension Structure

```
ID_CALMONTH (date type)
│
├─ 2026-01-01
├─ 2026-02-01
├─ 2026-03-01
├─ ...
└─ 2026-12-01

Converted to:
ID_CALMONTH_STD (char(7))
│
├─ "2026-01"
├─ "2026-02"
├─ "2026-03"
├─ ...
└─ "2026-12"
```

**Purpose:** Standardized format YYYY-MM for consistent grouping and reporting

---

## Category Dimension Structure

### Product Categories (Benchmark Mapping)

```
T_PRODUCT_CATEGORY.CATEGORY
│
├─ E-Bike related        ─────► BENCHMARK_CATEGORY = "E-Bike"
├─ MTB related           ─────► BENCHMARK_CATEGORY = "MTB"
├─ City/Trekking related ─────► BENCHMARK_CATEGORY = "City/Trekking"
├─ Kinder related        ─────► BENCHMARK_CATEGORY = "Kinder"
└─ Others                ─────► BENCHMARK_CATEGORY = "Sonstige"
```

### Cost Categories (To be discovered)

```
T_COST_RECORD.COST_CATEGORY (Actual names TBD)
│
├─ "???" ─────► OPERATING_COST_EUR (Rent, utilities, marketing?)
├─ "???" ─────► PERSONNEL_COST_EUR (Salaries, benefits?)
└─ "???" ─────► PROCUREMENT_EXTRA_EUR (Additional procurement?)
```

**Action Required:** Execute discovery query to identify actual category names

---

## Store Dimension

```
T_SALESORG.SALESORG_ID  →  T_SALESORG.STORE_LOCATION
│
├─ ?? (TBD) ────────────────► "Rosenheim"
└─ ?? (TBD) ────────────────► "Freiburg"
```

**Action Required:** Execute query 1.1 from ACTION_PLAN_QUERIES.sql to identify IDs

---

## Join Patterns in Benchmark Views

### Pattern 1: Sales Aggregation → KPI View
```sql
FROM V_BENCHMARK_SALES_AGG s
LEFT JOIN V_BENCHMARK_COSTS_AGG c
    ON c.ID_CALMONTH_STD = s.ID_CALMONTH_STD
    AND c.ID_STORE = s.ID_STORE
    AND c.ID_CATEGORY = s.ID_CATEGORY
LEFT JOIN V_BENCHMARK_HEADCOUNT h
    ON h.ID_CALMONTH_STD = s.ID_CALMONTH_STD
    AND h.ID_STORE = s.ID_STORE
```

**Why LEFT JOIN?**
- Not all month/store/category combinations may have costs
- Headcount is at Store level, not Category level

### Pattern 2: KPI → Store Comparison
```sql
SELECT
    k.ID_CALMONTH_STD,
    k.ID_CATEGORY,
    SUM(CASE WHEN k.STORE_NAME = 'Freiburg' THEN k.UMSATZ_EUR END) as UMSATZ_FREIBURG,
    SUM(CASE WHEN k.STORE_NAME = 'Rosenheim' THEN k.UMSATZ_EUR END) as UMSATZ_ROSENHEIM
FROM V_BENCHMARK_KPI k
WHERE k.STORE_NAME IN ('Freiburg', 'Rosenheim')
GROUP BY k.ID_CALMONTH_STD, k.ID_CATEGORY
```

**Purpose:** Pivot from Store rows to Store columns for side-by-side comparison

---

## Data Volume Estimates (Assuming full year 2026)

```
T_ETL_MONTHLY_SALES (Detail Level)
= 2 stores × 12 months × ~100 materials × ~10 transactions/month
≈ 24,000 - 100,000 rows

V_BENCHMARK_SALES_AGG (Aggregated)
= 2 stores × 12 months × 5 categories
= 120 rows

V_BENCHMARK_COSTS_AGG
= 2 stores × 12 months × 5 categories × 3 cost types
≈ 360 rows (or less if not all combinations exist)

V_BENCHMARK_HEADCOUNT
= 2 stores × 12 months
= 24 rows

V_BENCHMARK_KPI (Main view)
= 2 stores × 12 months × 5 categories
= 120 rows

V_BENCHMARK_STORE_COMPARISON
= 12 months × 5 categories
= 60 rows
```

**Performance Impact:** LOW - All aggregated views are small, well within performance targets

---

## NULL Handling Strategy

### Where NULLs Can Occur

```
V_BENCHMARK_COSTS_AGG.OPERATING_COST_EUR
│
└─ NULL if no operating costs for that month/store/category

V_BENCHMARK_HEADCOUNT.EMPLOYEE_COUNT
│
└─ NULL if no employee data available
   OR 0 if calculated but no employees

V_BENCHMARK_KPI calculations:
│
├─ BRUTTOGEWINN_MARGE_PROZ
│  └─ NULL if REVENUE = 0 (avoid division by zero)
│
├─ BETRIEBSKOSTEN_QUOTE_PROZ
│  └─ NULL if REVENUE = 0
│
├─ PERSONALKOSTEN_ANTEIL_PROZ
│  └─ NULL if BRUTTOGEWINN <= 0
│
└─ UMSATZ_PRO_MA_EUR
   └─ NULL if EMPLOYEE_COUNT = 0 or NULL
```

**Strategy:** Use CASE statements to return NULL instead of dividing by zero

```sql
CASE WHEN s.REVENUE_EUR = 0 THEN NULL
     ELSE s.GROSS_PROFIT_EUR * 100.0 / s.REVENUE_EUR
END AS BRUTTOGEWINN_MARGE_PROZ
```

---

## Summary: Data Model Layers

1. **Master Data** (Static or slow-changing)
   - T_SALESORG, T_MATERIAL, T_PRODUCT_CATEGORY, T_EMPLOYEE

2. **Transactional Data** (Monthly loads)
   - T_ETL_MONTHLY_SALES, T_ETL_MONTHLY_COSTS

3. **Enrichment Views** (Already exist)
   - V_LIST_MONTHLY_SALES, V_LIST_MONTHLY_COSTS

4. **Standardization Layer** (To build)
   - V_BENCHMARK_SALES_STD

5. **Aggregation Layer** (1 exists, 2 to build)
   - V_BENCHMARK_SALES_AGG ✅
   - V_BENCHMARK_COSTS_AGG ⬜
   - V_BENCHMARK_HEADCOUNT ⬜

6. **KPI Layer** (To build)
   - V_BENCHMARK_KPI

7. **Reporting Layer** (To build)
   - V_BENCHMARK_STORE_COMPARISON
   - V_BENCHMARK_EXPORT_MONTHLY

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-25 | Initial data model documentation |

---

**Related Documents:**
- EXECUTIVE_SUMMARY.md
- ANALYSIS_DATABASE_SYSTEM_CONCEPT.md
- ACTION_PLAN_QUERIES.sql
