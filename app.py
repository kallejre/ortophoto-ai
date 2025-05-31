from fastapi import FastAPI
from pathlib import Path

DB_PATH = Path('db/fotoladu.sqlite.db')

app = FastAPI()

@app.on_event('startup')
async def startup() -> None:
    if not DB_PATH.exists():
        from db.create_db import init_db
        init_db(DB_PATH)

@app.get('/')
def read_root():
    return {"status": "ok"}
