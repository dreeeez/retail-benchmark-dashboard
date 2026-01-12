"""
Prüft welche Stores tatsächlich Daten haben
"""
import sys
import os
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

from src.db.connection import get_connection

print("=" * 70)
print("VERFÜGBARE STORES MIT DATEN")
print("=" * 70)

try:
    conn = get_connection()
    cursor = conn.cursor()

    # Prüfe welche Stores in der Sales-Detail-View Daten haben
    cursor.execute("""
        SELECT DISTINCT IdStore, StoreName, COUNT(*) as AnzahlDatensaetze
        FROM list_views.V_LIST_G18_BENCHMARK_SALES_DETAIL
        GROUP BY IdStore, StoreName
        ORDER BY IdStore
    """)

    stores = cursor.fetchall()

    if len(stores) == 0:
        print("❌ KEINE Stores mit Daten gefunden!")
        print("   → Der Datengenerator hat möglicherweise noch keine Daten erzeugt")
    else:
        print(f"✅ {len(stores)} Store(s) mit Daten gefunden:\n")
        for store_id, store_name, count in stores:
            print(f"   Store ID {store_id}: {store_name} ({count:,} Datensätze)")

        print("\n" + "=" * 70)
        print("KONFIGURIERTE STORES IN src/config/stores.py:")
        print("=" * 70)
        from src.config.stores import STORES
        for s in STORES:
            print(f"   Store ID {s['id']}: {s['name']}")

        print("\n" + "=" * 70)
        print("EMPFEHLUNG:")
        print("=" * 70)
        configured_ids = {s['id'] for s in STORES}
        available_ids = {s[0] for s in stores}

        if configured_ids == available_ids:
            print("✅ Alle konfigurierten Stores haben Daten!")
        else:
            missing = configured_ids - available_ids
            extra = available_ids - configured_ids

            if missing:
                print(f"❌ Diese konfigurierten Stores haben KEINE Daten: {missing}")
            if extra:
                print(f"⚠️ Diese Stores haben Daten, sind aber NICHT konfiguriert: {extra}")
                print(f"\n   → Ändere src/config/stores.py auf IDs: {sorted(available_ids)}")

    conn.close()

except Exception as e:
    print(f"❌ FEHLER: {e}")
    import traceback
    print(traceback.format_exc())

print("=" * 70)
