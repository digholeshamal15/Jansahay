import csv
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from PIL import Image
from app import app, database
from unittest.mock import patch
from service_model import load_service

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        app.config.update(TESTING=True,DATABASE=str(self.root/'tracker.sqlite'),UPLOAD_DIR=str(self.root/'photos'))
        self.client=app.test_client()
    def tearDown(self):self.temp.cleanup()
    def create(self,**changes):
        data={'body':'Please inspect the water supply.','issue':'No water for two days.','category':'water','lang':'en','location':'Pimpri','municipality':'pcmc','status':'ready'}
        data.update(changes)
        response=self.client.post('/api/drafts',json=data)
        self.assertEqual(response.status_code,201,response.get_data(as_text=True))
        return response.get_json()['id']
    def photo(self,filename='photo.png'):
        buffer=io.BytesIO();Image.new('RGB',(12,12),'red').save(buffer,format='PNG');buffer.seek(0)
        return self.client.post('/api/photos',data={'photo':(buffer,filename)},content_type='multipart/form-data')
    def test_legacy_migration_preserves_drafts_and_ids(self):
        db=sqlite3.connect(app.config['DATABASE'])
        db.execute('CREATE TABLE drafts (id INTEGER PRIMARY KEY, category TEXT, lang TEXT, location TEXT, body TEXT, created TEXT)')
        db.execute('INSERT INTO drafts VALUES(7,?,?,?,?,?)',('water','mr','पुणे','जुनी तक्रार','2025-01-01'))
        db.commit();db.close()
        for _ in range(2):
            rows=self.client.get('/api/drafts').get_json()
            self.assertEqual(len(rows),1);self.assertEqual(rows[0]['id'],7)
            self.assertEqual(rows[0]['body'],'जुनी तक्रार');self.assertEqual(rows[0]['status'],'draft')
            self.assertEqual(rows[0]['reference'],'');self.assertEqual(rows[0]['photos'],[])
    def test_followup_reference_dates_and_history(self):
        idx=self.create()
        response=self.client.patch(f'/api/drafts/{idx}',json={'status':'submitted','reference':'PCMC-123','submitted_on':'2026-10-22','note':'Submitted on the official portal.'})
        self.assertEqual(response.status_code,200)
        self.client.patch(f'/api/drafts/{idx}',json={'status':'follow_up','note':'Called the service desk.'})
        record=self.client.get(f'/api/drafts/{idx}').get_json()
        self.assertEqual(record['reference'],'PCMC-123');self.assertEqual(record['submitted_on'],'2026-10-22')
        self.assertEqual(record['status'],'follow_up');self.assertEqual(len(record['history']),3)
        self.assertEqual(record['history'][-1]['note'],'Called the service desk.')
        self.assertEqual(self.client.patch(f'/api/drafts/{idx}',json={'status':'resolved'}).status_code,200)
    def test_portal_handoff_never_marks_submission(self):
        idx=self.create()
        before=self.client.get(f'/api/drafts/{idx}').get_json()
        response=self.client.post(f'/api/drafts/{idx}/handoff',json={})
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.get_json()['submitted']);self.assertEqual(response.get_json()['url'],'https://www.pcmchelpline.in/')
        after=self.client.get(f'/api/drafts/{idx}').get_json()
        for key in ('body','status','reference','submitted_on'):self.assertEqual(before[key],after[key])
        self.assertEqual(after['history'][-1]['action'],'portal_handoff')
        other=self.create(municipality='unknown')
        self.assertEqual(self.client.post(f'/api/drafts/{other}/handoff',json={}).status_code,400)
    def test_all_five_categories_and_other_in_three_languages(self):
        for lang in ('en','hi','mr'):
            for category in ('water','garbage','roads','lights','drainage','other'):
                with self.subTest(lang=lang,category=category):
                    r=self.client.post('/api/analyze',json={'text':'My original issue.','lang':lang,'category':category,'location':'Pune'})
                    self.assertEqual(r.status_code,200);self.assertEqual(r.get_json()['category'],category)
                    self.assertIn('My original issue.',r.get_json()['draft'])
    def test_optional_facts_are_only_included_when_provided(self):
        data={'text':'The light is broken.','category':'lights','details':{'duration':'since Monday','answers':{'light_count':'two lights'}}}
        r=self.client.post('/api/analyze',json=data).get_json()
        self.assertIn('since Monday',r['draft']);self.assertIn('two lights',r['draft'])
        r=self.client.post('/api/analyze',json={'text':'The light is broken.','category':'lights'}).get_json()
        self.assertNotIn('since Monday',r['draft']);self.assertNotIn('two lights',r['draft'])
        self.assertNotIn('Recurring problem:',r['draft'])
    def test_search_and_exports_with_history_and_unicode(self):
        idx=self.create(body='पाणी येत नाही।',location='पिंपरी',reference='=1+1')
        self.assertEqual(len(self.client.get('/api/drafts?q=पिंपरी&status=ready').get_json()),1)
        self.assertEqual(self.client.get('/api/drafts?q=not-present').get_json(),[])
        response=self.client.get('/api/drafts/export?format=json')
        record=response.get_json()['complaints'][0]
        self.assertEqual(record['id'],idx);self.assertIn('history',record);self.assertEqual(record['body'],'पाणी येत नाही।')
        self.assertIn('attachment',response.headers['Content-Disposition'])
        rows=list(csv.DictReader(io.StringIO(self.client.get('/api/drafts/export?format=csv').get_data(as_text=True).lstrip('\ufeff'))))
        self.assertEqual(rows[0]['reference'],"'=1+1")
    def test_photo_validation_safe_storage_and_delete_cascade(self):
        response=self.photo('../../unsafe.png');self.assertEqual(response.status_code,201)
        photo=response.get_json();files=list((self.root/'photos').iterdir())
        self.assertEqual(files[0].name,photo['id']+'.jpg');self.assertFalse((self.root/'unsafe.png').exists())
        served=self.client.get(photo['url']);self.assertEqual(served.mimetype,'image/jpeg')
        image=Image.open(io.BytesIO(served.data));self.assertFalse(image.getexif());served.close()
        idx=self.create(photo_ids=[photo['id']])
        self.assertEqual(len(self.client.get(f'/api/drafts/{idx}').get_json()['photos']),1)
        self.assertEqual(self.client.delete(f'/api/drafts/{idx}').status_code,200)
        self.assertFalse(files[0].exists());self.assertEqual(self.client.get(photo['url']).status_code,404)
        with database() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM history').fetchone()[0],0)
    def test_invalid_uploads_rejected(self):
        cases=[('bad.png',b'<html>not an image</html>'),('bad.svg',b'<svg/>'),('bad.jpg',b'GIF89a'),('huge.png',b'x'*(5*1024*1024+1))]
        for name,content in cases:
            with self.subTest(name=name):
                response=self.client.post('/api/photos',data={'photo':(io.BytesIO(content),name)},content_type='multipart/form-data')
                self.assertIn(response.status_code,(400,413))
        self.assertFalse(list((self.root/'photos').glob('*')))
    def test_photo_count_and_cross_complaint_linking(self):
        photos=[self.photo().get_json()['id'] for _ in range(4)]
        response=self.client.post('/api/drafts',json={'body':'hello','category':'other','photo_ids':photos})
        self.assertEqual(response.status_code,400);self.assertEqual(self.client.get('/api/drafts').get_json(),[])
        self.create(photo_ids=photos[:1])
        response=self.client.post('/api/drafts',json={'body':'other record','photo_ids':photos[:1]})
        self.assertEqual(response.status_code,400)
    def test_invalid_status_date_details_and_origin(self):
        idx=self.create()
        for data in ({'status':'automatically_verified'},{'submitted_on':'2026-02-31'},{'details':{'recurring':False}},{'note':'x'*1501}):
            self.assertEqual(self.client.patch(f'/api/drafts/{idx}',json=data).status_code,400)
        self.assertEqual(self.client.patch(f'/api/drafts/{idx}',json={'status':'resolved'},headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/photos',data={},headers={'Origin':'https://evil.example'}).status_code,403)
    def test_partial_model_download_falls_back_to_training_data(self):
        with patch('service_model.joblib.load',side_effect=ValueError('truncated model')):
            vectorizer,classifier,x,rows,info=load_service()
        self.assertGreater(len(rows),90)
        self.assertEqual(info['mode'],'fitted locally from bundled training rows')
        self.assertEqual(classifier.predict(vectorizer.transform(['The streetlight near our house is not working']))[0],'lights')
    def test_directory_uses_reviewed_https_links(self):
        rows=self.client.get('/api/authorities').get_json()
        self.assertEqual({a['id'] for a in rows},{'pcmc','pmc','maharashtra'})
        for row in rows:
            self.assertTrue(row['url'].startswith('https://'));self.assertIn('gov.in',row['source_url']);self.assertEqual(row['verified_on'],'2026-10-22')

if __name__=='__main__':unittest.main()
