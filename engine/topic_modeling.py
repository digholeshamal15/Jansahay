"""Module I: Latent Semantic Indexing (LSI) and Latent Dirichlet Allocation (LDA)."""
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD, LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
from engine.preprocessing import tokenize_words

def generate_topic_label(terms: list[str]) -> str:
    """Derive an interpretable domain topic label from top terms."""
    terms_set = set(t.lower() for t in terms)
    if terms_set & {'water', 'supply', 'tap', 'drinking', 'pipeline', 'leakage', 'meter', 'पाणी', 'पानी', 'नल'}:
        return "Water Supply & Pipeline Networks"
    elif terms_set & {'road', 'pothole', 'potholes', 'footpath', 'traffic', 'pavement', 'सड़क', 'रस्ता', 'खड्डा'}:
        return "Road Infrastructure & Traffic Hazards"
    elif terms_set & {'flood', 'flooding', 'rain', 'waterlogging', 'drain', 'drainage', 'gutter', 'sewage', 'पाणी तुंबणे', 'गटार'}:
        return "Monsoon Flooding & Drainage Overflow"
    elif terms_set & {'light', 'lights', 'lamp', 'streetlight', 'streetlights', 'power', 'electricity', 'बत्ती', 'दिवा', 'वीज'}:
        return "Streetlighting & Electrical Power Grid"
    elif terms_set & {'garbage', 'waste', 'trash', 'dustbin', 'dump', 'cleaning', 'कचरा', 'कूड़ा', 'स्वच्छता'}:
        return "Solid Waste Management & Sanitation"
    elif terms_set & {'hospital', 'health', 'doctor', 'dengue', 'malaria', 'disease', 'medicine', 'आरोग्य', 'दवाखाना'}:
        return "Public Health & Disease Prevention"
    elif terms_set & {'safety', 'emergency', 'police', 'fire', 'hazard', 'accident', 'danger', 'सुरक्षा', 'धोका'}:
        return "Public Safety & Emergency Access"
    elif terms_set & {'officer', 'office', 'complaint', 'delay', 'portal', 'tender', 'प्रशासन', 'तक्रार'}:
        return "Civic Administration & Service Response"
    else:
        return f"Civic Theme: {', '.join(terms[:3]).title()}"

