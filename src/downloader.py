from __future__ import annotations

"""src/downloader.py - Class-based helper around Maa-amet *Fotoladu*.

This refactor wraps the earlier functional helpers in an **importable class** so
FastAPI (or any other caller) can keep one long-lived instance that shares the
base download folder and database handle.

Usage
-----
```python
from pathlib import Path
from src.downloader import FotoladuDownloader, SearchParams, BBoxParams

dl = FotoladuDownloader(db_path=Path("app.db"))
dl.download_via_search(SearchParams(foto_nr=532, lkcount=60))
# or
box = BBoxParams(a_lat=58.676, a_lng=27.107, u_lat=58.725, u_lng=27.209)
dl.ingest_bbox(box)
```
"""

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import logging
from db.create_db import init_db
from pydantic import BaseModel, Field, validator

__all__ = [
    "SearchParams",
    "BBoxParams",
    "FotoladuDownloader",
]

logger = logging.getLogger("uvicorn.error")

# ---------------------------------------------------------------------------
# Endpoint constants
# ---------------------------------------------------------------------------

BASE_URL = "https://fotoladu.maaamet.ee"
SEARCH_URL = f"{BASE_URL}/otsing_arhiiv.php"
BBOX_URL = f"{BASE_URL}/paring_db_arhiiv.php"
NEAREST_URL = f"{BASE_URL}/paring_closest_arhiiv.php"
IMAGE_URL = f"{BASE_URL}/data/archive/arhiiv"

# ---------------------------------------------------------------------------
# Pydantic query models
# ---------------------------------------------------------------------------


