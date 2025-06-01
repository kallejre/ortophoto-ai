
import sys
import logging
from pathlib import Path
import cv2

# Does work with BW and colour images.
# May provide undesireable rsults if single flight was recorded on
# different film rolls. (Meaning there's varying colour/brightnes distortion)
# Current solution is to take average of precntiles, not precentile of averages.

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
    files = sorted((path / VARIANT).glob("*.jpg"))
    for f in files:
        img = cv2.imread(str(f), cv2.IMREAD_COLOR_BGR)
        if img is not None:
            imgs.append(img)
    if not imgs:
        logging.info(f"No images found in {(path / VARIANT)}")
        return

    avg_path = OUT_DIR / path.parent.name / path.name / "average.jpg"
    corrected_avg_path = OUT_DIR / path.parent.name / path.name / "average_corrected.jpg"
    out_dir = OUT_DIR / path.parent.name / path.name / VARIANT
    out_dir.mkdir(parents=True, exist_ok=True)

    balanced, corrected_avg, avg = batch_tone_balance(
        imgs,
        save_avg=avg_path,
        save_corrected_avg=corrected_avg_path,
    )
    for im, f in zip(balanced, files):
        cv2.imwrite(str(out_dir / f.name), im, [int(cv2.IMWRITE_JPEG_QUALITY), 85])


def main(resume_from: int = 1) -> None:
    folders = _kaust_folders(RAW_DIR)
    for idx, kaust in enumerate(folders, start=1):
        if idx < resume_from:
            continue
        file_count = len( sorted((kaust / VARIANT).glob("*.jpg")))
        logger.info(f"[{idx}/{len(folders)}] Processing {kaust} - {file_count} files")
        process_kaust(kaust)
    logger.info("Done")


if __name__ == "__main__":
    main()
