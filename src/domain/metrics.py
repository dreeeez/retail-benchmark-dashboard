"""
Benchmark Dashboard - Gruppe 18
Metriken-Berechnung

KPI-Extraktion aus Views und Legacy-Berechnung.
"""

import pandas as pd
from src.utils.safe import safe_sum, safe_mean


def get_store_data(df, filiale_col: str, store_name: str):
    """Filtert DataFrame für einen Store"""
    return df[df[filiale_col].str.contains(store_name, case=False, na=False)]


def get_kpis_from_view(kpi_df, store_id: int) -> dict:
    """Extrahiert KPIs für einen Store aus V_LIST_G18_BENCHMARK_KPI

    ERSETZT calculate_kpis() - keine Python-Berechnung mehr!
    Alle KPIs kommen direkt aus der View.

    Args:
        kpi_df: DataFrame aus load_kpi()
        store_id: Store-ID (z.B. 3, 5, 14)

    Returns:
        Dict mit allen KPIs
    """
    store_data = kpi_df[kpi_df['IdStore'] == store_id]

    if store_data.empty:
        return {
            'umsatz': 0, 'nettogewinn': 0, 'marge': 0, 'bruttogewinn': 0,
            'kosten': 0, 'wareneinsatz': 0, 'personalkosten': 0,
            'betriebskosten': 0, 'beschaffungskosten': 0, 'marketingkosten': 0,
            'bruttomarge': 0, 'nettomarge': 0
        }

    # Aggregiere über alle Monate (falls mehrere Zeilen)
    umsatz = store_data['TotalRevenueEur'].sum()  # Jetzt bereits Netto-Umsatz (mit Discount-Abzug)
    bruttogewinn = store_data['TotalGrossProfitEur'].sum()
    nettogewinn = store_data['NetProfitEur'].sum()
    gesamtkosten_opex = store_data['TotalCostsEur'].sum()

    # Optional: TotalDiscountEur für Transparenz
    total_discount = store_data.get('TotalDiscountEur', pd.Series([0])).sum()

    # Einzelne Kostenkomponenten (OPEX)
    personalkosten = store_data['HumanResourcesEur'].sum()
    betriebskosten = store_data['FacilityManagementEur'].sum()
    beschaffungskosten = store_data['LogisticsEur'].sum()
    marketing = store_data['MarketingEur'].sum()

    # Wareneinsatz (COGS) = Umsatz - Bruttogewinn
    # Entspricht den Transfer-Preisen / Einkaufskosten der verkauften Waren
    # Bruttogewinn = Umsatz - Wareneinsatz → Wareneinsatz = Umsatz - Bruttogewinn
    # HINWEIS: Umsatz ist jetzt bereits Netto (Brutto-Umsatz - Rabatte)
    wareneinsatz = umsatz - bruttogewinn

    # Gesamtkosten = Wareneinsatz (COGS) + OPEX (Personal, Betrieb, Logistik, Marketing)
    gesamtkosten = wareneinsatz + gesamtkosten_opex

    # Margen (Durchschnitt falls mehrere Monate)
    bruttomarge = store_data['GrossProfitMarginPct'].mean() if not store_data['GrossProfitMarginPct'].isna().all() else 0
    nettomarge = store_data['NetProfitMarginPct'].mean() if not store_data['NetProfitMarginPct'].isna().all() else 0

    return {
        'umsatz': umsatz,
        'nettogewinn': nettogewinn,
        'marge': nettomarge,
        'bruttogewinn': bruttogewinn,
        'kosten': gesamtkosten,
        'wareneinsatz': wareneinsatz,
        'personalkosten': personalkosten,
        'betriebskosten': betriebskosten,
        'beschaffungskosten': beschaffungskosten,
        'marketingkosten': marketing,
        'bruttomarge': bruttomarge,
        'nettomarge': nettomarge
    }


def calculate_kpis(store_df) -> dict:
    """LEGACY: Berechnet KPIs für einen Store aus Export-DataFrame

    DEPRECATED: Nutze get_kpis_from_view() für View-basierte KPIs!
    Diese Funktion bleibt für Abwärtskompatibilität.
    """
    umsatz = safe_sum(store_df, 'umsatz')
    bruttogewinn = safe_sum(store_df, 'bruttogewinn')
    wareneinsatz = umsatz - bruttogewinn

    personalkosten = safe_sum(store_df, 'humanresources')
    betriebskosten = safe_sum(store_df, 'facilitymanagement')
    beschaffungskosten = safe_sum(store_df, 'logistics')
    marketing = safe_sum(store_df, 'marketing')

    gesamtkosten = wareneinsatz + personalkosten + betriebskosten + beschaffungskosten + marketing

    return {
        'umsatz': umsatz,
        'nettogewinn': safe_sum(store_df, 'nettogewinn'),
        'marge': safe_mean(store_df, 'nettogewinnmarge'),
        'bruttogewinn': bruttogewinn,
        'kosten': gesamtkosten,
        'wareneinsatz': wareneinsatz,
        'personalkosten': personalkosten,
        'betriebskosten': betriebskosten,
        'beschaffungskosten': beschaffungskosten,
        'marketingkosten': marketing
    }
