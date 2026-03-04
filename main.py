
from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os

app = FastAPI()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
        DATABASE_URL = "postgresql://urc_rankings_user:HJE2yXrSMxFtqS4bRcTSlw5t6KBcRmVc@dpg-d6juiq3h46gs73e26g8g-a.ohio-postgres.render.com/urc_rankings"
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
        
@app.post("/vote")
def vote(winner_id: int, loser_id: int):
    K = 32

    with engine.connect() as conn:
        winner = conn.execute(text("SELECT rating FROM items WHERE id=:id"),
                              {"id": winner_id}).fetchone()
        loser = conn.execute(text("SELECT rating FROM items WHERE id=:id"),
                             {"id": loser_id}).fetchone()

        Ra, Rb = winner[0], loser[0]

        expected_a = 1 / (1 + 10 ** ((Rb - Ra) / 400))
        expected_b = 1 / (1 + 10 ** ((Ra - Rb) / 400))

        new_Ra = Ra + K * (1 - expected_a)
        new_Rb = Rb + K * (0 - expected_b)

        conn.execute(text("UPDATE items SET rating=:r WHERE id=:id"),
                     {"r": new_Ra, "id": winner_id})
        conn.execute(text("UPDATE items SET rating=:r WHERE id=:id"),
                     {"r": new_Rb, "id": loser_id})
        conn.commit()

    return {"status": "updated"}

from fastapi.responses import HTMLResponse

@app.get("/app", response_class=HTMLResponse)
def app_page():
    return """
    <html>
    <body>
        <button onclick="vote(1,2)">Option 1</button>
        <button onclick="vote(2,1)">Option 2</button>

        <script>
        function vote(winner, loser){
            fetch(`/vote?winner_id=${winner}&loser_id=${loser}`, {
                method: "POST"
            });
        }
        </script>
    </body>
    </html>
    """
