"""
Benchmark Dashboard - Gruppe 18
User Authentication Module

Authentifizierung gegen T_USER Tabelle mit Security Level Check
Nutzt fixe Service-Account-Verbindung aus config.json
"""

import pandas as pd
from src.db.connection import db_connection


def authenticate_user(username: str, password: str) -> dict:
    """Authentifiziert einen User gegen T_USER und prüft Security Level

    Nutzt eine fixe DB-Verbindung (Service-Account aus config.json)
    und prüft nur gegen die T_USER Tabelle.

    Args:
        username: Benutzername
        password: Passwort

    Returns:
        dict mit:
        - authenticated: bool (True wenn erfolgreich)
        - security_level: int (Security Level des Users, None wenn nicht auth)
        - message: str (Fehlermeldung oder Erfolg)
        - username: str (Username aus DB, nur bei Erfolg)
    """
    # pymssql verwendet %s, pyodbc verwendet ?
    query_pymssql = """
        SELECT USERNAME, ISNULL(SECURITYLEVEL, 0) AS SECURITYLEVEL
        FROM dbo.LOV_USER_LOGINS
        WHERE UPPER(USERNAME) = UPPER(%s) AND USERPASS = %s
    """
    query_pyodbc = """
        SELECT USERNAME, ISNULL(SECURITYLEVEL, 0) AS SECURITYLEVEL
        FROM dbo.LOV_USER_LOGINS
        WHERE UPPER(USERNAME) = UPPER(?) AND USERPASS = ?
    """

    try:
        with db_connection() as conn:
            # Versuche pymssql-Syntax, dann pyodbc-Syntax
            try:
                df = pd.read_sql(query_pymssql, conn, params=(username, password))
            except Exception:
                df = pd.read_sql(query_pyodbc, conn, params=[username, password])

            if len(df) == 0:
                return {
                    'authenticated': False,
                    'security_level': None,
                    'message': 'Ungültige Anmeldedaten'
                }

            row = df.iloc[0]
            db_username = row['USERNAME']
            security_level = int(row['SECURITYLEVEL'])

            # Prüfe ob Level 3 oder 4
            if security_level not in [3, 4]:
                return {
                    'authenticated': False,
                    'security_level': security_level,
                    'message': f'Keine Berechtigung (Security Level {security_level}). Level 3 oder 4 erforderlich.'
                }

            return {
                'authenticated': True,
                'security_level': security_level,
                'message': 'Anmeldung erfolgreich',
                'username': db_username
            }

    except Exception as e:
        return {
            'authenticated': False,
            'security_level': None,
            'message': f'DB-Fehler: {str(e)}'
        }


def dev_bypass_login() -> dict:
    """Dev-Bypass für schnelles Testen (SPÄTER ENTFERNEN!)

    Returns:
        dict mit authenticated=True und Security Level 4
    """
    return {
        'authenticated': True,
        'security_level': 4,
        'message': 'DEV MODE - Bypass aktiv',
        'username': 'dev_user'
    }
