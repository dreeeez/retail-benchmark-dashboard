"""
Benchmark Dashboard - Gruppe 18
Login-Funktionen gegen T_USER
"""

import pandas as pd
from src.db.connection import db_connection


def check_login(username: str, password: str) -> dict | None:
    """Prüft Login gegen T_USER

    Args:
        username: Benutzername
        password: Passwort (Klartext)

    Returns:
        Dict mit User-Infos bei Erfolg, None bei Fehlschlag
        {
            'user_id': int,
            'username': str,
            'security_level': int
        }
    """
    # Login-Check gegen T_USER (case-insensitive)
    login_query = """
    SELECT ID_USER, USERNAME, ISNULL(SECURITYLEVEL, 0) AS SECURITYLEVEL
    FROM T_USER
    WHERE UPPER(USERNAME) = UPPER(?) AND USERPASS = ?
    """

    try:
        with db_connection() as conn:
            df = pd.read_sql(login_query, conn, params=[username, password])

            if len(df) == 1:
                row = df.iloc[0]
                return {
                    'user_id': int(row['ID_USER']),
                    'username': row['USERNAME'],
                    'security_level': int(row['SECURITYLEVEL'])
                }
            return None
    except Exception as e:
        print(f"Login-Fehler: {e}")
        return None


def get_user_security_level(username: str) -> int | None:
    """Holt Security Level für einen User über Stored Function

    Args:
        username: Benutzername

    Returns:
        Security Level als int (0, 1, 2 oder 3), None bei Fehler
    """
    query = "SELECT dbo.fn_get_user_securitylevel(?) AS SECURITYLEVEL"

    try:
        with db_connection() as conn:
            df = pd.read_sql(query, conn, params=[username])

            if len(df) == 1:
                return int(df.iloc[0]['SECURITYLEVEL'])
            return None
    except Exception:
        return None
