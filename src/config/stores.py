"""
Benchmark Dashboard - Gruppe 18
Store-Konfiguration

Modulares System - neue Stores einfach hier hinzufügen
WICHTIG: Store-IDs werden dynamisch in SQL-Queries eingefügt!
"""

# =============================================================================
# STORE KONFIGURATION
# =============================================================================
# Neue Stores einfach hier hinzufügen - Dashboard passt sich automatisch an
# Die IDs werden dynamisch in alle SQL-Queries eingefügt (kein Hardcoding mehr!)

STORES = [
    {
        'id': 51014014,  # Geändert von 14 auf 51014014 (LIVE-Daten)
        'name': 'Rosenheim',
        'short': 'ROS',
        'color': '#00d4ff',
        'color_bg': 'rgba(0, 212, 255, 0.2)',
    },
    {
        'id': 51005005,  # Geändert von 5 auf 51005005 (LIVE-Daten)
        'name': 'Freiburg im Breisgau',
        'short': 'FRE',
        'color': '#7b2cbf',
        'color_bg': 'rgba(123, 44, 191, 0.2)',
    },
    {
        'id': 51003003,  # Geändert von 3 auf 51003003 (LIVE-Daten)
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
# DYNAMISCHE STORE-ID GENERIERUNG
# =============================================================================

def get_store_ids() -> list:
    """Gibt Liste aller Store-IDs zurück"""
    return [store['id'] for store in STORES]


def get_store_ids_sql() -> str:
    """Gibt Store-IDs als SQL-kompatiblen String zurück: '3, 5, 14'"""
    return ', '.join(str(s['id']) for s in STORES)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_store_by_name(name: str):
    """Findet Store-Config anhand des Namens (case-insensitive, partial match)"""
    name_lower = name.lower()
    for store in STORES:
        if store['name'].lower() in name_lower or name_lower in store['name'].lower():
            return store
    return None


def get_store_by_id(store_id: int):
    """Findet Store-Config anhand der ID"""
    for store in STORES:
        if store['id'] == store_id:
            return store
    return None


def get_store_color(store_name: str) -> str:
    """Gibt Farbe für Store zurück"""
    store = get_store_by_name(store_name)
    return store['color'] if store else '#ffffff'


def get_store_color_bg(store_name: str) -> str:
    """Gibt Hintergrundfarbe für Store zurück"""
    store = get_store_by_name(store_name)
    return store['color_bg'] if store else 'rgba(255, 255, 255, 0.1)'


def get_all_store_names() -> list:
    """Gibt Liste aller Store-Namen zurück"""
    return [store['name'] for store in STORES]
