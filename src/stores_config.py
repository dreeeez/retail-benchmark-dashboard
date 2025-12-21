"""
Benchmark Dashboard - Gruppe 18
Store & Kategorien Konfiguration

Modulares System - neue Stores/Kategorien einfach hier hinzufügen
"""

# =============================================================================
# STORE KONFIGURATION
# =============================================================================
# Neue Stores einfach hier hinzufügen - Dashboard passt sich automatisch an

STORES = [
    {
        'id': 14,
        'name': 'Rosenheim',
        'short': 'ROS',
        'color': '#00d4ff',
        'color_bg': 'rgba(0, 212, 255, 0.2)',
    },
    {
        'id': 5,
        'name': 'Freiburg im Breisgau',
        'short': 'FRE',
        'color': '#7b2cbf',
        'color_bg': 'rgba(123, 44, 191, 0.2)',
    },
    {
        'id': 3,
        'name': 'Karlsruhe',
        'short': 'KAR',
        'color': '#ff6b6b',
        'color_bg': 'rgba(255, 107, 107, 0.2)',
    },
    # Neuen Store hinzufügen:
    # {
    #     'id': 7,
    #     'name': 'München',
    #     'short': 'MUC',
    #     'color': '#00ff88',
    #     'color_bg': 'rgba(0, 255, 136, 0.2)',
    # },
]

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

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_store_by_name(name):
    """Findet Store-Config anhand des Namens (case-insensitive, partial match)"""
    name_lower = name.lower()
    for store in STORES:
        if store['name'].lower() in name_lower or name_lower in store['name'].lower():
            return store
    return None

def get_store_by_id(store_id):
    """Findet Store-Config anhand der ID"""
    for store in STORES:
        if store['id'] == store_id:
            return store
    return None

def get_store_color(store_name):
    """Gibt Farbe für Store zurück"""
    store = get_store_by_name(store_name)
    return store['color'] if store else '#ffffff'

def get_store_color_bg(store_name):
    """Gibt Hintergrundfarbe für Store zurück"""
    store = get_store_by_name(store_name)
    return store['color_bg'] if store else 'rgba(255, 255, 255, 0.1)'

def get_category_color(category_name):
    """Gibt Farbe für Produktkategorie zurück"""
    name_lower = category_name.lower()
    for cat in PRODUCT_CATEGORIES:
        if cat['name'].lower() in name_lower or name_lower in cat['name'].lower():
            return cat['color']
    return '#ffffff'

def get_all_store_names():
    """Gibt Liste aller Store-Namen zurück"""
    return [store['name'] for store in STORES]

def get_all_category_names():
    """Gibt Liste aller Kategorie-Namen zurück"""
    return [cat['name'] for cat in PRODUCT_CATEGORIES]

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

def get_color_for_index(index):
    """Gibt Farbe aus Palette für Index zurück (zyklisch)"""
    return COLOR_PALETTE[index % len(COLOR_PALETTE)]
