# Benchmark System - Gruppe 18
## Rosenheim vs. Freiburg/Karlsruhe Vergleich

---

## Überblick

Dieses System vergleicht die Performance von zwei Filialgruppen:
- **Rosenheim** (ID_STORE = 14)
- **Freiburg/Karlsruhe kombiniert** (ID_STORE = 3, 5)

Das System besteht aus **6 Views** in **5 Layern** (Standardisierung → Aggregation → KPI → Vergleich → Export).

---

## Layer 1: Standardisierung

### View 1: `list_views.V_LIST_G18_BENCHMARK_SALES_STD`

**Zweck:** Verkaufsdaten standardisieren und mit Stammdaten anreichern

**Output-Struktur:**

| Spalte | Typ | Beschreibung | Beispiel |
|--------|-----|--------------|----------|
| `IdCalmonthStd` | varchar | Monat im Format YYYY-MM | '2024-09' |
| `IdStore` | int | Filial-ID | 3, 5, oder 14 |
| `StoreName` | varchar | Filialname | 'Karlsruhe', 'Freiburg', 'Rosenheim' |
| `IdMaterial` | int | Material-ID | 9 |
| `MaterialDescription` | varchar | Produktbeschreibung | 'Town Lite Rohloff GTS 2012 He' |
| `BenchmarkCategory` | varchar | Produktkategorie | 'E-Bike', 'MTB', 'City/Trekking', 'Kinder', 'Sonstige' |
| `RevenueEur` | money | Umsatz in EUR | 7797.00 |
| `GrossProfitEur` | money | Bruttogewinn (berechnet) | 1084.20 |
| `TransferCostEur` | money | Transferpreis pro Einheit | 6237.60 |
| `SalesPriceEur` | money | Verkaufspreis pro Einheit | 2599.00 |
| `Quantity` | int | Verkaufte Menge | 3 |

**Besonderheiten:**
- Bruttogewinn wird berechnet: `RevenueEUR - (TransferPriceEUR * SalesAmount)`
- Produktkategorien werden aus der Produktbeschreibung abgeleitet
- Nur die 3 Benchmark-Filialen (3, 5, 14) werden berücksichtigt

---

## Layer 2: Aggregation

### View 2: `list_views.V_LIST_G18_BENCHMARK_SALES_AGG`

**Zweck:** Verkaufsdaten nach Monat, Filiale und Kategorie aggregieren

**Output-Struktur:**

| Spalte | Typ | Beschreibung | Beispiel |
|--------|-----|--------------|----------|
| `IdCalmonthStd` | varchar | Monat im Format YYYY-MM | '2024-09' |
| `IdStore` | int | Filial-ID | 3 |
| `StoreName` | varchar | Filialname | 'Karlsruhe' |
| `BenchmarkCategory` | varchar | Produktkategorie | 'E-Bike' |
| `TotalRevenueEur` | money | Gesamtumsatz der Kategorie | 45000.00 |
| `TotalGrossProfitEur` | money | Gesamtbruttogewinn | 12500.00 |
| `TotalTransferCostEur` | money | Gesamte Transferkosten | 32500.00 |
| `AvgSalesPriceEur` | money | Durchschnittlicher Verkaufspreis | 2500.00 |
| `TotalQuantity` | int | Gesamtmenge verkauft | 18 |

**Gruppierung:** Eine Zeile pro Monat + Filiale + Kategorie

**Beispiel:**
```
2024-09 | Karlsruhe | E-Bike    | 45000.00 EUR | 18 Stück
2024-09 | Karlsruhe | MTB       | 30000.00 EUR | 12 Stück
2024-09 | Freiburg  | E-Bike    | 38000.00 EUR | 15 Stück
```

---

### View 3: `list_views.V_LIST_G18_BENCHMARK_COSTS_AGG`

**Zweck:** Kosten nach Monat und Filiale aggregieren

**Output-Struktur:**

| Spalte | Typ | Beschreibung | Beispiel |
|--------|-----|--------------|----------|
| `IdCalmonthStd` | varchar | Monat im Format YYYY-MM | '2024-09' |
| `IdStore` | int | Filial-ID | 3 |
| `StoreName` | varchar | Filialname | 'Karlsruhe' |
| `TotalCostsEur` | money | Gesamtkosten | 25000.00 |
| `PersonnelCostsEur` | money | Personalkosten (Gehalt + Sozialkosten) | 15000.00 |
| `OperatingCostsEur` | money | Betriebskosten (Miete + Marketing + Kommission) | 8000.00 |
| `AdditionalProcurementCostsEur` | money | Zusätzliche Beschaffungskosten | 2000.00 |

