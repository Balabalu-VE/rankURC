
from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os

app = FastAPI()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
        DATABASE_URL = "sqlite:///./local.db"
engine = create_engine(DATABASE_URL)

@app.get("/")
def home():
        return {"message": "Ranking app running"}

@app.get("/init")
def init():
        with engine.connect() as conn:
                    conn.execute(text("""
                                CREATE TABLE IF NOT EXISTS items (
                                                id SERIAL PRIMARY KEY,
                                                                name TEXT,
                                                                                rating FLOAT DEFAULT 1200
                                                                                            )
                                                                                                    """))
                            conn.commit()
                                return {"status": "table created"}
