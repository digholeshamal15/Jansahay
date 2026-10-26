"""Download pinned Hugging Face CSVs, map relevant labels, and split by complaint pattern.
No login, remote code execution, auto-translation or fabricated extra examples.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unicodedata
import urllib.request
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import GroupShuffleSplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from service_model import ROOT, read_rows

SOURCES = {
    'public_grievance': {'repo':'hackermango/Public_Grievance_Dataset','revision':'0f0eba3851e698758bba892c39bdf308c13472dd','file':'Public_Grievance_Dataset.csv'},
    'civicdex': {'repo':'JadeSamLee/civicdex','revision':'b46543ef1e35936ee713faf008d995fc28abbc1e','file':'civicdex_main.csv'}
}
PUBLIC_LABELS = {
    'Pothole or damaged road':'roads','Road excavation restoration':'roads','Footpath obstruction or damage':'roads',
    'Bridge or culvert maintenance':'roads','Public works quality or delay':'roads',
    'Streetlight outage':'lights','Missed waste collection':'garbage','Public bin overflow':'garbage',
    'Drain cleaning':'drainage','Sewage overflow':'drainage','Water connection or meter':'water',
    'Water quality concern':'water','Leakage and pipe repair':'water','Irregular water supply':'water'
}
CIVIC_LABELS = {'sanitation':'garbage','water_supply':'water','street_lighting':'lights','drainage':'drainage','roads':'roads'}
BOILERPLATE = ('i first sought help','i have not been able','i made an earlier request','the matter was raised',
               'despite contacting','the issue has continued','it has continued','please note that',
               'the matter has continued','this has disrupted','the delay is affecting','the issue is creating',
               'several households','a clear update','people who depend','please route','please register',
               'kindly investigate','please arrange','i request an acknowledgement','please verify',
               'the concern falls under','i am raising this under')

def normalize(text):
    return ' '.join(re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFC', text).casefold()).split())

def canonical_public(row):
    """Strip routing headers, named locations, and generic status/request boilerplate.
    The resulting core is used for grouping; full text is retained for training except explicit routing headers.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]+',row['grievance_text']) if s.strip()]
    usable=[]; core=[]
    department=row['department'].casefold()
    for sentence in sentences:
        lower=sentence.casefold()
        if department in lower or lower.startswith(('i am raising this under','the concern falls under')):
            continue
        usable.append(sentence)
        if lower.startswith(BOILERPLATE):
            continue
        c=lower
        for name in (row['locality'],row['city'],row['district'],row['state']):
            c=re.sub(r'\b'+re.escape(name.casefold())+r'\b',' ',c)
        # Drop a first sentence containing only the supplied subcategory + location.
        rest=c.replace(row['subcategory'].casefold(),' ')
        rest=re.sub(r'^(i am submitting this grievance about|i am seeking a status update regarding|i request assistance from the concerned office for|please review an unresolved public-service issue involving|this complaint concerns|kindly look into)\s*','',rest)
        rest=normalize(rest)
        if not rest or all(w in {'in','at','the','a','an','and'} for w in rest.split()):
            continue
        c=re.sub(r'^(i am submitting this grievance about|i request assistance from the concerned office for|please review an unresolved public-service issue involving|this complaint concerns|kindly look into|at)\s*','',c)
        c=re.sub(r'\s+(in|at)\s*[, ]*$','',c)
        core.append(normalize(c))
    full='. '.join(usable)+'.'
    key=' '.join(core) or normalize(row['subcategory'])
    return full, key

def fetch(source,cache_dir):
    cache_dir.mkdir(parents=True,exist_ok=True)
    path=cache_dir/(source['repo'].split('/')[0]+'_'+source['file'])
    url=f"https://huggingface.co/datasets/{source['repo']}/resolve/{source['revision']}/{source['file']}"
    if not path.exists():
        with urllib.request.urlopen(url,timeout=60) as response:
            data=response.read(30_000_001)
        if len(data)>30_000_000:raise ValueError('Source exceeds 30 MB limit')
        path.write_bytes(data)
    data=path.read_bytes()
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig')))),hashlib.sha256(data).hexdigest()

