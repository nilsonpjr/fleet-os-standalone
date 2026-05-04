import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao sys.path para importar core
sys.path.append(str(Path(__file__).parent.parent))

from core.database import Base, engine
# Import all models to ensure they are registered with Base.metadata
import main

def init_db():
    print("🛠️ Inicializando o esquema do banco de dados no novo Supabase...")
    Base.metadata.create_all(bind=engine)
    print("✅ Esquema criado com sucesso!")

if __name__ == "__main__":
    init_db()
