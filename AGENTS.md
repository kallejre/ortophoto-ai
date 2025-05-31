# Agents Overview

Two primary reference files are `readme.md` and `development-notes.md` (both names are lowercase).

The **Geo‑Tag Orthophoto Labeler** project builds a lightweight tool‑chain for processing vintage
aerial photographs from *Maa‑amet*’s Fotoladu archive.  We fetch scans, apply colour and vignette
correction, and present a browser UI so humans can tag roads, rivers, settlements and other features.  
Those curated labels will seed a future computer‑vision model that can automatically recognise the
same features, accelerating large‑scale geo‑tagging of historical imagery.

Technically, the stack centres on a Python **FastAPI** backend that serves random images and CRUD
endpoints, backed by a single‑file **SQLite** database.  A static HTML/HTMX front‑end lives in
`static/`, while background workers in `fetch.py` and `processing.py` handle download, preprocessing
and (later) model inference.  The layout is intentionally minimal—single‑command setup via
`./setup_env.sh`, no heavy dependencies until the AI phase—to keep the project easy to fork,
audit and run on modest hardware.

The environment doesn't support `nano` - use `cat`, `tail`, `head` or `grep` instead.
Also for finding files by filename, prefer `ls` or `find`.
