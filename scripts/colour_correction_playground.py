from pathlib import Path
import cv2
from src.image_utils import crop_borders, vignette_correct, batch_tone_balance
# Work in progress.
# This script's objective is to try out colour correction with one directory, without writing results to disk.

src = Path("path/to/image.jpg")
img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)

img = crop_borders(img)
img = vignette_correct(img)

balanced, _ = batch_tone_balance([img], save_avg=Path("avg.jpg"))
cv2.imwrite("balanced.jpg", balanced[0], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
