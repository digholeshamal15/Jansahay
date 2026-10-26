# What did we train, and on which data?

**The main service classifier is now trained on 1,331 messages: 1,241 external Hugging Face records plus the original 90 authored examples.** The fitted weights are included and used by the local app. HuffPost supplies only the methodological reference for assignment 2; it supplies no project data.

## Data preparation and split

Two pinned public Hugging Face CSVs were downloaded:

| Source | Upstream rows | Selected for JanSahay, before deduplication |
|---|---:|---:|
| hackermango/Public_Grievance_Dataset | 12,500 | 1,441 |
| JadeSamLee/civicdex, main CSV | 600 | 366 |
| **External total** | **13,100** | **1,807** |

Selection uses the publishers' existing category/subcategory labels, mapped to water, garbage, roads, lights and drainage. We exclude unrelated complaints rather than assign them guessed labels. Public Grievance's explicit routing-header sentences are removed. CivicDex contributes its English gloss field; its Tamil input is not relabelled as Hindi/Marathi.

There were **27 duplicate normalized messages**, leaving **1,780 external examples**. Underlying public-grievance issue cores are stripped of generic request/status boilerplate and location names for grouping. Similar cores (character similarity at least 0.85) are kept in the same complaint-pattern group. There are 459 external groups.

The external data was split by those groups, using a fixed seeded procedure that checks class coverage without consulting model scores. We then added the authored examples only to training. No validation/test records were passed to the supervised `.fit()` call. No automatic translations or duplicated copies were invented to increase the count.

| Partition | External | Authored | Total |
|---|---:|---:|---:|
| Train | 1,241 | 90 | 1,331 |
| Validation | 159 | 0 | 159 |
| Test | 380 | 0 | 380 |

Training sources: 1,017 Public Grievance + 224 CivicDex + 90 authored. Training languages: **1,271 English, 30 Hindi, 30 Marathi**. Both external evaluation partitions are English-only. The authored supplement is 6 examples per service per language.

The grievance source has little provenance documentation and visibly templated language. CivicDex's card describes prototype/synthetic data and says no real citizen data is included. These are not verified real citizen complaints. Grouping reduces simple template leakage but does not prove all semantic paraphrases are independent. We retained the publisher-declared MIT notices and exact revisions/checksums in `DATA_SOURCES.md` and `data/dataset_manifest.json`.

## Training the main model

1. Fit character 2–5-gram TF-IDF on training messages only, capped at 60,000 features.
2. Convert labelled complaints to those feature vectors.
3. Fit multiclass logistic regression with `C=8`, a fixed seed and up to 1,500 iterations.
4. Weight each language/category cell equally in total, so English's larger row count does not simply drown out the small Hindi/Marathi supplement. This changes weights, not the number of unique messages.
5. Evaluate on the group-separated validation and test partitions. Hyperparameters were fixed before observing the test results; no test-set tuning was performed.
6. Save the vectorizer and classifier together to `models/service_classifier.joblib`, with the training-data hash and library version in `models/service_metadata.json`.

The app checks the training hash and scikit-learn version before loading the bundled artifact. If they differ, it refits from `data/service_train.json`; it still never includes the held-out files. Saving a complaint does not update the model. Imported web pages update only the separate guidance index after restart.

## Measured results

| Measure | Validation: 159 English examples | Test: 380 English examples |
|---|---:|---:|
| Classifier accuracy, always chooses its top category | 93.1% | 97.1% |
| Classifier macro F1 | 0.941 | 0.972 |
| UI suggestion coverage after domain/score guards | 77.4% | 73.9% |
| Accuracy among UI suggestions | 98.4% | 98.2% |
| Accuracy counting manual-selection fallbacks as errors | 76.1% | 72.6% |

On the test set the UI suggested a category for 281 cases and requested manual selection for 99. The classifier's 97.1% score should not be presented as the user-facing pipeline's coverage or as Marathi/Hindi accuracy. See `reports/hf_evaluation.json` for per-class metrics, confusion matrices, errors and routing figures.

The separate `data/evaluation.json` has only 15 authored multilingual smoke messages (five per language). All were classified as intended in this run, but this is far too small and too close to the authored corpus to establish robust Marathi/Hindi performance. Native-language external data and a real usability/evaluation study are still needed.

## What else learns, and what uses rules?

| Component | Implementation and data |
|---|---|
| Main service routing | HF-trained TF-IDF + logistic regression described above; separate handwritten domain/abstention checks |
| Educational word vectors | PPMI + 24D SVD fitted on the original 90-message demo corpus |
| N-gram lab | Frequency models fitted separately on the 30 demo messages per language, with Laplace smoothing |
| Topic lab | Five-topic LDA fitted on the 90 demo messages |
| Related guidance | TF-IDF + LSA fitted on 15 grouped demo guides plus optional imported pages |
| Optional English POS/embedding classifier | A separate classifier using 30 authored English examples, word-vector means and POS counts; requires downloaded POS resources |
| Language hints | Existing langdetect profiles; not trained by us |
| English POS/statistical NER | Existing pretrained NLTK resources; not trained by us |
| Porter/WordNet | Algorithm and lexical resource; not a complaint-trained model |
| Hindi/Marathi place extraction | Authored place list and regex |
| Sentiment/emotion | Small authored lexicon and phrase rules; no sentiment classifier trained |
| Draft/interface language | Authored templates/translations; original issue text is preserved, with no free-text machine translation |
| Assignment 2 report | Language hints, tokenization and counts on civic messages; no model fitting |

The educational models remain small so their calculations can be inspected quickly. This upgrade trains the classifier used by the main complaint form; it does not claim every lab component uses thousands of rows or that any transformer/large language model was trained.

## Reproduce locally

After installing requirements, `python scripts/train_service.py` retrains using the included prepared data without internet. `python scripts/prepare_hf_data.py` first downloads the pinned source CSVs and rebuilds the split if you want to reproduce data preparation. It requires internet, fetches no private/gated data, and executes no dataset repository code.

For your viva: “Our service classifier was trained on 1,331 labelled examples, including 1,241 from two Hugging Face civic datasets. We used TF-IDF and logistic regression with group-separated English evaluation. The Hindi/Marathi data is still a small authored supplement. Other NLP tasks use lightweight lab models, pretrained resources, or transparent rules.”