**Kostenarten-Mapping:**

| Output-Spalte | Kostenkategorien (aus `V_LIST_MONTHLY_COSTS`) |
|---------------|-----------------------------------------------|
| `PersonnelCostsEur` | 'Monthly Salary' + 'Monthly Social Costs' |
| `OperatingCostsEur` | 'Monthly Rent' + 'Marketing Campaign' + 'Commission' |
| `AdditionalProcurementCostsEur` | 'Additional Procurement Costs' |

**Gruppierung:** Eine Zeile pro Monat + Filiale

---

## Layer 3: KPI-Berechnung

### View 4: `list_views.V_LIST_G18_BENCHMARK_KPI`

**Zweck:** Zentrale Kennzahlen (KPIs) pro Monat und Filiale berechnen

**Output-Struktur:**

| Spalte | Typ | Beschreibung | Berechnung | Beispiel |
|--------|-----|--------------|------------|----------|
| `IdCalmonthStd` | varchar | Monat | - | '2024-09' |
| `IdStore` | int | Filial-ID | - | 3 |
| `StoreName` | varchar | Filialname | - | 'Karlsruhe' |
| `TotalRevenueEur` | money | Gesamtumsatz (alle Kategorien) | SUM(RevenueEur) | 75000.00 |
| `TotalGrossProfitEur` | money | Gesamtbruttogewinn | SUM(GrossProfitEur) | 20000.00 |
| `TotalCostsEur` | money | Gesamtkosten | Aus COSTS_AGG | 25000.00 |
| `PersonnelCostsEur` | money | Personalkosten | Aus COSTS_AGG | 15000.00 |
| `OperatingCostsEur` | money | Betriebskosten | Aus COSTS_AGG | 8000.00 |
| `NetProfitEur` | money | Nettogewinn | GrossProfitEur - TotalCostsEur | -5000.00 |
| `GrossProfitMarginPct` | decimal | Bruttogewinn-Marge (%) | (GrossProfitEur / RevenueEur) * 100 | 26.67% |
| `OperatingCostRatioPct` | decimal | Betriebskosten-Quote (%) | (OperatingCostsEur / RevenueEur) * 100 | 10.67% |
| `PersonnelCostRatioPct` | decimal | Personalkosten-Anteil (%) | (PersonnelCostsEur / TotalCostsEur) * 100 | 60.00% |
| `NetProfitMarginPct` | decimal | Nettogewinn-Marge (%) | (NetProfitEur / RevenueEur) * 100 | -6.67% |

**Gruppierung:** Eine Zeile pro Monat + Filiale

**KPI-Erklärungen:**

1. **Bruttogewinn-Marge (%)**: Zeigt, wie viel vom Umsatz nach Abzug der Warenkosten übrig bleibt
   - Höher = besser
   - Benchmark: 20-30% ist typisch im Einzelhandel

2. **Betriebskosten-Quote (%)**: Zeigt den Anteil der Betriebskosten am Umsatz
   - Niedriger = besser
   - Beinhaltet Miete, Marketing, Kommissionen

3. **Personalkosten-Anteil (%)**: Zeigt, wie viel von den Gesamtkosten für Personal ausgegeben wird
   - Typisch: 50-70%

4. **Nettogewinn-Marge (%)**: Der "Bottom Line" - was am Ende übrig bleibt
   - Positiv = profitabel
   - Negativ = Verlust

---

## Layer 4: Vergleich (UNION)

### View 5: `list_views.V_LIST_G18_BENCHMARK_STORE_COMPARISON`

**Zweck:** Side-by-Side Vergleich der beiden Filialgruppen

**Output-Struktur:**

