# Dashboard Architektur - Gruppe 18

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BENUTZER                                        │
│                           (Browser/Streamlit)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAMLIT FRONTEND                                  │
│                              (app.py)                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Tab 1    │  │    Tab 2    │  │    Tab 3    │  │    Tab 4    │        │
│  │   Finanz-   │  │  Marketing  │  │   Kosten-   │  │  Produkt-   │        │
│  │ performance │  │             │  │   analyse   │  │ kategorien  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │                    SIDEBAR (Filter)                          │           │
│  │  • Monatsauswahl (Jan-Dez / Alle)                           │           │
│  │  • Store-Auswahl (Multi-Select)                             │           │
│  │  • Logout-Button                                            │           │
│  └──────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  AUTHENTIFIZIERUNG │     │     CHARTS      │     │   SERVICES      │
│  (src/auth/)       │     │  (src/charts/)  │     │ (src/services/) │
│                    │     │                 │     │                 │
│ • login_ui.py      │     │ • base.py       │     │ • aggregations  │
│ • authentication   │     │ • financial.py  │     │ • filters       │
│                    │     │ • marketing.py  │     │                 │
│ Security Level     │     │ • categories.py │     │ KPI-Berechnung  │
│ Check (3 oder 4)   │     │                 │     │ Daten-Aggregat. │
└─────────────────┘     │ Plotly Figures  │     └─────────────────┘
                         └─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│                        (src/db/repository.py)                                │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────┐        │
│   │              STREAMLIT CACHE (@st.cache_data)                  │        │
│   │                     TTL: 60-300 Sekunden                       │        │
│   └────────────────────────────────────────────────────────────────┘        │
│                                                                              │
│   • load_export_monthly()     → Tab 1: Trend-Charts                         │
│   • load_kpi()                → Tab 1: KPI-Cards                            │
│   • load_marketing_kpi()      → Tab 2: Marketing-KPIs                       │
│   • load_marketing_by_campaign() → Tab 2: ROAS, ROMI                        │
│   • load_costs_agg()          → Tab 3: Kostenübersicht                      │
│   • load_sales_agg()          → Tab 4: Kategorie-Analyse                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE CONNECTION                                  │
│                        (src/db/connection.py)                                │
│                                                                              │
│   ┌─────────────────────┐         ┌─────────────────────┐                   │
│   │   LOKAL (config.json) │         │  CLOUD (st.secrets) │                   │
│   │   Priorität 1        │         │  Priorität 2        │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
│                                                                              │
│   ┌─────────────────────┐         ┌─────────────────────┐                   │
│   │      pymssql        │ ──OR──▶ │      pyodbc         │                   │
│   │   (Cloud-kompatibel) │         │  (Lokal mit ODBC)   │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SQL SERVER                                         │
│                        (edu.hdm-server.eu)                                   │
│                          Database: ERPDEV                                    │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │                    SQL VIEWS (list_views)                   │           │
│   ├─────────────────────────────────────────────────────────────┤           │
│   │ V_LIST_G18_BENCHMARK_EXPORT_MONTHLY  → Monatliche KPIs      │           │
│   │ V_LIST_G18_BENCHMARK_KPI             → Aggregierte KPIs     │           │
│   │ V_LIST_G18_MARKETING_KPI_MONTHLY     → Marketing-Metriken   │           │
│   │ V_LIST_G18_MARKETING_BY_CAMPAIGN     → ROAS, ROMI, CPA      │           │
│   │ V_LIST_G18_BENCHMARK_COSTS_AGG       → Kostenübersicht      │           │
│   │ V_LIST_G18_BENCHMARK_SALES_AGG       → Verkaufsanalyse      │           │
│   │ V_LIST_G18_STORE_DETAILS             → Filial-Stammdaten    │           │
│   └─────────────────────────────────────────────────────────────┘           │
│                                    │                                         │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │                   BASE TABLES (dbo)                         │           │
│   ├─────────────────────────────────────────────────────────────┤           │
│   │ V_LIST_MONTHLY_SALES      → Verkaufsdaten                   │           │
│   │ T_MARKETING_CAMPAIGN_COST → Marketing-Kosten                │           │
│   │ LOV_USER_LOGINS           → Benutzer-Authentifizierung      │           │
│   │ T_STORE_COST              → Filial-Kosten                   │           │
│   └─────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Datenfluss

