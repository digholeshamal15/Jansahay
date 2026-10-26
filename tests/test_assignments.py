"""Numbered assignment evidence using the preserved NLP algorithms."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from app import app

class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        app.config.update(TESTING=True,DATABASE=str(Path(self.temp.name)/'assignments.sqlite'),UPLOAD_DIR=str(Path(self.temp.name)/'photos'))
        self.client=app.test_client()
    def tearDown(self):self.temp.cleanup()
    def run_assignment(self,number,**extra):
        data=dict(text='The water in Pune 411001 is dirty again on 22/10/2026.',lang='en',n=2)
        data.update(extra)
        response=self.client.post(f'/api/assignments/{number}/run',json=data)
        self.assertEqual(response.status_code,200,response.get_data(as_text=True))
        self.assertEqual(response.get_json()['assignment'],number)
        return response.get_json()['result']
    def test_catalog_has_all_eleven_with_translated_feature_mapping(self):
        rows=self.client.get('/api/assignments').get_json()
        self.assertEqual([r['id'] for r in rows],list(range(1,12)))
        for row in rows:
            for key in ('title','feature','purpose','limitation'):
                self.assertEqual(set(row[key]),{'en','hi','mr'});self.assertTrue(all(row[key].values()))
            self.assertTrue(row['files']);self.assertTrue(row['method'])
    def test_each_demo_returns_specific_evidence(self):
        results={i:self.run_assignment(i,html='<title>Guide</title><main>Water help</main>') for i in range(1,12)}
        expected={1:'extracted_text',2:'tokens',3:'english',4:'pos_embedding_classifier',5:'items',6:'top_features',7:'ngram_counts',8:'terms',9:'related_guidance',10:'topic_opinion',11:'draft'}
        for number,key in expected.items():self.assertIn(key,results[number])
        self.assertIn('stems',results[3]['english']);self.assertEqual(results[6]['training_messages'],1331)
        self.assertEqual(sum(t['documents'] for t in results[9]['topics']),90)
        self.assertEqual(results[7]['training_messages'],30);self.assertTrue(results[8]['probability']>0)
        self.assertEqual(results[10]['sentiment']['tone'],'negative')
    def test_html_demo_does_not_execute_or_fetch_and_removes_noncontent(self):
        with patch('requests.get',side_effect=AssertionError('Must remain offline')):
            result=self.run_assignment(1,html='<title>Guide</title><nav>Ignore</nav><main>पाणी मदत<script>alert(1)</script></main>')
        self.assertEqual(result['extracted_text'],'पाणी मदत');self.assertFalse(result['network_request_made'])
        self.assertIn('scripts/scrape.py',result['live_command'])
    def test_assignment_two_uses_civic_corpus_and_unicode(self):
        result=self.run_assignment(2,text='पाणी येत नाही। मदत करा।',lang='mr')
        self.assertEqual(result['tokens'],['पाणी','येत','नाही','मदत','करा']);self.assertEqual(result['sentence_count'],2)
        with patch('assignment_lab.summarize',return_value={'message_count':1331}) as summarize:
            self.assertEqual(self.run_assignment(2,corpus=True)['message_count'],1331)
            self.assertEqual(summarize.call_args.args[0].name,'service_train.json')
    def test_english_only_tasks_are_not_fabricated_for_indic(self):
        for lang in ('hi','mr'):
            norm=self.run_assignment(3,text='पाणी येत नाही।',lang=lang)['english']
            self.assertNotIn('lemmas',norm);self.assertNotIn('pos',norm)
            self.assertIn('English-only',self.run_assignment(4,lang=lang)['pos_embedding_classifier']['status'])
    def test_pipeline_matches_public_analysis_without_saving(self):
        data=dict(text='The streetlight is not working.',lang='en',location='Pimpri')
        demo=self.run_assignment(11,**data);real=self.client.post('/api/analyze',json=data).get_json()
        self.assertEqual(demo,real);self.assertIn('Pimpri',demo['draft'])
        self.assertEqual(self.client.get('/api/drafts').get_json(),[])
    def test_selected_ngram_order_and_validation(self):
        for n in (1,2,3):
            result=self.run_assignment(7,n=n);self.assertEqual(result['n'],n)
            self.assertTrue(all(len(x['context'])==n-1 for x in result['ngram_counts']))
            self.assertEqual(self.run_assignment(8,n=n)['n'],n)
        cases=[(0,{}),(12,{}),(2,{'text':''}),(2,{'lang':'bad'}),(8,{'n':True}),(8,{'n':4}),(2,{'corpus':'yes'}),(1,{'html':''}),(1,{'html':'x'*20001})]
        for number,extra in cases:
            self.assertEqual(self.client.post(f'/api/assignments/{number}/run',json={'text':'water issue','lang':'en',**extra}).status_code,400)
        self.assertEqual(self.client.post('/api/assignments/1/run',json={'html':'<p>test</p>'},headers={'Origin':'https://evil.example'}).status_code,403)
if __name__=='__main__':unittest.main()
