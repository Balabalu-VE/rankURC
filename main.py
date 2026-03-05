from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import json
import os
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse

# Use Render DATABASE_URL if available
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
        DATABASE_URL = "postgresql://urc_rankings_user:HJE2yXrSMxFtqS4bRcTSlw5t6KBcRmVc@dpg-d6juiq3h46gs73e26g8g-a.ohio-postgres.render.com/urc_rankings"

engine = create_engine(DATABASE_URL)


# Load videos from JSON
with open("youtube_videos.json", "r", encoding="utf-8") as f:
    videos = json.load(f)  # list of dicts


# ✅ Proper startup event
@asynccontextmanager
async def lifespan(app: FastAPI):
        with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS items (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        youtube_id TEXT UNIQUE NOT NULL,
                        rating FLOAT DEFAULT 1200
                );
                """))
                conn.commit()
                for v in videos:
                        
                        conn.execute(
                        text("""
                                INSERT INTO items (title, youtube_id)
                                VALUES (:title, :youtube_id)
                                ON CONFLICT (youtube_id) DO NOTHING
                        """),
                        v
                        )
                conn.commit()
        yield
app = FastAPI(lifespan=lifespan)
# Serve frontend
@app.get("/")
def read_index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Elo system
def update_elo(winner_rating, loser_rating, k=32):
    expected_win = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    winner_new = winner_rating + k * (1 - expected_win)
    loser_new = loser_rating + k * (0 - (1 - expected_win))
    return winner_new, loser_new

class Vote(BaseModel):
    winner_id: int
    loser_id: int

@app.post("/vote")
def vote(v: Vote):
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, rating FROM items WHERE id IN (:w,:l)"
        ), {"w": v.winner_id, "l": v.loser_id}).fetchall()

        if len(result) != 2:
            raise HTTPException(status_code=400, detail="Invalid item IDs")

        winner_rating = result[0][1] if result[0][0] == v.winner_id else result[1][1]
        loser_rating = result[1][1] if result[1][0] == v.winner_id else result[0][1]

        new_winner, new_loser = update_elo(winner_rating, loser_rating)

        conn.execute(text("UPDATE items SET rating=:r WHERE id=:id"),
                     {"r": new_winner, "id": v.winner_id})
        conn.execute(text("UPDATE items SET rating=:r WHERE id=:id"),
                     {"r": new_loser, "id": v.loser_id})

        conn.commit()

    return {"status": "updated"}

@app.get("/rankings")
def rankings():
    with engine.connect() as conn:
        result = conn.execute(text(
        "SELECT id, title, youtube_id, rating FROM items ORDER BY rating DESC"
        )).fetchall()

        return [
                {"id": r[0], "title": r[1], "youtube_id": r[2], "rating": r[3]}
                for r in result
        ]

@app.get("/pair")
def pair():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, title, youtube_id FROM items ORDER BY RANDOM() LIMIT 2"
        )).fetchall()

        return [
            {
                "id": r[0],
                "title": r[1],
                "youtube_id": r[2]
            }
            for r in result
        ]