class SearchParams(BaseModel):
    """Mirror parameters of ``otsing_arhiiv.php``."""

    foto_nr: Optional[int] = Field(None, description="Photo sequence number")
    aasta: str = ""
    kaardileht: str = ""
    lennu_nr: str = ""
    foto_tyyp: str = ""
    allikas: str = ""
    sailiku_nr: str = ""
    w: float = 611.4
    h: float = 739.2
    start: int = 0
    lkcount: int = 30

    @validator("lkcount")
    def _cap_lkcount(cls, v: int) -> int:  # noqa: N805 - pydantic naming
        return min(v, 60)

    def to_query(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class BBoxParams(BaseModel):
    """Bounding-box query mirroring ``paring_db_arhiiv.php`` (GeoJSON)."""

    aasta: str = ""
    a_lat: float
    a_lng: float
    u_lat: float
    u_lng: float
    m: int = 9
    arhiiv: str = "arhiiv"

    def to_query(self) -> Dict[str, Any]:
        return self.dict()


# Positional mapping used in the site’s JS call ``kuvapiltfuncarhiiv``
_KUVA_KEYS = [
    "id",
    "aasta",
    "B",
    "L",
    "tapsus",
    "w",
    "h",
    "peakaust",
    "kaust",
    "fail",
    "lend",
    "fotonr",
    "kaardileht",
    "tyyp",
    "allikas",
]

_KUVA_PATTERN = re.compile(r"kuvapiltfuncarhiiv\(([^)]*)\)")

# ---------------------------------------------------------------------------
# Helper functions (kept module-level for reuse/testing)
# ---------------------------------------------------------------------------


def _http_get(url: str, params: Dict[str, Any] | None = None, *, json: bool = False):
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json() if json else resp.text


def _parse_kuva_args(arg_str: str) -> Dict[str, Any]:
    import ast

    values = ast.literal_eval("[" + arg_str + "]")
    return {k: v for k, v in zip(_KUVA_KEYS, values)}


def _parse_search_html(html: str) -> List[Dict[str, Any]]:
    return [_parse_kuva_args(m.group(1)) for m in _KUVA_PATTERN.finditer(html)]


def _parse_search_meta(html: str) -> Dict[str, int]:
    """Extract pagination metadata from the search HTML."""

    def _int(m: Optional[re.Match]) -> int:
        if not m:
            return 0
        return int(m.group(1).replace(" ", ""))

    return {
        "total": _int(re.search(r"Leitud fotosid:\s*([\d\s]+)", html)),
        "pages": _int(re.search(r"var\s+lk_nr\s*=\s*(\d+)", html)),
        "rows": _int(re.search(r"var\s+ridu\s*=\s*(\d+)", html)),
        "limit": _int(re.search(r"var\s+limit\s*=\s*(\d+)", html)),
    }


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class FotoladuDownloader:
    """Stateful helper for downloading images + ingesting metadata."""

    def __init__(
        self,
        *,
        db_path: Path | str,
        base_path: Path | str = Path("data/raw"),
        variant: str = "reduced",
    ) -> None:
        """Create the downloader, preparing paths and DB connection."""
        self.db_path = Path(db_path)
        self.base_path = Path(base_path)
        self.variant = variant
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        # init_db()

    # ------------------------------------------------------------------
    # Database connection helpers
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return an open SQLite connection, creating it if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        else:
            try:
                self._conn.execute("SELECT 1")
            except sqlite3.ProgrammingError:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA synchronous=NORMAL")
        return self._conn

    def close(self) -> None:
        """Commit and close the SQLite connection if open."""
        if self._conn is not None:
            try:
                self._conn.commit()
            finally:
                self._conn.close()
                self._conn = None

    def __del__(self) -> None:  # noqa: D401 - simple finalizer
        """Ensure connection is closed on garbage collection."""
        try:
            self.close()
        except Exception:
            pass

    # ---------------------------------------------------------------------
    # Public high-level helpers
    # ---------------------------------------------------------------------

    def download_via_search(
        self, params: SearchParams | int, *, max_pages: int = 20
    ) -> None:
        """Download images for a search query and store metadata.

        The downloader fetches both the main ``variant`` (usually ``reduced``)
        and the ``thumbs`` version of each image.  Only the ``variant`` path is
        recorded in the database.

        ``max_pages`` guards against runaway downloads by limiting how many
        result pages are processed.  It defaults to 20, but a smaller number
        can be supplied by callers that need tighter control.
        """
        if isinstance(params, int):
            params = SearchParams(foto_nr=params)
        print(params)
        html = self._query_search(params)
        entries = _parse_search_html(html)
        # print(entries)
        meta = _parse_search_meta(html)
        self._bulk_ingest(entries)

        page_size = meta.get("rows", 0) * meta.get("limit", 0)
        if not page_size:
            page_size = len(entries)
        total_pages = meta.get("pages") or 1
        if meta.get("total") and page_size:
            total_pages = max(total_pages, (meta["total"] + page_size - 1) // page_size)

        for page in range(1, min(total_pages, max_pages)):
            params.start = page * page_size
            html = self._query_search(params)
            entries = _parse_search_html(html)
            self._bulk_ingest(entries)
        logging.info(f"Processed {min(total_pages, max_pages)} pages, with approx {page_size * min(total_pages, max_pages)} records")

    def download_by_kaust(self, kaust: str, *, max_pages: int = 50) -> None:
        """Download all images belonging to a Fotoladu directory."""
        params = SearchParams(sailiku_nr=kaust, lkcount=60)
        self.download_via_search(params, max_pages=max_pages)

    def ingest_bbox(self, box: BBoxParams) -> None:
        """Fetch GeoJSON metadata inside a bounding-box and download images.

        Similar to ``download_via_search`` this will pull both the main
        ``variant`` and the ``thumbs`` version for every returned frame, while
        storing only the ``variant`` path in the database.
        """

        gj = _http_get(BBOX_URL, params=box.to_query(), json=True)
        entries = [feat["properties"] for feat in gj.get("features", [])]
        self._bulk_ingest(entries)

    def nearest(self, lat: float, lon: float, *, year: str = "", leier: str = "1963") -> Dict[str, Any]:
        """Return the raw JSON of the “nearest frames” endpoint."""

        return _http_get(NEAREST_URL, params=dict(B=lat, L=lon, leier=leier, aasta=year), json=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _query_search(params: SearchParams | int) -> str:
        if isinstance(params, int):
            params = SearchParams(foto_nr=params)
        return _http_get(SEARCH_URL, params=params.to_query())

    def _bulk_ingest(self, metas: List[Dict[str, Any]]) -> None:
        """Insert a batch of metadata rows and download images."""
        conn = self._get_conn()
        try:
            for meta in metas:
                path = self._download_image(meta)
                self._insert_db(conn, meta, path)
            conn.commit()
        except KeyboardInterrupt:  # pragma: no cover - user triggered
            logger.info("Interrupted. Committing partial results before exit.")
            conn.commit()
            self.close()
            raise
        logger.debug(f"DL of {len(metas)} images completed")

    # Image download ----------------------------------------------------

    def _download_image(self, meta: Dict[str, Any]) -> Path:
        """Download both 'reduced' and thumbnail variants of an image."""

        def _get(variant: str) -> Path:
            url = f"{IMAGE_URL}/{meta['peakaust']}/{meta['kaust']}/{variant}/{meta['fail']}"
            dest_dir = self.base_path / meta["peakaust"] / meta["kaust"] / variant
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / meta["fail"]
            if not dest.exists():
                logger.debug("Downloading " + str(dest))
                data = requests.get(url, timeout=60).content
                dest.write_bytes(data)
            else:
                logger.debug("Skipping DL " + str(dest))
            return dest

        # Always download the main variant and a thumbnail
        path = _get(self.variant)
        if self.variant != "thumbs":
            _get("thumbs")
        return path

    # SQLite insert -----------------------------------------------------

    _INSERT_IMG = (
        "INSERT OR IGNORE INTO image (fotoladu_id, path, aasta, w, h, peakaust, kaust, fail, lend, fotonr, kaardileht, tyyp, allikas) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    _INSERT_LOC = "INSERT OR IGNORE INTO location (image_id, lat, lon, confidence) VALUES (?,?,?,?)"
    _SELECT_IMG_ID = "SELECT id FROM image WHERE fotoladu_id = ?"

    def _insert_db(self, db: sqlite3.Connection, meta: Dict[str, Any], path: Path) -> None:
        db.execute(
            self._INSERT_IMG,
            (
                meta.get("id"),
                str(path),
                meta.get("aasta"),
                meta.get("w"),
                meta.get("h"),
                meta.get("peakaust"),
                meta.get("kaust"),
                meta.get("fail"),
                meta.get("lend"),
                meta.get("fotonr"),
                meta.get("kaardileht"),
                meta.get("tyyp"),
                meta.get("allikas"),
            ),
        )
        row = db.execute(self._SELECT_IMG_ID, (meta.get("id"),)).fetchone()
        if row:
            db.execute(self._INSERT_LOC, (row[0], meta.get("B"), meta.get("L"), meta.get("tapsus")))