class TopicIntelligenceEngine:
    """Implements both LSI (TruncatedSVD on TF-IDF) and LDA (Dirichlet Allocation on Counts)."""
    
    def __init__(self, texts: list[dict], n_topics: int = 5, random_state: int = 7):
        self.n_topics = n_topics
        self.random_state = random_state
        self.docs = texts
        self.is_valid = len(texts) >= 5
        
        self.lsi_components = []
        self.lda_topics = []
        self.doc_topic_matrix = None
        self.doc_lsi_matrix = None
        
        if not self.is_valid:
            return
            
        raw_texts = [d['text'] for d in texts]
        
        # 1. Latent Semantic Indexing (LSI)
        self.tfidf_vectorizer = TfidfVectorizer(
            tokenizer=tokenize_words,
            token_pattern=None,
            min_df=2,
            max_df=0.85,
            sublinear_tf=True
        )
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(raw_texts)
            n_lsi_comp = min(n_topics, tfidf_matrix.shape[0] - 1, tfidf_matrix.shape[1] - 1)
            if n_lsi_comp >= 2:
                self.lsi_svd = TruncatedSVD(n_components=n_lsi_comp, random_state=random_state)
                self.doc_lsi_matrix = self.lsi_svd.fit_transform(tfidf_matrix)
                
                feat_names = self.tfidf_vectorizer.get_feature_names_out()
                for i, comp in enumerate(self.lsi_svd.components_):
                    top_pos = [feat_names[idx] for idx in comp.argsort()[-6:][::-1]]
                    top_neg = [feat_names[idx] for idx in comp.argsort()[:4]]
                    self.lsi_components.append({
                        'component_id': i + 1,
                        'variance_ratio': round(float(self.lsi_svd.explained_variance_ratio_[i]), 4),
                        'dominant_terms': top_pos,
                        'opposing_terms': top_neg,
                        'label': generate_topic_label(top_pos)
                    })
        except Exception:
            self.lsi_components = []
            
        # 2. Latent Dirichlet Allocation (LDA)
        self.count_vectorizer = CountVectorizer(
            tokenizer=tokenize_words,
            token_pattern=None,
            min_df=2,
            max_df=0.85
        )
        try:
            count_matrix = self.count_vectorizer.fit_transform(raw_texts)
            n_lda_comp = min(n_topics, count_matrix.shape[0], count_matrix.shape[1])
            if n_lda_comp >= 2:
                self.lda = LatentDirichletAllocation(
                    n_components=n_lda_comp,
                    max_iter=20,
                    random_state=random_state,
                    learning_method='batch'
                )
                self.doc_topic_matrix = self.lda.fit_transform(count_matrix)
                
                words = self.count_vectorizer.get_feature_names_out()
                dominant_topics = self.doc_topic_matrix.argmax(axis=1)
                
                for topic_idx, topic_weights in enumerate(self.lda.components_):
                    top_word_indices = topic_weights.argsort()[-8:][::-1]
                    top_words = [words[i] for i in top_word_indices]
                    term_weights = [round(float(topic_weights[i] / topic_weights.sum()), 3) for i in top_word_indices]
                    
                    # Docs where this topic is dominant
                    doc_count = int(np.sum(dominant_topics == topic_idx))
                    sample_doc_indices = [idx for idx, d in enumerate(dominant_topics) if d == topic_idx][:3]
                    sample_titles = [texts[idx].get('title', texts[idx]['text'][:60]) for idx in sample_doc_indices]
                    
                    self.lda_topics.append({
                        'topic_id': topic_idx + 1,
                        'label': generate_topic_label(top_words),
                        'top_words': top_words,
                        'term_weights': term_weights,
                        'document_count': doc_count,
                        'proportion': round(doc_count / max(1, len(texts)), 3),
                        'sample_documents': sample_titles
                    })
        except Exception:
            self.lda_topics = []

    def get_summary(self) -> dict:
        """Return structured LSI and LDA results for the dashboard."""
        if not self.is_valid:
            return {
                'status': 'insufficient_corpus',
                'message': f"Corpus contains only {len(self.docs)} documents. Topic modeling requires at least 5 documents for meaningful distributions.",
                'lsi_components': [],
                'lda_topics': []
            }
            
        return {
            'status': 'success',
            'corpus_size': len(self.docs),
            'method_comparison': {
                'lsi': 'TruncatedSVD on TF-IDF Matrix (Linear Algebra / Singular Value Decomposition). Finds orthogonal latent semantic axes.',
                'lda': 'Latent Dirichlet Allocation on Word Counts (Generative Bayesian Probabilistic Model). Models documents as mixtures of latent Dirichlet topics.'
            },
            'lsi_components': self.lsi_components,
            'lda_topics': self.lda_topics
        }
        
    def find_lsi_similar(self, doc_idx: int, top_k: int = 3) -> list[dict]:
        """Find related documents using cosine similarity in the latent LSI space."""
        if self.doc_lsi_matrix is None or doc_idx >= len(self.docs):
            return []
        target_vec = self.doc_lsi_matrix[doc_idx:doc_idx+1]
        sims = cosine_similarity(target_vec, self.doc_lsi_matrix)[0]
        
        ranked = sims.argsort()[::-1]
        results = []
        for i in ranked:
            if i != doc_idx and len(results) < top_k and sims[i] > 0.15:
                results.append({
                    'index': i,
                    'title': self.docs[i].get('title', self.docs[i]['text'][:60]),
                    'similarity': round(float(sims[i]), 3)
                })
        return results
