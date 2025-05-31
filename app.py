from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from db.create_db import init_db

DB_PATH = Path("db/fotoladu.sqlite.db")
STATIC_DIR = Path("static")
STATIC_DIR_readme = Path("readme-images")

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/readme-images", StaticFiles(directory=STATIC_DIR_readme), name="static")


@app.on_event("startup")
async def startup() -> None:
    if not DB_PATH.exists():
        init_db(DB_PATH)


@app.get("/")
def read_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/random")
def random_image():
    """Return placeholder random image data."""
    return {"id": 1, "url": "/readme-images/readme-C662-1971-532-edited.png"}
