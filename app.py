"""Run: python app.py. Local Flask app; no government submission/status API."""
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
from uuid import uuid4
import csv
import io
import json
import os
import warnings
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, UnidentifiedImageError
from i18n import COPY, CATEGORIES, CHECKLISTS, NAMES, TONES, EXAMPLES
from product_copy import UI, SAMPLES
from workflow import (AUTHORITIES, AUTHORITY_MAP, STATUSES, OTHER, QUESTIONS, DETAIL_LABELS,
                      migrate, text_value, details_value, valid_date, record_dict, now)
from nlp import Engine, language_hint, sentiment
from assignment_lab import CATALOG, run_assignment

from contextlib import contextmanager
from engine.pipeline import UnifiedNLPEngine
from engine.narrative_graph import NarrativeGraphEngine
from engine.ingestion import (
    parse_csv_content, parse_txt_content, scrape_web_page,
    load_bundled_service_dataset, load_huffpost_sample, check_duplicate, calculate_sha256
)
from engine.classification import CATEGORIES_9

ROOT=Path(__file__).parent
app=Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=6*1024*1024,DATABASE=str(ROOT/'instance/drafts.sqlite3'),UPLOAD_DIR=str(ROOT/'instance/photos'))
engine=Engine()
unified_engine=UnifiedNLPEngine()
ALL_CATEGORIES={**CATEGORIES,'other':OTHER}
MAX_PHOTO_BYTES=5*1024*1024
Image.MAX_IMAGE_PIXELS=16_000_000

@contextmanager
def database():
    db = migrate(app.config['DATABASE'])
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def payload():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):raise ValueError('JSON object required')
    return data

def choice(data,key,options,default):
    value=data.get(key,default)
    if not isinstance(value,str) or value not in options:raise ValueError(f'Invalid {key}')
    return value

def photo_ids(data):
    ids=data.get('photo_ids',[])
    if not isinstance(ids,list) or len(ids)>3 or any(not isinstance(i,str) or len(i)!=32 for i in ids) or len(set(ids))!=len(ids):
        raise ValueError('Use at most three distinct photo IDs')
    return ids

def link_photos(db,draft_id,ids):
    for photo_id in ids:
        row=db.execute('SELECT draft_id FROM photos WHERE id=?',(photo_id,)).fetchone()
        if row is None or row['draft_id'] not in (None,draft_id):raise ValueError('Photo is missing or belongs to another complaint')
    existing=db.execute('SELECT COUNT(*) FROM photos WHERE draft_id=?',(draft_id,)).fetchone()[0]
    added=sum(db.execute('SELECT draft_id FROM photos WHERE id=?',(i,)).fetchone()['draft_id'] is None for i in ids)
    if existing+added>3:raise ValueError('At most three photos per complaint')
    for photo_id in ids:db.execute('UPDATE photos SET draft_id=? WHERE id=?',(draft_id,photo_id))

@app.before_request
def local_only():
    if urlsplit(request.host_url).hostname not in ('127.0.0.1','localhost','::1'):
        return jsonify(error='Localhost access only'),403
    if request.is_json and (request.content_length or 0)>64*1024:return jsonify(error='JSON request too large'),413
    if request.method in ('POST','DELETE','PUT','PATCH'):
        origin=request.headers.get('Origin')
        if origin and origin.rstrip('/')!=request.host_url.rstrip('/'):
            return jsonify(error='Origin not allowed'),403

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    if request.path.startswith('/api/'):response.headers['Cache-Control']='no-store'
    return response

@app.errorhandler(ValueError)
def invalid(error):return jsonify(error=str(error)),400
@app.errorhandler(413)
def too_large(error):return jsonify(error='Upload/request too large. Each photo must be at most 5 MB.'),413

@app.get('/')
def index():return render_template('index.html')
@app.get('/api/config')
def config():return jsonify(copy=COPY,ui=UI,samples=SAMPLES,categories=ALL_CATEGORIES,categories_9=CATEGORIES_9,names=NAMES,examples=EXAMPLES,questions=QUESTIONS,authorities=AUTHORITIES,statuses=STATUSES)
@app.get('/api/authorities')
def authorities():return jsonify(AUTHORITIES)

@app.post('/api/analyze')
def analyze():
    return analyze_data(payload())