def group_patterns(rows):
    # Group exact/near-identical underlying complaint patterns across both datasets.
    unique=sorted({r['pattern'] for r in rows})
    matrix=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5)).fit_transform(unique)
    similarity=cosine_similarity(matrix)
    parent=list(range(len(unique)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,j in zip(*np.where(np.triu(similarity,k=1)>=.85)):
        a,b=find(int(i)),find(int(j))
        if a!=b:parent[b]=a
    mapping={key:f'pattern_{find(i):04d}' for i,key in enumerate(unique)}
    for row in rows:row['group_id']=mapping[row.pop('pattern')]
    return len({r['group_id'] for r in rows})

def split_groups(rows):
    indexes=np.arange(len(rows));groups=[r['group_id'] for r in rows]
    # Select the first seeded split with every class represented; no model or scores consulted.
    expected=set(r['category'] for r in rows)
    for seed in range(7,507):
        a,b=next(GroupShuffleSplit(n_splits=1,test_size=.20,random_state=seed).split(indexes,groups=groups))
        train,val_local=next(GroupShuffleSplit(n_splits=1,test_size=.15,random_state=seed).split(a,groups=[groups[i] for i in a]))
        train_idx=a[train];val_idx=a[val_local]
        splits={'train':[rows[i] for i in train_idx], 'validation':[rows[i] for i in val_idx], 'test':[rows[i] for i in b]}
        if all(set(r['category'] for r in split)==expected for split in splits.values()):
            return splits,seed
    raise ValueError('Could not form class-complete disjoint groups')

def prepare(cache_dir):
    rows=[];metadata=[]
    for name,source in SOURCES.items():
        upstream,checksum=fetch(source,cache_dir)
        selected=[]
        for r in upstream:
            if name=='public_grievance':
                category=PUBLIC_LABELS.get(r['subcategory'])
                if not category:continue
                text,pattern=canonical_public(r)
                source_id=r['grievance_id'];source_kind='provenance undocumented; templated text'
            else:
                category=CIVIC_LABELS.get(r['category'])
                if not category:continue
                text=r['english_gloss'].strip();pattern=normalize(text)
                source_id=r['request_id'];source_kind='prototype/synthetic per dataset card'
            if not text:continue
            selected.append(dict(text=text,lang='en',category=category,source=source['repo'],source_id=source_id,
                                 source_kind=source_kind,pattern=pattern))
        rows.extend(selected)
        metadata.append({**source,'sha256':checksum,'upstream_rows':len(upstream),'selected_rows':len(selected),'license':'MIT (declared by publisher)'})
    # Remove duplicate normalized text; drop conflicting labels rather than guess.
    buckets=defaultdict(list)
    for r in rows:buckets[normalize(r['text'])].append(r)
    clean=[];conflicts=0
    for same in buckets.values():
        if len({r['category'] for r in same})>1:
            conflicts+=len(same);continue
        clean.append(same[0])
    groups=group_patterns(clean)
    splits,seed=split_groups(clean)
    # Supplement only the training partition with the original authored examples.
    heldout={normalize(r['text']) for split in ('validation','test') for r in splits[split]}
    all_hf={normalize(r['text']) for r in clean}
    supplement=[]
    for i,row in enumerate(read_rows(ROOT/'data/training.json')):
        if normalize(row['text']) in heldout or normalize(row['text']) in all_hf:continue
        # Author-created examples are explicitly recorded; they are never presented as HF language data.
        supplement.append({**row,'source':'JanSahay authored','source_id':f'demo_{i:03d}', 'source_kind':'authored demonstration', 'group_id':f'authored_{i:03d}'})
    splits['train'].extend(supplement)
    for split,items in splits.items():
        (ROOT/f'data/service_{split}.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest={'sources':metadata,'scope':'English source data filtered to five civic services; authored Hindi/Marathi supplement only.',
              'hf_selected_before_dedup':len(rows),'hf_unique_after_dedup':len(clean),'duplicate_rows_removed':len(rows)-len(clean)-conflicts,
              'conflicting_rows_removed':conflicts,'hf_pattern_groups':groups,'split_seed':seed,
              'split_method':'GroupShuffleSplit on source complaint cores; >=0.85 character similarity joins near-identical cores; all groups disjoint. Seed chosen for class coverage only.',
              'authored_supplement':len(supplement),'counts':{s:{'rows':len(v),'categories':dict(Counter(r['category'] for r in v)), 'languages':dict(Counter(r['lang'] for r in v)), 'sources':dict(Counter(r['source'] for r in v))} for s,v in splits.items()},
              'limitations':['No native Hindi/Marathi external data found among the selected open sources.','Source provenance is not evidence of real citizen submissions; Public Grievance appears templated and CivicDex says no real citizen data.','Exact/core grouping reduces simple leakage but does not establish independence of all semantic paraphrases.','This is an in-domain prototype benchmark; real Marathi/Hindi and real citizen evaluation is still needed.']}
    (ROOT/'data/dataset_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-dir',type=Path,default=ROOT/'data/source_cache');args=p.parse_args()
    prepare(args.cache_dir)
