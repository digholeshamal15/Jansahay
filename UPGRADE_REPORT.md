# Numbered assignment mapping update — 25 October 2026

The existing Project lab now has a prominent **Assignments** navigation entry and eleven numbered cards. Every card names its exact JanSahay feature, purpose, method, limitations and source files, and runs an assignment-specific demonstration with readable results. English, Hindi and Marathi instructions are authored; technical method/result names may remain English.

New files: `assignment_lab.py`, `static/assignments.js`, `tests/test_assignments.py`, `tests/browser_assignments.cjs`, `reports/browser_assignments.txt`.
Updated files: `app.py`, `product_copy.py`, `templates/index.html`, `static/app.js`, `static/style.css`, `README.md`, `ASSIGNMENTS.md`, `VERIFICATION.md`, this report and captured backend/browser logs.

The existing `/api/lab` and `/api/topics` routes and combined inspector remain available. New `/api/assignments` and numbered run endpoints adapt the same NLP functions; no algorithms or training data were replaced. The public analysis function was factored into `analyze_data` so Assignment 11 returns the exact real analysis response without database writes. **No database migration or schema change was needed in this update.**

Assignment 1 clearly separates offline pasted-HTML extraction from the existing terminal-based live scraper. Assignment 2 uses civic text and the actual bundled 1,331-message corpus, with HuffPost only a methodological reference. Assignment 7 displays both input N-grams and learned counts; 8 displays probability steps separately. LSI/LDA guidance, sentiment/topic opinions, entities, normalization, vectors and classification have separate evidence views. Raw JSON copy and all previous NLP outputs remain available.

**Verified: 33 backend tests passed** (previous 26 retained + 7 new). Actual browser checks passed across all 11 demos, real corpus analysis, multilingual input retention, inspector, copied JSON, keyboard selection and assignment desktop/mobile axe scans. See VERIFICATION.md and logs for exact scope. Optional English pretrained-resource installation remains blocked in this environment; missing models are explicitly marked. Native-language statistical NER/POS, live scraping from the browser, live government tracking and new model training were not added.

The previous upgrade report follows for the preserved complaint workflow, database changes and earlier implementation details.

---

# JanSahay upgrade report

## Result and purpose

JanSahay remains a local Flask application. A citizen can describe a civic problem, prepare an editable complaint, find the reviewed official channel, submit there manually, and maintain a local follow-up record. The existing trained classifier, five services, multilingual text handling and NLP Assignment Lab are preserved.

## Implemented

- A mobile-friendly home page with Report a problem, a three-step guided workflow, My complaints and a separate Project lab.
- English, Hindi and Marathi interface copy; language changes preserve entered text, selected details, photos and edited complaints.
- Honest NLP suggestions, manual confirmation/override and Other / Not sure. Optional category-specific answers, landmarks, duration, recurring issues and supporting facts.
- Editable complaints containing supplied facts; explicit Save Draft, actual clipboard Copy and UTF-8 text Download.
- A source-supported PCMC/PMC/Maharashtra authority directory and external-site notice. The handoff saves locally and records an event without claiming submission or changing status to Submitted Externally.
- SQLite search/filter/edit/delete, JSON/CSV exports, acknowledgement numbers, submission dates, notes and chronological history. Five local statuses are clearly labelled as user-recorded.
- Optional validated photos: JPEG/PNG/WebP, 5 MB and 16 MP limits, maximum three per complaint, random filenames, decoded-content checks, EXIF/GPS stripping and deletion cleanup.
- Large touch targets, keyboard focus and skip navigation, accessible labels, improved contrast, reduced-motion rules and a bundled Devanagari font.

## Files changed or added

| Files | Change |
|---|---|
| `app.py` | Existing Flask app extended with safe tracker CRUD/history, handoff, exports, upload validation and local request guards; existing NLP routes retained |
| `workflow.py` (new) | Additive migration, statuses, directory, category questions and detail validation |
| `product_copy.py` (new) | Authored English/Hindi/Marathi product copy and examples |
| `templates/index.html`, `static/app.js`, `static/style.css` | Public three-step workflow, home/dashboard/Lab, state retention and responsive accessible design |
| `static/fonts/NotoSansDevanagari.ttf`, `static/fonts/OFL.txt` (new) | Local Devanagari font and licence |
| `data/authorities.json`, `AUTHORITY_SOURCES.md` (new) | Reviewed directory, official evidence, dates and availability caveats |
| `service_model.py` | Load compatible stored weights; recover from damaged/incompatible artifacts using the same bundled training rows |
| `models/service_classifier.joblib`, `models/service_metadata.json`, `reports/hf_evaluation.json` | Regenerated with the existing script/data after a truncated artifact was detected; original model design and recorded metrics retained |
| `requirements.txt`, `tested-versions.txt` | Pillow dependency and actual verification environment versions |
| `tests/test_workflow.py` (new) | Twelve new regression tests; all original fourteen tests in `tests/test_project.py` retained |
| `README.md`, `ASSIGNMENTS.md`, `VERIFICATION.md` | Installation/upgrade/demo instructions, preserved assignment mapping, evidence and limitations |
| `UPGRADE_REPORT.md`, `reports/backend_tests.txt`, `reports/browser_tests.txt` (new) | Delivery report and captured actual test runs |

Existing `nlp.py`, `i18n.py`, training datasets, preparation/training scripts and the core NLP algorithms remain in the project. The main model still trains on 1,331 examples, including 1,241 selected Hugging Face records; this UI upgrade does not claim a new larger training corpus.

## Database changes and preservation

Migration runs inside a SQLite transaction with foreign keys enabled. It adds `status`, `reference`, `issue`, `municipality`, `details_json`, `submitted_on` and `updated` only when absent. It adds `history` and `photos` tables linked to drafts, and sets schema version 3. Original IDs, category, language, location, body and creation timestamps are preserved. No existing draft table is dropped. History and linked photos are removed only when the user explicitly deletes the complaint.

The migration test uses an actual legacy six-column database with an existing Marathi draft and runs migration twice. It verifies the old record and ID survive. Your personal database is not included in this distribution. Stop the old app, back up `instance/`, copy it into the extracted new project, then start the app as documented in README.

## Validation actually executed

**26/26 backend tests passed** (14 existing + 12 new), plus Python compilation, JavaScript syntax checking and direct trained-artifact loading. Actual Chromium checks passed for English, Hindi and Marathi, clipboard/text/JSON downloads, optional photos, language retention, local tracking, handoff safety, search/delete, Lab output and 390-pixel layout. Four views had no automated axe A/AA violations; keyboard navigation and rendered layouts were also inspected. See `VERIFICATION.md` and captured logs for exact scope and the non-failing ResourceWarning in the backend run.

## Incomplete or deliberately limited

There is no government API, automatic submission or verified real-time status. Official source pages support directory links, but PCMC/state destination fetches timed out. Users must submit and record references manually. No voice/GPS/trends/reminders were added. Optional pretrained NLTK resources were unavailable for full end-to-end English POS/NER/WordNet checks and need the documented one-time download. Free text is not machine-translated; Hindi/Marathi model accuracy needs better native-language data and evaluation. Automatic cleanup of abandoned, unlinked photo uploads is not implemented. Exports omit image bytes. Python 3.12 was actually tested; Python 3.11 setup is documented but not executed in this environment.