def analyze_data(data):
    text=text_value(data,'text',required=True);location=text_value(data,'location',160)
    lang=choice(data,'lang',COPY,'en');text_lang=choice(data,'text_lang',COPY,lang)
    category=choice(data,'category',['auto',*ALL_CATEGORIES],'auto')
    municipality=choice(data,'municipality',['unknown',*AUTHORITY_MAP],'unknown')
    details=details_value(data.get('details',{}))
    result=engine.classify(text);selected=result['category'] if category=='auto' else category
    c=COPY[lang];draft=''
    if selected:
        title=ALL_CATEGORIES[selected][lang]
        facts=[];labels=DETAIL_LABELS[lang]
        for key in ('landmark','duration','recurring','extra'):
            value=details.get(key,'')
            if value:
                if key=='recurring':value=labels[value]
                facts.append(f'{labels[key]}: {value}')
        question=QUESTIONS.get(selected)
        if question and details['answers'].get(question['id']):facts.append(f"{question['label'][lang]}: {details['answers'][question['id']]}")
        recipient=AUTHORITY_MAP[municipality]['name'][lang] if municipality!='unknown' else ''
        body=f"{c['dept']}\n{recipient}".strip()
        draft=f"{body}\n\n{c['subject']}: {c['draft_title']} — {title}\n{c['place']}: {location or '____________'}\n\n{c['details']}:\n{text}"
        if facts:draft+='\n\n'+'\n'.join(facts)
        draft+=f"\n\n{c['request']}\n\n{c['thanks']}"
    tone=sentiment(text)
    return jsonify(category=selected,category_name=ALL_CATEGORIES[selected][lang] if selected else c['unknown'],chosen_by='model' if category=='auto' else 'user',classification=result,draft=draft,checklist=CHECKLISTS[lang],language_hint=language_hint(text),tone=TONES[tone['tone']][lang],related=engine.related(text,text_lang),guidance=c['generic'])

@app.post('/api/lab')
def lab():
    data=payload();text=text_value(data,'text',required=True);lang=choice(data,'lang',COPY,'en');n=data.get('n',2)
    if type(n) is not int or n not in (1,2,3):raise ValueError('n must be 1, 2 or 3')
    result=engine.inspect(text,lang,n)
    result['related_guidance']=engine.related(text,lang)
    return jsonify(result)
@app.get('/api/assignments')
def assignments():
    return jsonify(CATALOG)

@app.post('/api/assignments/<int:number>/run')
def assignment_run(number):
    if number not in range(1,12):raise ValueError('Unknown assignment')
    data=payload();lang=choice(data,'lang',COPY,'en')
    text=text_value(data,'text',required=number!=1)
    n=data.get('n',2)
    if type(n) is not int or n not in (1,2,3):raise ValueError('n must be 1, 2 or 3')
    corpus=data.get('corpus',False)
    if type(corpus) is not bool:raise ValueError('corpus must be true or false')
    html=text_value(data,'html',20000,required=number==1)
    pipeline=analyze_data(data).get_json() if number==11 else None
    return jsonify(assignment=number,result=run_assignment(number,engine,text,lang,n,html,corpus,pipeline))

@app.get('/api/topics')
def topics():return jsonify(engine.topics())

def filtered_records(db,history=False):
    query=request.args.get('q','').strip()
    if len(query)>200:raise ValueError('Search is too long')
    status=request.args.get('status','all')
    if status not in ('all',*STATUSES):raise ValueError('Invalid status filter')
    terms=[];args=[]
    if query:
        needle='%'+query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        terms.append("(body LIKE ? ESCAPE '\\' OR location LIKE ? ESCAPE '\\' OR reference LIKE ? ESCAPE '\\' OR issue LIKE ? ESCAPE '\\')");args.extend([needle]*4)
    if status!='all':terms.append('status=?');args.append(status)
    sql='SELECT * FROM drafts'+(' WHERE '+' AND '.join(terms) if terms else '')+' ORDER BY id DESC'
    return [record_dict(db,row,history) for row in db.execute(sql,args)]

@app.get('/api/drafts')
def drafts():
    with database() as db:return jsonify(filtered_records(db))
