import psycopg2
from psycopg2 import extras
import json

# --- CONFIGURAÇÃO ---
OLD_DB_URL = "postgresql://postgres.vrikuvzrnpzxianctycs:!Nildani12@aws-1-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
NEW_DB_URL = "postgresql://postgres:4XbGBtC8PuVEHSeL@db.rjmvdmozszfdcpboztly.supabase.co:5432/postgres"

# Tabelas na ordem de dependência (Foreign Keys)
TABLES = [
    "tenants",
    "users",
    "clients",
    "marinas",
    "boats",
    "engines",
    "vehicles",
    "workshops",
    "fleet_requests",
    "workshop_quotes",
    "workshop_quote_items",
    "workshop_executions",
    "maintenance_schedules",
    "fleet_request_messages",
    "parts",
    "service_categories",
    "service_subcategories",
    "service_catalog",
    "service_orders",
    "service_items",
    "transactions",
    "company_info"
]

def migrate():
    print("🚀 Iniciando migração de dados entre projetos Supabase...")
    
    try:
        source_conn = psycopg2.connect(OLD_DB_URL)
        target_conn = psycopg2.connect(NEW_DB_URL)
        
        source_cur = source_conn.cursor(cursor_factory=extras.RealDictCursor)
        target_cur = target_conn.cursor()

        # Registrar adaptadores JSON
        extras.register_default_jsonb(conn_or_curs=target_cur)

        # Desabilitar constraints temporariamente (Replica role)
        print("🔓 Desabilitando triggers no destino...")
        target_cur.execute("SET session_replication_role = 'replica';")

        for table in TABLES:
            print(f"📦 Migrando tabela: {table}...", end=" ", flush=True)
            
            try:
                # 1. Ler dados da origem
                source_cur.execute(f"SELECT * FROM {table}")
                rows = source_cur.fetchall()
                
                if not rows:
                    print("Vazia. Pulando.")
                    continue
                
                # 2. Preparar campos (Escapando nomes de colunas com aspas duplas)
                columns = [f'"{col}"' for col in rows[0].keys()]
                
                # Tratar valores JSON/Dict antes de inserir
                def process_row(row):
                    processed = []
                    for val in row.values():
                        if isinstance(val, (dict, list)):
                            processed.append(json.dumps(val))
                        else:
                            processed.append(val)
                    return tuple(processed)

                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))}) ON CONFLICT DO NOTHING"
                
                # 3. Inserir no destino
                data = [process_row(row) for row in rows]
                target_cur.executemany(query, data)
                
                target_conn.commit()
                print(f"✅ {len(rows)} registros migrados.")
                
            except Exception as e:
                print(f"❌ Erro na tabela {table}: {e}")
                target_conn.rollback()

        # Restaurar triggers
        print("🔒 Restaurando triggers...")
        target_cur.execute("SET session_replication_role = 'origin';")
        target_conn.commit()
        
        print("\n✨ Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"💥 Erro fatal: {e}")
    finally:
        if 'source_conn' in locals(): source_conn.close()
        if 'target_conn' in locals(): target_conn.close()

if __name__ == "__main__":
    migrate()
