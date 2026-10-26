# JanSahay · जनसहाय

**Prepare a civic complaint, find its official channel, and keep your own follow-up record.**

JanSahay helps a person turn an everyday neighbourhood problem into a clear, editable complaint. It runs on their computer and supports **English, हिन्दी and मराठी**. Its purpose is preparation and local follow-up: the person submits the complaint through the authority's own website and records what happens next.

The existing five services are preserved: water supply, garbage collection, roads/footpaths, streetlights and drainage. **Other / Not sure** makes a general complaint without pretending the classifier knows the correct service. The original scikit-learn NLP models and Assignment Lab are retained.

There are no compulsory accounts, phone numbers, paid APIs or external AI calls. This remains a local Flask project, not a hosted ChatGPT/Sites website.

## 1. Technology stack

| Part | Choice | Why |
|---|---|---|
| UI | HTML, CSS, vanilla JavaScript | Responsive interface; no Node build step |
| Web backend | Python + Flask | Small codebase, easy to run and explain |
| Data storage | SQLite via Python's sqlite3 | Local drafts; no database server |
| Classification / TF-IDF / LSA / topics | scikit-learn | Inspectable classical NLP baselines |
| Tokens | Unicode-aware regex | Preserves Devanagari vowel marks |
| English linguistic tasks | NLTK | Porter stemmer, WordNet, POS, NER |
| Language hint | langdetect | Statistical hint; manual language selection takes priority |
| Web collection | Requests + BeautifulSoup | One manually requested public HTML page at a time |
| Photo validation | Pillow | Validate/re-encode local supporting photos |
| Embeddings | NumPy + PPMI + truncated SVD | Actual dense word-context vectors without a large model download |

You do not need React, MongoDB, Docker, a GPU, or a paid API for this scope.

## 2. Run in VS Code on Windows

Use **Python 3.11 or 3.12** and VS Code with Microsoft's Python extension. Download/extract the ZIP first; do not run from inside the ZIP viewer.

1. Open VS Code → **File → Open Folder** → choose the extracted **JanSahay** folder. You should see `app.py` and `requirements.txt` directly in the Explorer.
2. Open **Terminal → New Terminal**. Run these commands from that folder in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

If your installed version is 3.12, replace `py -3.11` with `py -3.12`. If the `py` launcher is unavailable but `python --version` shows 3.11/3.12, use `python -m venv .venv` for the first command.

3. Open **http://127.0.0.1:5000** in your browser.
4. In VS Code, use **Ctrl+Shift+P → Python: Select Interpreter** and select `.venv\Scripts\python.exe`. You can then use the supplied **JanSahay: local app** launch configuration from Run and Debug.
5. Stop the app with **Ctrl+C** in the terminal. Start it again with:

```powershell
.\.venv\Scripts\python.exe app.py
```

These commands call the virtual environment's Python directly, so PowerShell activation-policy changes are unnecessary. Package installation needs internet. The main complaint workflow runs offline after installation.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open http://127.0.0.1:5000. Use `.venv/bin/python` in place of the Windows executable in the examples below.

### If port 5000 is busy

PowerShell:

```powershell
$env:JANSAHAY_PORT="5001"
.\.venv\Scripts\python.exe app.py
```

Then open http://127.0.0.1:5001. On macOS/Linux run `JANSAHAY_PORT=5001 .venv/bin/python app.py`.

## 3. The three-step complaint workflow

Select **Report a problem** on the home page.

1. **Describe the issue:** type naturally in English, Hindi or Marathi. The five example buttons are optional starting points; replace their text with your own facts. Continue to get a category suggestion.
2. **Location and details:** confirm/change the suggested category, select PCMC, PMC, Maharashtra or Not sure, and enter the location. Optional fields include a landmark, issue duration, recurrence, one service-specific follow-up answer, other details and supporting photos. Uncertain classifications are labelled honestly; Other / Not sure stays available.
3. **Review and prepare:** read and edit the complaint. Only supplied facts are included. Copy it, download a UTF-8 text file, or save it to My complaints. The side panel identifies the selected official channel and explains the next steps.

**Save draft** also works before all details are complete. A final prepared complaint needs a location, but an unfinished saved draft does not.

Switching interface languages preserves the issue, location, optional answers, photos and edited complaint text. The interface and new complaint wrapper have authored translations. **The user's free text is not machine-translated**, and an existing edited complaint is not silently rewritten when changing the interface language. Re-prepare it explicitly if you want a new wrapper in the selected language.

