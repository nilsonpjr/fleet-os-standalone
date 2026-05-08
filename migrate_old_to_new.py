#!/usr/bin/env python3
"""
migrate_old_to_new.py
=====================
Migrates data from the OLD Maré Alta database to the NEW FleetOS database.

OLD: postgresql://postgres.vrikuvzrnpzxianctycs:...@aws-1-us-east-2.pooler.supabase.com:6543/postgres
NEW: postgresql://postgres.rjmvdmozszfdcpboztly:...@aws-1-us-west-2.pooler.supabase.com:5432/postgres

Tables migrated (in order to respect foreign keys):
  1. manufacturers  (boat/engine brands)
  2. models         (boat/engine model names per brand)
  3. clients        (boat owners)
  4. parts          (inventory / catalog)
  5. service_definitions (service catalog)
  6. boats
  7. engines        (linked to boats)

NOTE: All data is inserted into tenant_id=1 in the new DB (the main admin tenant).
      Adjust NEW_TENANT_ID if your setup differs.
"""

import psycopg2
import psycopg2.extras
import sys
from datetime import datetime

# ── Connection strings ───────────────────────────────────────────────────────
OLD_DB = "postgresql://postgres.vrikuvzrnpzxianctycs:!Nildani12@aws-1-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
NEW_DB = "postgresql://postgres.rjmvdmozszfdcpboztly:4XbGBtC8PuVEHSeL@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

# Target Tenant ID (Default is 2 for Maré Alta in the new system)
NEW_TENANT_ID = 2
if len(sys.argv) > 1:
    try:
        NEW_TENANT_ID = int(sys.argv[1])
    except ValueError:
        print(f"Usage: python3 migrate_old_to_new.py [NEW_TENANT_ID]")
        sys.exit(1)

# ── Helpers ──────────────────────────────────────────────────────────────────
def connect(dsn, label):
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        print(f"✅ Connected to {label}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to {label}: {e}")
        sys.exit(1)