| Spalte | Typ | Beschreibung | Beispiel |
|--------|-----|--------------|----------|
| `IdCalmonthStd` | varchar | Monat | '2024-09' |
| `StoreGroup` | varchar | Filialgruppe | 'Rosenheim' oder 'Freiburg/Karlsruhe' |
| `TotalRevenueEur` | money | Gesamtumsatz | 150000.00 |
| `TotalGrossProfitEur` | money | Gesamtbruttogewinn | 40000.00 |
| `TotalCostsEur` | money | Gesamtkosten | 50000.00 |
| `PersonnelCostsEur` | money | Personalkosten | 30000.00 |
| `OperatingCostsEur` | money | Betriebskosten | 16000.00 |
| `NetProfitEur` | money | Nettogewinn | -10000.00 |
| `GrossProfitMarginPct` | decimal | Bruttogewinn-Marge (%) | 26.67% |
| `OperatingCostRatioPct` | decimal | Betriebskosten-Quote (%) | 10.67% |
| `PersonnelCostRatioPct` | decimal | Personalkosten-Anteil (%) | 60.00% |
| `NetProfitMarginPct` | decimal | Nettogewinn-Marge (%) | -6.67% |

**Gruppierung:** Zwei Zeilen pro Monat (eine für jede Filialgruppe)

**Beispiel-Output:**
```
Monat   | Filialgruppe         | Umsatz     | Bruttogewinn | Nettogewinn | Bruttogewinn-Marge
--------|---------------------|------------|--------------|-------------|-------------------
2024-09 | Rosenheim           | 120000.00  | 32000.00     | -8000.00    | 26.67%
2024-09 | Freiburg/Karlsruhe  | 180000.00  | 48000.00     | -2000.00    | 26.67%
2024-10 | Rosenheim           | 135000.00  | 36000.00     | -4000.00    | 26.67%
2024-10 | Freiburg/Karlsruhe  | 195000.00  | 52000.00     | 2000.00     | 26.67%
```

**Wichtig:**
- Freiburg (ID 5) und Karlsruhe (ID 3) werden zu einer Gruppe kombiniert
- Alle Werte (Umsatz, Kosten, etc.) werden für Freiburg/Karlsruhe **addiert**
- KPIs werden für die kombinierte Gruppe **neu berechnet**

---

## Layer 5: Export

### View 6: `list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY`

**Zweck:** Export-fertige View mit deutschen Spaltennamen und gerundeten Werten

**Output-Struktur:**

| Spalte | Typ | Beschreibung | Beispiel |
|--------|-----|--------------|----------|
| `Monat` | varchar | Monat YYYY-MM | '2024-09' |
| `Filialgruppe` | varchar | Filialgruppe | 'Rosenheim' |
| `UmsatzEur` | decimal(18,2) | Umsatz (gerundet) | 120000.00 |
| `BruttogewinnEur` | decimal(18,2) | Bruttogewinn (gerundet) | 32000.00 |
| `GesamtkostenEur` | decimal(18,2) | Gesamtkosten (gerundet) | 40000.00 |
| `PersonalkostenEur` | decimal(18,2) | Personalkosten (gerundet) | 24000.00 |
| `BetriebskostenEur` | decimal(18,2) | Betriebskosten (gerundet) | 13000.00 |
| `NettogewinnEur` | decimal(18,2) | Nettogewinn (gerundet) | -8000.00 |
| `BruttogewinnMargeProzent` | decimal(18,2) | Bruttogewinn-Marge % (gerundet) | 26.67 |
| `BetriebskostenQuoteProzent` | decimal(18,2) | Betriebskosten-Quote % (gerundet) | 10.83 |
| `PersonalkostenAnteilProzent` | decimal(18,2) | Personalkosten-Anteil % (gerundet) | 60.00 |
| `NettogewinnMargeProzent` | decimal(18,2) | Nettogewinn-Marge % (gerundet) | -6.67 |

**Diese View ist ideal für:**
- Excel-Export
- PowerBI/Tableau Dashboards
- Management-Reports

**Alle Werte sind auf 2 Nachkommastellen gerundet!**

---

## Anwendungsbeispiele

### 1. Welche Filialgruppe ist profitabler?

```sql
SELECT
    Monat,
    Filialgruppe,
    UmsatzEur,
    NettogewinnEur,
    NettogewinnMargeProzent
FROM list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
ORDER BY Monat DESC, Filialgruppe;
```

### 2. Welche Produktkategorie verkauft sich am besten?

```sql
SELECT
    BenchmarkCategory,
    SUM(TotalRevenueEur) AS Gesamtumsatz,
    SUM(TotalQuantity) AS GesamtMenge
FROM list_views.V_LIST_G18_BENCHMARK_SALES_AGG
GROUP BY BenchmarkCategory
ORDER BY Gesamtumsatz DESC;
```