### Official portal handoff

For a known municipality, **Save & open official portal** saves the local complaint, shows a notice, and offers a link opening the external website in a new tab. Copy/download the text first if needed, then paste and submit it on the authority's site. Photos can be downloaded from their thumbnails and attached there yourself.

**Opening the portal does not submit the complaint and does not change its local status to Submitted Externally.** JanSahay sends no complaint text or photos automatically, does not log in, and has no government submission or live-status integration. The external site may require its own registration.

The directory initially includes PCMC SARATHI, PMC CARE and Maharashtra Aaple Sarkar Grievances. URLs are supported by official government source pages, checked on 22 October 2026. PCMC and Maharashtra destination fetches timed out during verification; official-source fallback links are included. These are reviewed directory links, not a promise of constant availability or of the correct jurisdiction for every issue. See **AUTHORITY_SOURCES.md**.

### My Complaints

The dashboard supports search by complaint text, location or official reference, status filters, reading/editing, deletion, and JSON/CSV exports. Each record can have an acknowledgement number, optional submission date and follow-up note. Updates are retained in complaint history.

The five local statuses are **Draft**, **Ready to Submit**, **Submitted Externally**, **Follow-up in Progress** and **Resolved**. The last three are recorded by the user; none is a verified government status. There are no automatic reminders, SLA guarantees, authority status checks or live notifications.

JSON exports include details, notes/history and photo metadata. CSV is a flat record summary and protects spreadsheet cells from formula injection. Exports follow the current search/filter. Image bytes are not embedded in exports: download photos separately or back up the entire `instance/` folder.

### Photos and local data

Photos are optional: up to **three per complaint**, JPEG/PNG/WebP, **5 MB each**, at most **16 megapixels**. The server checks decoded image content, rejects unsupported files, re-encodes pixels to JPEG with fresh random filenames, and strips EXIF/GPS metadata. Uploaded photos are stored immediately on this computer, even before the complaint is saved; text/details are stored only on explicit Save. Unlinked photos left by a closed browser remain in `instance/photos/` and are not automatically purged. The interface can remove photos while that unfinished complaint is open.

Saved records/history live in `instance/drafts.sqlite3`; photos live in `instance/photos/`. Deleting a complaint removes its linked photos and history. Interface language is kept in this browser's local storage. These local records are not encrypted or protected by user accounts: other people using the same computer account may access them. The app binds to localhost and checks request origin/host; it is not configured for a public or shared network deployment.

No geolocation is requested. Location is entered manually. Fonts and scripts are bundled, including Noto Sans Devanagari under its included OFL license, so the main workflow has no CDN/font network dependency.

### Upgrade without losing existing drafts

1. Stop the old server with Ctrl+C.
2. Back up the old project's entire `instance/` folder.
3. Extract this version into a new folder. Copy the old `instance/` folder into its `JanSahay` folder **before** starting the new app.
4. Install the updated requirements (Pillow is the added image-validation dependency), then run `app.py`.

Migrations add columns/tables inside a transaction and preserve draft IDs, bodies, languages, locations, timestamps and existing statuses/references. Existing drafts default to Draft where no prior status exists. They remain readable/editable even if older versions did not retain the original issue separately. No table is dropped and no old draft is deleted by migration.

## 4. Numbered assignment demonstrations and optional English models

