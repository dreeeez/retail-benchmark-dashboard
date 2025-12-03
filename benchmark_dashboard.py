"""
Benchmarking-System Dashboard
Gruppe 18: Marco, Harun, Duy
Phase 4 - Systemkonzept Benchmarking

Dieses Skript erstellt KPI-Visualisierungen und Benchmark-Reports
fuer die Filialen Rosenheim und Freiburg/Karlsruhe.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from db_connect import get_connection
import warnings
warnings.filterwarnings('ignore')

# Deutsche Monatsnamen
MONTH_NAMES_DE = {
    1: 'Jan', 2: 'Feb', 3: 'Mär', 4: 'Apr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Dez'
}


def get_benchmark_data():
    """Holt die Benchmark-Daten aus der Datenbank."""
    conn = get_connection()

    # KPI-Daten pro Filiale und Monat
    query_kpi = """
    SELECT
        ID_STORE,
        STORE_NAME,
        ID_CALMONTH,
        ID_CALMONTH_STD,
        BENCHMARK_CATEGORY,
        TOTAL_SALES_AMOUNT,
        REVENUE_EUR,
        GROSS_PROFIT_EUR,
        NET_PROFIT_EUR,
        TOTAL_COSTS_EUR,
        EMPLOYEE_COUNT,
        GROSS_MARGIN_PCT,
        NET_MARGIN_PCT,
        OPERATING_COST_RATIO_PCT,
        PERSONNEL_COST_RATIO_PCT,
        REVENUE_PER_EMPLOYEE
    FROM V_BENCHMARK_KPI
    ORDER BY ID_CALMONTH, STORE_NAME
    """

    # Filialvergleich
    query_comparison = """
    SELECT *
    FROM V_BENCHMARK_STORE_COMPARISON
    ORDER BY ID_CALMONTH, BENCHMARK_CATEGORY
    """

    # Export-Daten
    query_export = """
    SELECT *
    FROM V_BENCHMARK_EXPORT_MONTHLY
    ORDER BY ID_CALMONTH, STORE_NAME, BENCHMARK_CATEGORY
    """

    try:
        df_kpi = pd.read_sql(query_kpi, conn)
        df_comparison = pd.read_sql(query_comparison, conn)
        df_export = pd.read_sql(query_export, conn)
        conn.close()
        return df_kpi, df_comparison, df_export
    except Exception as e:
        print(f"Fehler beim Laden der Daten: {e}")
        print("Verwende Fallback-Abfrage auf Basistabellen...")
        return get_fallback_data(conn)


def get_fallback_data(conn):
    """Fallback falls Views noch nicht existieren - direkte Abfrage auf Basistabellen."""

    # Direkte Abfrage auf T_ETL_MONTHLY_SALES
    query_sales = """
    SELECT
        s.ID_STORE,
        so.STORE_LOCATION AS STORE_NAME,
        s.ID_CALMONTH,
        FORMAT(s.ID_CALMONTH, 'yyyy-MM') AS ID_CALMONTH_STD,
        pc.CATEGORY AS BENCHMARK_CATEGORY,
        SUM(s.SALES_AMOUNT) AS TOTAL_SALES_AMOUNT,
        SUM(s.REVENUE) AS REVENUE_EUR,
        SUM(s.GROSS_PROFIT_EUR) AS GROSS_PROFIT_EUR,
        AVG(s.SALES_PRICE_EUR) AS AVG_SALES_PRICE_EUR
    FROM T_ETL_MONTHLY_SALES s
    INNER JOIN T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
    INNER JOIN T_PRODUCT_CATEGORY pc ON s.ID_CATEGORY = pc.ID_CATEGORY
    WHERE so.STORE_LOCATION IN ('Rosenheim', 'Freiburg', 'Karlsruhe')
    GROUP BY s.ID_STORE, so.STORE_LOCATION, s.ID_CALMONTH, pc.CATEGORY
    ORDER BY s.ID_CALMONTH, so.STORE_LOCATION
    """

    try:
        df_kpi = pd.read_sql(query_sales, conn)
        # Berechne KPIs
        df_kpi['GROSS_MARGIN_PCT'] = (df_kpi['GROSS_PROFIT_EUR'] / df_kpi['REVENUE_EUR'] * 100).round(2)
        df_kpi['NET_PROFIT_EUR'] = df_kpi['GROSS_PROFIT_EUR']  # Vereinfacht ohne Kosten
        df_kpi['NET_MARGIN_PCT'] = df_kpi['GROSS_MARGIN_PCT']
        df_kpi['TOTAL_COSTS_EUR'] = 0
        df_kpi['EMPLOYEE_COUNT'] = 0
        df_kpi['OPERATING_COST_RATIO_PCT'] = 0
        df_kpi['PERSONNEL_COST_RATIO_PCT'] = 0
        df_kpi['REVENUE_PER_EMPLOYEE'] = 0

        conn.close()
        return df_kpi, pd.DataFrame(), df_kpi
    except Exception as e:
        print(f"Auch Fallback fehlgeschlagen: {e}")
        conn.close()
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def create_revenue_trend_chart(df_kpi, output_path='charts/revenue_trend.png'):
    """Erstellt ein Umsatz-Trenddiagramm."""
    if df_kpi.empty:
        print("Keine Daten fuer Umsatz-Trend vorhanden.")
        return

    # Aggregiere auf Monat/Filiale-Ebene
    df_monthly = df_kpi.groupby(['ID_CALMONTH', 'STORE_NAME']).agg({
        'REVENUE_EUR': 'sum',
        'GROSS_PROFIT_EUR': 'sum'
    }).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))

    for store in df_monthly['STORE_NAME'].unique():
        store_data = df_monthly[df_monthly['STORE_NAME'] == store]
        ax.plot(store_data['ID_CALMONTH'], store_data['REVENUE_EUR'] / 1000,
                marker='o', linewidth=2, label=store)

    ax.set_xlabel('Monat', fontsize=12)
    ax.set_ylabel('Umsatz (Tsd. EUR)', fontsize=12)
    ax.set_title('Monatlicher Umsatz nach Filiale', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart gespeichert: {output_path}")


def create_margin_comparison_chart(df_kpi, output_path='charts/margin_comparison.png'):
    """Erstellt ein Margen-Vergleichsdiagramm."""
    if df_kpi.empty:
        print("Keine Daten fuer Margen-Vergleich vorhanden.")
        return

    # Durchschnittliche Marge pro Filiale
    df_margins = df_kpi.groupby('STORE_NAME').agg({
        'GROSS_MARGIN_PCT': 'mean',
        'NET_MARGIN_PCT': 'mean'
    }).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(df_margins))
    width = 0.35

    bars1 = ax.bar([i - width/2 for i in x], df_margins['GROSS_MARGIN_PCT'],
                   width, label='Bruttomarge %', color='#2ecc71')
    bars2 = ax.bar([i + width/2 for i in x], df_margins['NET_MARGIN_PCT'],
                   width, label='Nettomarge %', color='#3498db')

    ax.set_xlabel('Filiale', fontsize=12)
    ax.set_ylabel('Marge (%)', fontsize=12)
    ax.set_title('Durchschnittliche Margen nach Filiale', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df_margins['STORE_NAME'])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Werte auf Balken anzeigen
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                   ha='center', va='bottom', fontsize=10)
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                   ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart gespeichert: {output_path}")


def create_category_revenue_chart(df_kpi, output_path='charts/category_revenue.png'):
    """Erstellt ein Umsatz-nach-Kategorie-Diagramm."""
    if df_kpi.empty:
        print("Keine Daten fuer Kategorie-Umsatz vorhanden.")
        return

    # Umsatz pro Kategorie und Filiale
    df_cat = df_kpi.groupby(['BENCHMARK_CATEGORY', 'STORE_NAME']).agg({
        'REVENUE_EUR': 'sum'
    }).reset_index()

    # Pivot fuer gruppierte Balken
    df_pivot = df_cat.pivot(index='BENCHMARK_CATEGORY', columns='STORE_NAME', values='REVENUE_EUR').fillna(0)

    fig, ax = plt.subplots(figsize=(14, 7))
    df_pivot.plot(kind='bar', ax=ax, width=0.8)

    ax.set_xlabel('Fahrradkategorie', fontsize=12)
    ax.set_ylabel('Umsatz (EUR)', fontsize=12)
    ax.set_title('Umsatz nach Kategorie und Filiale', fontsize=14, fontweight='bold')
    ax.legend(title='Filiale')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')

    # Formatiere Y-Achse in Tausend
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart gespeichert: {output_path}")


def create_kpi_cards(df_kpi, output_path='charts/kpi_cards.png'):
    """Erstellt KPI-Karten als Uebersicht."""
    if df_kpi.empty:
        print("Keine Daten fuer KPI-Karten vorhanden.")
        return

    # Gesamtwerte pro Filiale
    df_totals = df_kpi.groupby('STORE_NAME').agg({
        'REVENUE_EUR': 'sum',
        'GROSS_PROFIT_EUR': 'sum',
        'TOTAL_SALES_AMOUNT': 'sum',
        'GROSS_MARGIN_PCT': 'mean'
    }).reset_index()

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('KPI-Dashboard: Filialvergleich', fontsize=16, fontweight='bold', y=1.02)

    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']

    for idx, (ax, store) in enumerate(zip(axes.flat, df_totals['STORE_NAME'].unique())):
        store_data = df_totals[df_totals['STORE_NAME'] == store].iloc[0]

        # KPI-Werte
        revenue = store_data['REVENUE_EUR'] / 1000000
        profit = store_data['GROSS_PROFIT_EUR'] / 1000000
        margin = store_data['GROSS_MARGIN_PCT']
        units = store_data['TOTAL_SALES_AMOUNT']

        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')

        # Hintergrund
        ax.add_patch(plt.Rectangle((0.5, 0.5), 9, 9, fill=True,
                                    facecolor=colors[idx % len(colors)], alpha=0.1,
                                    edgecolor=colors[idx % len(colors)], linewidth=3))

        # Titel
        ax.text(5, 8.5, store, fontsize=18, fontweight='bold', ha='center',
                color=colors[idx % len(colors)])

        # KPIs
        ax.text(5, 6.5, f'Umsatz: {revenue:.2f} Mio EUR', fontsize=14, ha='center')
        ax.text(5, 5, f'Gewinn: {profit:.2f} Mio EUR', fontsize=14, ha='center')
        ax.text(5, 3.5, f'Marge: {margin:.1f}%', fontsize=14, ha='center')
        ax.text(5, 2, f'Verkaufte Einheiten: {int(units):,}', fontsize=14, ha='center')

    # Falls weniger als 4 Filialen, leere Subplots ausblenden
    for idx in range(len(df_totals), 4):
        axes.flat[idx].axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart gespeichert: {output_path}")


def create_benchmark_comparison_chart(df_comparison, output_path='charts/benchmark_comparison.png'):
    """Erstellt ein Benchmark-Vergleichsdiagramm Rosenheim vs Freiburg."""
    if df_comparison.empty:
        print("Keine Vergleichsdaten vorhanden.")
        return

    # Aggregiere ueber alle Kategorien
    df_totals = df_comparison.groupby('ID_CALMONTH_STD').agg({
        'ROS_REVENUE_EUR': 'sum',
        'FRK_REVENUE_EUR': 'sum',
        'DIFF_REVENUE_EUR': 'sum'
    }).reset_index()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Oberes Chart: Absolute Werte
    ax1.bar(range(len(df_totals)), df_totals['ROS_REVENUE_EUR'] / 1000,
            width=0.4, label='Rosenheim', color='#3498db', align='edge')
    ax1.bar([x + 0.4 for x in range(len(df_totals))], df_totals['FRK_REVENUE_EUR'] / 1000,
            width=0.4, label='Freiburg/Karlsruhe', color='#e74c3c', align='edge')

    ax1.set_xlabel('Monat')
    ax1.set_ylabel('Umsatz (Tsd. EUR)')
    ax1.set_title('Umsatzvergleich: Rosenheim vs. Freiburg/Karlsruhe', fontsize=14, fontweight='bold')
    ax1.set_xticks([x + 0.4 for x in range(len(df_totals))])
    ax1.set_xticklabels(df_totals['ID_CALMONTH_STD'], rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Unteres Chart: Differenz
    colors = ['#2ecc71' if x >= 0 else '#e74c3c' for x in df_totals['DIFF_REVENUE_EUR']]
    ax2.bar(range(len(df_totals)), df_totals['DIFF_REVENUE_EUR'] / 1000, color=colors)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    ax2.set_xlabel('Monat')
    ax2.set_ylabel('Differenz (Tsd. EUR)')
    ax2.set_title('Umsatzdifferenz (Rosenheim - Freiburg/Karlsruhe)', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(df_totals)))
    ax2.set_xticklabels(df_totals['ID_CALMONTH_STD'], rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart gespeichert: {output_path}")


def export_to_excel(df_export, output_path='benchmark_report.xlsx'):
    """Exportiert die Benchmark-Daten nach Excel."""
    if df_export.empty:
        print("Keine Daten fuer Excel-Export vorhanden.")
        return

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Gesamtuebersicht
        df_summary = df_export.groupby(['STORE_NAME', 'ID_CALMONTH_STD']).agg({
            'REVENUE_EUR': 'sum',
            'GROSS_PROFIT_EUR': 'sum',
            'NET_PROFIT_EUR': 'sum',
            'TOTAL_SALES_AMOUNT': 'sum',
            'TOTAL_COSTS_EUR': 'sum'
        }).reset_index()
        df_summary.to_excel(writer, sheet_name='Monatsuebersicht', index=False)

        # Details nach Kategorie
        df_export.to_excel(writer, sheet_name='Details', index=False)

        # KPIs pro Filiale
        df_kpis = df_export.groupby('STORE_NAME').agg({
            'REVENUE_EUR': 'sum',
            'GROSS_PROFIT_EUR': 'sum',
            'GROSS_MARGIN_PCT': 'mean',
            'NET_MARGIN_PCT': 'mean',
            'OPERATING_COST_RATIO_PCT': 'mean',
            'PERSONNEL_COST_RATIO_PCT': 'mean'
        }).reset_index()
        df_kpis.columns = ['Filiale', 'Gesamtumsatz', 'Gesamtgewinn',
                          'Ø Bruttomarge %', 'Ø Nettomarge %',
                          'Ø Betriebskostenquote %', 'Ø Personalkostenanteil %']
        df_kpis.to_excel(writer, sheet_name='KPIs', index=False)

    print(f"Excel-Report erstellt: {output_path}")


def main():
    """Hauptfunktion - erstellt alle Reports und Visualisierungen."""
    import os

    print("=" * 60)
    print("BENCHMARKING-SYSTEM - Gruppe 18")
    print("Filialvergleich: Rosenheim vs. Freiburg/Karlsruhe")
    print("=" * 60)
    print()

    # Charts-Verzeichnis erstellen
    os.makedirs('charts', exist_ok=True)

    # Daten laden
    print("Lade Daten aus der Datenbank...")
    df_kpi, df_comparison, df_export = get_benchmark_data()

    if df_kpi.empty:
        print("\nKeine Daten gefunden. Bitte stellen Sie sicher, dass:")
        print("1. Die Datenbankverbindung korrekt konfiguriert ist (config.json)")
        print("2. Die Views erstellt wurden (benchmark_views.sql ausfuehren)")
        print("3. Daten in den Basistabellen vorhanden sind")
        return

    print(f"\nGeladene Datensaetze:")
    print(f"  - KPI-Daten: {len(df_kpi)} Zeilen")
    print(f"  - Vergleichsdaten: {len(df_comparison)} Zeilen")
    print(f"  - Export-Daten: {len(df_export)} Zeilen")
    print()

    # Statistiken anzeigen
    print("Verfuegbare Filialen:", df_kpi['STORE_NAME'].unique().tolist())
    print("Zeitraum:", df_kpi['ID_CALMONTH'].min(), "bis", df_kpi['ID_CALMONTH'].max())
    print("Kategorien:", df_kpi['BENCHMARK_CATEGORY'].unique().tolist())
    print()

    # Charts erstellen
    print("Erstelle Visualisierungen...")
    create_revenue_trend_chart(df_kpi)
    create_margin_comparison_chart(df_kpi)
    create_category_revenue_chart(df_kpi)
    create_kpi_cards(df_kpi)

    if not df_comparison.empty:
        create_benchmark_comparison_chart(df_comparison)

    # Excel-Export
    print("\nErstelle Excel-Report...")
    export_to_excel(df_export)

    print()
    print("=" * 60)
    print("Benchmark-Analyse abgeschlossen!")
    print("=" * 60)
    print("\nErstellte Dateien:")
    print("  - charts/revenue_trend.png")
    print("  - charts/margin_comparison.png")
    print("  - charts/category_revenue.png")
    print("  - charts/kpi_cards.png")
    print("  - charts/benchmark_comparison.png")
    print("  - benchmark_report.xlsx")


if __name__ == "__main__":
    main()
