# Benchmarking System - Executive Summary

**Date:** 2025-11-25
**Project:** Branch Benchmarking Rosenheim & Freiburg
**Group:** 18 (Marco, Harun, Duy)

---

## 1. Current Status: Database vs. System Concept

### ✅ What We Have (Ready to Use)

| Component | Status | Notes |
|-----------|--------|-------|
| **T_ETL_MONTHLY_SALES** | ✅ Complete | All sales data available with revenue, gross profit, discounts |
| **T_ETL_MONTHLY_COSTS** | ✅ Complete | Monthly cost records exist |
| **T_SALESORG** | ✅ Complete | Branch master data (Rosenheim, Freiburg) |
| **T_EMPLOYEE** | ✅ Complete | Employee assignments and salaries |
| **T_MATERIAL** | ✅ Complete | Product master with categories |
| **V_LIST_MONTHLY_SALES** | ✅ Ready | Enriched sales view with material and campaign info |
| **V_LIST_MONTHLY_COSTS** | ✅ Ready | Enriched cost view with category names |
| **V_BENCHMARK_SALES_AGG** | ✅ **Already Implemented!** | First aggregation view from system concept section 4.2.1 |

---

### ⚠️ What Needs Action

| Component | Priority | Issue | Solution |
|-----------|----------|-------|----------|
| **T_STORE_HEADCOUNT** | 🔴 **HIGH** | Table doesn't exist | Calculate from T_EMPLOYEE or use fixed counts |
| **V_BENCHMARK_SALES_STD** | 🔴 **HIGH** | Missing standardization view | Create from T_ETL_MONTHLY_SALES + enrichment |
| **V_BENCHMARK_COSTS_AGG** | 🔴 **HIGH** | Not implemented | Create with cost category mapping |
| **V_BENCHMARK_HEADCOUNT** | 🔴 **HIGH** | Depends on headcount data | Create after headcount strategy decided |
| **V_BENCHMARK_KPI** | 🟡 **MEDIUM** | Central KPI view missing | Create after above views ready |
| **V_BENCHMARK_STORE_COMPARISON** | 🟡 **MEDIUM** | Comparison view missing | Create from V_BENCHMARK_KPI |
| **V_BENCHMARK_EXPORT_MONTHLY** | 🟢 **LOW** | Export view missing | Final reporting layer |

---

## 2. Critical Decisions Needed

### Decision 1: Headcount Data Strategy (Blocks KPI "Revenue per Employee")

**Options:**

**A) Calculate from T_EMPLOYEE** (Recommended)
- Count active employees per branch per month
- ⚠️ Limitation: Assumes all employees worked all analysis months
- ✅ Advantage: Uses existing data, no manual input

**B) Create T_STORE_HEADCOUNT table manually**
- Manually enter accurate employee counts per month/branch
- ✅ Advantage: Most accurate
- ⚠️ Disadvantage: Requires manual data entry

**C) Use fixed headcount per branch**
- Simple: 10 employees in Rosenheim, 8 in Freiburg (example)
- ✅ Advantage: Quickest implementation
- ⚠️ Disadvantage: Least accurate

**👉 Action Required:** Team decision on approach A, B, or C

---

### Decision 2: Cost Category Mapping

The system concept requires categorizing costs as:
- **Betriebskosten_EUR** (Operating Costs)
- **Personalkosten_EUR** (Personnel Costs)
- **Zusätzliche Beschaffungskosten_EUR** (Additional Procurement)

**👉 Action Required:** Execute query `ACTION_PLAN_QUERIES.sql` Section 1.2 to discover actual cost category names, then create mapping

---

## 3. Implementation Sequence

### Phase 1: Foundation (**Week 1** - Start Immediately)
1. ✅ **DONE:** Database structure analysis (this document)
2. ⬜ **Execute discovery queries** (`ACTION_PLAN_QUERIES.sql` Section 1)
3. ⬜ **Decide headcount strategy** (Decision 1)
4. ⬜ **Map cost categories** (Decision 2)
5. ⬜ **Create V_BENCHMARK_SALES_STD**

### Phase 2: Aggregation (**Week 2**)
6. ⬜ Create V_BENCHMARK_COSTS_AGG
7. ⬜ Create V_BENCHMARK_HEADCOUNT
8. ⬜ Validate V_BENCHMARK_SALES_AGG (already exists)

### Phase 3: KPIs (**Week 3**)
9. ⬜ Create V_BENCHMARK_KPI (all metrics)
10. ⬜ Test calculations manually (TF02)

### Phase 4: Reporting (**Week 4**)
11. ⬜ Create V_BENCHMARK_STORE_COMPARISON
12. ⬜ Create V_BENCHMARK_EXPORT_MONTHLY
13. ⬜ Create V_BENCHMARK_SALES_ERRORS (data quality)

### Phase 5: Testing & Acceptance (**Week 5**)
14. ⬜ Execute test cases TF01-TF05
15. ⬜ Verify acceptance criteria SPC01-SPC05
16. ⬜ Performance testing (<5 seconds)

---

## 4. KPI Calculation Status

