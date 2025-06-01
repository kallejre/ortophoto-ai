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


def _levels_map(ch: np.ndarray, p3: float, p50: float, p97: float) -> np.ndarray:
    """
    Piecewise‐linear tone mapping (levels) for a single channel array.
    Uses percentile breakpoints (p3, p50, p97).
    """
    xp = np.array([0.0, p3, p50, p97, 255.0], dtype=np.float32)
    fp = np.array([0.0, 0.0, 128.0, 255.0, 255.0], dtype=np.float32)

    # np.interp will handle all bounding and other issues.
    mapped = np.interp(ch.astype(np.float32), xp, fp)
    return mapped.astype(np.uint8)


def _apply_levels(
    img: np.ndarray, lows: np.ndarray, mids: np.ndarray, highs: np.ndarray
) -> np.ndarray:
    """Apply levels mapping per channel."""
    if img.ndim == 2 or img.shape[2] == 1:
        ch = img if img.ndim == 2 else img[:, :, 0]
        return _levels_map(ch, float(lows[0]), float(mids[0]), float(highs[0]))

    chans = []
    for i in range(img.shape[2]):
        chans.append(
            _levels_map(img[:, :, i], float(lows[i]), float(mids[i]), float(highs[i]))
        )
    return cv2.merge(chans)


def batch_tone_balance(
    images: list[np.ndarray], *, save_avg: Path | None = None, size: int = 512
) -> tuple[list[np.ndarray], np.ndarray]:
    """Apply tone balance to a batch using percentiles from the blurred average.

    Images are resized to 512x512. The blurred average (15px sigma) is used to
    calculate the 3rd, 50th and 97th percentiles. The same mapping is then
    applied to every image in the batch. If ``save_avg`` is given, the average is
    saved to that path.
    """
    """Resize images, compute average and per-channel levels adjustment."""

    resized = [
        cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA) for img in images
    ]
    # blurred = [cv2.GaussianBlur(im, (0, 0), sigmaX=15, sigmaY=15) for im in resized]
    blurred = resized
    avg_img = np.mean(np.stack([im.astype(np.float32) for im in blurred]), axis=0)
    avg_img_u8 = avg_img.astype(np.uint8)

    if save_avg is not None:
        save_avg.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(save_avg), avg_img_u8)

    # Average the percentiles from individual images
    percs = [np.percentile(im, [3, 50, 97], axis=(0, 1)) for im in blurred]
    percs = np.stack(percs, axis=0)
    mean_percs = percs.mean(axis=0)

    if mean_percs.ndim == 1:
        lows = np.array([mean_percs[0]])
        mids = np.array([mean_percs[1]])
        highs = np.array([mean_percs[2]])
    else:
        lows, mids, highs = mean_percs[:, 0], mean_percs[:, 1], mean_percs[:, 2]

    corrected = [_apply_levels(img, lows, mids, highs) for img in images]
    return corrected, avg_img_u8
