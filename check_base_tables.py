"""
Prüft ob Daten in Basis-Tabellen existieren
"""
import sys
import os
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

from src.db.connection import get_connection

print("=" * 70)
print("PRÜFE BASIS-TABELLEN")
print("=" * 70)

# Mögliche Tabellennamen für Monthly Sales/Costs
possible_tables = [
    'T_MONTHLY_SALES',
    'T_MONTHLY_COST',
    'T_SALES',
    'T_COST',
    'V_MONTHLY_SALES',
    'V_MONTHLY_COST',
    'MONTHLY_SALES',
    'MONTHLY_COST'
]

try:
    conn = get_connection()
    cursor = conn.cursor()

    # Liste alle Tabellen/Views in der Datenbank
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%MONTHLY%' OR TABLE_NAME LIKE '%SALES%' OR TABLE_NAME LIKE '%COST%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)

    tables = cursor.fetchall()

    print(f"\n{len(tables)} Tabellen/Views mit 'MONTHLY', 'SALES' oder 'COST' gefunden:\n")

    for schema, name, table_type in tables:
        # Prüfe ob Tabelle Daten hat
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{name}]")
            count = cursor.fetchone()[0]
            status = f"✅ {count:,} Zeilen" if count > 0 else "⚠️ LEER"
            print(f"   {table_type:10} {schema}.{name:40} {status}")
        except Exception as e:
            print(f"   {table_type:10} {schema}.{name:40} ❌ Fehler: {str(e)[:50]}")

    conn.close()

except Exception as e:
    print(f"❌ FEHLER: {e}")
    import traceback
    print(traceback.format_exc())

print("\n" + "=" * 70)
