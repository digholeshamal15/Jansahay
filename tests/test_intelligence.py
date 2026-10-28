"""Automated tests for JanSahay Integrated NLP Intelligence Platform (EchoTrace AI)."""
import json
import unittest
from engine.preprocessing import analyze_text, tokenize_words, tokenize_sentences, detect_language
from engine.linguistics import analyze_linguistics
from engine.entities import extract_entities
from engine.embeddings import WordEmbeddingModel
from engine.classification import IssueClassifier, CATEGORIES_9
from engine.ngrams import NGramLanguageModel, extract_corpus_ngrams
from engine.topic_modeling import TopicIntelligenceEngine
from engine.sentiment_opinions import analyze_sentiment_and_emotions
from engine.narrative_graph import NarrativeGraphEngine
from engine.ingestion import calculate_sha256, check_duplicate, parse_csv_content, parse_txt_content, load_huffpost_sample
from engine.pipeline import UnifiedNLPEngine
from app import app

class IntelligencePlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = UnifiedNLPEngine()
        cls.client = app.test_client()

    def test_module_b_preprocessing_and_counts(self):
        text = "Heavy rainfall caused severe waterlogging in Pune. Residents reported damaged roads!"
        res = analyze_text(text, declared_lang='en')
        self.assertGreater(res['word_count'], 5)
        self.assertEqual(res['sentence_count'], 2)
        self.assertEqual(res['effective_language'], 'en')
        self.assertIn('rainfall', res['tokens'])
        self.assertIn('pune', res['tokens'])
        self.assertNotIn('in', res['cleaned_text'].split())  # stop word removed in cleaned text

    def test_module_c_stemming_and_lemmatization(self):
        words = ['operating', 'feet', 'broken', 'complaints']
        res = analyze_linguistics(words, lang='en')
        self.assertIn('comparison_table', res)
        # Check comparison table
        feet_entry = next((r for r in res['comparison_table'] if r['original'] == 'feet'), None)
        self.assertIsNotNone(feet_entry)
        self.assertEqual(feet_entry['lemma'], 'foot')

    def test_module_d_pos_tagging_and_embeddings(self):
        words = ['broken', 'streetlight', 'damaged', 'quickly']
        ling = analyze_linguistics(words, lang='en')
        self.assertGreater(len(ling['pos_tags']), 0)
        
        # Test word embeddings
        model = self.engine.embeddings
        self.assertGreater(model.vocab_size, 10)
        vec = model.get_vector('water')
        if vec is not None:
            self.assertEqual(len(vec), 24)
            neighbors = model.nearest_neighbors('water', top_k=3)
            self.assertIsInstance(neighbors, list)

    def test_module_d_classification_9_categories(self):
        sample_road = "Deep potholes on the main highway road are causing severe vehicle damage and traffic jams."
        res = self.engine.classifier.classify(sample_road, lang='en')
        self.assertEqual(res['predicted_category'], 'roads')
        self.assertGreater(res['confidence'], 0.20)
        self.assertGreater(len(res['ranking']), 5)
        self.assertIn('roads', [r['category'] for r in res['ranking']])

    def test_module_e_named_entity_recognition(self):
        text = "Pune Municipal Corporation PMC officials visited Kothrud near 411038 on Monday."
        ner = extract_entities(text, lang='en')
        labels = [e['label'] for e in ner['entities']]
        self.assertTrue('GPE' in labels or 'LOC' in labels)
        self.assertTrue('ORG' in labels)
        self.assertTrue('PIN_CODE' in labels)
        self.assertTrue('DATE' in labels)

    def test_module_g_and_h_ngrams_and_sequence_probability(self):
        text = "Drinking water supply is irregular."
        model = self.engine.ngram_models[('en', 2)]
        score = model.score_sequence(text)
        self.assertIn('sequence_probability', score)
        self.assertIn('perplexity', score)
        self.assertGreater(score['perplexity'], 0.0)
        self.assertGreater(len(score['steps']), 0)

    def test_module_i_topic_modeling(self):
        docs = [
            {'id': '1', 'title': 'Water tap leak', 'text': 'Severe water supply disruption and tap pipe leakages.'},
            {'id': '2', 'title': 'Drinking water', 'text': 'Drinking water pipeline contamination and low pressure.'},
            {'id': '3', 'title': 'Road pothole', 'text': 'Damaged road surface with large dangerous potholes.'},
            {'id': '4', 'title': 'Footpath damage', 'text': 'Pavement and footpath excavation broken by contractors.'},
            {'id': '5', 'title': 'Flooding underpass', 'text': 'Monsoon rain caused waterlogging and drain overflow.'},
            {'id': '6', 'title': 'Drain silt', 'text': 'Blocked drainage and sewage overflow on residential streets.'}
        ]
        topic_engine = TopicIntelligenceEngine(docs, n_topics=2)
        summary = topic_engine.get_summary()
        self.assertEqual(summary['status'], 'success')
        self.assertGreater(len(summary['lda_topics']), 0)

    def test_module_j_sentiment_and_opinion_mining(self):
        text = "The water supply was completely blocked. We are very frustrated by the delayed response."
        res = analyze_sentiment_and_emotions(text)
        self.assertEqual(res['tone'], 'negative')
        self.assertLess(res['polarity_score'], 0.0)
        emotions = [e['emotion'] for e in res['emotions']]
        self.assertIn('frustration', emotions)
        self.assertGreater(len(res['opinions_mined']), 0)
        self.assertEqual(res['opinions_mined'][0]['target_issue'], 'Water Supply')

    def test_module_a_ingestion_and_deduplication(self):
        sample = "Potholes on Karve Road need immediate repair by PMC."
        hash_val = calculate_sha256(sample)
        self.assertEqual(len(hash_val), 64)
        existing = [{'id': 'doc_1', 'text': sample, 'sha256': hash_val}]
        dup = check_duplicate(sample, existing)
        self.assertTrue(dup['is_duplicate'])
        self.assertEqual(dup['duplicate_type'], 'exact')
        
        # Test CSV parsing
        csv_data = "text,location,category\nWater pipeline burst,Shivajinagar,water"
        parsed = parse_csv_content(csv_data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['location'], 'Shivajinagar')

    def test_narrative_graph_and_contradictions(self):
        docs = [
            {'id': '1', 'title': 'Water Restored', 'text': 'Water supply in Kothrud was completely restored and fixed today.', 'location': 'Kothrud', 'category': 'water'},
            {'id': '2', 'title': 'No Water Supply', 'text': 'No water supply in Kothrud for three days, taps are still dry and broken.', 'location': 'Kothrud', 'category': 'water'}
        ]
        engine = NarrativeGraphEngine(docs)
        graph = engine.build_graph()
        self.assertGreater(graph['node_count'], 2)
        contradictions = engine.detect_contradictions()
        self.assertGreater(len(contradictions), 0)
        self.assertEqual(contradictions[0]['report_a']['stance'], 'Resolved / Restored')

    def test_api_endpoints_integration(self):
        # 1. Overview
        r_over = self.client.get('/api/overview')
        self.assertEqual(r_over.status_code, 200)
        data = r_over.get_json()
        self.assertIn('total_documents', data)
        self.assertIn('categories_breakdown', data)
        
        # 2. Documents listing
        r_docs = self.client.get('/api/documents')
        self.assertEqual(r_docs.status_code, 200)
        docs = r_docs.get_json()
        self.assertIsInstance(docs, list)
        
        # 3. Create document
        r_create = self.client.post('/api/documents', json={
            'title': 'Test Flood Incident',
            'text': 'Severe flash flood inundated main road in Pune with knee-deep water.',
            'location': 'Pune',
            'lang': 'en',
            'category': 'auto'
        })
        self.assertEqual(r_create.status_code, 201)
        created = r_create.get_json()
        doc_id = created['id']
        
        # 4. Get document
        r_get = self.client.get(f'/api/documents/{doc_id}')
        self.assertEqual(r_get.status_code, 200)
        
        # 5. NLP explain
        r_exp = self.client.post('/api/nlp-explain', json={
            'text': 'Potholes on the street need repair.',
            'lang': 'en',
            'n': 2
        })
        self.assertEqual(r_exp.status_code, 200)
        exp = r_exp.get_json()
        self.assertIn('preprocessing', exp)
        self.assertIn('linguistics', exp)
        self.assertIn('entities', exp)
        self.assertIn('classification', exp)
        self.assertIn('sequence_probability', exp)
        
        # Clean up
        self.client.delete(f'/api/documents/{doc_id}')

if __name__ == '__main__':
    unittest.main()