@app.get('/api/drafts/<int:draft_id>')
def get_record(draft_id):
    with database() as db:
        row=db.execute('SELECT * FROM drafts WHERE id=?',(draft_id,)).fetchone()
        return (jsonify(record_dict(db,row,True)),200) if row else (jsonify(error='Complaint not found'),404)

@app.post('/api/drafts')
def save():
    data=payload();body=text_value(data,'body',12000,True);location=text_value(data,'location',160)
    category=choice(data,'category',ALL_CATEGORIES,'other');lang=choice(data,'lang',COPY,'en')
    status=choice(data,'status',STATUSES,'draft');municipality=choice(data,'municipality',['unknown',*AUTHORITY_MAP],'unknown')
    issue=text_value(data,'issue');details=details_value(data.get('details',{}));ids=photo_ids(data)
    reference=text_value(data,'reference',120);submitted=valid_date(text_value(data,'submitted_on',10))
    stamp=now()
    with database() as db:
        cursor=db.execute('INSERT INTO drafts(category,lang,location,body,created,status,reference,issue,municipality,details_json,submitted_on,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(category,lang,location,body,stamp,status,reference,issue,municipality,json.dumps(details,ensure_ascii=False),submitted,stamp))
        idx=cursor.lastrowid;link_photos(db,idx,ids)
        db.execute('INSERT INTO history(draft_id,action,new_status,created) VALUES(?,?,?,?)',(idx,'created',status,stamp))
    return jsonify(id=idx,status=status),201

@app.patch('/api/drafts/<int:draft_id>')
def update_record(draft_id):
    data=payload();changes={}
    if not data:raise ValueError('No changes supplied')
    for key,limit in [('body',12000),('location',160),('reference',120),('issue',3000)]:
        if key in data:changes[key]=text_value(data,key,limit,key=='body')
    if 'status' in data:changes['status']=choice(data,'status',STATUSES,'draft')
    if 'category' in data:changes['category']=choice(data,'category',ALL_CATEGORIES,'other')
    if 'lang' in data:changes['lang']=choice(data,'lang',COPY,'en')
    if 'municipality' in data:changes['municipality']=choice(data,'municipality',['unknown',*AUTHORITY_MAP],'unknown')
    if 'submitted_on' in data:changes['submitted_on']=valid_date(text_value(data,'submitted_on',10))
    if 'details' in data:changes['details_json']=json.dumps(details_value(data['details']),ensure_ascii=False)
    note=text_value(data,'note',1500);ids=photo_ids(data) if 'photo_ids' in data else None
    if not changes and not note and ids is None:raise ValueError('No supported changes supplied')
    with database() as db:
        old=db.execute('SELECT * FROM drafts WHERE id=?',(draft_id,)).fetchone()
        if old is None:return jsonify(error='Complaint not found'),404
        changed={k:v for k,v in changes.items() if old[k]!=v}
        if changed:
            changed['updated']=now()
            db.execute('UPDATE drafts SET '+','.join(k+'=?' for k in changed)+' WHERE id=?',[*changed.values(),draft_id])
        if ids is not None:link_photos(db,draft_id,ids)
        if changed or note:
            db.execute('INSERT INTO history(draft_id,action,old_status,new_status,note,created) VALUES(?,?,?,?,?,?)',(draft_id,'updated',old['status'],changes.get('status',old['status']),note,now()))
    return jsonify(updated=True)

@app.post('/api/drafts/<int:draft_id>/handoff')
def handoff(draft_id):
    with database() as db:
        row=db.execute('SELECT * FROM drafts WHERE id=?',(draft_id,)).fetchone()
        if row is None:return jsonify(error='Complaint not found'),404
        authority=AUTHORITY_MAP.get(row['municipality'])
        if not authority:raise ValueError('Choose a municipality before opening an official channel')
        # Deliberately records only a portal handoff. No status/date/reference changes.
        db.execute('INSERT INTO history(draft_id,action,old_status,new_status,note,created) VALUES(?,?,?,?,?,?)',(draft_id,'portal_handoff',row['status'],row['status'],authority['url'],now()))
        return jsonify(url=authority['url'],status=row['status'],submitted=False)

@app.delete('/api/drafts/<int:draft_id>')
def delete(draft_id):
    with database() as db:
        files=[p['storage_name'] for p in db.execute('SELECT storage_name FROM photos WHERE draft_id=?',(draft_id,))]
        cursor=db.execute('DELETE FROM drafts WHERE id=?',(draft_id,))
    if not cursor.rowcount:return jsonify(error='Complaint not found'),404
    for filename in files:(Path(app.config['UPLOAD_DIR'])/filename).unlink(missing_ok=True)
    return jsonify(deleted=True)

@app.get('/api/drafts/export')
def export_records():
    with database() as db:rows=filtered_records(db,True)
    format=request.args.get('format','json')
    if format=='json':
        output=json.dumps({'exported_at':now(),'status_source':'User-recorded local statuses; not verified government status','complaints':rows},ensure_ascii=False,indent=2)
        return app.response_class(output,mimetype='application/json',headers={'Content-Disposition':'attachment; filename="JanSahay-complaints.json"'})
    if format!='csv':raise ValueError('Export format must be json or csv')
    stream=io.StringIO();writer=csv.writer(stream)
    keys=['id','category','lang','municipality','location','status','reference','submitted_on','body']
    writer.writerow(keys)
    for row in rows:
        values=[]
        for key in keys:
            value=str(row.get(key,''))
            if value.lstrip().startswith(('=','+','-','@')):value="'"+value
            values.append(value)
        writer.writerow(values)
    return app.response_class('\ufeff'+stream.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename="JanSahay-complaints.csv"'})

@app.post('/api/photos')
def upload_photo():
    file=request.files.get('photo')
    if file is None or not file.filename:raise ValueError('Choose a photograph')
    if Path(file.filename).suffix.lower() not in ('.jpg','.jpeg','.png','.webp'):raise ValueError('Use a JPG, PNG or WebP photograph')
    data=file.stream.read(MAX_PHOTO_BYTES+1)
    if not data or len(data)>MAX_PHOTO_BYTES:raise ValueError('Each photo must be 1 byte to 5 MB')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            image=Image.open(io.BytesIO(data))
            if image.format not in ('JPEG','PNG','WEBP'):raise ValueError('Unsupported image content')
            image.verify()
            source=Image.open(io.BytesIO(data));source.load()
            if source.width*source.height>16_000_000:raise ValueError('Photo must be at most 16 megapixels')
            # Re-encode pixels, removing filename, EXIF/GPS and embedded metadata.
            clean=Image.new('RGB',source.size,'white')
            if source.mode in ('RGBA','LA'):
                rgba=source.convert('RGBA');clean.paste(rgba,mask=rgba.getchannel('A'))
            else:clean.paste(source.convert('RGB'))
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as e:
        raise ValueError('This file is not a valid, safely sized photograph') from e
    idx=uuid4().hex;filename=idx+'.jpg';folder=Path(app.config['UPLOAD_DIR']);folder.mkdir(parents=True,exist_ok=True)
    clean.save(folder/filename,format='JPEG',quality=88)
    try:
        with database() as db:db.execute('INSERT INTO photos(id,storage_name,created) VALUES(?,?,?)',(idx,filename,now()))
    except Exception:
        (folder/filename).unlink(missing_ok=True);raise
    return jsonify(id=idx,url=f'/api/photos/{idx}'),201

@app.get('/api/photos/<photo_id>')
def photo(photo_id):
    with database() as db:row=db.execute('SELECT storage_name FROM photos WHERE id=?',(photo_id,)).fetchone()
    if row is None:return jsonify(error='Photo not found'),404
    return send_file(Path(app.config['UPLOAD_DIR'])/row['storage_name'],mimetype='image/jpeg',max_age=0)
@app.delete('/api/photos/<photo_id>')
def remove_photo(photo_id):
    with database() as db:
        row=db.execute('SELECT * FROM photos WHERE id=?',(photo_id,)).fetchone()
        if row is None:return jsonify(error='Photo not found'),404
        db.execute('DELETE FROM photos WHERE id=?',(photo_id,))
        if row['draft_id'] is not None:db.execute('INSERT INTO history(draft_id,action,note,created) VALUES(?,?,?,?)',(row['draft_id'],'photo_removed','Supporting photo removed',now()))
    (Path(app.config['UPLOAD_DIR'])/row['storage_name']).unlink(missing_ok=True)
    return jsonify(deleted=True)

def ensure_seed_documents():
    """Populate initial representative incident reports & news if documents table is empty."""
    with database() as db:
        count = db.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
        if count == 0:
            seeds = load_huffpost_sample() + load_bundled_service_dataset(limit=16)
            for item in seeds:
                doc_id = item.get('id') or uuid4().hex[:12]
                analysis = unified_engine.analyze_document(item['text'], item.get('lang', 'en'), item.get('category', 'other'))
                db.execute(
                    'INSERT OR IGNORE INTO documents(id, title, text, category, location, lang, source, source_type, created_at, sha256, metadata_json) '
                    'VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                    (doc_id, item.get('title', item['text'][:50]), item['text'],
                     analysis['classification']['category'], item.get('location', 'unknown'),
                     item.get('lang', 'en'), item.get('source', 'Bundled'), item.get('source_type', 'seed'),
                     item.get('created_at', now()), item.get('sha256', calculate_sha256(item['text'])),
                     json.dumps(item.get('metadata', {})))
                )
                db.execute(
                    'INSERT OR REPLACE INTO analysis_cache(doc_id, analysis_json, updated) VALUES(?,?,?)',
                    (doc_id, json.dumps(analysis), now())
                )

def fetch_stored_documents(db, limit=300):
    rows = db.execute('SELECT * FROM documents ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    docs = []
    for r in rows:
        d = dict(r)
        try: d['metadata'] = json.loads(d.get('metadata_json', '{}'))
        except: d['metadata'] = {}
        cache_row = db.execute('SELECT analysis_json FROM analysis_cache WHERE doc_id=?', (d['id'],)).fetchone()
        if cache_row:
            try:
                c = json.loads(cache_row['analysis_json'])
                d['tone'] = c.get('sentiment_analysis', {}).get('tone', 'neutral')
                d['polarity'] = c.get('sentiment_analysis', {}).get('polarity_score', 0.0)
                d['entities'] = c.get('entities', {}).get('entities', [])
                d['confidence'] = c.get('classification', {}).get('confidence', 0.0)
                d['emerging_risks'] = c.get('emerging_risks', [])
            except:
                pass
        docs.append(d)
    return docs

@app.get('/api/overview')
def intelligence_overview():
    ensure_seed_documents()
    with database() as db:
        docs = fetch_stored_documents(db, limit=300)
    analytics = unified_engine.run_corpus_analytics(docs)
    analytics['evaluation_metrics'] = unified_engine.classifier.evaluation_metrics
    return jsonify(analytics)

@app.get('/api/documents')
def list_documents():
    ensure_seed_documents()
    with database() as db:
        docs = fetch_stored_documents(db, limit=300)
    q = request.args.get('q', '').strip().lower()
    cat = request.args.get('category', 'all')
    tone = request.args.get('sentiment', 'all')
    lang_filter = request.args.get('lang', 'all')
    
    filtered = []
    for d in docs:
        if q and (q not in d['text'].lower() and q not in d['title'].lower() and q not in d.get('location', '').lower()):
            continue
        if cat != 'all' and d['category'] != cat:
            continue
        if tone != 'all' and d.get('tone') != tone:
            continue
        if lang_filter != 'all' and d.get('lang') != lang_filter:
            continue
        filtered.append(d)
    return jsonify(filtered)

@app.post('/api/documents')
def create_document():
    data = payload()
    text = text_value(data, 'text', limit=12000, required=True)
    title = data.get('title', '').strip() or (text[:60] + '...')
    category = data.get('category', 'auto')
    location = data.get('location', '').strip() or 'unknown'
    doc_lang = data.get('lang', 'en')
    source = data.get('source', '').strip() or 'Manual Entry'
    
    with database() as db:
        existing = fetch_stored_documents(db)
        dup = check_duplicate(text, existing)
        doc_id = uuid4().hex[:12]
        analysis = unified_engine.analyze_document(text, doc_lang, category)
        final_cat = analysis['classification']['category']
        
        db.execute(
            'INSERT INTO documents(id, title, text, category, location, lang, source, source_type, created_at, sha256, metadata_json) '
            'VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            (doc_id, title[:160], text, final_cat, location[:120], doc_lang, source[:120], 'manual_entry', now(), calculate_sha256(text), json.dumps({'is_duplicate': dup['is_duplicate']}))
        )
        db.execute(
            'INSERT OR REPLACE INTO analysis_cache(doc_id, analysis_json, updated) VALUES(?,?,?)',
            (doc_id, json.dumps(analysis), now())
        )
    return jsonify(id=doc_id, title=title, category=final_cat, duplicate_info=dup, analysis=analysis), 201

@app.get('/api/documents/<doc_id>')
def get_document(doc_id):
    with database() as db:
        row = db.execute('SELECT * FROM documents WHERE id=?', (doc_id,)).fetchone()
        if not row:
            return jsonify(error='Document not found'), 404
        doc = dict(row)
        cache_row = db.execute('SELECT analysis_json FROM analysis_cache WHERE doc_id=?', (doc_id,)).fetchone()
        if cache_row:
            try: analysis = json.loads(cache_row['analysis_json'])
            except: analysis = None
        else:
            analysis = None
        if analysis is None:
            analysis = unified_engine.analyze_document(doc['text'], doc['lang'], doc['category'])
            db.execute('INSERT OR REPLACE INTO analysis_cache(doc_id, analysis_json, updated) VALUES(?,?,?)', (doc_id, json.dumps(analysis), now()))
    return jsonify(document=doc, analysis=analysis)

@app.delete('/api/documents/<doc_id>')
def delete_document(doc_id):
    with database() as db:
        cursor = db.execute('DELETE FROM documents WHERE id=?', (doc_id,))
        if cursor.rowcount == 0:
            return jsonify(error='Document not found'), 404
    return jsonify(deleted=True)

@app.post('/api/documents/upload')
def upload_document_file():
    file = request.files.get('file')
    if file is None or not file.filename:
        raise ValueError('Please choose a CSV or TXT file to upload')
    ext = Path(file.filename).suffix.lower()
    if ext not in ('.csv', '.txt'):
        raise ValueError('Only .csv and .txt files are supported')
    content = file.stream.read(4*1024*1024).decode('utf-8', errors='replace')
    
    if ext == '.csv':
        items = parse_csv_content(content)
    else:
        items = parse_txt_content(content, filename=file.filename)
        
    if not items:
        raise ValueError('No readable text records found in the uploaded file')
        
    imported = 0
    duplicates = 0
    with database() as db:
        existing = fetch_stored_documents(db)
        for item in items[:40]:
            dup = check_duplicate(item['text'], existing)
            if dup['is_duplicate']:
                duplicates += 1
                continue
            doc_id = uuid4().hex[:12]
            analysis = unified_engine.analyze_document(item['text'], item.get('lang', 'en'), item.get('category', 'auto'))
            final_cat = analysis['classification']['category']
            db.execute(
                'INSERT INTO documents(id, title, text, category, location, lang, source, source_type, created_at, sha256, metadata_json) '
                'VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (doc_id, item.get('title', item['text'][:50]), item['text'], final_cat, item.get('location', 'unknown'),
                 item.get('lang', 'en'), item.get('source', file.filename), f"file_upload_{ext[1:]}", now(), item['sha256'],
                 json.dumps(item.get('metadata', {})))
            )
            db.execute(
                'INSERT OR REPLACE INTO analysis_cache(doc_id, analysis_json, updated) VALUES(?,?,?)',
                (doc_id, json.dumps(analysis), now())
            )
            imported += 1
            existing.append({'id': doc_id, 'text': item['text'], 'sha256': item['sha256']})
            
    return jsonify(imported_count=imported, duplicates_skipped=duplicates, total_rows=len(items)), 201

@app.post('/api/documents/scrape')
def scrape_document():
    data = payload()
    url = data.get('url', '').strip()
    if not url:
        raise ValueError('URL is required')
    item = scrape_web_page(url)
    with database() as db:
        existing = fetch_stored_documents(db)
        dup = check_duplicate(item['text'], existing)
        doc_id = uuid4().hex[:12]
        analysis = unified_engine.analyze_document(item['text'], item.get('lang', 'en'), 'auto')
        final_cat = analysis['classification']['category']
        db.execute(
            'INSERT INTO documents(id, title, text, category, location, lang, source, source_type, created_at, sha256, metadata_json) '
            'VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            (doc_id, item['title'], item['text'], final_cat, item['location'], item['lang'], url, 'web_scrape', now(), item['sha256'],
             json.dumps({'url': url, 'is_duplicate': dup['is_duplicate']}))
        )
        db.execute(
            'INSERT OR REPLACE INTO analysis_cache(doc_id, analysis_json, updated) VALUES(?,?,?)',
            (doc_id, json.dumps(analysis), now())
        )
    return jsonify(id=doc_id, title=item['title'], category=final_cat, is_duplicate=dup['is_duplicate'], analysis=analysis), 201

