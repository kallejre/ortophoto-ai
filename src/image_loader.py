from __future__ import annotations
"""src/image_loader.py  - random-image selector with URL helpers.

~~~~~~~~~~~~~~~~~~~~~~~
* URLs are now rooted at **`/data/...`** → `/data/raw/...`, `/data/corrected/...`,
  `/data/raw/.../thumbs/...` so they match a site where `/data` is the static
  root directory.
* ``_build_urls`` no longer hard-codes the variant folder name ("reduced").  It
  instead treats **`parts[-2]`** as the *variant* (e.g. `reduced`, `hd`, `scan`)
  and swaps just that segment for `thumbs`.  Future variant folders therefore
  work automatically.
  
Returned keys
-------------
* every column of the `image` table (id, path, aasta, …)
* `url`           - preferred variant (corrected ▸ raw ▸ thumb)
* `url_corrected` - empty string if the corrected file is absent
* `url_raw`       - always present (DB path)
* `url_thumb`     - empty if the thumb is missing

```jsonc
{
  "id": 42,
  "fotoladu_id": 261295,
  "path": "data/raw/ka/1985_K150_O35_38/reduced/1985-K150-670.jpg",
  "aasta": "1985",
  ...,
  "url": "/corrected/ka/1985_K150_O35_38/reduced/1985-K150-670.jpg",
  "url_corrected": "/corrected/ka/1985_K150_O35_38/reduced/1985-K150-670.jpg",
  "url_raw": "/raw/ka/1985_K150_O35_38/reduced/1985-K150-670.jpg",
  "url_thumb": "/raw/ka/1985_K150_O35_38/thumbs/1985-K150-670.jpg"
}
```
"""

from pathlib import Path
import sqlite3
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants - resolve once so they work on any OS
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # points to repo root
_DATA_DIR     = _PROJECT_ROOT / "data"
_DATA_RAW     = _DATA_DIR / "raw"
_DATA_CORR    = _DATA_DIR / "corrected"
_URL_PREFIX   = "/data"  # every public URL will start with this

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _rel_under_raw(p: Path) -> Path:
    """Return *p* relative to data/raw."""
    p = Path(p)
    try:
        return p.relative_to(_DATA_RAW)
    except ValueError:
        pass  # fall through
    # Handle mixed /absolute and backslash cases
    parts = [seg for seg in p.parts if seg not in ("data", "raw")]
    if parts and parts[0] == "":
        parts = parts[1:]
    return Path(*parts)


def _thumb_rel(raw_rel: Path) -> Path | None:
    """Return a Path for the thumbs variant if that file exists under raw."""
    if len(raw_rel.parts) < 2:
        return None
    *prefix, variant, filename = raw_rel.parts
    thumb_rel = Path(*prefix, "thumbs", filename)
    thumb_path = _DATA_RAW / thumb_rel
    return thumb_rel if thumb_path.exists() else None


def _build_urls(raw_path_str: str) -> Dict[str, str]:
    """Compose corrected/raw/thumb URLs (all forward slashes)."""
    raw_rel = _rel_under_raw(Path(raw_path_str))  # ka/.../reduced/img.jpg

    # raw
    raw_url = f"{_URL_PREFIX}/raw/{raw_rel.as_posix()}"

    # corrected
    corrected_path = _DATA_CORR / raw_rel
    corrected_url = (
        f"{_URL_PREFIX}/corrected/{raw_rel.as_posix()}"
        if corrected_path.exists()
        else ""
    )

    # thumb (swap variant folder)
    thumb_rel = _thumb_rel(raw_rel)
    thumb_url = (
        f"{_URL_PREFIX}/raw/{thumb_rel.as_posix()}" if thumb_rel is not None else ""
    )

    preferred = corrected_url or raw_url or thumb_url

    return {
        "url": preferred,
        "url_corrected": corrected_url,
        "url_raw": raw_url,
        "url_thumb": thumb_url,
    }


# ----------------------------------
# Main class - unchanged public API
# ----------------------------------

class ImageLoader:
    """Pick random rows from SQLite *image* table and attach URLs.

    A fresh connection is opened **per call** so FastAPI worker threads never
    share the same SQLite handle (avoids the *check_same_thread* error).  If
    you call ``random_images`` many times per request you can still cache your
    own connection externally.
    """

    def __init__(self, *, db_path: Path | str):
        self.db_path = Path(db_path)

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # ---- Public API ----------------------------------------------------
    def random_images(self, n: int = 1) -> List[Dict[str, Any]]:
        if n < 1:
            n = 1
            # raise ValueError("n must be >= 1")

        # Open connection *inside* the calling thread
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM image ORDER BY RANDOM() LIMIT ?", (n,)
            ).fetchall()

        result: List[Dict[str, Any]] = []
        for row in rows:
            meta = dict(row)
            meta.update(_build_urls(meta["path"]))
            result.append(meta)
        return result
