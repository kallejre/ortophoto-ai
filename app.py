from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from db.create_db import init_db, DB_PATH
from pathlib import Path
from src.downloader import FotoladuDownloader, SearchParams

STATIC_DIR = Path("static")
STATIC_DIR_readme = Path("readme-images")

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/readme-images", StaticFiles(directory=STATIC_DIR_readme), name="static")
downloader = None


@app.on_event("startup")
async def startup() -> None:
    if not DB_PATH.exists():
        init_db(DB_PATH)
        print("Created DB")
    global downloader
    if not downloader:
        downloader = FotoladuDownloader(db_path=DB_PATH)
        print("Downloader init")


@app.get("/")
def read_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/random")
def random_image():
    """Return placeholder random image data."""
    return {"id": 1, "url": "/readme-images/readme-C662-1971-532-edited.png"}


@app.post("/api/download")
async def api_download(nr: int, background_tasks: BackgroundTasks):
    """
    Trigger image download in a background task.

    Queue a download task for every image whose *photo sequence number*
    matches `nr` (same as typing it into Fotoladu's "Foto nr" field).
    """
    params = SearchParams(foto_nr=nr, lkcount=60)  # 60 = max per page
    background_tasks.add_task(downloader.download_via_search, params)
    return {"status": "started", "nr": nr}
