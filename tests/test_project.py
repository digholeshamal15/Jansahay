import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app import app,engine
from nlp import NGramModel,tokenize,sentiment
from scripts.civic_assignment import summarize
from scripts.scrape import extract
from service_model import ROOT, read_rows, training_hash

class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();app.config.update(TESTING=True,DATABASE=str(Path(self.temp.name)/'drafts.sqlite3'));self.client=app.test_client()
    def tearDown(self):self.temp.cleanup()
    def test_multilingual_category_and_original_text(self):
        cases=[('en','The streetlight near my house is not working','lights'),('hi','हमारे घर में पानी नहीं आ रहा है','water'),('mr','आमच्या गल्लीतला कचरा उचलला नाही','garbage')]
        for lang,text,category in cases:
            with self.subTest(lang=lang):
                r=self.client.post('/api/analyze',json=dict(text=text,lang=lang,text_lang=lang))
                self.assertEqual(r.status_code,200);data=r.get_json();self.assertEqual(data['category'],category);self.assertIn(text,data['draft'])
    def test_unknown_and_override(self):
        data=self.client.post('/api/analyze',json={'text':'quantum telescope galaxy spectrometer'}).get_json()
        self.assertIsNone(data['category']);self.assertEqual(data['draft'],'')
        data=self.client.post('/api/analyze',json={'text':'quantum telescope galaxy spectrometer','category':'roads'}).get_json()
        self.assertEqual(data['category'],'roads');self.assertEqual(data['chosen_by'],'user')
    def test_storage_requires_explicit_save_and_delete(self):
        self.client.post('/api/analyze',json={'text':'water supply stopped yesterday'})
        self.assertEqual(self.client.get('/api/drafts').get_json(),[])
        r=self.client.post('/api/drafts',json={'body':'माझी तक्रार','category':'water','lang':'mr'})
        self.assertEqual(r.status_code,201);idx=r.get_json()['id']
        self.assertEqual(self.client.get('/api/drafts').get_json()[0]['body'],'माझी तक्रार')
        self.assertEqual(self.client.delete(f'/api/drafts/{idx}').status_code,200)
        self.assertEqual(self.client.get('/api/drafts').get_json(),[])
    def test_validation_and_origin(self):
        for data in ({'text':''},{'text':'abc','lang':'xx'},{'text':['bad']},{'text':'x'*3001},{'text':'abc','category':'fake'},{'text':'abc','lang':[]}):
            self.assertEqual(self.client.post('/api/analyze',json=data).status_code,400)
        self.assertEqual(self.client.post('/api/analyze',json={'text':'hi'},headers={'Origin':'https://unrelated.example'}).status_code,403)
    def test_indic_combining_marks_and_danda(self):
        self.assertEqual(tokenize('पाणी नाही।'),['पाणी','नाही'])
        self.assertEqual(tokenize('पानी नहीं।'),['पानी','नहीं'])
    def test_ngram_hand_calculation_normalization_and_unknown(self):
        model=NGramModel(['a b','a c'],2)
        self.assertEqual(len(model.vocab),5)
        # P(a|BOS)=3/7; P(b|a)=2/7; P(EOS|b)=2/6 => 2/49.
        self.assertAlmostEqual(model.score('a b')['probability'],2/49)
        self.assertAlmostEqual(sum(model.conditional(('a',),w) for w in model.vocab),1)
        self.assertTrue(math.isfinite(model.score('unseen term')['log_probability']))
    def test_no_fake_indic_pos(self):
        d=self.client.post('/api/lab',json={'text':'पुण्यात पाणी येत नाही।','lang':'mr'}).get_json()
        self.assertEqual(d['word_count'],4);self.assertNotIn('pos',d['english'])
        self.assertTrue(d['entities']['items']);self.assertEqual(d['ngram']['n'],2)
    def test_civic_message_statistics(self):
        path=Path(self.temp.name)/'civic.json'
        rows=[{'text':'Water is dirty. Please help!','lang':'en','category':'water'},
              {'text':'पानी नहीं आता।','lang':'hi','category':'water'},
              {'text':'पाणी येत नाही। मदत करा।','lang':'mr','category':'water'},
              {'text':22},{'category':'water'},{'text':'  '}]
        path.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
        r=summarize(path)
        self.assertEqual(r['message_count'],3)
        self.assertEqual(r['word_count'],13)
        self.assertEqual(r['sentence_count'],5)
        self.assertEqual(r['declared_language_counts'],{'en':1,'hi':1,'mr':1})
        self.assertEqual(sum(r['detected_language_counts'].values()),3)
        self.assertEqual(r['category_counts'],{'water':3})
        self.assertEqual(r['invalid_rows'],3)
        self.assertEqual(r['examples'][2]['tokens'],['पाणी','येत','नाही','मदत','करा'])
        self.assertNotIn('date_filter',r)
    def test_civic_jsonl_and_limit(self):
        path=Path(self.temp.name)/'civic.jsonl'
        path.write_text('invalid json\n'+json.dumps({'text':'Water is dirty.','lang':'en'})+'\n'+json.dumps({'text':'पाणी नाही।','lang':'mr'}),encoding='utf-8')
        r=summarize(path,limit=1)
        self.assertEqual(r['message_count'],1)
        self.assertEqual(r['invalid_rows'],1)
        self.assertEqual(r['category_counts'],{'unspecified':1})
        with self.assertRaises(ValueError):summarize(path,limit=-1)
    def test_scraper_html_extraction(self):
        title,text=extract('<title>Local help</title><body><nav>Ignore</nav><main>Water service <script>secret</script><p>Details</p></main></body>')
        self.assertEqual(title,'Local help');self.assertIn('Details',text);self.assertNotIn('secret',text);self.assertNotIn('Ignore',text)
    def test_topics_and_sentiment(self):
        self.assertEqual(len(self.client.get('/api/topics').get_json()['topics']),5)
        self.assertEqual(sentiment('not good')['tone'],'negative')
        self.assertEqual(sentiment('thank you, the problem is fixed')['tone'],'positive')
        self.assertEqual(sentiment('Thank you but the water is dirty')['tone'],'mixed')
    def test_external_split_integrity(self):
        splits={name:read_rows(ROOT/f'data/service_{name}.json') for name in ('train','validation','test')}
        groups={name:{r['group_id'] for r in rows} for name,rows in splits.items()}
        texts={name:{' '.join(r['text'].casefold().split()) for r in rows} for name,rows in splits.items()}
        for a,b in [('train','validation'),('train','test'),('validation','test')]:
            self.assertFalse(groups[a]&groups[b])
            self.assertFalse(texts[a]&texts[b])
        self.assertTrue(all(r['source']!='JanSahay authored' for name in ('validation','test') for r in splits[name]))
    def test_main_app_uses_hf_trained_model(self):
        info=engine.training_info
        self.assertGreater(info['training_messages'],90)
        self.assertIn('hackermango/Public_Grievance_Dataset',info['training_sources'])
        metadata=json.loads((ROOT/'models/service_metadata.json').read_text())
        self.assertEqual(metadata['training_sha256'],training_hash(ROOT/'data/service_train.json'))
        result=self.client.post('/api/analyze',json={'text':'The streetlight near our house is not working'}).get_json()
        self.assertEqual(result['classification']['training']['training_messages'],len(read_rows(ROOT/'data/service_train.json')))
    def test_page_and_local_assets(self):
        self.assertEqual(self.client.get('/').status_code,200)
        for asset in ('app.js','style.css'):
            response=self.client.get('/static/'+asset)
            self.assertEqual(response.status_code,200)
            response.close()

if __name__=='__main__':unittest.main()
