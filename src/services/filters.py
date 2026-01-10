"""
Benchmark Dashboard - Gruppe 18
Filter-Funktionen

Hilfsfunktionen zum Filtern von DataFrames nach Store.
"""

import pandas as pd


def filter_by_store_name(df: pd.DataFrame, store: dict, store_name_col: str = None) -> pd.DataFrame:
    """Filtert DataFrame nach Store-Namen

    Args:
        df: DataFrame
        store: Store-Config Dict
        store_name_col: Name der Store-Spalte (optional, wird gesucht)

    Returns:
        Gefilterter DataFrame
    """
    if store_name_col is None:
        store_name_col = next(
            (c for c in df.columns if 'storename' in c.lower().replace('_', '')),
            None
        )

    if store_name_col is None:
        return df

    return df[df[store_name_col].astype(str).str.contains(store['name'], case=False, na=False)]


def filter_by_store_id(df: pd.DataFrame, store: dict, store_id_col: str = None) -> pd.DataFrame:
    """Filtert DataFrame nach Store-ID

    Args:
        df: DataFrame
        store: Store-Config Dict
        store_id_col: Name der ID-Spalte (optional, wird gesucht)

    Returns:
        Gefilterter DataFrame
    """
    if store_id_col is None:
        store_id_col = next(
            (c for c in df.columns if c.lower() in ['idstore', 'id_store']),
            None
        )

    if store_id_col is None:
        return df

    return df[df[store_id_col] == store['id']]


def create_store_filter(df: pd.DataFrame):
    """Erstellt eine passende Filter-Funktion basierend auf den Spalten

    Args:
        df: DataFrame

    Returns:
        Filter-Funktion (df, store) -> filtered_df
    """
    store_name_col = next(
        (c for c in df.columns if 'storename' in c.lower().replace('_', '')),
        None
    )
    store_id_col = next(
        (c for c in df.columns if c.lower() in ['idstore', 'id_store']),
        None
    )

    if store_name_col:
        return lambda d, s: filter_by_store_name(d, s, store_name_col)
    elif store_id_col:
        return lambda d, s: filter_by_store_id(d, s, store_id_col)
    else:
        return lambda d, s: d
