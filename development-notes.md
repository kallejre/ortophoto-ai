# Development notes

> Basically readme part 2 - focuses on what I am actually doing and why.

### Initial ideas

I do not want to write much UI code, so I prefer a static HTML/JS web application for the UI, with a separate backend. THere are 2 possible frameworks worth investigating:

* **FastAPI** will handle the backend `/api` routes.
* **Flask** feels overly complicated for this use-case.

### Directory structure

```text
project/
├── app.py          # FastAPI app, serves /api/*
├── static/         # index.html, script.js, style.css
├── data/           # raw/ processed/
├── db/             # fotoladu.sqlite.db
└── fetch.py export.py utilities.py
```

### Development phases - plan 1

* **Environment setup** - create `venv`, install packages.
* **Image downloader** - reuse a directory layout similar to Maa-amet, but simplified.
  Example source files:

  * <https://fotoladu.maaamet.ee/data/archive/arhiiv/ma_neg/158-C-871-73/reduced/1973-C871-345.jpg>
  * <https://fotoladu.maaamet.ee/data/archive/arhiiv/ma_neg_ngr/346-C871-A-73/reduced/1973-C871-A-345.jpg>  
    become
  * `./data/raw/158-C-871-73/reduced/1973-C871-345.jpg`
  * `./data/raw/346-C871-A-73/reduced/1973-C871-A-345.jpg`  
    Priorities: download `thumbs` and `reduced` sizes first.
* **Randomised downloader** - use `otsing_arhiiv.php`.
  * Later we could replicate the existing archive search UI.
  * Another option is to download all images from the same flight for averaging and other corrections. We'd need to handle pagination then.
* **Metadata capture** - parse and store basic metadata from the same `otsing_arhiiv.php` page.
* **Backend for image labelling metadata**
  * Basic CRUD for an image’s tags; data stored in SQLite.

    ```json
    {
      "img_id": 1234, "fotoladu_id": 321,
      "tags": {"tag1": true, "tag2": false, "tag3": null}
    }
    ```

  * DB tables:
    * `Image` (id, fotoladu\_id, path\_on\_disk)
    * `Location` (lat, lon, X, Y, confidence, source)
    * `Tags` (id, img, tag, state)
  * Add basic logging and async download handling.
* **Labelling front-end prototype**
  * Load a random image from the API.
  * Checkboxes for various tags (toggle via keyboard shortcuts?).
  * Submit and load the next image.
  * UI built with Bootstrap.
  * Image ID lives in the URL hash.
  * Keep track of tagging stats.
* **Basic geohinting** - given known positions of previous images in a sequence, guess the next image location.
  * Probably out of scope for this repo.
* **Advanced image post-processing** - colour correction, etc.
  * Crop obvious borders.
  * Calculate the average of one flight/batch.
  * Vignette correction.
  * From the average image, define parameters to correct colour or contrast, then apply them to the whole flight.
* **AI experiments**
  * Build a Jupyter notebook.
  * Try training on \~30 images.

---

### Possible labeling tags / classifiers

* Coastline (sea or major lake)
* Long straight line (railway or motorway)
* Wide long straight line (airfield)
* Settlements - tihe(dam)asustus
  * City - large portion of image filled
  * Town - entire settlement would fill 50-90% of single image
  * Village - small cluster of around 10 streets
  * Linear settlement - Ridaküla
  * Farm - One or more sparse clusters of residential buildings
* River
* Forest
* Field
* Industrial

### Possibly noteworthy links

<https://developers.google.com/machine-learning/crash-course/exercises>
<https://www.geeksforgeeks.org/opencv-python-tutorial/>
<https://fpcv.cs.columbia.edu/>

### Tools (heard of or used before)

* Label Studio
* CVAT
* Roboflow - apparently already have an account?

### Environment setup

The repository includes `requirements.txt` listing the basic packages needed for the downloader and API. To create a virtual environment and install them run:

```bash
./setup_env.sh
```

This script creates `.ortho-venv/` and installs the packages with `pip`. No AI training libraries are included yet.
