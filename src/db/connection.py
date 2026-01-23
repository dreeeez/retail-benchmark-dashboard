"""
Benchmark Dashboard - Gruppe 18
Datenbankverbindung

Unterstützt:
- Streamlit Cloud via st.secrets
- Lokale Entwicklung via .streamlit/secrets.toml oder config.json
"""

import json
from pathlib import Path
from contextlib import contextmanager

# Fixe DB-Konfiguration (Server + Database sind immer gleich)
DB_SERVER = "edu.hdm-server.eu"
DB_DATABASE = "ERPDEV"


def get_db_config():
    """Lädt DB-Konfiguration aus config.json oder Streamlit Secrets

    Priorität:
    1. config.json (lokale Entwicklung)
    2. st.secrets (Streamlit Cloud)

    Returns:
        dict mit server, database, user, password
    """
    # 1. Versuche config.json (lokal)
    config_path = Path(__file__).resolve().parent.parent.parent / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # 2. Fallback: Streamlit Secrets (Cloud)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and "database" in st.secrets:
            return {
                'server': st.secrets["database"].get("server", DB_SERVER),
                'database': st.secrets["database"].get("database", DB_DATABASE),
                'user': st.secrets["database"]["user"],
                'password': st.secrets["database"]["password"]
            }
    except Exception:
        pass

    raise FileNotFoundError(
        f"Keine DB-Konfiguration gefunden. Gesucht: {config_path}"
    )


def get_connection():
    """Erstellt Verbindung zur SQL Server Datenbank

    Versucht pymssql zuerst (Cloud-kompatibel), dann pyodbc als Fallback.
    """
    cfg = get_db_config()

    # Versuche zuerst pymssql (funktioniert überall ohne ODBC Driver)
    try:
        import pymssql
        return pymssql.connect(
            server=cfg['server'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database']
        )
    except Exception:
        pass

    # Fallback: pyodbc (lokal mit ODBC Driver)
    import pyodbc
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['user']};"
        f"PWD={cfg['password']};"
        "Encrypt=no;"
    )
    return pyodbc.connect(conn_str)


@contextmanager
def db_connection():
    """Context Manager für sichere DB-Verbindungen.

    Garantiert automatisches Schließen auch bei Exceptions.

    Verwendung:
        with db_connection() as conn:
            df = pd.read_sql(query, conn)
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
