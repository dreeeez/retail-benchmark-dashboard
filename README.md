# Benchmark Dashboard - Gruppe 18

Streamlit-basiertes Dashboard zum Vergleich von Filial-KPIs.

## Voraussetzungen

- Python 3.10+
- SQL Server Zugang (ODBC Driver 18)
- Installierte SQL-Views (siehe `sql/`)

## Installation

```bash
pip install -r requirements.txt
```

## Konfiguration

`config.json` im Root-Verzeichnis erstellen (siehe `config.example.json`):

```json
{
    "server": "dein-server",
    "database": "deine-db",
    "user": "username",
    "password": "passwort"
}
```

## Starten

```bash
streamlit run app.py
```

## Projektstruktur

```
src/
├── config/      # Store-, Farb- und Kategorie-Konfiguration
├── db/          # Datenbankverbindung, SQL-Queries, Data-Loader
├── domain/      # KPI-Berechnungen, Spalten-Mapping
├── services/    # Filter und Aggregationen
├── charts/      # Plotly-Visualisierungen
├── ui/          # Streamlit-Komponenten und CSS
└── utils/       # Hilfsfunktionen (Formatierung, Safe-Operationen)
```

## Stores hinzufügen

Neue Stores in `src/config/stores.py` eintragen:

```python
STORES = [
    {'id': 14, 'name': 'Rosenheim', 'short': 'ROS', 'color': '#00d4ff', ...},
    # Neuen Store hier hinzufügen
]
```

Die Store-IDs werden automatisch in alle SQL-Queries eingefügt.

## Features

- Finanzperformance (Umsatz, Margen, EBIT)
- Marketing-Analyse (ROAS, CPA, Kampagnen)
- Kostenstruktur (Personal, Betrieb, Logistik)
- Produktkategorien (Umsatzverteilung, Preissegmente)
- Datenexport (CSV)
