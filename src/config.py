"""
Benchmark Dashboard - Gruppe 18
Konfiguration und Konstanten

WICHTIG: Store- und Kategorie-Konfiguration ist jetzt in stores_config.py
"""

from src.stores_config import STORES, PRODUCT_CATEGORIES, get_store_color, get_category_color

# =============================================================================
# ALLGEMEINE FARBEN
# =============================================================================
COLORS = {
    'positive': '#00ff88',
    'negative': '#ff4757',
    'neutral': '#ffd93d',
    'background': 'rgba(255, 255, 255, 0.1)',
}

# Legacy Support - dynamisch aus STORES generieren
for store in STORES:
    COLORS[store['name'].lower()] = store['color']
    COLORS[f"{store['name'].lower()}_bg"] = store['color_bg']

# =============================================================================
# KATEGORIEN-FARBEN (aus stores_config.py)
# =============================================================================
CAT_COLORS = {cat['name']: cat['color'] for cat in PRODUCT_CATEGORIES}

# =============================================================================
# MONATSNAMEN
# =============================================================================
MONTH_NAMES = {
    'all': 'Gesamtjahr 2024',
    '2024-01': 'Januar 2024', '2024-02': 'Februar 2024', '2024-03': 'März 2024',
    '2024-04': 'April 2024', '2024-05': 'Mai 2024', '2024-06': 'Juni 2024',
    '2024-07': 'Juli 2024', '2024-08': 'August 2024', '2024-09': 'September 2024',
    '2024-10': 'Oktober 2024', '2024-11': 'November 2024', '2024-12': 'Dezember 2024'
}
