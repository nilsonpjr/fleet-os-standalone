from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import main
from modules.auth.models import User

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

users = db.query(User).filter(User.email == "viverdi@viverdi.com.br").all()
for u in users:
    print(u.id, u.email, u.partner_id)
