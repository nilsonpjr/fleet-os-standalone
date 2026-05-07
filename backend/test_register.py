from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import main  # Import all models into registry!
from modules.auth.crud import create_user
from modules.auth.schemas import UserCreate

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

user = UserCreate(name="Teste", email="teste999@viverdi.com.br", password="123", role="PARTNER", partner_id=1)
try:
    created = create_user(db, user, tenant_id=2)
    print("Success:", created.id)
except Exception as e:
    import traceback
    traceback.print_exc()
