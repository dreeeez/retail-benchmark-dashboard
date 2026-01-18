"""
Benchmark Dashboard - Gruppe 18
Store-Konfiguration

DYNAMISCHES SYSTEM - Stores werden automatisch aus der Datenbank geladen
Nur Stores mit Sales-Daten werden berücksichtigt (keine reinen Kosten-Stores)
"""

import streamlit as st
import pandas as pd

# =============================================================================
# FARBPALETTE FÜR STORES
# =============================================================================
# Vordefinierte Farben für bis zu 10 Stores
STORE_COLORS = [
    {'color': '#00d4ff', 'color_bg': 'rgba(0, 212, 255, 0.2)'},     # Cyan
    {'color': '#7b2cbf', 'color_bg': 'rgba(123, 44, 191, 0.2)'},    # Lila
    {'color': '#ff6b6b', 'color_bg': 'rgba(255, 107, 107, 0.2)'},   # Rot
    {'color': '#00ff88', 'color_bg': 'rgba(0, 255, 136, 0.2)'},     # Grün
    {'color': '#ffba08', 'color_bg': 'rgba(255, 186, 8, 0.2)'},     # Gelb
    {'color': '#ff006e', 'color_bg': 'rgba(255, 0, 110, 0.2)'},     # Pink
    {'color': '#8338ec', 'color_bg': 'rgba(131, 56, 236, 0.2)'},    # Violett
    {'color': '#06ffa5', 'color_bg': 'rgba(6, 255, 165, 0.2)'},     # Mint
    {'color': '#fb5607', 'color_bg': 'rgba(251, 86, 7, 0.2)'},      # Orange
    {'color': '#3a86ff', 'color_bg': 'rgba(58, 134, 255, 0.2)'},    # Blau
]


# =============================================================================
# DYNAMISCHE STORE-LADEN AUS DATENBANK
# =============================================================================

def _load_stores_from_db() -> list:
    """
    Lädt alle Stores mit Sales-Daten aus der Datenbank.
    INTERN - nutze get_stores() statt dieser Funktion!

    Berücksichtigt nur Stores die:
    - Sales-Umsatz haben (RevenueEUR > 0)
    - In V_LIST_MONTHLY_SALES vorhanden sind

    Returns:
        Liste von Store-Dictionaries mit id, name, short, color, color_bg
    """
    # Import hier um zirkuläre Abhängigkeit zu vermeiden
    from src.db.connection import get_connection

    try:
        conn = get_connection()

        # Query: Alle Stores mit Sales-Daten
        query = """
        SELECT DISTINCT
            s.ID_STORE AS id,
            s.StoreName AS name
        FROM dbo.V_LIST_MONTHLY_SALES s
        WHERE s.RevenueEUR > 0  -- Nur Stores mit tatsächlichen Sales
        ORDER BY s.StoreName
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return []

        # Erstelle Store-Dictionaries mit Farben
        stores = []
        for idx, row in df.iterrows():
            # Short-Name: Erste 3 Buchstaben des Store-Namens
            short = ''.join([c for c in row['name'] if c.isalpha()])[:3].upper()

            # Farbe aus Palette (zyklisch wenn mehr als 10 Stores)
            color_idx = idx % len(STORE_COLORS)

            stores.append({
                'id': int(row['id']),
                'name': row['name'],
                'short': short,
                'color': STORE_COLORS[color_idx]['color'],
                'color_bg': STORE_COLORS[color_idx]['color_bg'],
            })

        return stores

    except Exception as e:
        # Kein st.error hier - wird im get_stores() behandelt
        raise e


# =============================================================================
# AKTIVE STORES (LAZY LOADING)
# =============================================================================

def get_stores() -> list:
    """
    Gibt die Liste der Stores zurück.
    Lädt sie beim ersten Aufruf aus der Datenbank (lazy loading).
    Cached in Session-State für Performance.

    WICHTIG: Erst nach Login aufrufen, sonst keine DB-Credentials verfügbar!
    """
    # Prüfe ob bereits geladen
    if 'loaded_stores' in st.session_state and st.session_state.loaded_stores:
        return st.session_state.loaded_stores

    # Versuche zu laden
    try:
        stores = _load_stores_from_db()
        if stores:
            st.session_state.loaded_stores = stores
            return stores
    except Exception as e:
        st.error(f"Fehler beim Laden der Stores: {e}")

    return []


# Legacy-Kompatibilität: STORES als Property-Wrapper
# ACHTUNG: Direkter Zugriff auf STORES beim Import funktioniert nicht mehr!
# Stattdessen get_stores() verwenden.
STORES = []  # Platzhalter für Abwärtskompatibilität


# =============================================================================
# STORE-ID GENERIERUNG
# =============================================================================

def get_store_ids() -> list:
    """Gibt Liste aller Store-IDs zurück"""
    return [store['id'] for store in get_stores()]


def get_store_ids_sql() -> str:
    """Gibt Store-IDs als SQL-kompatiblen String zurück: '51003003, 51005005, 51014014'"""
    stores = get_stores()
    if not stores:
        return '0'  # Fallback um SQL-Fehler zu vermeiden
    return ', '.join(str(s['id']) for s in stores)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_store_by_name(name: str):
    """Findet Store-Config anhand des Namens (case-insensitive, partial match)"""
    if not name:
        return None
    name_lower = name.lower()
    for store in get_stores():
        if store['name'].lower() in name_lower or name_lower in store['name'].lower():
            return store
    return None


def get_store_by_id(store_id: int):
    """Findet Store-Config anhand der ID"""
    for store in get_stores():
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
    return [store['name'] for store in get_stores()]


def reload_stores():
    """
    Lädt Stores neu aus der Datenbank.
    Nützlich wenn neue Stores hinzugekommen sind.
    """
    # Session-Cache löschen und neu laden
    if 'loaded_stores' in st.session_state:
        del st.session_state.loaded_stores
    return get_stores()
