# Latest verification — numbered assignment mapping

Checked **25 October 2026** using Python 3.12 and Chromium 134 / Playwright 1.51.1. Python 3.11 instructions remain in README; that runtime was not executed here.

- **33 backend tests passed:** all previous 26 tests plus seven assignment tests. Tests check all eleven catalog entries and specific result structures, Unicode civic text, truthful English-only handling, offline HTML extraction without network calls, the real pipeline without saves, N-gram order and invalid requests.
- Actual browser checks ran every assignment and rendered its relevant evidence. The actual 1,331-message corpus summary ran in the browser. Hindi/Marathi interface changes preserved demo input and the separately chosen analysis language. JSON result copy, original full inspector/topics, keyboard selection, unfinished citizen-complaint retention and no demo database writes passed.
- Automated axe A/AA scans passed on the assignment desktop and Marathi 390px mobile views; no page overflow was found. Rendered layouts were inspected. This is not full accessibility certification.
- The full citizen browser workflow was rerun successfully as well: multilingual complaints, photos, copy/download, portal safety, tracker updates, search/export/delete and mobile layout.
- Captured current logs: `reports/backend_tests.txt`, `reports/browser_assignments.txt`. The browser test ships at `tests/browser_assignments.cjs` with optional setup in README.
- Python compilation and JavaScript syntax checks passed. The optional NLTK downloader was attempted again and blocked by its configured-proxy security check; no bypass was enabled. The UI displays the resource requirement.

The earlier upgrade verification below records the original workflow scope and unchanged model limits. Its 26-test count is historical; the current count is 33.

---

# Verification — JanSahay upgrade

Checked on **22 October 2026**, using Python **3.12** and actual Chromium **134** through Playwright **1.51.1**. Python 3.11 installation instructions are supplied, but a Python 3.11 runtime was not available for this verification.

## Automated backend checks

Command, from the project folder:

```bash
python -m unittest discover -s tests -v
```

**26 tests passed**: all 14 existing tests were retained and 12 new workflow tests were added. The captured run is in `reports/backend_tests.txt`.

| Requirement | Evidence actually checked |
|---|---|
| English, Hindi and Marathi | Original text/category regression tests plus every manual category in every language; browser generation/edit/save flows in all three languages |
| Five existing categories | Water, garbage, roads, lights and drainage retained; manual Other option also checked |
| Uncertain classification | Unknown-message fallback in backend and actual browser; no sixth trained class invented |
| Existing drafts | Six-column legacy SQLite fixture migrated twice; original ID, Marathi body and other data retained with safe defaults |
| Official handoff | URL returned and local history recorded; body, status, reference and submission date remained unchanged; unknown municipality rejected |
| Follow-up | Reference/date/status/notes saved, retrieved and recorded in history |
| Search/export/delete | Unicode search, filtered JSON with history, CSV formula escaping, record deletion and linked photo/history cleanup |
| Upload security | Valid photo re-encoded with safe filename and stripped metadata; fake PNG, SVG, renamed GIF, oversize files, excess photos and cross-record reuse rejected |
| Assignment Lab | Existing NLP tests retained; actual browser opened the Lab and received output; optional pretrained-resource limitations below |
| Local security | Invalid input and unrelated-origin mutations rejected |
| Model resilience | Damaged artifact fallback fits the same bundled service training data; valid regenerated artifact loaded directly |

A non-failing Python ResourceWarning about an unclosed temporary file occurred in the captured backend run; the run completed successfully. Python compilation and JavaScript syntax checks also passed.

## Actual browser checks

The captured output is in `reports/browser_tests.txt`. A temporary SQLite database and photo directory were used; no government form was submitted.

- Keyboard-only skip link, Report a problem, issue entry and Continue worked.
- English complaint preparation retained optional facts; Copy wrote the actual clipboard; Download produced a text file containing the complaint.
- Hindi and Marathi flows generated a complaint, rejected SVG, accepted a valid photo, retained inputs across language changes, and saved edited text.
- Portal notice contained the reviewed PCMC URL; opening the handoff notice left the complaint Ready to Submit.
- Dashboard updates stored a user-recorded Submitted Externally status, reference and date. Search, filtered JSON download and deletion worked.
- Other / Not sure worked in the browser. The Lab displayed output.
- Desktop and 390-pixel mobile layouts were visually inspected. No horizontal overflow occurred in the checked mobile views. Bundled Devanagari font glyph coverage was checked.
- Automated axe checks reported no violations under the selected WCAG A/AA rule tags on home, review, tracker and Marathi mobile views. This is not a complete accessibility audit or certification.

## Model and assignment scope

The main character TF-IDF + logistic-regression classifier still uses **1,331 training messages**: 1,241 selected Hugging Face examples and 90 authored messages. Its stored artifact was regenerated with the existing training script/data after detecting a truncated file; the algorithm, training split and hyperparameters were preserved. Direct artifact loading succeeded.

The prepared validation set has 159 external English examples and the test set has 380. Recorded test macro F1 is 0.972, accuracy 97.1%; UI suggestion coverage is 73.9%, with 98.2% accuracy among accepted suggestions. These are in-domain English prototype results from synthetic/templated sources, not evidence of real-world Hindi/Marathi accuracy. Details remain in `reports/hf_evaluation.json`, `TRAINING.md` and `DATA_SOURCES.md`.

Assignment 2 applies language detection, word/sentence counts and tokenization to JanSahay civic messages. HuffPost remains a methods reference, not the project's dataset. Existing Unicode, n-gram hand-calculation, TF-IDF, embeddings, sentiment, topic and split-integrity tests still pass.

## External dependencies and limits

- Official PCMC, PMC and Maharashtra source pages were reviewed; see `AUTHORITY_SOURCES.md`. PCMC and state destination fetches timed out. Source endorsement is verified; continuous portal availability, login and submission are not.
- There is no authorised government integration. Submission and government-status verification are manual; all tracker statuses are local and user-recorded.
- Optional NLTK pretrained resources could not be downloaded in this environment because of proxy restrictions. Their unavailable-resource path works. English WordNet, pretrained POS/statistical NER and POS + embedding classification require `python scripts/download_nltk.py` and were not end-to-end verified with those resources here. Hindi/Marathi are not falsely processed with English POS/WordNet models.
- Live scraping was not exercised; visible HTML extraction was tested with a fixture. Review robots rules and site availability for any demonstration URL.
- User free text is not automatically translated. Native-language training examples remain limited (30 Hindi and 30 Marathi in the authored supplement).
- Photos are optional and stored immediately. Abandoned unlinked photos are not automatically purged. JSON/CSV exports contain photo metadata, not image bytes; back up `instance/` to retain everything.
- No GPS, voice typing, trend charts, automatic reminders or live government tracking were added.

## Reproducibility

The backend tests ship in `tests/` and use temporary data. Browser checks were executed as an external Playwright QA harness; Node/Playwright are not required to run JanSahay. Tested Python package versions are recorded in `tested-versions.txt`. Install bounded requirements in a clean virtual environment and rerun the tests on the demonstration computer.