@app.post('/api/documents/import-dataset')
def import_dataset():
    data = payload()
    dataset_name = data.get('dataset', 'civic')
    limit = int(data.get('limit', 20))
    limit = max(1, min(limit, 50))
    
    if dataset_name == 'huffpost':
        items = load_huffpost_sample()
    elif dataset_name == 'civic':
        items = load_bundled_service_dataset(limit=limit)
    else:
        raise ValueError("Invalid dataset. Choose 'civic' or 'huffpost'.")
        
    imported = 0
    with database() as db:
        existing = fetch_stored_documents(db)
        for item in items:
            dup = check_duplicate(item['text'], existing)
            if dup['is_duplicate']:
                continue
            doc_id = item.get('id') or uuid4().hex[:12]
            analysis = unified_engine.analyze_document(item['text'], item.get('lang', 'en'), item.get('category', 'auto'))
            final_cat = analysis['classification']['category']
            db.execute(
                'INSERT OR IGNORE INTO documents(id, title, text, category, location, lang, source, source_type, created_at, sha256, metadata_json) '
                'VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (doc_id, item.get('title', item['text'][:50]), item['text'], final_cat, item.get('location', 'unknown'),
                 item.get('lang', 'en'), item.get('source', dataset_name), f"dataset_{dataset_name}", now(), item['sha256'],
                 json.dumps(item.get('metadata', {})))
            )
            db.execute(
                'INSERT OR REPLACE INTO analysis_cache(doc_id, analysis_json, updated) VALUES(?,?,?)',
                (doc_id, json.dumps(analysis), now())
            )
            imported += 1
            existing.append({'id': doc_id, 'text': item['text'], 'sha256': item['sha256']})
            
    return jsonify(imported_count=imported, dataset=dataset_name), 201

