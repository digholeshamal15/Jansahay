# JanSahay · EchoTrace AI
### Integrated Public Natural Language Processing (NLP) Intelligence Platform
**Civic Grievances, Incident Reports, Public Opinion & Risk Discovery Engine**

---

## 1. Project Context & Executive Overview

**JanSahay · EchoTrace AI** is an end-to-end Natural Language Processing (NLP) intelligence platform designed for third-year B.Tech CSE (AI & ML) academic evaluation, practical viva examination, and portfolio demonstration. 

Rather than presenting an isolated collection of homework exercises, the platform demonstrates **how all 11 core syllabus NLP techniques (Modules A through J) work together inside a real-world civic intelligence and risk discovery architecture**.

The platform bridges two interconnected systems:
1. **JanSahay (Citizen Complaint Assistant & Local Follow-up Tracker):** An accessible, multilingual interface helping citizens draft formal, structured civic grievances (in English, हिन्दी, and मराठी), route them to verified municipal portals (PMC, PCMC, Aaple Sarkar), and maintain follow-up logs with local SQLite persistence.
2. **EchoTrace AI (Hidden Narrative & Operational Risk Discovery Engine):** A corpus-level intelligence engine that ingests citizen complaints, news articles, disaster reports, and public statements to uncover latent thematic links, geographic hotspots, public sentiment/emotional polarization, candidate contradictory claims across independent sources, and inferred operational hazards (e.g., contaminated water supply, road gridlock delaying ambulances, electrical fire hazards).

---

## 2. System Architecture & Integrated Pipeline

