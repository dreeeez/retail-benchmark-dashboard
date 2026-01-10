"""
Benchmark Dashboard - Gruppe 18
Produktkategorien-Konfiguration
"""

# =============================================================================
# PRODUKTKATEGORIEN KONFIGURATION
# =============================================================================

PRODUCT_CATEGORIES = [
    {'name': 'City Bikes', 'short': 'CITY', 'color': '#00d4ff'},
    {'name': 'E-Trekking', 'short': 'ETRK', 'color': '#7b2cbf'},
    {'name': 'Kid Bikes', 'short': 'KIDS', 'color': '#ff6b6b'},
    {'name': 'Mountain Bikes', 'short': 'MTB', 'color': '#00ff88'},
    {'name': 'Race Bikes', 'short': 'RACE', 'color': '#ffd93d'},
    {'name': 'Trekking Bikes', 'short': 'TREK', 'color': '#ff9f43'},
]

# Farb-Palette für dynamische Zuweisung (falls mehr Stores/Kategorien)
COLOR_PALETTE = [
    '#00d4ff',  # Cyan
    '#7b2cbf',  # Lila
    '#ff6b6b',  # Rot
    '#00ff88',  # Grün
    '#ffd93d',  # Gelb
    '#ff9f43',  # Orange
    '#a55eea',  # Violett
    '#26de81',  # Mint
    '#fd79a8',  # Pink
    '#74b9ff',  # Hellblau
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_category_color(category_name: str) -> str:
    """Gibt Farbe für Produktkategorie zurück"""
    name_lower = category_name.lower()
    for cat in PRODUCT_CATEGORIES:
        if cat['name'].lower() in name_lower or name_lower in cat['name'].lower():
            return cat['color']
    return '#ffffff'


def get_all_category_names() -> list:
    """Gibt Liste aller Kategorie-Namen zurück"""
    return [cat['name'] for cat in PRODUCT_CATEGORIES]


def get_color_for_index(index: int) -> str:
    """Gibt Farbe aus Palette für Index zurück (zyklisch)"""
    return COLOR_PALETTE[index % len(COLOR_PALETTE)]