Open **Assignments** in the top navigation (the footer's Project lab also opens it). All **11 syllabus assignments** have a numbered card. Select one to see its JanSahay feature, purpose, existing implementation method, limitations and source files. Use **Use an example**, choose the analysis language, then **Run this assignment**. Only that assignment's evidence is shown as readable counts, tokens, tables or text. Raw JSON is available separately and can be copied.

| No. | Assignment | Visible feature / result |
|---|---|---|
| 1 | Web scraping | Offline pasted-HTML extraction; title, readable text and counts; terminal command for permitted live collection |
| 2 | Language/counts/tokenization | Language hint, words, sentences and tokens; actual bundled 1,331-message civic-corpus analysis |
| 3 | Stemming/WordNet | Original-word → stem/lemma tables; explicit missing-resource or English-only note |
| 4 | POS/embeddings/classification | POS tags, 24D vector sample/neighbours, English embedding classifier and separate public classifier |
| 5 | NER | Entity text, label and producing method; statistical-resource status |
| 6 | TF-IDF | Formula, weighted character-feature table and service ranking |
| 7 | N-gram models | Input N-grams, learned counts, contexts, vocabulary size and smoothed probabilities; choose 1/2/3 grams |
| 8 | Sequence probability | Conditional steps, probability product, log probability and perplexity |
| 9 | LSI/LDA | Same-language related guidance and five corpus topics |
| 10 | Sentiment/emotions/opinion mining | Lexical cues, tone, emotions and LDA topic × tone counts |
| 11 | Integrated mini project | The same public complaint-analysis response and draft; links to the real complaint workflow/tracker |

These demonstrations run locally and **never save or submit complaints**. Editing a demo does not alter an unfinished citizen complaint. Interface-language changes preserve demo input and its separately selected analysis language. Results describe the input used at Run time; rerun after changes. Corpus analysis reports declared and detected languages separately and does not retrain anything.

**Assignment 1 is labelled honestly:** the browser demo parses pasted HTML without fetching a page or running its scripts. Use the existing `scripts/scrape.py` command with a permitted public HTTPS page for live collection, and restart the app to index the saved guidance. Assignment 2 uses HuffPost only as a methods reference and uses JanSahay civic data.

The expandable **Full NLP inspector** retains all original combined outputs and the topic button. Technical algorithm names and some result fields stay in English for the viva; assignment cards and instructions support English, Hindi and Marathi.


Use the assignment-specific views for demonstrations, or open the Full NLP inspector for the original combined output.

For complete **English** WordNet, POS, statistical NER, and POS + embedding classification, download NLTK resources once:

```powershell
.\.venv\Scripts\python.exe scripts\download_nltk.py
```

Restart the application afterward. This downloads resources into the project's `nltk_data/` folder. The app never downloads models at startup. If downloads are blocked by a proxy, security policy or network restriction, the lab displays an unavailable message; the ordinary complaint workflow continues working. Use the downloader on a network permitted by your institution rather than changing security settings.

**Hindi/Marathi scope:** original-script tokenization, multilingual classification, lexical sentiment, entities from a small place list / regex, n-grams, and UI templates. English Porter stemming, WordNet, POS and English statistical NER are deliberately not applied to Devanagari text. The entity output labels which method produced each item.

## 5. Civic-message text analysis (assignment 2 adapted)

The HuffPost assignment is a **reference for the NLP methods**: language detection, word count, sentence count and tokenization. JanSahay applies these methods directly to its own multilingual civic messages. No HuffPost/news dataset, headline fields, or 2012–2018 date filter is required.

Analyze all 1,331 bundled service-training messages:

```powershell
.\.venv\Scripts\python.exe scripts\civic_assignment.py
```

This produces `civic_text_report.json`: message/word/sentence totals, detected-language distribution, separately recorded declared-language labels, service-category counts, and example token lists. A sample report is included. Language detection is an estimate, especially for short Hindi/Marathi messages; it does not simply copy the declared language.

You can also supply your own JSON array or JSONL civic corpus:

```powershell
.\.venv\Scripts\python.exe scripts\civic_assignment.py "C:\path\to\civic_messages.json" --output civic_text_report.json
```

Each record uses this format:

```json
{"text": "आमच्या भागात पाणी येत नाही.", "lang": "mr", "category": "water"}
```

`text` is required; `lang` and `category` are optional labels. Pass `data/training.json` explicitly to analyze only the original 90 authored demo messages. Use `--limit 20` to inspect a smaller subset. Project lab also displays counts, tokens and a language hint for a message entered interactively. This statistics script does not train a model.

## 6. Web scraping exercise (assignment 1)

Use a relevant public local-authority service page that you are allowed to collect. Supply its final HTTPS URL and the language of its content:

```powershell
.\.venv\Scripts\python.exe scripts\scrape.py "https://your-authority.example/service-page" --lang mr
```

Replace the example URL with a real page before running. The scraper checks `robots.txt`, accepts public HTTPS hosts, refuses redirects, applies time/size limits, extracts visible HTML text and saves source URL/time to `data/scraped.json`. It fetches only the specified page and robots file; it does not crawl a site. It does not run JavaScript, OCR PDFs, or bypass access restrictions. Some sites require a final redirected URL or do not allow this script.

Restart the app to add collected pages to the local LSA guidance search. Imported excerpts are shown with their source link. Review their relevance and accuracy yourself. The bundled guides are **authored demonstration content**, not scraped or verified government guidance.

## 7. Training, verification and evaluation

The main service classifier now ships with **trained weights** at `models/service_classifier.joblib`. It was trained on **1,331 messages**: **1,241 selected Hugging Face examples plus 90 authored examples**. It uses character TF-IDF and logistic regression, with sample weights balancing language/category cells.

Sources are [hackermango/Public_Grievance_Dataset](https://huggingface.co/datasets/hackermango/Public_Grievance_Dataset) (12,500 upstream rows) and [JadeSamLee/civicdex](https://huggingface.co/datasets/JadeSamLee/civicdex) (the 600-row main CSV). We selected only records matching the five services, removed 27 duplicate messages, and separated complaint-pattern groups across train, validation and test. **The whole 12,500-row dataset was not used for training.**

| Partition | External HF examples | Authored supplement | Total |
|---|---:|---:|---:|
| Training | 1,241 | 90 | 1,331 |
| Validation | 159 | 0 | 159 |
| Test | 380 | 0 | 380 |

The larger external data is **English-only**. Training includes 1,271 English, 30 Hindi and 30 Marathi messages. Hindi/Marathi remain a small authored baseline; this upgrade does not establish robust multilingual accuracy. The larger grievance source appears templated and has minimal provenance documentation; CivicDex describes itself as a prototype with synthetic examples. We do not describe these as verified real citizen submissions.

The fixed classifier achieved **0.972 macro F1 / 97.1% accuracy on 380 held-out English examples**. The user interface adds a domain-word guard and abstention thresholds: it suggested a category for **281/380 (73.9%)**, with **98.2% accuracy among those suggestions**; 99 required manual selection. Accuracy counting abstentions as errors was 72.6%. See `reports/hf_evaluation.json` for both sets of figures. These are in-domain prototype results, not real-world or Hindi/Marathi benchmark scores.

The main app loads the bundled classifier; if the training data/scikit-learn version changes or the model file is incomplete, it refits from the bundled training partition. It never trains on validation/test records. The separate educational embeddings, LDA, n-grams and optional English POS/embedding classifier still use the 90-message demo corpus for lightweight, inspectable lab calculations.

To retrain the main classifier offline from the included prepared training data:

```powershell
.\.venv\Scripts\python.exe scripts\train_service.py
```

To reproduce downloading and preparing the pinned Hugging Face sources (internet required), then train:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_hf_data.py
.\.venv\Scripts\python.exe scripts\train_service.py
```

The download script uses public CSV files without executing repository code. Source revisions, SHA-256 checksums, mappings, duplicate counts and split details are in `data/dataset_manifest.json` and `DATA_SOURCES.md`.


```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\evaluate.py
```

The automated tests cover the three language paths, original-text preservation, out-of-domain fallback, explicit draft storage/deletion, request validation, Unicode tokenization, a hand-checked n-gram probability, civic-message statistics and JSON/JSONL input handling, HTML extraction, sentiment and topics. Tests write drafts only to a temporary database.

`data/training.json` contains **90 authored examples**. `data/evaluation.json` contains **15 separate authored smoke examples**, five per language. They are intentionally small; passing these does not establish real-world accuracy. Before a college pilot, collect consenting users' examples, label them independently, split by original issue/author, and report per-language macro F1, confusion matrices, abstention rate and failures on unrelated/mixed messages. Keep the holdout set untouched while tuning. Use a separate set for evaluating any embedding classifier; the supplied evaluation script measures only the main routing baseline.

For a full explanation of learned models, pretrained resources and rules, see **TRAINING.md**. Saving a draft does not retrain any model.

The service model combines a small domain-word guard, character TF-IDF and logistic regression. It abstains on some unsupported/low-similarity messages. Its scores and abstention thresholds are heuristic, not calibrated certainty. It can still make mistakes. Sentiment/emotion is a small lexical baseline; it is not used to decide service priority.

## 8. Project layout

```text
JanSahay/
  app.py                    Flask routes, tracker APIs and validated photo uploads
  workflow.py               Additive migrations, details and authority directory
  product_copy.py           Guided interface translations
  nlp.py                    NLP lab, pipeline and probability calculations
  service_model.py          Main HF-trained service classifier
  i18n.py                   Three-language UI and complaint templates
  requirements.txt
  README.md
  ASSIGNMENTS.md            Exact mapping and viva explanations
  VERIFICATION.md           What was and was not tested here
  TRAINING.md               Which parts learn, use pretrained resources, or use rules
  civic_text_report.json    Sample statistics for the 1,331 civic messages
  DATA_SOURCES.md           External data provenance, mappings and notices
  models/service_classifier.joblib
  models/service_metadata.json
  reports/hf_evaluation.json
  templates/index.html
  static/app.js
  static/assignments.js     Numbered assignment demos and readable results
  assignment_lab.py        Syllabus mapping and existing-algorithm adapters
  static/style.css
  data/training.json
  data/service_train.json
  data/service_validation.json
  data/service_test.json
  data/dataset_manifest.json
  data/evaluation.json
  data/build_seed.py        Rebuild authored examples
  scripts/download_nltk.py
  scripts/civic_assignment.py
  scripts/scrape.py
  scripts/evaluate.py
  scripts/prepare_hf_data.py
  scripts/train_service.py
  tests/test_project.py     Original 14 tests preserved
  tests/test_workflow.py    Workflow, migration, upload, tracker and export tests
  tests/test_assignments.py Seven assignment mapping/evidence regression tests
  tests/browser_assignments.cjs Optional actual-browser assignment QA
  data/authorities.json
  AUTHORITY_SOURCES.md
  UPGRADE_REPORT.md
  static/fonts/            Bundled Devanagari font and OFL license
  .vscode/launch.json
```

Created at runtime: `instance/drafts.sqlite3`, optional `nltk_data/`, optional `data/scraped.json`. Saved drafts are plain text in the local SQLite database, shared by anyone using this app on the same computer account. Delete drafts through the interface; removing the database file also removes them all. No telemetry, remote AI calls, external fonts, or CDN scripts are used. Scraping/downloading resources happens only through the explicit scripts.

## 9. Demonstration guide

1. Run `app.py`, open localhost, and choose Report a problem.
2. Write an English streetlight complaint, select PCMC, add a location, duration and the number of affected lights.
3. Switch to Marathi and back; show that the entered data remains intact. Optionally upload a small valid photo, then try an SVG or renamed non-image and show rejection.
4. Prepare the final complaint, edit a sentence, copy it, download it and save it.
5. Select Save & open official portal. Show the departure notice; opening the link must not mark the complaint submitted. You need not actually submit a test complaint to an authority.
6. In My complaints, record a reference and submission date, change to Submitted Externally, then add a follow-up note. Show the history.
7. Search the reference, export the filtered JSON, and delete a disposable test record.
8. Try Hindi and Marathi messages and all five categories. Try an unrelated message and show the Other / Not sure path.
9. Open Assignments in the top navigation. Select the numbered cards to show each feature separately. Run 1 with sample HTML, 2 with your text and the civic corpus, 6 for weighted features, 7/8 for counts/probabilities, 9/10 for topics/opinions and 11 for the real complaint pipeline. English pretrained POS/WordNet/NER in 3/4/5 still require the optional download described above.
10. Run `python -m unittest discover -s tests -v`. Read **VERIFICATION.md** and **UPGRADE_REPORT.md** for actual checks and limits.

Optional browser QA (Node is only needed for these checks, not for JanSahay):

```bash
npm install --no-save playwright@1.51.1 @axe-core/playwright
npx playwright install chromium
node tests/browser_assignments.cjs
```

Use `JANSAHAY_PYTHON` to select the virtual-environment interpreter if `python` does not resolve to it. The browser test starts its own local server on port 5024 and uses temporary complaint data. It checks all 11 demos, real corpus statistics, Unicode/language retention, JSON copy, full inspector, keyboard selection and desktop/mobile accessibility scans.

Core work takes priority here. Voice typing, trend charts, GPS, automatic reminders, government API integration and machine translation are not implemented.

## References

- [Flask installation and virtual environments](https://flask.palletsprojects.com/en/stable/installation/)
- [Microsoft: Flask in VS Code](https://code.visualstudio.com/docs/python/tutorial-flask)
- [NLTK model/data installation](https://www.nltk.org/data.html)
- [NLTK WordNet](https://www.nltk.org/howto/wordnet.html)
- [scikit-learn decomposition: SVD, LSA and LDA](https://scikit-learn.org/stable/modules/decomposition.html)
