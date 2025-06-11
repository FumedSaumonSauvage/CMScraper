# CMScraper : computer vision based scraper for polls in FB groups

## Quick recap

Warning: this documentation has not been updated in a long time. May be incorrect or irrelevant now.

### What is it?
CMScraper is designed as a mean to automatically gather data from polls on FB groups. It is being developed to tackle the tedious task of collecting data by hand to analyze polls results as a non admin.

### What is it not?
- A general purpose scraper for FB or anything else
- A spam bot that can post in groups or perform any other action besides viewing specific aspects

### How does it work?
CMScraper works by viewing pages like an human: althoug FB has put considerable means into obfuscating the code of its pages to prevent scraping with a simple regex, its human interface is rearkably clear and readable. As such, it can be read by a robot using basic computer vision techniques and minimal training. The robot can then extract the semantic parts of the page, and navigate it simulating a classic mouse pointer.

## Get started

Install the required python packages: `pip install "numpy<2.0"  python-dotenv pytesseract opencv-python ultralytics`

You will need to also install tesseract ouside of pip (e.g. `brew install tesseract` on mac).

Then, create a `.env` from the template containing the following:
- `MODEL`: path to the detection model
- `INDICE_CONF`: confidence index to believe that a detection is actually true. Recommended around 0.7

## Design
CMScraper relies on YOLO for semantic segmentation of the interface it sees, and simple Python to handle the logic. The polls are stored in a JSON file, and specific names of people are put in a database to prevent multiplying persons in case of an OCR bug.
YOLOv8 has been trained on ~100 manually annotated frames: the training datasets are not shared for obvious privacy reasons, but the weights are given. After reading the frames and detecting the interessant parts, some tests are performed to verify the integrity of the detected poll to prevent a degradation of resulting data integrity.

### Class diagram

![Class diagram](assets_doc/contraintes_composition.png)