import sys
from pathlib import Path

# Add project root to sys.
# This is temporary change.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path
from db.create_db import DB_PATH
from src.downloader import FotoladuDownloader

DEFAULT_PAGES = 50


def main() -> None:
    dl = FotoladuDownloader(db_path=DB_PATH)
    raw_dir = Path("data/raw")

    folders = [f for f in raw_dir.iterdir() if f.is_dir()]
    total = len(folders)

    print(f"Found {total} folders in {raw_dir}")

    for i, folder in enumerate(folders, start=1):
        print(f"[{i}/{total}] Processing folder: {folder.name}")
        dl.download_by_kaust(folder.name, max_pages=DEFAULT_PAGES)
        print(f"[{i}/{total}] Completed")


if __name__ == "__main__":
    main()
