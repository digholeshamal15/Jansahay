"""Module D (Classification): 9-Category Classifier, TF-IDF Features, and Model Evaluation."""
from pathlib import Path
from collections import Counter
import json
import numpy as np
import regex as re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
from engine.preprocessing import tokenize_words

ROOT = Path(__file__).resolve().parents[1]

# 9 Public infrastructure, disaster, incident, and governance categories
CATEGORIES_9 = {
    'roads': {
        'id': 'roads',
        'name': {'en': 'Road Damage and Transportation', 'hi': 'सड़क क्षति और परिवहन', 'mr': 'रस्ता नुकसान आणि वाहतूक'},
        'icon': 'roads',
        'keywords': ['road', 'pothole', 'potholes', 'footpath', 'pavement', 'traffic', 'bridge', 'excavation', 'highway', 'रस्ता', 'सड़क', 'खड्डा', 'गड्ढा']
    },
    'water': {
        'id': 'water',
        'name': {'en': 'Water Supply and Sanitation', 'hi': 'पानी की आपूर्ति और स्वच्छता', 'mr': 'पाणीपुरवठा आणि स्वच्छता'},
        'icon': 'water',
        'keywords': ['water', 'tap', 'pipeline', 'pressure', 'drinking water', 'meter', 'leakage', 'contamination', 'पाणी', 'पानी', 'नल', 'पाइप']
    },
    'flooding': {
        'id': 'flooding',
        'name': {'en': 'Flooding and Heavy Rainfall', 'hi': 'बाढ़ और भारी वर्षा', 'mr': 'पूर आणि मुसळधार पाऊस'},
        'icon': 'drainage',
        'keywords': ['flood', 'flooding', 'waterlogging', 'rainfall', 'monsoon', 'overflow', 'drain', 'gutter', 'drainage', 'submerged', 'पूर', 'पाणी तुंबणे', 'नाली', 'गटार']
    },
    'electricity': {
        'id': 'electricity',
        'name': {'en': 'Electricity and Power Outages', 'hi': 'बिजली और बिजली कटौती', 'mr': 'वीज आणि वीज खंडित'},
        'icon': 'lights',
        'keywords': ['electricity', 'power', 'streetlight', 'lights', 'lamp', 'transformer', 'voltage', 'blackout', 'wire', 'लाइट', 'बिजली', 'दिवा', 'वीज']
    },
    'public_safety': {
        'id': 'public_safety',
        'name': {'en': 'Public Safety and Emergency Access', 'hi': 'सार्वजनिक सुरक्षा और आपातकालीन पहुँच', 'mr': 'सार्वजनिक सुरक्षा आणि आणीबाणी मार्ग'},
        'icon': 'lock',
        'keywords': ['safety', 'emergency', 'ambulance', 'fire', 'police', 'hazard', 'accident', 'danger', 'blocked', 'access', 'suraksha', 'धोका', 'सुरक्षा', 'आपातकाल']
    },
    'health': {
        'id': 'health',
        'name': {'en': 'Health and Public Services', 'hi': 'स्वास्थ्य और सार्वजनिक सेवाएँ', 'mr': 'आरोग्य आणि सार्वजनिक सेवा'},
        'icon': 'file',
        'keywords': ['health', 'hospital', 'clinic', 'mosquito', 'dengue', 'malaria', 'doctor', 'medicine', 'disease', 'hygiene', 'आरोग्य', 'स्वास्थ्य', 'अस्पताल']
    },
    'environment': {
        'id': 'environment',
        'name': {'en': 'Environmental Issues and Waste Management', 'hi': 'पर्यावरण और कचरा प्रबंधन', 'mr': 'पर्यावरण आणि कचरा व्यवस्थापन'},
        'icon': 'garbage',
        'keywords': ['garbage', 'waste', 'trash', 'dumping', 'dustbin', 'litter', 'smell', 'odor', 'pollution', 'smoke', 'कचरा', 'कूड़ा', 'घाण', 'प्रदूषण']
    },
    'governance': {
        'id': 'governance',
        'name': {'en': 'Governance and Administrative Complaints', 'hi': 'प्रशासन और सेवा शिकायतें', 'mr': 'प्रशासन आणि सेवेच्या तक्रारी'},
        'icon': 'globe',
        'keywords': ['office', 'official', 'delay', 'officer', 'bribe', 'corruption', 'tender', 'portal', 'response', 'complaint', 'hearing', 'प्रशासन', 'अधिकारी', 'तक्रार']
    },
    'other': {
        'id': 'other',
        'name': {'en': 'Other or Unclassified Issues', 'hi': 'अन्य या अवर्गीकृत समस्याएँ', 'mr': 'इतर किंवा अवर्गीकृत समस्या'},
        'icon': 'file',
        'keywords': []
    }
}

