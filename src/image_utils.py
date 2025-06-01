"""Placeholder image processing utilities."""

import cv2
from pathlib import Path
import numpy as np


def crop_borders(img: np.ndarray) -> np.ndarray:
    """Crop scanner borders using the heuristic described in the README."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(g, 8, 255, cv2.THRESH_BINARY_INV)
    m = cv2.floodFill(m, None, (0, 0), 255)[1]
    m = cv2.dilate(m, np.ones((8, 8), np.uint8))
    x, y, w, h = cv2.boundingRect(255 - m)
    return img[y : y + h, x : x + w]


def vignette_correct(img: np.ndarray) -> np.ndarray:
    """Apply a very rough vignette correction."""
    h, w = img.shape[:2]
    scale = 512.0 / w
    small = cv2.resize(img, (512, int(h * scale)), interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(small, (0, 0), sigmaX=120 * scale, sigmaY=120 * scale)
    blur = cv2.resize(blur, (w, h), interpolation=cv2.INTER_LINEAR)
    corrected = img.astype(np.float32) / np.maximum(blur.astype(np.float32), 1)
    corrected = cv2.normalize(corrected, None, 0, 255, cv2.NORM_MINMAX)
    return corrected.astype(np.uint8)


def compute_luma_stats(img: np.ndarray) -> dict:
    """Return simple luma statistics for quality control."""
    b, g, r = cv2.split(img)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    p2, p98 = np.percentile(luma, [2, 98])
    return {
        "mean": float(np.mean(luma)),
        "std": float(np.std(luma)),
        "p2": float(p2),
        "p98": float(p98),
    }


def _levels_map_old(channel: np.ndarray, p3: float, p50: float, p97: float) -> np.ndarray:
    """Return channel mapped so that p3->0, p50->128 and p97->255."""
    out = channel.astype(np.float32)
    mask_lo = out <= p50
    out[mask_lo] = (out[mask_lo] - p3) * (128.0 / max(p50 - p3, 1e-5))
    mask_hi = ~mask_lo
    out[mask_hi] = 128.0 + (out[mask_hi] - p50) * (127.0 / max(p97 - p50, 1e-5))
    return np.clip(out, 0, 255).astype(np.uint8)

def _levels_map(img: np.ndarray, p3, p50, p97) -> np.ndarray:
    """Piecewise linear tone mapping helper."""
    if img.ndim == 2:
        xp = np.array([0, p3, p50, p97, 255], dtype=np.float32)
        fp = np.array([0, 0, 128, 255, 255], dtype=np.float32)
        mapped = np.interp(img, xp, fp)
        return mapped.astype(np.uint8)

    out = []
    for c in range(img.shape[2]):
        xp = np.array([0, p3[c], p50[c], p97[c], 255], dtype=np.float32)
        fp = np.array([0, 0, 128, 255, 255], dtype=np.float32)
        out.append(np.interp(img[:, :, c], xp, fp))
    return np.stack(out, axis=2).astype(np.uint8)


def batch_tone_balance(images: list[np.ndarray], *, save_avg: Path | None = None) -> list[np.ndarray]:
    """Apply tone balance to a batch using percentiles from the blurred average.

    Images are resized to 512x512. The blurred average (15px sigma) is used to
    calculate the 3rd, 50th and 97th percentiles. The same mapping is then
    applied to every image in the batch. If ``save_avg`` is given, the average is
    saved to that path.
    """
    if not images:
        return []

    resized = [cv2.resize(im, (512, 512), interpolation=cv2.INTER_AREA) for im in images]
    blurred = [cv2.GaussianBlur(im, (0, 0), sigmaX=15, sigmaY=15) for im in resized]
    avg = np.mean(np.stack([b.astype(np.float32) for b in blurred]), axis=0)

    if save_avg is not None:
        save_avg.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(save_avg), avg.astype(np.uint8))

    if avg.ndim == 2:  # greyscale
        params = [tuple(np.percentile(avg, [3, 50, 97]))]
    else:
        params = [tuple(np.percentile(avg[:, :, c], [3, 50, 97])) for c in range(3)]

    balanced = []
    for img in images:
        if img.ndim == 2:
            p = params[0]
            balanced.append(_levels_map(img, *p))
            continue
        channels = [_levels_map(img[:, :, i], *params[i]) for i in range(3)]
        balanced.append(cv2.merge(channels))
    return balanced
