"""
Test-Script um Datenbankverbindung und Views zu prüfen
"""
import sys
import traceback
import os

# Fix encoding for Windows console
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("BENCHMARK DATABASE CONNECTION TEST")
print("=" * 70)

# Test 1: Config laden
print("\n[1/5] Config-Datei laden...")
try:
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    print(f"✅ Config geladen: Server={config.get('server')}, DB={config.get('database')}")
except Exception as e:
    print(f"❌ FEHLER: {e}")
    sys.exit(1)

# Test 2: Connection testen
print("\n[2/5] Datenbankverbindung testen...")
try:
    from src.db.connection import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"✅ Verbindung erfolgreich!")
    print(f"   SQL Server Version: {version[:50]}...")
    conn.close()
except Exception as e:
    print(f"❌ VERBINDUNGSFEHLER:")
    print(traceback.format_exc())
    sys.exit(1)

# Test 3: Schema prüfen
print("\n[3/5] Prüfe ob Schema 'list_views' existiert...")
try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SCHEMA_NAME
        FROM INFORMATION_SCHEMA.SCHEMATA
        WHERE SCHEMA_NAME = 'list_views'
    """)
    result = cursor.fetchone()
    if result:
        print(f"✅ Schema 'list_views' existiert")
    else:
        print(f"❌ Schema 'list_views' NICHT GEFUNDEN!")
        print("   → Views müssen in diesem Schema erstellt werden")
    conn.close()
except Exception as e:
    print(f"⚠️ Fehler beim Schema-Check: {e}")

# Test 4: Views prüfen
print("\n[4/5] Prüfe ob Views existieren...")
try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_NAME LIKE 'V_LIST_G18%'
        ORDER BY TABLE_NAME
    """)
    views = cursor.fetchall()

    if len(views) == 0:
        print("❌ KEINE Views gefunden!")
        print("   → Die Views aus sql/CREATE_VIEWS.sql müssen deployed werden")
    else:
        print(f"✅ {len(views)} Views gefunden:")
        for schema, name in views:
            print(f"   - {schema}.{name}")

    conn.close()
except Exception as e:
    print(f"⚠️ Fehler beim View-Check: {e}")

# Test 5: Testquery auf erste View
print("\n[5/5] Teste Daten-Abfrage...")
try:
    from src.config.stores import STORES
    from src.db.queries import SQL_EXPORT_MONTHLY, build_month_filter
    import pandas as pd

    store_ids = ', '.join(str(s['id']) for s in STORES)
    month_filter = build_month_filter('all', 'Monat')

    query = SQL_EXPORT_MONTHLY.format(store_ids=store_ids, month_filter=month_filter)
    print(f"   Query: {query[:100]}...")

    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()

    if len(df) > 0:
        print(f"✅ Daten erfolgreich geladen: {len(df)} Zeilen")
        print(f"   Spalten: {list(df.columns)[:5]}...")
    else:
        print(f"⚠️ Query erfolgreich, aber KEINE Daten zurückgegeben")
        print(f"   → Prüfe ob Stores {store_ids} Daten haben")

except Exception as e:
    print(f"❌ QUERY-FEHLER:")
    print(traceback.format_exc())

print("\n" + "=" * 70)
print("TEST ABGESCHLOSSEN")
print("=" * 70)