```
+---------------------------------------------------------------------------------------------------+
|                                 DATA INGESTION & ACQUISITION (Module A)                           |
|   • Web Scraper (Requests + BeautifulSoup + robots.txt)   • CSV & TXT Batch Upload Parser         |
|   • Curated Repositories (1,331 Civic Records + HuffPost News Category Sample)                    |
|   • Exact (SHA-256) & Near-Duplicate (Token Jaccard Similarity) Detection Guard                   |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                               PREPROCESSING & TOKENIZATION (Module B)                             |
|   • Unicode NFC Normalization (Preserving Devanagari Matras & Combining Marks)                    |
|   • Multilingual Word & Sentence Tokenization   • Language Detection (Statistical + Hint)         |
|   • Corpus-Aware Stop Words Removal (English, Hindi, Marathi)   • Text Statistics (TTR, Len, Lex) |
+---------------------------------------------------------------------------------------------------+
                                                  │
                        ┌─────────────────────────┴─────────────────────────┐
                        ▼                                                   ▼
+---------------------------------------------------+   +-------------------------------------------+
|      LINGUISTIC MORPHOLOGY (Module C & D)         |   |    NAMED ENTITY RECOGNITION (Module E)    |
| • Porter Stemmer & Snowball Stemmer (Heuristic)   |   | • NLTK Statistical MaxEnt Chunking        |
| • WordNet Lemmatizer (POS-Aware Dictionary Lookup)|   | • Civic Gazetteer (Indian Cities, PMC)    |
| • Penn Treebank & Simplified POS Tagging          |   | • Regular Expression Rule Recognizers     |
| • Morphological Comparison & Mismatch Explanation |   |   (PIN Codes, Dates, Times, Quantities)   |
+---------------------------------------------------+   +-------------------------------------------+
                        │                                                   │
                        └─────────────────────────┬─────────────────────────┘
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                        DISTRIBUTIONAL SEMANTICS & VECTOR EMBEDDINGS (Module D)                    |
|   • Dense 24-Dimensional Word Vectors via PPMI (Positive Pointwise Mutual Information) + SVD      |
|   • Cosine Distance Semantic Nearest Neighbors Matrix   • Document-Level Mean Dense Vectors       |
+---------------------------------------------------------------------------------------------------+
                                                  │
                        ┌─────────────────────────┴─────────────────────────┐
                        ▼                                                   ▼
+---------------------------------------------------+   +-------------------------------------------+
|    SUPERVISED 9-CLASS CLASSIFIER (Module D & F)   |   |    STATISTICAL LANGUAGE MODEL (Module G/H)|
| • Sublinear TF-IDF Character & Word N-grams       |   | • Unigram, Bigram, and Trigram Counts     |
| • Stratified Logistic Regression (96.3% Acc)      |   | • Laplace Add-1 Smoothing (P(w|h))        |
| • Contributing Features Weight Explainability     |   | • Log-Likelihood & Perplexity Evaluation  |
| • Civic Domain Guard Abstention Mechanism         |   | • Step-by-Step Viva Probability Breakdown |
+---------------------------------------------------+   +-------------------------------------------+
                        │                                                   │
                        └─────────────────────────┬─────────────────────────┘
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                     UNSUPERVISED TOPIC MODELING & SEMANTIC REDUCTION (Module I)                   |
|   • Latent Semantic Indexing (LSI): Truncated SVD on Document-Term TF-IDF Matrix                  |
|   • Latent Dirichlet Allocation (LDA): Generative Probabilistic Topic Modeling on Word Counts      |
|   • Document-Topic Distribution Mixture & Human-Interpretable Topic Clustering                    |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                    OPINION MINING, SENTIMENT & RISK SYNTHESIS (Module J & EchoTrace)              |
|   • Lexicon-Based Sentiment Polarity with Negation Windows & Valence Shifters                     |
|   • 6-Class Emotional Tone Detection (Frustration, Anger, Concern, Fear, Sadness, Relief)         |
|   • Target-Stance-Evidence Triplets (Target Issue Entity · Expressed Stance · Evidence Sentence)   |
|   • Multi-Entity EchoTrace Narrative Graph (Documents, Categories, Locations, Entities)           |
|   • Candidate Contradiction Detection (Divergent Stances in Shared Domain / Location)             |
|   • Inferred Operational Risks Synthesis (Infrastructure Hazards, Disease Risks, Grid Outages)    |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Syllabus Mapping Matrix (Modules A – J)

Every mandatory assignment and syllabus requirement is implemented with genuine, transparent mathematical algorithms (without external ChatGPT/OpenAI API dependencies):

| Module | Syllabus Requirement | Core Implementation File | Algorithmic Method | Where to Inspect in UI | Viva Academic Talking Point |
|---|---|---|---|---|---|
| **A** | **Data Ingestion & Web Scraping** | [`engine/ingestion.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/ingestion.py) | Requests, BeautifulSoup4, `urllib.robotparser`, CSV/TXT parsers, SHA-256 hash & token Jaccard similarity deduplication | Documents → *Ingest Document* modal, *Import Dataset* modal | Why web crawlers must respect `robots.txt` and polite rate limits; how SHA-256 prevents identical records and token Jaccard catches slight paraphrasing. |
| **B** | **Text Preprocessing, Tokenization & Statistics** | [`engine/preprocessing.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/preprocessing.py) | Unicode NFC normalization, Devanagari vowel-mark preserving regex tokenization, sentence splitting, multilingual stop words removal (en, hi, mr), Type-Token Ratio (TTR) | NLP Methods Lab → Tab 1 (*Preprocessing & Counts*) | Why basic whitespace regex `\w+` strips Devanagari combining characters (matras) creating invalid sub-tokens; how TTR measures lexical diversity. |
| **C** | **Morphological Analysis: Stemming vs Lemmatization** | [`engine/linguistics.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/linguistics.py) | NLTK Porter Stemmer, Snowball Stemmer, WordNet Lemmatizer with Penn Treebank POS-to-WordNet mapping | NLP Methods Lab → Tab 2 (*Stemming vs Lemmatization*) | Heuristic suffix-stripping rules (Porter) operate without a dictionary and can produce non-words (e.g. `community` → `commun`), whereas Lemmatization consults WordNet morphology and POS context. |
| **D** | **Part-of-Speech Tagging** | [`engine/linguistics.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/linguistics.py) | NLTK Averaged Perceptron Tagger (Penn Treebank tagset) with mapping to simplified Universal POS tags (NOUN, VERB, ADJ, ADV, etc.) | NLP Methods Lab → Tab 3 (*POS & NER*) | How POS context resolves syntactic ambiguity (e.g., "water" as NOUN vs VERB); why POS tags are essential inputs for correct lemmatization. |
| **D** | **Word Vector Embeddings** | [`engine/embeddings.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/embeddings.py) | 24-Dimensional Positive Pointwise Mutual Information (PPMI) co-occurrence matrix decomposed via TruncatedSVD; cosine similarity nearest neighbors | NLP Methods Lab → Tab 4 (*TF-IDF & Embeddings*) | Distributional hypothesis: "words that occur in similar contexts have similar meanings" (Harris, 1954); how PPMI reweights raw co-occurrence counts to penalize frequent stopwords. |
| **D & F** | **9-Category Text Classification** | [`engine/classification.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/classification.py) | Character N-grams (3–5 grams) and Word N-grams sublinear TF-IDF vectorizer + Stratified Multinomial Logistic Regression; feature contribution weights | Overview Hub (Metrics, Confusion Matrix) & NLP Lab → Tab 5 | Sublinear TF scaling ($1 + \log(tf)$) prevents high-frequency term domination; character n-grams handle typos, misspellings, and transliterated Indian English cleanly. |
| **E** | **Named Entity Recognition & Gazetteer** | [`engine/entities.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/entities.py) | NLTK Maximum Entropy Statistical Chunker (`ne_chunk`) + Curated Indian Municipal Gazetteer (Pune, Hadapsar, PCMC, etc.) + Regex entities (PIN, Dates, Quantities) | NLP Methods Lab → Tab 3 (*POS & NER*) | Hybrid NER combining statistical ML (for generalized Person/Org/GPE) with domain gazetteers ensures high recall on Indian localities and postal PIN codes. |
| **F** | **TF-IDF Feature Extraction** | [`engine/pipeline.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/pipeline.py) | Scikit-learn TfidfVectorizer with sublinear TF scaling and smooth IDF: $\text{TF-IDF}(t, d) = (1 + \log \text{tf}) \times \log\left(\frac{1 + N}{1 + \text{df}}\right)$ | NLP Methods Lab → Tab 4 (*TF-IDF & Embeddings*) | How IDF penalizes ubiquitous words across the corpus while highlighting distinctive incident keywords (e.g. "transformer", "waterlogging", "contaminate"). |
| **G & H** | **N-gram Language Modeling & Laplace Smoothing** | [`engine/ngrams.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/ngrams.py) | Unigram, bigram, trigram vocabulary tracking; Laplace add-1 smoothing: $P(w_i \mid w_{i-1}) = \frac{C(w_{i-1}, w_i) + 1}{C(w_{i-1}) + \|V\|}$; Log-likelihood & Perplexity calculation | NLP Methods Lab → Tab 6 (*N-grams & Sequence Prob*) | The zero-frequency problem: an unseen bigram assigns zero probability to an entire sentence; Laplace smoothing redistributes probability mass to ensure non-zero scores; perplexity as branching factor. |
| **I** | **Topic Modeling: LSI & LDA** | [`engine/topic_modeling.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/topic_modeling.py) | Latent Semantic Indexing (TruncatedSVD on TF-IDF) vs Latent Dirichlet Allocation (Variational Bayes on count vectors); human-readable topic labeling | NLP Methods Lab → Tab 7 (*LSI & LDA Topics*) | Mathematical difference: LSI uses linear algebraic matrix decomposition (SVD) producing orthogonal semantic components with positive/negative weights; LDA is a generative probabilistic Bayesian model using Dirichlet priors. |
| **J** | **Opinion Mining, Emotion & Stance** | [`engine/sentiment_opinions.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/sentiment_opinions.py) | Lexicon sentiment polarity with 3-token negation windows ("not clean" → positive to negative inversion), 6 emotional tone detectors, Target-Stance-Evidence extraction | Public Opinion view & NLP Lab → Tab 8 (*Sentiment & Opinions*) | Why bag-of-words sentiment fails on negation without contextual lookback; how extracting exact supporting evidence sentences anchors claims to ground truth. |
| **EchoTrace** | **Narrative Graph & Contradiction Detection** | [`engine/narrative_graph.py`](file:///c:/Users/Shamal/OneDrive/Desktop/jan/JanSahay/engine/narrative_graph.py) | Multi-entity bipartite/heterogeneous graph generation; cosine similarity clustering in shared thematic/geographic loci to detect divergent claims | EchoTrace Graph view (Canvas + Contradictions list) | Identifying operational discrepancies: e.g. an administrative report claiming "leak repaired" versus a persistent resident complaint of "no water" in the same ward. |

---

## 4. User Interface Navigation & Feature Guide

The application features a modern, responsive single-page web architecture across 7 integrated panels:

### 1. Executive Intelligence Hub (`hub`)
- **Key Performance Indicators (KPIs):** Total analyzed records, dominant municipal domain, negative sentiment ratio, active inferred hazards, unsupervised topics discovered, and candidate contradictions flagged.
- **9-Category Public Issue Distribution:** Interactive progress bars with issue frequency and percentages.
- **Sentiment & Emotion Polarity:** Composite segmented polarity bar (Negative, Neutral, Positive, Mixed) and prominent emotional tone pills.
- **Geographic Hotspots:** Top locations identified by the gazetteer and NER with incident counts.
- **Emerging N-grams:** High-frequency bigrams and trigrams extracted across all reports.
- **Academic Model Evaluation Card:** Live holdout test metrics (96.3% Accuracy, 0.958 Weighted F1, 0.606 Macro F1, 270 test samples) and an interactive confusion matrix toggle.

### 2. Document Intelligence Repository (`docs`)
- **Filter Toolbar:** Live multi-parameter filtering by search term (title, text, location), category, sentiment, and language.
- **Document Cards Grid:** Displays each report's category badge, sentiment badge, snippet, extracted location, language pill, and inferred risk count.
- **Deep Document Detail Drawer:** Clicking *Deep NLP Report* opens an inspection drawer showing full text, inferred risks with severity, classification confidence, sentiment breakdown, recognized entities, and sequence perplexity.
- **One-Click Ingestion & Import:**
  - *Manual Ingest:* Enter text, headline, location, and choose auto or manual category.
  - *File Upload:* Parse batch `.csv` files or `.txt` reports with automatic duplicate detection.
  - *Web Scraper:* Enter public URLs to fetch, parse, and ingest articles respecting `robots.txt`.
  - *Curated Datasets:* 1-click import of the 1,331 JanSahay civic dataset or the HuffPost news sample.

### 3. EchoTrace Narrative Graph & Contradictions (`graph`)
- **Interactive Force-Directed Physics Canvas:** Renders a spring-physics network graph linking Documents (purple), Categories (green), Locations (amber), and Entities (red).
- **Node Dragging & Inspector:** Drag nodes across the canvas; click any node to open the inspector displaying connected relationships and reasons (e.g. `BELONGS_TO`, `REPORTED_AT`, `MENTIONS`, `RELATED_REPORT`).
- **Candidate Contradictions Panel:** Flags opposing operational claims in the same location and category (e.g., resolution vs persistent failure), displaying textual snippets, similarity scores, and conflicting stances.

### 4. Public Opinion & Risk Discovery (`opinion`)
- **Mined Opinions Table:** Structured table displaying Target Issue, Expressed Stance (support, oppose, complaint, neutral), Sentiment & Emotion, Exact Quoted Evidence Sentence, and a clickable link to the source report.
- **Topic-Wise Sentiment Matrix:** Cards breaking down opinion distributions (positive vs negative) across discovered LDA topic clusters.

### 5. NLP Methods & Explainability Lab (`lab`)
- **Interactive Text Inspector:** Test any custom incident report, citizen complaint, or preloaded sample (Pune Flood, Water Contamination, Streetlight Hazard, Hindi Garbage, Marathi Potholes).
- **8 Deep Syllabus Tabs:**
  1. *Preprocessing & Counts:* Word count, sentence count, char count, language detection, token chips, stopword chips, side-by-side original vs cleaned text.
  2. *Stemming vs Lemmatization:* Educational explanation + comparison table of Porter Stem vs WordNet Lemma with POS context.
  3. *POS & NER:* Tokens with Penn Treebank tags + universal category, extracted entities, and color-coded entity markup.
  4. *TF-IDF & Embeddings:* Top TF-IDF n-grams table + 24D PPMI-SVD dense vector preview + cosine nearest neighbors.
  5. *9-Class Classifier:* Predicted class, confidence badge, all 9 category probabilities, contributing n-gram features, and domain guard status.
  6. *Sequence Probability:* N-gram order, vocabulary size, log-likelihood, perplexity, and step-by-step $P(w_i \mid h)$ factors table.
  7. *LSI & LDA Topics:* Latent semantic indexing components and Dirichlet topic clusters with terms and document weights.
  8. *Sentiment & Opinions:* Tone polarity score, emotion gauges (frustration, anger, concern, fear, sadness, relief), and mined target-stance triplets.

### 6. Citizen Complaint Assistant (`home`)
- **Preserved 3-Step Wizard:** Step 1 (Describe), Step 2 (Location & Details), Step 3 (Review & Ready Draft).
- **Faithful Complaint Drafting:** Auto-sizing official draft formatted clearly without fabricated facts.
- **Municipal Authority Routing:** Direct links and guidelines for PCMC SARATHI, PMC CARE, and Maharashtra Aaple Sarkar.
- **Supporting Photos:** Upload up to 3 JPG/PNG/WebP photos with local thumbnail previews.

### 7. Local Complaint Tracker (`saved`)
- **SQLite Persistence:** Stored locally in `instance/drafts.sqlite3`.
- **Search & Filters:** Filter by status (Draft, Ready to Submit, Submitted Externally, Follow-up in Progress, Resolved).
- **Tracking & History:** Record official reference numbers, submission dates, and follow-up notes with complete chronological audit history.
- **Data Export:** Export records to JSON or CSV (with formula injection protection).

---

## 5. Academic Evaluation & Classifier Performance

The primary 9-category public issue classifier was evaluated using stratified holdout validation (80% train, 20% test) across 1,346 annotated records:

- **Total Samples:** 1,346 records (1,076 train, 270 test)
- **Feature Extraction:** Sublinear Character N-grams (3 to 5 grams) + Word Unigrams/Bigrams
- **Classifier Model:** Multinomial Logistic Regression (L2 regularization, $\mathcal{C}=1.0$)
- **Holdout Test Accuracy:** **96.3%**
- **Weighted Average F1-Score:** **0.958**
- **Macro Average F1-Score:** **0.606** (due to ultra-rare disaster classes with 1 holdout sample)

### Per-Class Performance Summary

| Category | Precision | Recall | F1-Score | Holdout Support |
|---|---|---|---|---|
| **Water Supply** | 0.986 | 0.972 | **0.979** | 71 |
| **Roads & Potholes** | 0.943 | 0.965 | **0.954** | 86 |
| **Drainage & Flooding** | 0.973 | 0.973 | **0.973** | 37 |
| **Environment & Sanitation** | 0.976 | 0.976 | **0.976** | 41 |
| **Electricity & Lights** | 0.941 | 1.000 | **0.970** | 32 |
| **Public Safety** | 0.000 | 0.000 | 0.000 | 1 |
| **Public Health** | 0.000 | 0.000 | 0.000 | 1 |
| **Governance** | 0.000 | 0.000 | 0.000 | 1 |

*Note on Domain Guard:* For inputs lacking civic infrastructure terminology (e.g., generic conversational greetings), the system abstains and categorizes as `other` rather than making a high-confidence false assertion.

---

## 6. Installation & Execution Guide

### Prerequisites
- Python **3.11** or **3.12**
- Microsoft Windows, macOS, or Linux
- Modern web browser (Chrome, Edge, Firefox, Safari)

### Step 1: Clone / Open Repository
Open terminal in the project directory:
```powershell
cd c:\Users\Shamal\OneDrive\Desktop\jan\JanSahay
```

### Step 2: Set Up Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Install required dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 3: Launch Local Application
```powershell
.\.venv\Scripts\python.exe app.py
```
The application will start on: **`http://127.0.0.1:5000`**

### Step 4: Run Automated Verification Test Suite
To execute the comprehensive test suite (44 automated unit tests covering all 11 syllabus modules, database migrations, and REST APIs):
```powershell
.\.venv\Scripts\python.exe -m unittest discover tests -v
```

---

## 7. Viva Examination & Practical Viva Preparation Guide

When presenting this project to an examiner or viva committee, use the following explanations:

### Q1: "Why did you build an integrated platform instead of separate homework demo pages?"
> *"In real-world engineering, NLP techniques do not operate in a vacuum. A raw citizen report or news article first requires preprocessing (Module B) to normalize Unicode and handle Devanagari scripts; then morphological lemmatization (Module C) and POS tagging (Module D) normalize verbs and nouns; NER (Module E) identifies the geographic locality; TF-IDF and Logistic Regression (Module D & F) classify the municipal domain; PPMI-SVD embeddings (Module D) find related reports; N-gram language modeling (Module G/H) assesses fluency; topic modeling (Module I) discovers latent themes across the city; and sentiment/opinion mining (Module J) extracts operational risk and public stance. The integrated architecture proves that these 11 syllabus components build upon each other in a production-grade data pipeline."*

### Q2: "What is the mathematical difference between Stemming and Lemmatization?"
> *"Stemming is a rule-based heuristic suffix chopping algorithm (like the Porter stemmer) that iteratively removes known English inflectional endings (e.g., `-ing`, `-ed`, `-sses`). It does not consult a lexicon, meaning it can produce non-words (e.g. `community` → `commun`, `flying` → `fli`). Lemmatization, by contrast, uses a lexical database (WordNet) and considers the word's grammatical context via Part-of-Speech tagging. It reduces a word to its canonical lemma (e.g. `caring` with verb POS becomes `care`, while with noun POS remains `caring`)."*

### Q3: "Explain Laplace Smoothing and the Zero-Frequency Problem in N-gram models."
> *"In Maximum Likelihood Estimation (MLE) of N-gram language models, the conditional probability is calculated as:*
> $$P_{\text{MLE}}(w_i \mid w_{i-1}) = \frac{\text{Count}(w_{i-1}, w_i)}{\text{Count}(w_{i-1})}$$
> *If a specific pair of words $(w_{i-1}, w_i)$ never occurred in the training corpus, $\text{Count}(w_{i-1}, w_i) = 0$. Because the joint sequence probability is a product of terms:*
> $$P(w_1, \dots, w_k) = \prod_{i=1}^k P(w_i \mid w_{i-1})$$
> *A single zero probability causes the entire sentence probability to collapse to zero. Laplace (Add-1) smoothing resolves this by adding 1 to every numerator and adding the vocabulary size $|V|$ to the denominator:*
> $$P_{\text{Laplace}}(w_i \mid w_{i-1}) = \frac{\text{Count}(w_{i-1}, w_i) + 1}{\text{Count}(w_{i-1}) + |V|}$$
> *This guarantees non-zero probabilities, redistributes probability mass to unseen events, and enables robust Perplexity calculation: $\text{PP}(W) = \exp\left(-\frac{1}{N} \ln P(W)\right)$."*

### Q4: "How does PPMI-SVD word embedding work without deep learning?"
> *"PPMI (Positive Pointwise Mutual Information) measures the association between a target word $w$ and context word $c$ relative to chance:*
> $$\text{PMI}(w, c) = \log_2 \frac{P(w, c)}{P(w) P(c)} = \log_2 \frac{\text{Count}(w, c) \times N}{\text{Count}(w) \times \text{Count}(c)}$$
> *PPMI replaces negative values with 0 ($\max(\text{PMI}, 0)$) to eliminate uninformative sparse pairs. We construct a word-context PPMI matrix $M \in \mathbb{R}^{V \times V}$ and apply Truncated Singular Value Decomposition (SVD):*
> $$M \approx U_k \Sigma_k V_k^T$$
> *Setting $k = 24$ yields a compact 24-dimensional dense vector representation for each word ($W = U_k \Sigma_k^{1/2}$), enabling semantic cosine similarity without downloading multi-gigabyte neural networks."*

### Q5: "What is the difference between LSI and LDA Topic Modeling?"
> *"Latent Semantic Indexing (LSI) is a linear algebra approach using SVD on the TF-IDF matrix. It identifies orthogonal axes of maximum variance, meaning terms can have negative weights and topics are geometric projections. Latent Dirichlet Allocation (LDA) is a generative probabilistic Bayesian model. It models each document as a Dirichlet-distributed mixture over $K$ latent topics, and each topic as a Dirichlet-distributed mixture over vocabulary words. LDA produces strictly non-negative, interpretable probability distributions."*

### Q6: "How does EchoTrace AI detect candidate contradictions?"
> *"EchoTrace AI groups reports that share high semantic similarity (TF-IDF cosine distance $> 0.28$) and refer to the same geographic location and infrastructure category. It evaluates the mined stances and sentiment polarity. If one report asserts resolution (e.g. 'work completed', 'water restored') while an adjacent report asserts disruption or persistent outage (e.g. 'tap still dry', 'pothole remains open'), EchoTrace flags the pair as a candidate contradiction for administrative investigation."*

---

## 8. Directory Structure

```
JanSahay/
├── app.py                      # Flask REST API server, endpoints & routes
├── workflow.py                 # SQLite database schema, migrations & context managers
├── product_copy.py             # Multilingual UI copy & localized metadata
├── requirements.txt            # Python dependencies (Flask, scikit-learn, NLTK, etc.)
├── README.md                   # Complete architectural, syllabus & viva documentation
│
├── engine/                     # Core Integrated NLP Intelligence Engine
│   ├── __init__.py             # Package exports
│   ├── preprocessing.py       # Module B: Unicode NFC, regex tokens, Devanagari, TTR
│   ├── linguistics.py          # Module C & D: Porter/Snowball stems, WordNet lemmas, POS
│   ├── entities.py             # Module E: NLTK NER, Indian gazetteer, PIN & regex entities
│   ├── embeddings.py           # Module D: 24D PPMI-SVD word vectors, cosine neighbors
│   ├── classification.py       # Module D & F: Sublinear char TF-IDF + Logistic Regression
│   ├── ngrams.py               # Module G & H: N-gram language model & Laplace smoothing
│   ├── topic_modeling.py       # Module I: LSI (TruncatedSVD) vs LDA (Latent Dirichlet)
│   ├── sentiment_opinions.py   # Module J: Polarity with negation, emotions, stance triplets
│   ├── narrative_graph.py      # EchoTrace: Multi-entity connection graph & contradictions
│   ├── ingestion.py            # Module A: CSV/TXT parsers, web scraper, SHA-256 deduplication
│   └── pipeline.py             # Unified pipeline orchestrator & risk synthesis engine
│
├── data/                       # Datasets & Curated Corpora
│   ├── service_train.json      # 1,331 verified civic complaints (en, hi, mr)
│   ├── authorities.json        # Municipal authority directory (PMC, PCMC, Aaple Sarkar)
│   └── ...
│
├── static/                     # Frontend Assets
│   ├── app.js                  # Complete client-side logic, routing & canvas visualizer
│   ├── assignments.js          # Guarded legacy helper utilities
│   ├── style.css               # Rich visual design system, glassmorphism, responsive grid
│   └── fonts/                  # Bundled Devanagari fonts (Noto Sans)
│
├── templates/                  # Frontend Views
│   └── index.html              # Single-page template with 7 integrated panels & 3 modals
│
└── tests/                      # Automated Verification Test Suite
    ├── test_intelligence.py    # Comprehensive tests for Modules A–J & REST APIs
    ├── test_workflow.py        # Database migrations & tracking tests
    └── test_project.py         # Baseline test assertions
```

---

## 9. Academic Integrity & Technical Limitations

- **No Simulated / Fake Responses:** All calculations (PPMI vectors, Laplace probabilities, TF-IDF weights, WordNet lemmas, LDA topic distributions) are executed live by genuine Python NLP algorithms.
- **Privacy & Offline First:** User complaints and local drafts are processed locally on the host machine without external cloud API transmissions.
- **Multilingual Scope:** Deep morphological WordNet lemmatization is supported for English; tokenization, vocabulary counts, stop words removal, and TF-IDF character classification are natively supported across English, Hindi, and Marathi.
- **Official Government Handoff:** JanSahay provides accurate routing, official URLs, and formal drafts for civic submission, but does not claim automated government login or live municipal database integration.
