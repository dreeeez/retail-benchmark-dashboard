"""
Benchmark Dashboard - Gruppe 18
Aggregations-Funktionen

Funktionen zur Aggregation von KPIs und Metriken.
"""


def aggregate_marketing_kpis(marketing_df, store_id: int) -> dict:
    """Aggregiert Marketing-KPIs für einen Store

    Args:
        marketing_df: DataFrame aus load_marketing_kpi()
        store_id: Store-ID

    Returns:
        Dict mit Marketing-KPIs
    """
    store_data = marketing_df[marketing_df['IdStore'] == store_id]

    if store_data.empty:
        return {
            'umsatz_mit_marketing': 0,
            'umsatz_ohne_marketing': 0,
            'umsatz_gesamt': 0,
            'marketing': 0,
            'roas': 0,
            'cpa': 0,
            'stueck_mit_marketing': 0,
            'stueck_gesamt': 0,
            'marketing_quote': 0
        }

    umsatz_mit_marketing = store_data['MarketingAttributedRevenueEur'].sum()
    umsatz_ohne_marketing = store_data['MarketingIndependentRevenueEur'].sum()
    umsatz_gesamt = store_data['TotalRevenueEur'].sum()
    marketing = store_data['MarketingCostEur'].sum()
    stueck_mit_marketing = store_data['MarketingAttributedQuantity'].sum()
    stueck_gesamt = store_data['QuantityTotal'].sum()

    roas = umsatz_mit_marketing / marketing if marketing > 0 else 0
    cpa = marketing / stueck_mit_marketing if stueck_mit_marketing > 0 else 0
    marketing_quote = (marketing / umsatz_gesamt * 100) if umsatz_gesamt > 0 else 0

    return {
        'umsatz_mit_marketing': umsatz_mit_marketing,  # Marketing-attributierter Umsatz
        'umsatz_ohne_marketing': umsatz_ohne_marketing,  # Marketing-unabhängiger Umsatz
        'umsatz_gesamt': umsatz_gesamt,
        'marketing': marketing,
        'roas': roas,
        'cpa': cpa,
        'stueck_mit_marketing': stueck_mit_marketing,
        'stueck_gesamt': stueck_gesamt,
        'marketing_quote': marketing_quote
    }


def calculate_cost_percentages(kpis: dict) -> dict:
    """Berechnet Kostenanteile in Prozent vom Umsatz

    Args:
        kpis: KPI-Dict aus get_kpis_from_view()

    Returns:
        Dict mit Prozent-Werten
    """
    umsatz = kpis.get('umsatz', 0)

    if umsatz <= 0:
        return {
            'wareneinsatz_pct': 0,
            'personal_pct': 0,
            'miete_pct': 0,
            'logistik_pct': 0,
            'marketing_pct': 0,
            'gesamt_pct': 0
        }

    return {
        'wareneinsatz_pct': kpis.get('wareneinsatz', 0) / umsatz * 100,
        'personal_pct': kpis.get('personalkosten', 0) / umsatz * 100,
        'miete_pct': kpis.get('betriebskosten', 0) / umsatz * 100,
        'logistik_pct': kpis.get('beschaffungskosten', 0) / umsatz * 100,
        'marketing_pct': kpis.get('marketingkosten', 0) / umsatz * 100,
        'gesamt_pct': kpis.get('kosten', 0) / umsatz * 100
    }
