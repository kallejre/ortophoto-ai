"""Placeholder image processing utilities."""

import cv2
import numpy as np


def crop_borders(img: np.ndarray) -> np.ndarray:
    """Crop scanner borders using the heuristic described in the README."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(g, 8, 255, cv2.THRESH_BINARY_INV)
    m = cv2.floodFill(m, None, (0, 0), 255)[1]
    m = cv2.dilate(m, np.ones((8, 8), np.uint8))
    x, y, w, h = cv2.boundingRect(255 - m)
    return img[y:y+h, x:x+w]


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