```
┌──────────┐    Login     ┌──────────┐   Query    ┌──────────┐
│  User    │ ──────────▶  │ Streamlit │ ────────▶  │   SQL    │
│ (Browser)│              │   App    │            │  Server  │
└──────────┘              └──────────┘            └──────────┘
     ▲                         │                       │
     │                         │                       │
     │    Dashboard            │   DataFrame           │
     └─────────────────────────┴───────────────────────┘
```

---

## Authentifizierungs-Flow

```
┌─────────────┐
│ Login-Page  │
│ (Username,  │
│  Password)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│   authenticate_user()       │
│   (Service-Account-Query)   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Check: LOV_USER_LOGINS     │
│  • Username + Password      │
│  • Security Level           │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐     ┌─────────────────┐
│  Security Level 3 oder 4?   │─NO─▶│  Zugriff        │
└──────┬──────────────────────┘     │  verweigert     │
       │ YES                         └─────────────────┘
       ▼
┌─────────────────────────────┐
│   Session State setzen      │
│   • authenticated = True    │
│   • security_level          │
│   • username                │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│     Dashboard anzeigen      │
└─────────────────────────────┘
```

---

## KPI-Berechnungen

### ROAS (Return on Advertising Spend)
```
ROAS = RevenueEur / CostEur

Beispiel: 10.000€ Umsatz / 1.000€ Kosten = 10x
```

### ROMI (Return on Marketing Investment)
```
ROMI = CampaignProfit / CostEur
     = (RevenueEur - CostEur - DiscountEur) / CostEur
     ≈ ROAS - 1  (wenn Discount klein)

Beispiel: 8.900€ Profit / 1.000€ Kosten = 8.9x
```

### Bruttomarge
```
Bruttomarge (%) = Bruttogewinn / Umsatz × 100
```

---

## Projektstruktur

```
Benchmark_18/
├── app.py                      # Haupt-Streamlit-App
├── config.json                 # DB-Credentials (lokal, gitignore)
│
├── src/
│   ├── auth/
│   │   ├── authentication.py   # Login-Logik
│   │   └── login_ui.py         # Login-UI-Komponenten
│   │
│   ├── charts/
│   │   ├── base.py             # Shared Chart-Funktionen
│   │   ├── financial.py        # Tab 1: Finanz-Charts
│   │   ├── marketing.py        # Tab 2: Marketing-Charts
│   │   └── categories.py       # Tab 4: Kategorie-Charts
│   │
│   ├── config/
│   │   ├── stores.py           # Store-Konfiguration
│   │   └── categories.py       # Produktkategorien
│   │
│   ├── db/
│   │   ├── connection.py       # DB-Verbindung
│   │   ├── queries.py          # SQL-Queries
│   │   └── repository.py       # Data Loader mit Cache
│   │
│   ├── services/
│   │   ├── aggregations.py     # KPI-Aggregationen
│   │   └── filters.py          # Daten-Filter
│   │
│   └── utils/
│       └── formatting.py       # Formatierungs-Helfer
│
├── sql/
│   └── CREATE_VIEWS.sql        # SQL View Definitionen
│
└── .streamlit/
    └── secrets.toml            # Cloud-Credentials (gitignore)
```

---

## Technologie-Stack

| Komponente | Technologie |
|------------|-------------|
| **Frontend** | Streamlit |
| **Charts** | Plotly |
| **Database** | SQL Server |
| **DB-Connector** | pymssql / pyodbc |
| **Caching** | Streamlit Cache |
| **Deployment** | Streamlit Cloud |
| **Versionierung** | Git |