| KPI | Data Available? | Calculation Ready? |
|-----|-----------------|-------------------|
| **Gross Margin %** | ✅ Yes (GROSS_PROFIT_EUR / REVENUE) | ✅ Ready |
| **Operating Cost Ratio %** | ⚠️ Need cost category mapping | After Phase 1 |
| **Personnel Cost Ratio %** | ⚠️ Need cost breakdown | After Phase 1 |
| **Revenue per Employee** | ❌ Missing headcount data | After Decision 1 |
| **Average Sales Price** | ✅ Yes (REVENUE / SALES_AMOUNT) | ✅ Ready |
| **Total Costs** | ⚠️ Need cost aggregation | After Phase 2 |

---

## 5. Risk Assessment

| Risk | Impact | Mitigation Status |
|------|--------|-------------------|
| **Missing T_STORE_HEADCOUNT table** | 🔴 HIGH | ✅ 3 solution options identified |
| **Incomplete monthly data for 2026** | 🔴 HIGH | ⬜ Run data quality check (Section 2.4 in queries) |
| **Unknown cost category names** | 🟡 MEDIUM | ⬜ Discovery query ready (Section 1.2) |
| **Performance issues** | 🟢 LOW | ⬜ Test with Section 7 queries |

---

## 6. Files Created for You

### 📄 [ANALYSIS_DATABASE_SYSTEM_CONCEPT.md](ANALYSIS_DATABASE_SYSTEM_CONCEPT.md)
**Purpose:** Complete technical analysis (19 pages)
**Contains:**
- Detailed database structure analysis
- Table-by-table assessment
- Data flow diagrams
- SQL implementation templates
- Test strategies

### 📄 [ACTION_PLAN_QUERIES.sql](ACTION_PLAN_QUERIES.sql)
**Purpose:** Ready-to-execute SQL queries
**Contains:**
- 8 sections of discovery and validation queries
- Data quality checks
- Cost analysis queries
- Headcount calculation examples
- Performance testing queries

**👉 Execute these queries first to gather information!**

---

## 7. Next Immediate Actions (Today)

### 1. Execute Discovery Queries (30 minutes)
```sql
-- Run these from ACTION_PLAN_QUERIES.sql:
-- Section 1.1: Identify Store IDs
-- Section 1.2: Discover Cost Categories
-- Section 1.3: Check Available Months
-- Section 1.5: Analyze Employee Distribution
```

### 2. Team Meeting: Make Decisions (30 minutes)
- **Decision 1:** Choose headcount strategy (A, B, or C)
- **Decision 2:** Review cost categories and create mapping

### 3. Data Quality Validation (30 minutes)
```sql
-- Run Section 2 from ACTION_PLAN_QUERIES.sql:
-- Check for missing data, negative values, completeness
```

### 4. Start Implementation (remainder of day)
- Create V_BENCHMARK_SALES_STD based on template
- (See ANALYSIS document Section 9.1 for SQL template)

---

## 8. Success Criteria (From System Concept)

| ID | Criterion | Status | Notes |
|----|-----------|--------|-------|
| **SPC01** | Net profit = Gross profit - Total costs | ⬜ | Need cost aggregation |
| **SPC02** | Total costs = sum of all cost categories | ⬜ | Need cost mapping |
| **SPC03** | All 12 months present for both branches | ⬜ | **Check immediately** (Query 2.4) |
| **SPC04** | Role-based access control | ⬜ | Phase 5 |
| **SPC05** | Query performance < 5 seconds | ⬜ | Test in Phase 5 |

---

## 9. Key Findings

### ✅ Good News
1. **V_BENCHMARK_SALES_AGG already exists** - saves significant time
2. **All base data tables are present** - T_ETL_MONTHLY_SALES, T_ETL_MONTHLY_COSTS, etc.
3. **Enriched views available** - V_LIST_MONTHLY_SALES and V_LIST_MONTHLY_COSTS already join master data
4. **Material categorization possible** - T_PRODUCT_CATEGORY exists with proper structure

### ⚠️ Challenges
1. **Headcount data missing** - Critical for "Revenue per Employee" KPI
2. **Cost category mapping unknown** - Must discover actual category names in database
3. **Personnel cost calculation complex** - Need to combine salary + commission + social costs
4. **7 views still need implementation** - But we have templates ready

---

## 10. Questions for Project Sponsors

1. **Headcount Data:**
   - Is there an ETL process that can provide T_STORE_HEADCOUNT?
   - Or should we calculate from T_EMPLOYEE?
   - Or use fixed counts?

2. **Analysis Period:**
   - Confirm analysis period is January-December 2026?
   - Is data complete for all 12 months?

3. **Personnel Costs:**
   - Are personnel costs included in T_ETL_MONTHLY_COSTS?
   - Or should we calculate from T_EMPLOYEE + T_APPLICANTS?

4. **Timeline:**
   - Is 5-week implementation timeline acceptable?
   - Any specific deadlines?

---

## Document References

- **System Concept PDF:** `MS04_Benchmark_Gruppe_18 (2).pdf`
- **Database Structure:** `db_structure.xlsx`
- **Technical Analysis:** `ANALYSIS_DATABASE_SYSTEM_CONCEPT.md`
- **SQL Queries:** `ACTION_PLAN_QUERIES.sql`

---

**Status:** Analysis Complete ✅
**Next Step:** Execute discovery queries and make decisions 🚀
**Estimated Time to First Working View:** 2-3 hours after decisions made

---

**Prepared by:** Claude AI Analysis
**For:** Group 18 (Marco, Harun, Duy)
**Date:** 2025-11-25
