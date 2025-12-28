from fastapi import FastAPI
from sqlalchemy import text

from db import engine

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-health")
def db_health():
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()

    return {"db": "ok", "select": value}
