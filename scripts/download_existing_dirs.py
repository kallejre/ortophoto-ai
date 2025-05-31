import sys
import logging
from pathlib import Path

# Add project root to sys.path to make imports work
# This is temporary change.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.create_db import DB_PATH
from src.downloader import FotoladuDownloader

# 3) Configure logging with timestamps
# Format: 2025-06-01 12:34:56 INFO: Your message here
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("__name__")

DEFAULT_PAGES = 50


def main() -> None:
    # Initialize downloader once, pointing at the same DB_PATH used elsewhere
    dl = FotoladuDownloader(db_path=DB_PATH)
    raw_dir = Path("data/raw")

    # ① Gather all subdirectories under data/raw
    folders = [f for f in raw_dir.iterdir() if f.is_dir()]
    total = len(folders)
    logger.info(f"Found {total} folders in `{raw_dir}` to process.")

    # ② Iterate and download by 'kaust'
    for idx, folder in enumerate(folders, start=1):
        kaust_name = folder.name
        logger.info(f"[{idx}/{total}] Starting download for folder: {kaust_name!r}")
        try:
            dl.download_by_kaust(kaust_name, max_pages=DEFAULT_PAGES)
            logger.info(f"[{idx}/{total}] Completed folder: {kaust_name!r}")
        except Exception as e:
            logger.exception(f"[{idx}/{total}] Error processing folder {kaust_name!r}: {e}")
    logger.info("All directories processed. Exiting.")


if __name__ == "__main__":
    main()
