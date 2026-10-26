"""Fit only service_train.json; select no settings on the test set; save weights and reports."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import joblib
import numpy as np
import sklearn
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from service_model import ROOT, CATEGORIES, read_rows, fit_service, training_hash, domain_terms_present
from sklearn.metrics.pairwise import cosine_similarity


def train():
    path=ROOT/'data/service_train.json'
    if not path.exists():raise SystemExit('Run python scripts/prepare_hf_data.py first.')
    rows=read_rows(path)
    vectorizer,classifier,x=fit_service(rows)
    labels=list(CATEGORIES)
    reports={}
    for name in ('validation','test'):
        test=read_rows(ROOT/f'data/service_{name}.json')
        actual=[r['category'] for r in test]
        q=vectorizer.transform([r['text'] for r in test])
        probabilities=classifier.predict_proba(q)
        predicted=classifier.classes_[probabilities.argmax(axis=1)].tolist()
        nearest=cosine_similarity(q,x).max(axis=1)
        routed=[p if domain_terms_present(r['text']) and sim>=.12 and probability.max()>=.30 else 'unknown'
                for r,p,sim,probability in zip(test,predicted,nearest,probabilities)]
        accepted=[(a,p) for a,p in zip(actual,routed) if p!='unknown']
        routing={'coverage':len(accepted)/len(test),'accepted_count':len(accepted),'abstained_count':routed.count('unknown'),
                 'accuracy_counting_abstention_as_error':accuracy_score(actual,routed),
                 'accuracy_when_suggesting':sum(a==p for a,p in accepted)/len(accepted) if accepted else None,
                 'macro_f1':classification_report(actual,routed,labels=labels,output_dict=True,zero_division=0)['macro avg']['f1-score']}

        reports[name]={'samples':len(test),'accuracy':accuracy_score(actual,predicted),
                       'classification_report':classification_report(actual,predicted,labels=labels,output_dict=True,zero_division=0),
                       'confusion_matrix':confusion_matrix(actual,predicted,labels=labels).tolist(),'labels':labels,'ui_routing':routing,
                       'languages':dict(Counter(r['lang'] for r in test)),
                       'errors':[{'source':r['source'],'source_id':r['source_id'],'expected':a,'predicted':p} for r,a,p in zip(test,actual,predicted) if a!=p]}
    meta={'trained_at':datetime.now(timezone.utc).isoformat(),'training_sha256':training_hash(path),
          'training_messages':len(rows),'sklearn_version':sklearn.__version__,
          'sources':dict(Counter(r['source'] for r in rows)),'languages':dict(Counter(r['lang'] for r in rows)),
          'method':'Character 2–5-gram TF-IDF (max 60000), logistic regression C=8; weights balance language/category cells.',
          'settings':'Fixed before inspecting held-out results; no parameter search on test set.',
          'evaluation_scope':'Classifier argmax and UI routing with abstention are reported separately. Test data is English-only, synthetic/templated; not a Marathi/Hindi benchmark.',
          'reports':reports}
    (ROOT/'models').mkdir(exist_ok=True);(ROOT/'reports').mkdir(exist_ok=True)
    joblib.dump({'vectorizer':vectorizer,'classifier':classifier},ROOT/'models/service_classifier.joblib',compress=3)
    (ROOT/'models/service_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'reports/hf_evaluation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Trained messages:',len(rows));print('Sources:',meta['sources']);print('Languages:',meta['languages'])
    for split,result in reports.items():
        print(f"{split}: n={result['samples']}, accuracy={result['accuracy']:.3f}, macro F1={result['classification_report']['macro avg']['f1-score']:.3f}")
    print('Saved models/service_classifier.joblib and reports/hf_evaluation.json')

if __name__=='__main__':train()
