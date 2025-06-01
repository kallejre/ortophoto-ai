from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from db.create_db import init_db, DB_PATH
from pathlib import Path
from src.downloader import FotoladuDownloader, SearchParams
from src.image_loader import ImageLoader

STATIC_DIR = Path("static")
DATA_DIR = Path("data")

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
downloader = None
imgloader = None


@app.on_event("startup")
async def startup() -> None:
    if not DB_PATH.exists():
        init_db(DB_PATH)
        print("Created DB")
    global downloader
    if not downloader:
        downloader = FotoladuDownloader(db_path=DB_PATH)
        print("Downloader init")
    global imgloader
    if not imgloader:
        imgloader = ImageLoader(db_path=DB_PATH)
        print("ImageLoader init")


@app.get("/")
def read_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/random")
def random_image(count: int | None = 5):
    """Return placeholder random image data."""
    try:
        print(123)
        return imgloader.random_images(n=count)
    except Exception as err:
        print(err)
        raise err


@app.post("/api/download")
async def api_download(
    background_tasks: BackgroundTasks,
    nr: int | None = None,
    kaust: str | None = None,
):
    """
    Trigger image download in a background task.

    Queue a download task for every image whose *photo sequence number*
    matches `nr` (same as typing it into Fotoladu's "Foto nr" field).
    """
    pages = 50
    if kaust:
        background_tasks.add_task(downloader.download_by_kaust, kaust, max_pages=pages)
        return {"status": "started", "kaust": kaust}

    if nr is not None:
        params = SearchParams(foto_nr=nr, lkcount=60)
        background_tasks.add_task(downloader.download_via_search, params)
        return {"status": "started", "nr": nr}

    return {"error": "specify either nr or kaust"}