@app.get('/api/narrative-graph')
def narrative_graph():
    ensure_seed_documents()
    with database() as db:
        docs = fetch_stored_documents(db)
    graph = NarrativeGraphEngine(docs).build_graph()
    return jsonify(graph)

@app.get('/api/contradictions')
def contradictions():
    ensure_seed_documents()
    with database() as db:
        docs = fetch_stored_documents(db)
    items = NarrativeGraphEngine(docs).detect_contradictions()
    return jsonify(items)

@app.get('/api/opinions')
def opinions():
    ensure_seed_documents()
    all_opinions = []
    with database() as db:
        docs = fetch_stored_documents(db)
        for d in docs:
            cache_row = db.execute('SELECT analysis_json FROM analysis_cache WHERE doc_id=?', (d['id'],)).fetchone()
            if cache_row:
                try:
                    c = json.loads(cache_row['analysis_json'])
                    ops = c.get('sentiment_analysis', {}).get('opinions_mined', [])
                    for o in ops:
                        all_opinions.append({
                            **o,
                            'document_id': d['id'],
                            'document_title': d['title'],
                            'location': d.get('location', 'unknown'),
                            'source': d.get('source', '')
                        })
                except Exception:
                    pass
    return jsonify(all_opinions)

@app.post('/api/nlp-explain')
def nlp_explain():
    data = payload()
    text = text_value(data, 'text', limit=12000, required=True)
    lang = choice(data, 'lang', COPY, 'en')
    n = data.get('n', 2)
    if type(n) is not int or n not in (1, 2, 3):
        raise ValueError('n must be 1, 2, or 3')
        
    analysis = unified_engine.analyze_document(text, declared_lang=lang, manual_category='auto')
    model = unified_engine.ngram_models.get((lang, n), unified_engine.ngram_models.get(('en', n)))
    analysis['sequence_probability'] = model.score_sequence(text) if model else {}
    return jsonify(analysis)

if __name__=='__main__':
    port=int(os.environ.get('JANSAHAY_PORT','5000'))
    print(f'JanSahay is ready: http://127.0.0.1:{port}')
    app.run(host='127.0.0.1',port=port,debug=False)
