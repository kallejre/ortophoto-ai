
import sys
import logging
from pathlib import Path
import cv2

# FIXME - Does not work for BW images.
# may work for colour images, but for BW the averaging is too heavy.
# Possible solution is to take average of precntiles, not precentile of averages.

# Add project root to sys.path to make imports work
# This is temporary change.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.image_utils import batch_tone_balance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/corrected")
VARIANT = "reduced"


def _kaust_folders(base: Path) -> list[Path]:
    folders = []
    for peakaust in base.iterdir():
        if not peakaust.is_dir():
            continue
        for kaust in peakaust.iterdir():
            if kaust.is_dir():
                folders.append(kaust)
    return folders


def process_kaust(path: Path) -> None:
    imgs = []
    files = sorted((path / "reduced").glob("*.jpg"))
    for f in files:
        img = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)
        if img is not None:
            imgs.append(img)
    if not imgs:
        logging.info(f"No images found in {(path / "reduced")}")
        return

    avg_path = OUT_DIR / path.parent.name / path.name / "average.jpg"
    out_dir = OUT_DIR / path.parent.name / path.name / VARIANT
    out_dir.mkdir(parents=True, exist_ok=True)

    balanced, avg = batch_tone_balance(imgs, save_avg=avg_path)
    for im, f in zip(balanced, files):
        cv2.imwrite(str(out_dir / f.name), im)


def main() -> None:
    folders = _kaust_folders(RAW_DIR)
    for idx, kaust in enumerate(folders, start=1):
        logger.info(f"[{idx}/{len(folders)}] Processing {kaust}")
        process_kaust(kaust)
    logger.info("Done")


if __name__ == "__main__":
    main()