def fetch_all(conn, sql, params=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def execute(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)

def upsert_returning_id(conn, sql, params):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None

# ── Migration steps ──────────────────────────────────────────────────────────

def migrate_manufacturers(old, new):
    print("\n── Manufacturers ──────────────────────────────────")
    rows = fetch_all(old, "SELECT * FROM manufacturers ORDER BY id")
    print(f"  Found {len(rows)} rows in old DB")
    id_map = {}
    for r in rows:
        new_id = upsert_returning_id(new,
            """INSERT INTO manufacturers (tenant_id, name, type)
               VALUES (%s, %s, %s)
               ON CONFLICT DO NOTHING
               RETURNING id""",
            (NEW_TENANT_ID, r["name"], r["type"])
        )
        if new_id:
            id_map[r["id"]] = new_id
        else:
            # Conflict: find existing
            existing = fetch_all(new,
                "SELECT id FROM manufacturers WHERE tenant_id=%s AND name=%s AND type=%s",
                (NEW_TENANT_ID, r["name"], r["type"])
            )
            if existing:
                id_map[r["id"]] = existing[0]["id"]
    new.commit()
    print(f"  ✅ Migrated {len(id_map)} manufacturers")
    return id_map

def migrate_models(old, new, manufacturer_map):
    print("\n── Engine / Boat Models ───────────────────────────")
    rows = fetch_all(old, "SELECT * FROM models ORDER BY id")
    print(f"  Found {len(rows)} rows in old DB")
    count = 0
    for r in rows:
        mfr_id = manufacturer_map.get(r["manufacturer_id"])
        if not mfr_id:
            print(f"  ⚠️  Skipping model '{r['name']}' — manufacturer not found")
            continue
        upsert_returning_id(new,
            """INSERT INTO models (name, manufacturer_id)
               VALUES (%s, %s)
               ON CONFLICT DO NOTHING
               RETURNING id""",
            (r["name"], mfr_id)
        )
        count += 1
    new.commit()
    print(f"  ✅ Migrated {count} models")

def migrate_clients(old, new):
    print("\n── Clients ─────────────────────────────────────────")
    rows = fetch_all(old, "SELECT * FROM clients ORDER BY id")
    print(f"  Found {len(rows)} rows in old DB")
    id_map = {}
    for r in rows:
        new_id = upsert_returning_id(new,
            """INSERT INTO clients (tenant_id, name, document, type, phone, email, address)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT DO NOTHING
               RETURNING id""",
            (
                NEW_TENANT_ID,
                r.get("name", ""), r.get("document", ""), r.get("type", "PF"),
                r.get("phone"), r.get("email"), r.get("address")
            )
        )
        if new_id:
            id_map[r["id"]] = new_id
        else:
            existing = fetch_all(new,
                "SELECT id FROM clients WHERE tenant_id=%s AND document=%s",
                (NEW_TENANT_ID, r.get("document", ""))
            )
            if existing:
                id_map[r["id"]] = existing[0]["id"]
    new.commit()
    print(f"  ✅ Migrated {len(id_map)} clients")
    return id_map

def migrate_parts(old, new):
    print("\n── Parts (Inventory) ───────────────────────────────")
    rows = fetch_all(old, "SELECT * FROM parts ORDER BY id")
    print(f"  Found {len(rows)} rows in old DB")
    count = 0
    for r in rows:
        try:
            upsert_returning_id(new,
                """INSERT INTO parts (tenant_id, sku, name, quantity, cost, price, min_stock, location, manufacturer, \"group\", subgroup)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (tenant_id, sku) DO UPDATE
                     SET name=EXCLUDED.name, price=EXCLUDED.price, quantity=EXCLUDED.quantity
                   RETURNING id""",
                (
                    NEW_TENANT_ID,
                    r.get("sku", f"P-{r['id']}"), r.get("name", ""),
                    r.get("quantity") or r.get("stock_quantity") or 0,
                    r.get("cost") or r.get("cost_price") or 0,
                    r.get("price") or r.get("sale_price") or 0,
                    r.get("min_stock") or 0,
                    r.get("location"), r.get("manufacturer"),
                    r.get("group") or r.get("category"),
                    r.get("subgroup")
                )
            )
            count += 1
        except Exception as e:
            new.rollback()
            print(f"  ⚠️  Skipping part {r.get('sku')}: {e}")
    new.commit()
    print(f"  ✅ Migrated {count} parts")

def migrate_service_definitions(old, new):
    print("\n── Service Definitions ─────────────────────────────")
    # Try both tables: service_definitions and service_catalog
    rows = []
    try:
        rows = fetch_all(old, "SELECT * FROM service_definitions ORDER BY id")
    except Exception:
        pass
    if not rows:
        try:
            rows = fetch_all(old, "SELECT * FROM service_catalog ORDER BY id")
        except Exception:
            pass
    print(f"  Found {len(rows)} rows in old DB")
    count = 0
    for r in rows:
        try:
            upsert_returning_id(new,
                """INSERT INTO service_definitions (tenant_id, code, name, category, description, default_price)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT DO NOTHING
                   RETURNING id""",
                (
                    NEW_TENANT_ID,
                    r.get("code"), r.get("name", ""),
                    r.get("category"), r.get("description"),
                    r.get("default_price") or r.get("price") or 0
                )
            )
            count += 1
        except Exception as e:
            new.rollback()
            print(f"  ⚠️  Skipping service {r.get('name')}: {e}")
    new.commit()
    print(f"  ✅ Migrated {count} service definitions")

def migrate_boats_and_engines(old, new, client_map):
    print("\n── Boats & Engines ─────────────────────────────────")
    boats = fetch_all(old, "SELECT * FROM boats ORDER BY id")
    print(f"  Found {len(boats)} boats in old DB")
    boat_map = {}
    skipped = 0
    for b in boats:
        new_client_id = client_map.get(b["client_id"])
        if not new_client_id:
            print(f"  ⚠️  Skipping boat '{b['name']}' — client {b['client_id']} not migrated")
            skipped += 1
            continue
        new_id = upsert_returning_id(new,
            """INSERT INTO boats (tenant_id, client_id, name, hull_id, usage_type, model)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT DO NOTHING
               RETURNING id""",
            (
                NEW_TENANT_ID, new_client_id,
                b.get("name", ""), b.get("hull_id", ""),
                b.get("usage_type"), b.get("model")
            )
        )
        if new_id:
            boat_map[b["id"]] = new_id
        else:
            existing = fetch_all(new,
                "SELECT id FROM boats WHERE tenant_id=%s AND hull_id=%s",
                (NEW_TENANT_ID, b.get("hull_id", ""))
            )
            if existing:
                boat_map[b["id"]] = existing[0]["id"]
    new.commit()
    print(f"  ✅ Migrated {len(boat_map)} boats (skipped {skipped})")

    # Engines
    engines = fetch_all(old, "SELECT * FROM engines ORDER BY id")
    print(f"  Found {len(engines)} engines in old DB")
    eng_count = 0
    for e in engines:
        new_boat_id = boat_map.get(e["boat_id"])
        if not new_boat_id:
            continue
        try:
            upsert_returning_id(new,
                """INSERT INTO engines (tenant_id, boat_id, serial_number, motor_number, model, sale_date, warranty_status, warranty_validity, client_name, hours, year)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT DO NOTHING
                   RETURNING id""",
                (
                    NEW_TENANT_ID, new_boat_id,
                    e.get("serial_number", ""),
                    e.get("motor_number"),
                    e.get("model", ""),
                    e.get("sale_date"),
                    e.get("warranty_status"),
                    e.get("warranty_validity"),
                    e.get("client_name"),
                    e.get("hours") or 0,
                    e.get("year")
                )
            )
            eng_count += 1
        except Exception as ex:
            new.rollback()
            print(f"  ⚠️  Skipping engine {e.get('serial_number')}: {ex}")
    new.commit()
    print(f"  ✅ Migrated {eng_count} engines")

def migrate_maintenance_kits(old, new):
    print("\n── Maintenance Kits ────────────────────────────────")
    try:
        kits = fetch_all(old, "SELECT * FROM maintenance_kits ORDER BY id")
    except Exception:
        print("  ⚠️  Table maintenance_kits not found in old DB, skipping")
        return
    print(f"  Found {len(kits)} kits in old DB")
    count = 0
    for k in kits:
        try:
            new_kit_id = upsert_returning_id(new,
                """INSERT INTO maintenance_kits (tenant_id, name, brand, engine_model, interval_hours, description)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT DO NOTHING
                   RETURNING id""",
                (
                    NEW_TENANT_ID,
                    k.get("name", ""), k.get("brand"),
                    k.get("engine_model"), k.get("interval_hours"),
                    k.get("description")
                )
            )
            count += 1
        except Exception as e:
            new.rollback()
            print(f"  ⚠️  Skipping kit {k.get('name')}: {e}")
    new.commit()
    print(f"  ✅ Migrated {count} maintenance kits")

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print(" FleetOS — Data Migration from Maré Alta → New DB")
    print("=" * 60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    old = connect(OLD_DB, "OLD (Maré Alta)")
    new = connect(NEW_DB, "NEW (FleetOS)")

    try:
        manufacturer_map = migrate_manufacturers(old, new)
        migrate_models(old, new, manufacturer_map)
        client_map = migrate_clients(old, new)
        migrate_parts(old, new)
        migrate_service_definitions(old, new)
        migrate_boats_and_engines(old, new, client_map)
        migrate_maintenance_kits(old, new)

        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
    except Exception as e:
        new.rollback()
        print(f"\n❌ Fatal error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        old.close()
        new.close()
