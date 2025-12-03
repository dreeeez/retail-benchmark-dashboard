# Benchmarking-System - Gruppe 18
## Phase 4 - Systemkonzept

**Projektname:** Benchmarking-System für Filialen Rosenheim & Freiburg/Karlsruhe
**Verfasser:** Marco, Harun, Duy
**Datum:** 17.11.2025

---

## Übersicht

Dieses System ermöglicht den Vergleich (Benchmarking) der Filialen Rosenheim und Freiburg/Karlsruhe anhand verschiedener KPIs wie Umsatz, Bruttogewinn, Margen und Kostenquoten.

## Dateistruktur

```
Benchmark_18/
├── benchmark_views.sql          # SQL Views für das Benchmarking
├── benchmark_dashboard.py       # Python Dashboard-Skript
├── benchmark_analysis.ipynb     # Jupyter Notebook für interaktive Analyse
├── db_connect.py                # Datenbankverbindung
├── config.json                  # Konfigurationsdatei (DB-Credentials)
├── fetch_data.py               # Einfaches Datenabfrage-Skript
└── README.md                    # Diese Dokumentation
```

## Installation

### 1. SQL Views erstellen

Führe das SQL-Skript auf dem SQL Server aus:

```sql
-- Im SQL Server Management Studio oder Azure Data Studio:
-- Öffne benchmark_views.sql und führe es aus
```

**Erstellte Views:**
- `V_BENCHMARK_SALES_STD` - Standardisierte Verkaufsdaten
- `V_BENCHMARK_SALES_ERRORS` - Fehlerdaten (optional)
- `V_BENCHMARK_SALES_AGG` - Aggregierte Verkaufsdaten
- `V_BENCHMARK_COSTS_AGG` - Aggregierte Kostendaten
- `V_BENCHMARK_COSTS_TOTAL` - Gesamtkosten
- `V_BENCHMARK_HEADCOUNT` - Mitarbeiteranzahl
- `V_BENCHMARK_KPI` - Zentrale KPI-View
- `V_BENCHMARK_STORE_COMPARISON` - Filialvergleich
- `V_BENCHMARK_EXPORT_MONTHLY` - Export-View

### 2. Python-Umgebung einrichten

```bash
# Erforderliche Pakete installieren
pip install pandas matplotlib openpyxl pyodbc
```

### 3. Datenbank-Konfiguration

Die `config.json` enthält die Datenbankverbindung:

```json
{
    "server": "edu.hdm-server.eu",
    "database": "ERPDEV",
    "user": "w25s228",
    "password": "******"
}
```

## Verwendung

### Dashboard ausführen

```bash
python benchmark_dashboard.py
```

Das Dashboard erstellt:
- Charts im Ordner `charts/`
- Excel-Report `benchmark_report.xlsx`

### Jupyter Notebook

```bash
jupyter notebook benchmark_analysis.ipynb
```

Für interaktive Analyse und Exploration der Daten.

## Implementierte KPIs

| KPI | Formel | Beschreibung |
|-----|--------|--------------|
| Bruttogewinn-Marge (%) | Bruttogewinn / Umsatz × 100 | Profitabilität vor Kosten |
| Nettomarge (%) | (Bruttogewinn - Gesamtkosten) / Umsatz × 100 | Profitabilität nach Kosten |
| Betriebskosten-Quote (%) | Betriebskosten / Umsatz × 100 | Effizienz der Betriebsführung |
| Personalkosten-Anteil (%) | Personalkosten / Umsatz × 100 | Anteil der Personalkosten |
| Umsatz pro Mitarbeiter | Umsatz / Mitarbeiteranzahl | Produktivität |

## View-Schichten

```
┌─────────────────────────────────────────┐
│        V_BENCHMARK_EXPORT_MONTHLY       │  Export/Reporting
├─────────────────────────────────────────┤
│  V_BENCHMARK_KPI  │  V_BENCHMARK_STORE_ │  KPI & Vergleich
│                   │     COMPARISON      │
├─────────────────────────────────────────┤
│ V_BENCHMARK_SALES_AGG │ V_BENCHMARK_    │  Aggregation
│                       │ COSTS_TOTAL     │
├─────────────────────────────────────────┤
│      V_BENCHMARK_SALES_STD              │  Standardisierung
├─────────────────────────────────────────┤
│  T_ETL_MONTHLY_SALES  │ T_ETL_MONTHLY_  │  Basistabellen
│  T_SALESORG │ T_MATERIAL│ COSTS         │
└─────────────────────────────────────────┘
```

## Rollen & Berechtigungen

| Rolle | Zugriff auf Views |
|-------|-------------------|
| Management | V_BENCHMARK_KPI, V_BENCHMARK_STORE_COMPARISON, V_BENCHMARK_EXPORT_MONTHLY |
| Controlling | Alle Views inkl. Fehler-View |
| Vertrieb | V_BENCHMARK_KPI (gefiltert) |

## Testfälle

- **TF01:** Monatsaggregation korrekt
- **TF02:** Kennzahlenberechnung korrekt
- **TF03:** Fehlerdaten werden erkannt
- **TF04:** Filialvergleich korrekt
- **TF05:** Export-View vollständig

## Akzeptanzkriterien

- **SPC01:** Nettogewinn = Bruttogewinn - Gesamtkosten
- **SPC02:** Gesamtkosten entsprechen Summe der Einzelkosten
- **SPC03:** 12 Monate Daten für beide Filialen
- **SPC04:** Rollenbasierte Zugriffskontrolle
- **SPC05:** View-Abruf < 5 Sekunden

---

**Gruppe 18** | Phase 4 - Systemkonzept Benchmarking
