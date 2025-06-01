import sys
import logging
from pathlib import Path
import cv2

# FIXME - Does not work for BW images.
# may work for colour images, but for BW the averaging is too heavy.

# Add project root to sys.path to make imports work
# This is temporary change.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.image_utils import batch_tone_balance

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

RAW_ROOT = Path("data/raw")
OUT_ROOT = Path("data/corrected")
VARIANT = "reduced"


def process_kaust(peakaust: Path, kaust: Path) -> None:
    """Load all images under kaust, balance them and save to OUT_ROOT."""
    img_dir = kaust / VARIANT
    imgs = []
    paths = sorted(img_dir.glob("*.jpg"))
    if not paths:
        return
    for p in paths:
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is not None:
            imgs.append(img)
    if not imgs:
        logging.info(f"No images found in {variant_dir}")
        return

    avg_path = OUT_ROOT / peakaust.name / kaust.name / "average.jpg"
    balanced = batch_tone_balance(imgs, save_avg=avg_path)

    out_dir = OUT_ROOT / peakaust.name / kaust.name / VARIANT
    out_dir.mkdir(parents=True, exist_ok=True)
    for src, img in zip(paths, balanced):
        cv2.imwrite(str(out_dir / src.name), img)
    logging.info("Processed %s", kaust)


def main() -> None:
    for peakaust in RAW_ROOT.iterdir():
        if not peakaust.is_dir():
            continue
        for kaust in peakaust.iterdir():
            if kaust.is_dir():
                process_kaust(peakaust, kaust)


if __name__ == "__main__":
    main()