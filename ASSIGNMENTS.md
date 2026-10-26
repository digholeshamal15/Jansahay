# Assignment coverage and viva guide

This adapts the **11 assignments in your uploaded image** into the JanSahay project. For assignment 2, the HuffPost exercise is a methodological reference only: apply its language detection, word/sentence counting and tokenization to JanSahay civic messages. No news dataset is required. Live scraping needs a permitted public page. English POS/WordNet/statistical NER require the optional model download.

| No. | Assignment | Implementation / demonstration | Contribution to the project |
|---|---|---|---|
| 1 | Scrape the web | `scripts/scrape.py`; source URL + timestamp; robots.txt; BeautifulSoup | Import selected public service information into guidance search |
| 2 | Language detection, counts and tokenization; news exercise used as a reference | `scripts/civic_assignment.py`; JanSahay civic messages in JSON/JSONL; 1,331 bundled service-training records (including 90 authored examples) | Analyze English, Hindi and Marathi complaints with the same NLP operations |
| 3 | English stemming and WordNet lemmatization | `nlp.py: english_analysis`; Porter and POS-aware WordNet | Demonstrates normalization on English text in the lab |
| 4 | POS + word embeddings + classification | `english_analysis`, `Engine.embedding_classifier`; POS-ratio features + averaged PPMI-SVD embeddings → logistic regression | English lab classifier; separate HF-trained multilingual TF-IDF classifier powers the public form |
| 5 | Named entity recognition | `entities`; NLTK English statistical NER after download; gazetteer and regex labelled separately | Shows possible locations, dates, postal codes; user-entered location remains authoritative |
| 6 | TF-IDF | `service_model.fit_service`, `Engine.guide_vector`; top query feature weights in lab | Character n-gram features for routing and guidance indexing |
| 7 | N-gram models | `NGramModel`; unigram, bigram, trigram selectable in lab | Local language-model experiment using same-language demo texts |
| 8 | Probability of a word sequence | `NGramModel.score`; per-step probability, total probability, log probability, perplexity | Step-by-step numerical evidence for the language model |
| 9 | LSI or LDA | Both: TF-IDF → truncated SVD for guide retrieval; count vectors → LDA for topics | Related guidance and exploratory corpus themes |
| 10 | Sentiment, emotions, opinion mining + topics | `sentiment`, `Engine.topics`; lexical polarity/cues, emotion cues, tone counts by LDA topic | Illustrative analysis of feedback themes; no automatic urgency decision |
| 11 | End-to-end NLP mini project | `app.py`, `nlp.py`, local UI and SQLite | A person can prepare and retain a multilingual civic complaint |

## Visible assignment mapping in the application

Choose **Assignments** from the top navigation. The page displays all 11 numbered cards, each with the exact related JanSahay feature. Selecting a card opens its purpose, algorithm, scope, source files, runnable input and assignment-specific result. The main citizen workflow remains separate.

| Card | What to run / explain in the visible result |
|---|---|
| 01 | Use example HTML → extract readable text. Explain that this is offline parsing; the shown `scripts/scrape.py` command does actual permitted web collection. |
| 02 | Analyze a civic message → language, word/sentence counts and tokens. Use Analyze bundled civic corpus for the actual 1,331-row corpus. HuffPost is only a methods reference. |
| 03 | Use the English example → word/stem table and WordNet lemmas when installed. Missing resources and Indic exclusions are explicit. |
| 04 | Use English → POS tags, dense SVD vector/neighbours, separate English embedding classifier and HF-trained public classifier. Do not call TF-IDF an embedding. |
| 05 | Use the example → places/date/PIN entities with each extraction method labelled. English statistical NER needs optional resources. |
| 06 | Run → normalized TF-IDF weights and class ranking. These are character features from the same public routing model. |
| 07 | Select unigram/bigram/trigram → input N-grams and counts learned from 30 same-language demo messages. |
| 08 | Run → per-word conditional probability, product, log probability and perplexity, including EOS/UNK handling. |
| 09 | Run → LSA related guidance and LDA corpus themes, with authored/source attribution. |
| 10 | Use the sentiment example → lexical evidence, emotion cues and topic-wise tone counts. This remains a limited rule baseline. |
| 11 | Run → exactly the public analysis pipeline's draft/classification response, without saving. Open the citizen workflow to explicitly edit/save/track. |

Readable result tables are primary; expandable raw JSON remains available with Copy result JSON. Full NLP inspector retains the previous combined inspector and topic output. Assignment demos make no network requests or database writes. Interface changes preserve the current example and analysis-language selection. Optional English models are never fabricated when missing.

## Main flow

1. Select Report a problem and describe the issue. In step 2 confirm the service, select a municipality and add the location and optional facts; step 3 prepares the editable complaint. Interface language changes preserve the entered data.
2. Unicode-normalize for analysis and tokenize without dropping Devanagari marks. Preserve the user's original text for the draft.
3. Estimate a language hint. The user's selected language takes precedence.
4. Check a small domain-word list and classify using the bundled TF-IDF + logistic regression model trained on 1,331 messages (1,241 external HF records plus 90 authored messages).
5. Retrieve same-language guidance with TF-IDF → SVD → cosine similarity.
6. Fill an authored complaint template; show checklist; allow editing.
7. Copy/download locally or explicitly save to SQLite. Use the reviewed external portal link to submit yourself, then maintain the local status/reference/date/follow-up history. A portal handoff is not a submission.
8. Inspect the numbered Assignments page for assignment-specific evidence.

POS, sentiment, entities and n-gram probability are educational outputs. They are not used to infer whether a person is truthful, to promise a department, or to prioritize a complaint.

## Formula notes

### TF-IDF

For a term/feature t in document d, the scikit-learn defaults used here apply smoothed IDF:

