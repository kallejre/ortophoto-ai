# Geo‑Tag Orthophoto Labeler

A small side-project to aid semi‑automatic geo‑tagging of scanned historical orthophotos.

I initially wished to add disclaimer about AI-generated content, but as LLM failed to produce even meaningful readme file, I'll keep just prompt and disclaimer.

> For starters, Write basic introduction readme to this project. I want to create a simple python web application for processing images..  The big idea of this project is to aid geo-tagging scans of archived. ortophotos. using image labelling ai. to do so, first step is to build streamlined UI for tagging geographical features in photos. Add warning that large portion of the project is AI generated. Components of this project will be python-based web server that can load random images from web service and store metadatainto sqlite database.

> **⚠️ LLM content notice**
> Large portions of this codebase, documentation, and future model pipelines are expected to be generated **with the assistance of generative‑AI tools**.
> Please audit and test the output carefully before deploying in production.

-----

Anyways, purpose of this readme is to define problem(s) trying to solve, and estimated path of yak shaving.

Glossary and backgorund info

* [Fotoladu](https://fotoladu.maaamet.ee/?basemap=digiaero&fotoarhiiv&overlay=tyhi)
* [Map sheet numbering system](https://geoportaal.maaamet.ee/est/ruumiandmed/kaardilehtede-susteemid/1963-a-kaardilehtede-susteem-p229.html)

## Goals

* Main goal - Build experimental system to potentially aid image tagging for Fotoladu.  
* Side goal - learn about computer vision oriented AI

Eventually this is going to be likely fail due to considerable amount of work needed.

## Possible path of solutions and deductions

*(Despite being bullet-point list, this was originally not written by AI, yet)*  
*I have later requested GPT to run grammar and syntax checks on this document*

* We could improve manual image placement suggestions by showing pin where next image could be placed  
    Side-note - users might become too fixated to that pin and would place image there even when it's incorrect
* Since majority of images are taken sequentially from plane using some kind of automation, we can relatively safely predict location of next image in sequence. Gap between two consecutive images is usually 3-5 km.  
    Side-note - old orthophotos include clock in some corner. Given three images with timestamps and two with positioning allows us to roughly estimate distance between image sequences even when images are not in immediate vincity. See images [272268](https://fotoladu.maaamet.ee/arhiiv=272268) and [272267](https://fotoladu.maaamet.ee/arhiiv=272267) as great counterexample. Two images were digitalized after one-another, but were originally taken 44 frames apart, one at 18:42:48, other at 19:07:23
![Image taken 15th of June 1970 at 18:42:48](readme-images/readme-C602-5-1970-06-15.png)
* About 99.99% of images are consistently oriented correctly north-up. Image 272268 (a.k.a 5th image of flight C-602) above is counterexample that prompted formalizing this project.
* We could estimate image locations even more accurately by comparing two images and detecting overlapping parts THis step is eased because usually images are taken sequentially and therefore matching algorithm already knows which image likely is closes match to observer one
* That method may cause risk of drifting difference between old imagery and new modern background imagery. especially when using historic background layer which may have incorrect georeference on it's own.
* We miht be able to rely on relatively fixed features such as old farmhouses, major railways, distinctively shaped land plots (see image 272268 above)
* Since every image may not have such key feature, it could be wise to attept stich together individual frames and then georeference features far away from each other and interpolate result to entire stiching
* They already have [dedicated layer group](https://fotoladu.maaamet.ee/?basemap=digiaero&minimap=1983%20Maa-amet&zlevel=11,24.50177,58.38413&fotoarhiiv&overlay=1983) in Fotoladu application where they already have done this.  
    For some reason images that were used for stiching, were not georeferenced, event thogh somewhere in their system has to be individual frame positions' information
* It's highly likely that Land Board has already working AI solutions for this exact purpose. On the other hand scanning 50 yrs old archive footage has probably low priority and therefore less likely to be developed.

PS. I haven't consulted with Land and Spatial Development Board beforehand, so this entire project might be obsolete before readme is even started.

## Bring in the AI

* This leads us to conclusion that after positioning first few images, it's relatively easy to position new images
* Therefore biggest challenge is knowing where or how to place first few images of one flight's sequence.
* Those images do not neccessarily have to be first images of flight, as one could also traverse array in reverse (Although current fotoladu application does not allow later)
* If we can position any image in uninterrupted seuqence, then every other image could be positioned too.
* Every\* photo has standard marking consisting of flight number, date and sequence number.  
  \* Excluding few special series from other sources, such as WW2 era German reconnaissance flights.
* Flight number is already somehow linked to old map sheet numbering scheme, most often [C-63 system](https://geoportaal.maaamet.ee/est/ruumiandmed/kaardilehtede-susteemid/1963-a-kaardilehtede-susteem-p229.html)
* Sheet number is neither reliable or accurate way to locate images. Judging by data it seems that sheet number is determined by (temporary) location of an individual photo or flight or vice versa. When image has not been georeferenced, it shown to be located somewhere on the sheet, but likely nowhere near actual location.
  * Apparently default location of image is integer value of WGS84 coordiantes it's located at (e.g 59.0, 24.0)
* single flight can encopass muliple map sheets
* Man-made features tend to have been built using straight lines, making them easier to spot on images.
* As mentioned earlier, most likely places that could be located, are man-made features that have stood there for decades or centuries, such as railways or farmhouses
* Even better, if we have cluster of buildings - also known as town or village.
* Therefore we should focus on detecting images, that have not been geolocated, but likely seem to contain human settlements.
* Sounds like great task for computer vision based AI.
* After AI has detected settlements, we could assess size of them (percentage of image containing settlement) and then try to match shape or road network with modern known urban street networks.
* We could then use conventional image stiching techniques combined with sequence-induced-optimizations to build rest of images around pinpointed urban imagery.
* Second brach of inquiry could be object detection AI for reading metadata from image - locating image number and analogue clock; reading their values.
* In theory this should be super easy and standardized problem to solve. I'm worried my laptop is very likely unable to train even single layer CNN for single epoch to even try it out.
* That's why this project ought to include some conventional OpenCV2-based signal processing too.

### Solution

* In order to develop AI, we need to train model. As mentioned above, i don't have resources to properly train one.
* However, I could create labelling tool.
    Well, there's abundance of possible tagging softwares, challenge is determining which ones are free, could potentially be locally hosted and most importantly, are for tagging whole image, not annotating objects in image
* As i don't want to download images to local PC, and to future proof tagging data for potentially integrating with official Fotoladu, i could use sqlite local DB to store image metadata and/or tagging information about images.
* Fotoladu doen't have much of API. For downloading images, i could use image search results.
* Most diverse results can be queried by searching images by individual frame number, using 3-digit integer as search term.  
    E.g GET
 <https://fotoladu.maaamet.ee/otsing_arhiiv.php?foto_nr=432&aasta=&kaardileht=&lennu_nr=&foto_tyyp=&allikas=&sailiku_nr=&w=611.4&h=739.2&start=0&lkcount=10>  
* Despite `lkcount=10` this link returns HTML page containing 30 image urls. Images are 'large', 512 px along longer edge, usualy around 40-50 kB. Image urls are contained withing `<img>` tags, therefore I'll need regex there.
* Speaking of preprocessing, probably equalizing filter and high-pass should be applied before training.
* Biggest problem with image search is that they may already include georeferenced images.
* Due to number of images, might be worth investigating if there are other API endpoints for querying img metadata.

### Technical

Estonia uses EPSG:3301 projection, which is XY system measuring meters from equator and Meridian.
Fotoladu images are not square, but typical thumbnails have both sides usually around 490..530 px
For starers, it might be easier to use whole image labelling AI and later specialize into keypoint detection or image segmentation.

Before directing to AI training, it might be good idea to standardise image colours. In theory equalizing each channel of NIR image may restore the original colours. However in case of black-white images, we should instead try to tweak light balance to achieve image's mean pixel brightness of 50%. Since most images contain either pure black or pure white border pixels, we should exclude them from equalization, maybe bottom 12 and top 3 thresholds. This thresholding won't work if image is too dark. Perhaps light balance should still be first step.

All this was for near-infrared colour images, but what about monotone BW images? I can't think of anything more than same brightness balance tweak as with individual colour channels. Assuming that camera had same settings during flight, then we should run calculations on avrage of entire batch, because otherwize flights over areas with different albedo (such as fields vs sea) will show same object significally in different tones.

Basically, objective of thresholding is to detect and remove image frames. Maybe there's better way to crop off borders of film scans?

Maybe first step is to colour correct all images in single batch by calclating their average vingette and then somehow correct them? Also apply blur before averaging.  
Image equalization won't work when dealing with images with very limited luminosity range, such as [pictures of sea](https://fotoladu.maaamet.ee/data/archive/arhiiv/ma_neg_ngr/324-C-413-68/reduced/1968-C413-614.jpg).

![alt text](readme-C662-1971-532.jpg)![alt text](readme-C662-1971-532-edited.png)

(AI snippet)
The first milestone is a streamlined UI that lets archivists and volunteers quickly tag geographical features (roads, rivers, building footprints, land‑use areas, etc.) in raster imagery. In later phases, those human‑confirmed tags will be used to train and fine‑tune image‑labeling models that can auto‑suggest tags for new, un‑seen scans.

#### AI generated summary of image processing notes

I asked for input on what or how to approach to image processing and since it pointed out some alleged best practices and opencv2 features ,  requested to write summary sutiable for later using as input for coding.

With some technical expalnations.  
**First-pass normalisation steps for Fotoladu frames.**
We are assuming to deal with medium image size of 512 px.

#### 0 · Decide if the frame is colour or B/W

*Goal – route each frame to the correct branch without external metadata.*

* **Quick heuristic** – sample a 128 × 128 px patch dead-centre.
  *If* `std(R-G) + std(G-B) < 5 % of total luma std` → probably B/W.
  *Small colour casts from ageing film still trigger the colour path; that is acceptable.*
* **Fallback** – if the three **digital-number** (DN) histograms – DN = the raw 8-bit scanner value 0…255 – have ≥ 95 % of their mass inside the same 10-DN bin (e.g. 120-129), treat as B/W.
* **Log the decision** – write a flag into SQLite (`is_color = 0/1`) for reproducibility.

#### 1 · Common pre-steps (both B/W & colour)

* **Crop borders early**
  *How* → look in the grey image and threshold out very dark / very bright pixels, then:

  1. **Flood-fill** – start at (0, 0) and grow into every neighbour that passes the threshold; this finds the connected border blob (scanner platen, black tape, etc.).
  2. **Dilate by 8 px** – morphological dilation (= Photoshop’s *Maximum* filter) expands that blob eight pixels inward; this margin ensures later stats never sample ragged border leftovers.
  3. Invert the mask, take its bounding box, crop the photo.

  *5-line sketch* (illustrative):

  ```python
  g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  _, m = cv2.threshold(g, 8, 255, cv2.THRESH_BINARY_INV)      # 8 ≈ noise floor
  m = cv2.floodFill(m, None, (0, 0), 255)[1]                  # step 1
  m = cv2.dilate(m, np.ones((8, 8), np.uint8))                # step 2
  x, y, w, h = cv2.boundingRect(255 - m)                      # step 3
  cropped = img[y:y+h, x:x+w]
  ```

* **Vignette (illumination) correction**

  1. Down-sample to 512 px width.
  2. Blur with a *very* wide Gaussian (σ ≈ 120 px).
  3. Divide the full-res image by the up-scaled blur field, then rescale to 0-255.
     *Corners end up within ± 5 % of centre brightness on > 90 % of flights.*

* **Per-frame metrics** (for QC SQL queries later)
  Compute `mean, std, p2, p98` of **luma** – luma = `0.299 R + 0.587 G + 0.114 B`, i.e. perceptual brightness – and insert into table `frame_stats`.

#### 2 · Branch A – B/W (panchromatic) frames

*(Panchromatic = one grey channel that covered the entire visible spectrum in the 1960s film stock; still “monochrome”, but not tied to a single colour band.)*

* **Global percentile stretch** – use flight-wide ⟨p2, p98⟩; `dst = (src-p2)/(p98-p2)` → uniform contrast across the roll.
* **Conditional CLAHE** – **C**ontrast-**L**imited **A**daptive **H**istogram **E**qualisation (`tile = 64×64, clip = 2`). Run only if `std(luma) < 30` **after** the stretch (handles dull, low-contrast scans).
* **Optional unsharp display copy** – 1.2 px radius, 0.7 weight; store separately, never feed to ML.

#### 3 · Branch B – NIR false-colour (CIR) frames

*Objective: recover a *clean* vintage CIR palette – magenta vegetation, cyan water – by neutralising age-induced yellow/orange bias, **not** by faking natural RGB.*

1. **Channel alignment** – register **G→R** and **NIR→R** via phase correlation (max ± 4 px) to remove purple fringes.
2. **Black-point subtraction** – subtract each channel’s 1-percentile DN (scanner dark current).
3. **Grey-World gain balance** – per channel: `gain_c = mean(all) / mean(c)`; multiply & clip → a neutral grey baseline.
4. **Per-flight 3-band LUT** – map each channel’s cumulative histogram to that of the best-looking frame in the same flight; apply with `cv2.LUT` → consistent colour across the strip.
5. **Outputs**

   * `roll_CIR_master.tif` – 3-band, radiometrically honest, EPSG 3301.
   * `roll_CIR_display.jpg` – 80 % JPEG for the web UI (same colours, smaller size).

*(QA hint – quick NDVI on a pine stand: if healthy conifers are positive and water is near zero, colour correction is “good enough”.)*

#### 4 · Post-steps (both branches)

* **Tiny median filter** – 1 px window; replace any isolated 0 or 255 “salt-and-pepper” pixel with the neighbourhood median.
* **Update DB** – mark `processed = 1`, store `path_master`, `path_display`, timestamp.

#### Notes & constants

* All thresholds are percentile-based; we never assume the scan contains “pure” white or black patches.
* Vignette blur σ ≈ 120 px is tuned for 1920-px thumbnails; scale ∝ long edge.
* For the 0.1 % of severely under-exposed B/W frames, consider log-domain equalisation instead of linear.
* Future idea – auto-flag frames whose NDVI < 0 over evergreen forests (likely mis-aligned channels).

-----

#### Maa-amet fotoladu API endpoints

* GET <https://fotoladu.maaamet.ee/otsing_arhiiv.php?foto_nr=532&aasta=&kaardileht=&lennu_nr=&foto_tyyp=&allikas=&sailiku_nr=&w=611.4&h=739.2&start=0&lkcount=10> - this contains image URL list and basic metadata.
* GET <https://fotoladu.maaamet.ee/paring_closest_arhiiv.php?B=59&L=24&lahimad=&id=261295&leier=1963> - produces list of nearby georeferenced images.

I have no idea where metadata is downloaded from in Fotoladu.

Image endpoints:

* <https://fotoladu.maaamet.ee/data/archive/arhiiv/ka_ngr/1983_L964_O35_25/thumbs/1983-L964-426.jpg> (100x100 px)
* <https://fotoladu.maaamet.ee/data/archive/arhiiv/ka_ngr/1983_L964_O35_25/hd/1983-L964-426.jpg> (1920x1920 px)
* <https://fotoladu.maaamet.ee/data/archive/arhiiv/ka_ngr/1983_L964_O35_25/reduced/1983-L964-426.jpg> (512x512 px)
* ![pilt](https://fotoladu.maaamet.ee/data/archive/arhiiv/ka_ngr/1983_L964_O35_25/thumbs/1983-L964-426.jpg)

## License

[GPL or MIT](LICENSE) (will be subject to change.)

-----

*Happy mapping!*
