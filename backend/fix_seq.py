from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as conn:
    conn.execute(text("SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));"))
    conn.commit()
    print("Sequence fixed!")
