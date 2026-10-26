"""Local complaint details, authority directory and additive SQLite migration."""
from pathlib import Path
import json
import sqlite3
from datetime import date, datetime, timezone

ROOT=Path(__file__).parent
AUTHORITIES=json.loads((ROOT/'data/authorities.json').read_text(encoding='utf-8'))
AUTHORITY_MAP={a['id']:a for a in AUTHORITIES}
STATUSES=('draft','ready','submitted','follow_up','resolved')
OTHER={'en':'Other / Not sure','hi':'अन्य / निश्चित नहीं','mr':'इतर / खात्री नाही'}
# Question keys are stable; answers are optional user-provided facts.
QUESTIONS={
 'water':{'id':'water_issue','label':{'en':'What is wrong with the supply? (optional)','hi':'पानी की आपूर्ति में क्या समस्या है? (वैकल्पिक)','mr':'पाणीपुरवठ्यात काय अडचण आहे? (ऐच्छिक)'}},
 'garbage':{'id':'collection','label':{'en':'When was waste last collected? (optional)','hi':'आखिरी बार कचरा कब उठाया गया? (वैकल्पिक)','mr':'कचरा शेवटचा कधी उचलला? (ऐच्छिक)'}},
 'roads':{'id':'road_spot','label':{'en':'Which road or footpath section is affected? (optional)','hi':'सड़क या फुटपाथ का कौन सा हिस्सा खराब है? (वैकल्पिक)','mr':'रस्ता किंवा पदपथाचा कोणता भाग खराब आहे? (ऐच्छिक)'}},
 'lights':{'id':'light_count','label':{'en':'How many lights are affected? (optional)','hi':'कितनी लाइट खराब हैं? (वैकल्पिक)','mr':'किती दिवे बंद आहेत? (ऐच्छिक)'}},
 'drainage':{'id':'drain_issue','label':{'en':'Where is the blockage or overflow? (optional)','hi':'रुकावट या गंदा पानी कहाँ है? (वैकल्पिक)','mr':'गटार कुठे तुंबले आहे किंवा सांडपाणी कुठे वाहते? (ऐच्छिक)'}}}
DETAIL_LABELS={
 'en':{'landmark':'Nearby landmark','duration':'Issue duration','recurring':'Recurring problem','extra':'Additional details','yes':'Yes','no':'No','unsure':'Not sure'},
 'hi':{'landmark':'पास की पहचान','duration':'समस्या की अवधि','recurring':'बार-बार होने वाली समस्या','extra':'अतिरिक्त विवरण','yes':'हाँ','no':'नहीं','unsure':'निश्चित नहीं'},
 'mr':{'landmark':'जवळची खूण','duration':'समस्येचा कालावधी','recurring':'वारंवार होणारी समस्या','extra':'अतिरिक्त तपशील','yes':'होय','no':'नाही','unsure':'खात्री नाही'}}

def now():return datetime.now(timezone.utc).isoformat()

def migrate(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path);db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    # Existing drafts and IDs are preserved, including older schemas.
    with db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS drafts (id INTEGER PRIMARY KEY, category TEXT, lang TEXT, location TEXT, body TEXT, created TEXT)')
        columns={r['name'] for r in db.execute('PRAGMA table_info(drafts)')}
        additions={'status':"TEXT NOT NULL DEFAULT 'draft'",'reference':"TEXT NOT NULL DEFAULT ''",'issue':"TEXT NOT NULL DEFAULT ''",'municipality':"TEXT NOT NULL DEFAULT 'unknown'",'details_json':"TEXT NOT NULL DEFAULT '{}'",'submitted_on':"TEXT NOT NULL DEFAULT ''",'updated':"TEXT NOT NULL DEFAULT ''"}
        for name,spec in additions.items():
            if name not in columns:db.execute(f'ALTER TABLE drafts ADD COLUMN {name} {spec}')
        db.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, draft_id INTEGER NOT NULL REFERENCES drafts(id) ON DELETE CASCADE, action TEXT NOT NULL, old_status TEXT, new_status TEXT, note TEXT NOT NULL DEFAULT "", created TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS photos (id TEXT PRIMARY KEY, draft_id INTEGER REFERENCES drafts(id) ON DELETE CASCADE, storage_name TEXT NOT NULL, created TEXT NOT NULL)')
        db.execute('PRAGMA user_version=3')
    return db

def text_value(data,key,limit=3000,required=False):
    value=data.get(key,'')
    if not isinstance(value,str):raise ValueError(f'{key}: text required')
    value=value.strip()
    if len(value)>limit or (required and not value):raise ValueError(f'{key}: use 1–{limit} characters')
    return value

def details_value(value):
    if not isinstance(value,dict):raise ValueError('details must be an object')
    result={k:text_value(value,k,limit) for k,limit in [('landmark',160),('duration',120),('extra',1000)]}
    recurring=value.get('recurring','')
    if not isinstance(recurring,str) or recurring not in ('','yes','no','unsure'):raise ValueError('Invalid recurring choice')
    result['recurring']=recurring
    answers=value.get('answers',{})
    if not isinstance(answers,dict):raise ValueError('answers must be an object')
    allowed={q['id'] for q in QUESTIONS.values()}
    if any(k not in allowed for k in answers):raise ValueError('Unknown follow-up question')
    result['answers']={k:text_value(answers,k,250) for k in answers}
    return result

def valid_date(value):
    if value:
        try:date.fromisoformat(value)
        except ValueError:raise ValueError('Use a valid submission date in YYYY-MM-DD format')
    return value

def record_dict(db,row,history=False):
    data=dict(row)
    try:data['details']=json.loads(data.pop('details_json'))
    except (ValueError,TypeError):data['details']={}
    data['photos']=[{'id':p['id'],'url':f"/api/photos/{p['id']}"} for p in db.execute('SELECT id FROM photos WHERE draft_id=? ORDER BY created',(row['id'],))]
    if history:data['history']=[dict(h) for h in db.execute('SELECT * FROM history WHERE draft_id=? ORDER BY id',(row['id'],))]
    return data