### 3. Kostenstruktur-Analyse

```sql
SELECT
    Filialgruppe,
    AVG(PersonalkostenAnteilProzent) AS DurchschnittPersonalkostenAnteil,
    AVG(BetriebskostenQuoteProzent) AS DurchschnittBetriebskostenQuote
FROM list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
GROUP BY Filialgruppe;
```

### 4. Zeitliche Entwicklung (Trend)

```sql
SELECT
    Monat,
    Filialgruppe,
    UmsatzEur,
    NettogewinnEur
FROM list_views.V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
ORDER BY Monat ASC, Filialgruppe;
```

---

## Architektur-Übersicht

```
Layer 1: STANDARDISIERUNG
└── V_LIST_G18_BENCHMARK_SALES_STD
    (Verkaufsdaten aufbereiten)

Layer 2: AGGREGATION
├── V_LIST_G18_BENCHMARK_SALES_AGG
│   (Verkäufe nach Monat/Filiale/Kategorie)
└── V_LIST_G18_BENCHMARK_COSTS_AGG
    (Kosten nach Monat/Filiale)

Layer 3: KPI-BERECHNUNG
└── V_LIST_G18_BENCHMARK_KPI
    (Kennzahlen berechnen)

Layer 4: VERGLEICH
└── V_LIST_G18_BENCHMARK_STORE_COMPARISON
    (Rosenheim vs. Freiburg/Karlsruhe)

Layer 5: EXPORT
└── V_LIST_G18_BENCHMARK_EXPORT_MONTHLY
    (Export-fertig, deutsche Spalten)
```

---

## Datenfluss

1. **Rohdaten** (V_LIST_MONTHLY_SALES, V_LIST_MONTHLY_COSTS)
   ↓
2. **Standardisierung** (Datumsformate, Kategorien zuweisen)
   ↓
3. **Aggregation** (Summen und Durchschnitte berechnen)
   ↓
4. **KPI-Berechnung** (Margen, Quoten, Anteile)
   ↓
5. **Vergleich** (Zwei Filialgruppen kombinieren)
   ↓
6. **Export** (Deutsche Namen, runden)

---

## Wichtige Hinweise

### Bruttogewinn-Berechnung
```
Bruttogewinn = Umsatz - (Transferpreis × Menge)
Beispiel: 7797 EUR - (6237.60 EUR × 3) = -10915.80 EUR
```

### Filialgruppen
- **Rosenheim**: ID_STORE = 14 (einzelne Filiale)
- **Freiburg/Karlsruhe**: ID_STORE = 3, 5 (zwei Filialen kombiniert)

### Produktkategorien
Die Kategorien werden automatisch aus der Produktbeschreibung erkannt:
- **E-Bike**: Enthält "E-Bike" oder "E-Trekking"
- **MTB**: Enthält "MTB" oder "Mountain"
- **City/Trekking**: Enthält "City" oder "Trekking"
- **Kinder**: Enthält "Kid" oder "Kinder"
- **Sonstige**: Alles andere

---

## Troubleshooting

### Problem: Keine Daten in den Views
**Lösung:** Prüfen Sie, ob Daten für die Filialen 3, 5, 14 existieren:
```sql
SELECT ID_STORE, COUNT(*)
FROM dbo.V_LIST_MONTHLY_SALES
WHERE ID_STORE IN (3,5,14)
GROUP BY ID_STORE;
```

### Problem: Negative Bruttogewinne
**Ursache:** Transferpreis × Menge > Umsatz
**Lösung:** Dies ist korrekt - zeigt, dass mit Verlust verkauft wurde (z.B. durch hohe Rabatte)

### Problem: NULL-Werte bei KPIs
**Ursache:** Division durch Null (kein Umsatz oder keine Kosten)
**Lösung:** CASE-Statements verhindern dies bereits - NULL bedeutet "nicht berechenbar"

---

## Kontakt

Bei Fragen zum Benchmark-System:
- **Gruppe:** 18
- **Projekt:** Phase 4 - Benchmarking
- **Datei:** GRUPPE_18_BENCHMARK_VIEWS.sql

---

**Erstellt:** 2025-01-08
**Version:** 1.0
**Letzte Änderung:** 2025-01-08
