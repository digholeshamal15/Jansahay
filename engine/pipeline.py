"""Unified NLP Intelligence Pipeline coordinating all syllabus modules and intelligence features."""
import json
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from engine.preprocessing import analyze_text, tokenize_words
from engine.linguistics import analyze_linguistics
from engine.entities import extract_entities
from engine.embeddings import WordEmbeddingModel
from engine.classification import IssueClassifier, CATEGORIES_9
from engine.ngrams import NGramLanguageModel, extract_corpus_ngrams
from engine.topic_modeling import TopicIntelligenceEngine
from engine.sentiment_opinions import analyze_sentiment_and_emotions
from engine.narrative_graph import NarrativeGraphEngine

ROOT = Path(__file__).resolve().parents[1]

class UnifiedNLPEngine:
    """Central engine managing trained models, corpus indices, and integrated analysis."""
    
    def __init__(self):
        # 1. Load training corpus
        corpus_path = ROOT / 'data/service_train.json'
        if not corpus_path.exists():
            corpus_path = ROOT / 'data/training.json'
            
        self.training_rows = json.loads(corpus_path.read_text(encoding='utf-8')) if corpus_path.exists() else []
        self.training_texts = [r['text'] for r in self.training_rows if r.get('text')]
        
        # 2. Issue Classifier (9 categories)
        self.classifier = IssueClassifier()
        self.classifier.fit_from_data(self.training_rows, evaluate=True)
        
        # 3. Dense PPMI-SVD Word Embeddings (24D)
        self.embeddings = WordEmbeddingModel(self.training_texts, dimensions=24, window_size=2)
        
        # 4. Multilingual N-gram Models (Orders 1, 2, 3 for en, hi, mr)
        self.ngram_models = {}
        for lang in ('en', 'hi', 'mr'):
            lang_texts = [r['text'] for r in self.training_rows if r.get('lang') == lang]
            if not lang_texts:
                lang_texts = self.training_texts[:40]
            for n in (1, 2, 3):
                self.ngram_models[(lang, n)] = NGramLanguageModel(lang_texts, n=n, alpha=1.0)
                
        # 5. Global TF-IDF Document Index for related-report discovery
        self.doc_vectorizer = TfidfVectorizer(tokenizer=tokenize_words, token_pattern=None, min_df=1, max_df=0.85, sublinear_tf=True)
        self.doc_tfidf = self.doc_vectorizer.fit_transform(self.training_texts) if self.training_texts else None
        
        # 6. Global Topic Engine on training corpus
        topic_input = [{'id': f"train_{i}", 'text': t, 'title': t[:50]} for i, t in enumerate(self.training_texts[:200])]
        self.topic_engine = TopicIntelligenceEngine(topic_input, n_topics=5)
        
    def analyze_document(self, text: str, declared_lang: str = 'en', manual_category: str = 'auto') -> dict:
        """Execute the integrated end-to-end NLP analysis pipeline on a single document."""
        # Step 1: Preprocessing & Text Statistics (Module B)
        preproc = analyze_text(text, declared_lang=declared_lang)
        active_lang = preproc['effective_language']
        
        # Step 2: Morphology & Syntax (Module C & POS from Module D)
        linguistics = analyze_linguistics(preproc['tokens'], lang=active_lang)
        
        # Step 3: Named Entity Recognition (Module E)
        ner = extract_entities(text, lang=active_lang)
        
        # Step 4: Classification (Module D)
        clf_result = self.classifier.classify(text, lang=active_lang)
        final_category = clf_result['predicted_category'] if manual_category == 'auto' else manual_category
        cat_meta = CATEGORIES_9.get(final_category, CATEGORIES_9['other'])
        
        # Step 5: Word Embeddings (Module D)
        embed_inspect = self.embeddings.inspect_text_embeddings(text)
        
        # Step 6: TF-IDF Top Keywords & Weights (Module F)
        tfidf_features = []
        if self.doc_vectorizer:
            try:
                q_vec = self.doc_vectorizer.transform([text]).toarray()[0]
                feat_names = self.doc_vectorizer.get_feature_names_out()
                top_indices = q_vec.argsort()[-12:][::-1]
                tfidf_features = [
                    {'keyword': feat_names[i], 'tfidf_score': round(float(q_vec[i]), 4)}
                    for i in top_indices if q_vec[i] > 0
                ]
            except Exception:
                tfidf_features = []
                
        # Step 7: N-gram Sequence Probability (Module H)
        ngram_model = self.ngram_models.get((active_lang, 2), self.ngram_models.get(('en', 2)))
        seq_prob = ngram_model.score_sequence(text) if ngram_model else {}
        
        # Step 8: Sentiment, Emotion & Opinion Mining (Module J)
        sentiment_opinions = analyze_sentiment_and_emotions(text)
        
        # Step 9: Related Reports Retrieval (Cosine similarity on TF-IDF)
        related_reports = []
        if self.doc_vectorizer and self.doc_tfidf is not None:
            try:
                q_vec = self.doc_vectorizer.transform([text])
                sims = cosine_similarity(q_vec, self.doc_tfidf)[0]
                ranked_idx = sims.argsort()[::-1]
                for idx in ranked_idx[:4]:
                    if sims[idx] > 0.15:
                        match_row = self.training_rows[idx]
                        related_reports.append({
                            'text': match_row['text'],
                            'category': match_row.get('category', 'other'),
                            'similarity': round(float(sims[idx]), 3),
                            'source': match_row.get('source', 'Training Corpus')
                        })
            except Exception:
                related_reports = []
                
        # Step 10: Inferred Emerging Risks Synthesis
        emerging_risks = self._synthesize_risks(final_category, ner, sentiment_opinions)
        
        return {
            'input_text': text,
            'preprocessing': preproc,
            'linguistics': linguistics,
            'entities': ner,
            'classification': {
                'category': final_category,
                'category_name': cat_meta['name'].get(active_lang, cat_meta['name']['en']),
                'category_icon': cat_meta['icon'],
                'confidence': clf_result['confidence'],
                'confidence_percent': clf_result.get('confidence_percentage', 0.0),
                'is_uncertain': clf_result['is_uncertain'],
                'ranking': clf_result['ranking'],
                'contributing_features': clf_result['contributing_features'],
                'chosen_by': 'model' if manual_category == 'auto' else 'user'
            },
            'embeddings': embed_inspect,
            'tfidf_keywords': tfidf_features,
            'sequence_probability': seq_prob,
            'sentiment_analysis': sentiment_opinions,
            'related_reports': related_reports,
            'emerging_risks': emerging_risks,
            'pipeline_version': 'JanSahay-EchoTrace-v2.0'
        }
        
    def _synthesize_risks(self, category: str, ner: dict, sentiment: dict) -> list[dict]:
        """Synthesize inferred emerging risks and operational hazards from multi-module evidence."""
        risks = []
        tone = sentiment.get('tone', 'neutral')
        emotions = [e['emotion'] for e in sentiment.get('emotions', [])]
        loc = ner.get('primary_location') or 'affected vicinity'
        
        opinion_targets = {op['target_issue'] for op in sentiment.get('opinions_mined', [])}
        
        if category in ('flooding', 'drainage') or 'Flooding & Drainage' in opinion_targets:
            risks.append({
                'risk_type': 'Infrastructure & Waterlogging Hazard',
                'description': f"Possible disruption of vehicular transit and emergency vehicle access near {loc} due to accumulated storm water.",
                'severity': 'High' if 'fear' in emotions or tone == 'negative' else 'Medium',
                'evidence': 'Flooding keywords, drainage overflow indicators, and negative polarity cues.',
                'status': 'Inferred Risk (Requires Field Verification)'
            })
        if category in ('roads',) or 'Road & Transport' in opinion_targets:
            risks.append({
                'risk_type': 'Traffic & Roadway Safety Risk',
                'description': f"Physical road degradation (potholes/excavation) near {loc} presents accident hazard for two-wheelers and pedestrians.",
                'severity': 'Medium',
                'evidence': 'Road damage keywords and sentiment cues.',
                'status': 'Inferred Risk'
            })
        if category in ('electricity',) or 'Streetlights & Power' in opinion_targets:
            risks.append({
                'risk_type': 'Electrical Grid / Night Safety Hazard',
                'description': f"Darkened streets or transformer faults in {loc} may compromise public pedestrian safety and night security.",
                'severity': 'Medium',
                'evidence': 'Power failure and streetlight outage terms.',
                'status': 'Inferred Risk'
            })
        if category in ('environment', 'health') or ('Health & Disease' in opinion_targets or 'Waste & Sanitation' in opinion_targets):
            risks.append({
                'risk_type': 'Public Health & Disease Risk',
                'description': f"Uncollected waste or stagnant water near {loc} may trigger vector-borne disease incubation (e.g. dengue, malaria).",
                'severity': 'High' if 'fear' in emotions else 'Medium',
                'evidence': 'Sanitation breakdown and health hazard cues.',
                'status': 'Inferred Risk'
            })
        if category in ('public_safety',) or 'Public Safety & Access' in opinion_targets:
            risks.append({
                'risk_type': 'Emergency Obstruction Risk',
                'description': f"Physical barrier or dangerous hazard in {loc} threatening immediate citizen safety.",
                'severity': 'High',
                'evidence': 'Public safety cues and urgency expressions.',
                'status': 'Inferred Immediate Risk'
            })
            
        return risks

    def run_corpus_analytics(self, documents: list[dict]) -> dict:
        """Run corpus-level analytics across stored documents for the Intelligence Hub."""
        total_docs = len(documents)
        if total_docs == 0:
            return {
                'total_documents': 0,
                'categories_breakdown': {},
                'sentiment_breakdown': {},
                'top_locations': [],
                'top_topics': [],
                'emerging_ngrams': {},
                'timeline': []
            }
            
        # Category counts
        cat_counts = Counter(d.get('category', 'other') for d in documents)
        
        # Locations
        loc_counts = Counter(d.get('location') for d in documents if d.get('location') and d.get('location') not in ('unknown', '—'))
        
        # Sentiments
        sentiments = Counter()
        all_texts = [d.get('text', '') for d in documents if d.get('text')]
        
        for doc in documents:
            text = doc.get('text', '')
            tone = doc.get('tone') or analyze_sentiment_and_emotions(text)['tone']
            sentiments[tone] += 1
            
        # N-grams across corpus
        ngrams = extract_corpus_ngrams(all_texts, top_k=10)
        
        # Topic modeling across corpus
        topic_engine = TopicIntelligenceEngine(documents, n_topics=min(5, max(2, total_docs)))
        topic_summary = topic_engine.get_summary()
        
        # EchoTrace Graph
        graph_engine = NarrativeGraphEngine(documents)
        graph_data = graph_engine.build_graph()
        contradictions = graph_engine.detect_contradictions()
        
        return {
            'total_documents': total_docs,
            'categories_breakdown': dict(cat_counts),
            'sentiment_breakdown': dict(sentiments),
            'top_locations': [{'location': loc, 'count': c} for loc, c in loc_counts.most_common(8)],
            'topic_summary': topic_summary,
            'emerging_phrases': ngrams['bigrams'],
            'graph_data': graph_data,
            'contradictions': contradictions
        }
