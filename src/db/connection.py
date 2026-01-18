"""
Benchmark Dashboard - Gruppe 18
Datenbankverbindung

Unterstützt:
- Lokale Entwicklung via config.json
- Streamlit Cloud via Session-Credentials aus Login
"""

import json
import pyodbc
from pathlib import Path
from contextlib import contextmanager

# Fixe DB-Konfiguration (Server + Database sind immer gleich)
DB_SERVER = "edu.hdm-server.eu"
DB_DATABASE = "ERPDEV"


def get_db_config():
    """Lädt DB-Konfiguration aus config.json oder Session-Credentials

    Returns:
        dict mit server, database, user, password
    """
    # 1. Versuche config.json (lokale Entwicklung)
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # 2. Fallback: Session-Credentials aus Login (Cloud Deployment)
    try:
        import streamlit as st
        if st.session_state.get('db_user') and st.session_state.get('db_password'):
            return {
                'server': DB_SERVER,
                'database': DB_DATABASE,
                'user': st.session_state.db_user,
                'password': st.session_state.db_password
            }
    except Exception:
        pass

    raise FileNotFoundError(
        "Keine DB-Konfiguration gefunden. "
        "Bitte einloggen oder config.json erstellen."
    )


def get_connection():
    """Erstellt Verbindung zur SQL Server Datenbank"""
    cfg = get_db_config()

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
