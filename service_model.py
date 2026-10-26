"""Shared training and inference for the civic service routing model."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import joblib
import sklearn
import regex as re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).parent
CATEGORIES = ('water', 'garbage', 'roads', 'lights', 'drainage')

def read_rows(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def fit_service(rows):
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2,5), sublinear_tf=True, max_features=60000)
    x = vectorizer.fit_transform([r['text'] for r in rows])
    # Balance language/category cells through weights, without duplicating rows.
    cells = Counter((r['lang'], r['category']) for r in rows)
    weights = np.array([len(rows)/(len(cells)*cells[(r['lang'],r['category'])]) for r in rows])
    classifier = LogisticRegression(C=8, max_iter=1500, random_state=7).fit(x, [r['category'] for r in rows], sample_weight=weights)
    return vectorizer, classifier, x

def training_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_service():
    path = ROOT/'data/service_train.json'
    if not path.exists():
        path = ROOT/'data/training.json'
    rows = read_rows(path)
    artifact = ROOT/'models/service_classifier.joblib'
    meta_path = ROOT/'models/service_metadata.json'
    try:
        meta=json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    except (ValueError,OSError):
        meta={}
    valid = meta.get('training_sha256') == training_hash(path) and meta.get('sklearn_version') == sklearn.__version__
    vectorizer=classifier=x=None
    if valid and artifact.exists():
        try:
            bundle=joblib.load(artifact)
            vectorizer,classifier=bundle['vectorizer'],bundle['classifier']
            x=vectorizer.transform([r['text'] for r in rows])
            mode='loaded bundled trained model'
        except (EOFError,ValueError,OSError,ImportError,KeyError):
            # A partial download or incompatible artifact must not stop the local app.
            vectorizer=classifier=x=None
    if vectorizer is None:
        vectorizer,classifier,x=fit_service(rows)
        mode='fitted locally from bundled training rows'
    info = {'training_messages':len(rows), 'training_sources':dict(Counter(r.get('source','JanSahay authored') for r in rows)),
            'language_counts':dict(Counter(r['lang'] for r in rows)), 'mode':mode,
            'note':'External Hugging Face data is English only. Hindi/Marathi examples remain a small authored supplement.'}
    return vectorizer, classifier, x, rows, info


def domain_terms_present(text):
    english={'water','supply','tap','pipe','pressure','garbage','waste','rubbish','dustbin','pothole','potholes','road','roads','footpath','pavement','streetlight','streetlights','lamp','lamps','lights','light','drain','drainage','gutter','manhole','sewage','sewer','wastewater'}
    indic=['पाणी','पानी','नल','नळ','पाइप','पाईप','कचरा','कचऱ','कूड़','कूड़','कचरापेटी','खड्ड','गड्ढ','रस्त','सड़क','सड़क','फुटपाथ','पदपथ','दिव','लाइट','बत्ती','गटार','नाली','नाले','सीवर','सांडपाणी','मॅनहोल','मैनहोल']
    words=re.findall(r'[\p{L}\p{M}]+',text.casefold())
    return any(w in english or any(root in w for root in indic) for w in words)