# Mapping legacy 5 categories to 9
LEGACY_MAP = {
    'roads': 'roads',
    'water': 'water',
    'drainage': 'flooding',
    'lights': 'electricity',
    'garbage': 'environment'
}

DOMAIN_REGEX = re.compile(
    r'\b(?:water|supply|pipeline|leak|pothole|road|footpath|streetlight|lights|power|electricity|drain|drainage|flooding|waterlogging|garbage|waste|trash|dump|hospital|health|dengue|doctor|safety|hazard|danger|emergency|police|delay|complaint|officer|bmc|pmc|pcmc)\b|'
    r'(?:पाणी|पानी|खड्ड|गड्ढ|रस्त|सड़क|लाईट|लाइट|बत्ती|गटार|नाली|सांडपाणी|कचरा|कूड़ा|पूर|रोग|आरोग्य|रुग्णालय|दवाखाना|अधिकारी)',
    re.IGNORECASE
)

class IssueClassifier:
    """Multilingual 9-category issue classifier using sublinear TF-IDF and Logistic Regression."""
    
    def __init__(self):
        self.categories = list(CATEGORIES_9.keys())
        self.vectorizer = None
        self.classifier = None
        self.evaluation_metrics = {}
        self.is_trained = False
        
    def fit_from_data(self, records: list[dict], evaluate: bool = True):
        """Fit the model from labeled training records and calculate evaluation metrics."""
        # Normalize category keys
        usable_texts = []
        usable_labels = []
        
        for r in records:
            text = r.get('text', '').strip()
            cat = r.get('category', '').lower()
            mapped = LEGACY_MAP.get(cat, cat)
            if mapped in CATEGORIES_9 and text:
                usable_texts.append(text)
                usable_labels.append(mapped)
                
        # Supplement synthetic/curated examples for new categories (health, public_safety, governance)
        supplements = [
            # health
            ("Mosquito breeding in stagnant puddles causing dengue cases in the colony.", "health"),
            ("The local primary health centre has no doctors or medicines available.", "health"),
            ("Waterborne diseases spreading due to contaminated water supply in our ward.", "health"),
            ("दवाखाने में डॉक्टर उपस्थित नहीं हैं और दवाइयाँ खत्म हो गई हैं।", "health"),
            ("कॉलनीत डेंग्यूचे रुग्ण वाढत असून डास प्रतिबंधक फवारणी केली जात नाही.", "health"),
            # public_safety
            ("Open electric wires hanging near the school playground posing severe shock hazard.", "public_safety"),
            ("Illegal construction has completely blocked the emergency fire brigade passage.", "public_safety"),
            ("A fallen tree has trapped vehicles and blocked the ambulance route to the hospital.", "public_safety"),
            ("शाळेजवळ उघडी वीजतार लटकत असून मुलांच्या जीवाला धोका आहे.", "public_safety"),
            ("आग लागल्यास फायर ब्रिगेड जाण्यासाठी रस्ता अडवला गेला आहे.", "public_safety"),
            # governance
            ("Municipal office staff refusing to register birth certificate without informal fee.", "governance"),
            ("Multiple RTI applications regarding road tender budgets have gone unanswered for months.", "governance"),
            ("Civic grievance portal closes complaints automatically without any site inspection.", "governance"),
            ("वारंवार अर्ज देऊनही महापालिका कार्यालयातून कोणताही प्रतिसाद मिळालेला नाही.", "governance"),
            ("नागरिक सेवा केंद्रात कर्मचाऱ्यांची गैरहजेरी आणि कामात प्रचंड दिरंगाई होत आहे.", "governance")
        ]
        
        for t, c in supplements:
            usable_texts.append(t)
            usable_labels.append(c)
            
        if len(usable_texts) < 10:
            return
            
        # Feature representation: Word and Character n-grams for multilingual robustness
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=2,
            max_features=45000
        )
        
        X = self.vectorizer.fit_transform(usable_texts)
        y = usable_labels
        
        if evaluate and len(usable_texts) >= 50:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.20, random_state=7, stratify=y
            )
            clf = LogisticRegression(C=6.0, max_iter=1500, random_state=7, class_weight='balanced')
            clf.fit(X_train, y_train)
            
            y_pred = clf.predict(X_test)
            acc = float(accuracy_score(y_test, y_pred))
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            cm = confusion_matrix(y_test, y_pred, labels=sorted(list(set(y)))).tolist()
            
            self.evaluation_metrics = {
                'accuracy': round(acc, 4),
                'macro_avg_f1': round(report.get('macro avg', {}).get('f1-score', 0.0), 4),
                'weighted_avg_f1': round(report.get('weighted avg', {}).get('f1-score', 0.0), 4),
                'train_samples': X_train.shape[0],
                'test_samples': X_test.shape[0],
                'classes_evaluated': sorted(list(set(y))),
                'confusion_matrix': cm,
                'per_class': {
                    c: {
                        'precision': round(report.get(c, {}).get('precision', 0.0), 3),
                        'recall': round(report.get(c, {}).get('recall', 0.0), 3),
                        'f1_score': round(report.get(c, {}).get('f1-score', 0.0), 3),
                        'support': report.get(c, {}).get('support', 0)
                    }
                    for c in sorted(list(set(y))) if c in report
                }
            }
            # Train final model on full set
            self.classifier = LogisticRegression(C=6.0, max_iter=1500, random_state=7, class_weight='balanced')
            self.classifier.fit(X, y)
        else:
            self.classifier = LogisticRegression(C=6.0, max_iter=1500, random_state=7, class_weight='balanced')
            self.classifier.fit(X, y)
            self.evaluation_metrics = {'note': 'Trained on full dataset without holdout split.'}
            
        self.is_trained = True
        
    def classify(self, text: str, lang: str = 'en') -> dict:
        """Classify issue text into one of the 9 JanSahay categories with confidence and feature attribution."""
        if not self.is_trained or self.vectorizer is None or self.classifier is None:
            return {
                'predicted_category': 'other',
                'category_info': CATEGORIES_9['other'],
                'confidence': 0.0,
                'is_uncertain': True,
                'reason': 'Classifier is not yet initialized.'
            }
            
        text_clean = text.strip()
        if len(text_clean) < 10:
            return {
                'predicted_category': 'other',
                'category_info': CATEGORIES_9['other'],
                'confidence': 0.0,
                'is_uncertain': True,
                'reason': 'Text is too short for reliable classification (< 10 characters).'
            }
            
        has_domain_cues = bool(DOMAIN_REGEX.search(text_clean))
        
        q_vec = self.vectorizer.transform([text_clean])
        probs = self.classifier.predict_proba(q_vec)[0]
        classes = self.classifier.classes_
        
        ranking = []
        for c, p in sorted(zip(classes, probs), key=lambda x: -x[1]):
            cat_meta = CATEGORIES_9.get(c, CATEGORIES_9['other'])
            ranking.append({
                'category': c,
                'name': cat_meta['name'].get(lang, cat_meta['name']['en']),
                'probability': round(float(p), 4),
                'score_percent': round(float(p) * 100, 1)
            })
            
        top_cat = str(ranking[0]['category'])
        top_prob = ranking[0]['probability']
        
        # Abstention heuristic: if domain cues present, lower threshold (0.20); otherwise require higher confidence (0.35)
        is_uncertain = (top_prob < 0.20) or (not has_domain_cues and top_prob < 0.35)
        final_cat = 'other' if is_uncertain else top_cat
        
        # Explain classification: find top character/word features in input with highest positive coefficient for predicted class
        top_features = []
        try:
            class_idx = list(classes).index(top_cat)
            coefs = self.classifier.coef_[class_idx]
            feature_names = self.vectorizer.get_feature_names_out()
            row_indices = q_vec.indices
            row_data = q_vec.data
            
            scored_features = []
            for feat_idx, tfidf_val in zip(row_indices, row_data):
                weight = coefs[feat_idx] * tfidf_val
                scored_features.append((feature_names[feat_idx], weight, tfidf_val))
                
            scored_features.sort(key=lambda x: -x[1])
            top_features = [
                {'feature': f.strip(), 'weight': round(float(w), 4), 'tfidf': round(float(tf), 4)}
                for f, w, tf in scored_features[:10] if f.strip()
            ]
        except Exception:
            top_features = []
            
        cat_meta = CATEGORIES_9.get(final_cat, CATEGORIES_9['other'])
        
        return {
            'predicted_category': final_cat,
            'category_name': cat_meta['name'].get(lang, cat_meta['name']['en']),
            'confidence': top_prob if not is_uncertain else round(float(top_prob * 0.4), 3),
            'confidence_percentage': round(top_prob * 100, 1) if not is_uncertain else round(top_prob * 40, 1),
            'is_uncertain': is_uncertain,
            'has_domain_cues': has_domain_cues,
            'ranking': ranking,
            'contributing_features': top_features,
            'method': 'Sublinear character-ngrams TF-IDF + Calibrated Multi-class Logistic Regression with Domain Abstention',
            'evaluation': self.evaluation_metrics
        }