`idf(t) = ln((1 + N) / (1 + df(t))) + 1`

The main classifier uses sublinear term frequency:

`tf(t,d) = 1 + ln(count(t,d))` for a nonzero count.

`weight(t,d) = tf(t,d) × idf(t)`, followed by L2 normalization.

Main classifier features are **character** 2–5-grams. They are TF-IDF features, not word embeddings. Character features help with some spelling and inflection variation in the three scripts, but are not a general translation model.

### Dense word embeddings

Build a word–context co-occurrence matrix using a window of two words. Convert counts to positive pointwise mutual information:

`PPMI(w,c) = max(0, ln(P(w,c) / (P(w) × P(c))))`

Truncated SVD factorizes the matrix approximately:

`X ≈ U_k Σ_k V_kᵀ`

The rows of `U_k Σ_k` are 24-dimensional dense word vectors. The lab displays sample coordinates and cosine neighbours. These are **distributional SVD embeddings**, not Word2Vec/CBOW or neural embeddings. Vectors are learned from the small authored corpus; nearby words need not be meaningful and the vectors are not cross-lingually aligned.

For the English embedding classifier, average known-token vectors and concatenate four normalized POS counts: nouns, verbs, adjectives and adverbs. Train logistic regression on those features. Unknown words contribute no vector. English POS models must be installed before this classifier can run.

### LSA / LSI retrieval

Guides are represented by a document–character-feature TF-IDF matrix. Truncated SVD creates dense document coordinates. A query is transformed by the same fitted vectorizer and SVD. Rank same-language guides using:

`cos(q,d) = (q · d) / (||q|| × ||d||)`

This is a small LSA baseline, not retrieval-augmented generation. The app displays authored/source excerpts and never invents answers from a remote language model.

### N-gram sequence probability

For bigrams:

`P(w₁ … w_m, EOS) ≈ P(w₁ | BOS) × P(w₂ | w₁) × … × P(EOS | w_m)`

With Laplace smoothing:

`P(w | h) = (count(h,w) + α) / (count(h) + α × |V|)`

The code uses `α = 1`. Vocabulary contains observed words, `<UNK>` and `</s>`, but not `<s>`. Unknown query words map to `<UNK>`. An unseen context has a uniform smoothed distribution. Sentence boundary padding is `n−1` copies of `<s>`, and end-of-sentence is always scored.

Hand-check example: training texts are `a b` and `a c`. Vocabulary is `{a,b,c,<UNK>,</s>}`, so `|V| = 5`.

- `P(a | <s>) = (2+1)/(2+5) = 3/7`
- `P(b | a) = (1+1)/(2+5) = 2/7`
- `P(</s> | b) = (1+1)/(1+5) = 1/3`
- `P(a b </s>) = (3/7) × (2/7) × (1/3) = 2/49 ≈ 0.0408163`

Use log probability for long sequences:

`log P = Σ log P(wᵢ | hᵢ)`

`perplexity = exp(−log P / number_of_scored_tokens)`

Scored tokens include EOS. An extremely small displayed ordinary probability may underflow to zero, while log probability remains usable. Models are separate per selected language. Do not compare sentence quality across languages based on these tiny corpora.

### LDA and opinion mining

LDA receives a word-count matrix, **not TF-IDF**. Five topics are a demonstration hyperparameter. Topics are weighted word lists; they are not supervised service labels. A document is assigned to its highest-probability topic solely to show counts of lexical tone labels by topic.

The multilingual lexicon reports positive/negative cues, mixed/neutral tone, and limited frustration/anger/relief cues. It does not understand general negation, sarcasm or nuanced emotion. It is a baseline suitable for comparison with a later trained model, not evidence of emotional state.

## What to show during a demo

1. Run `python app.py` in your environment and open localhost.
2. Try an English streetlight message, Hindi garbage message and Marathi water message.
3. Review the category; change it manually if needed; edit and download a complaint.
4. Save, reload the saved-drafts tab, delete the saved draft.
5. In the lab, select English and inspect stems, POS, WordNet lemmas, entities, word vectors and the embedding-based classification after installing the resources.
6. Choose bigram/trigram and explain conditional probabilities and smoothing.
7. Show LDA topics and lexical-tone counts; explain language/topic confounding.
8. Run `scripts/civic_assignment.py` and show counts, language hints and tokens for JanSahay civic messages. Explain that the news assignment supplied the methods rather than the dataset.
9. Run scraping against a permitted real page and show the stored attribution and guidance result after restart.
10. Show `reports/hf_evaluation.json` for the 380-example held-out English test and UI abstention figures. Run the automated tests and the separate 15-example multilingual smoke script. Discuss the synthetic/templated sources and limited Hindi/Marathi data honestly.

## Evaluation that is still needed

The original 15-example multilingual evaluation is only a smoke test. The upgraded main classifier also has group-separated external English validation/test partitions; its classifier and UI-routing metrics are saved separately. These do not establish Hindi/Marathi or real citizen performance. For a defensible mini-project result, collect a larger, independently labelled set containing all languages, all services, unrelated queries, ambiguous messages and code-mixed examples. Use service macro F1 by language, confusion matrices, abstention coverage/error, entity precision/recall and a small usability study. Evaluate the separate embedding classifier against a TF-IDF baseline without training on the holdout examples.

The redesigned public workflow keeps technical NLP outputs in **Assignments**, accessed from the top navigation or the footer’s Project lab. Language hints, sentiment, TF-IDF, word vectors, n-gram probabilities, entities, POS/normalization, LDA topics and related-guidance retrieval remain available there. The main trained service classifier still predicts only the five original labels; Other / Not sure is a user-confirmed general fallback, not a sixth trained class.
