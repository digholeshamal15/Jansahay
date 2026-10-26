"""Report a small independent authored smoke set. Not a production benchmark."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sklearn.metrics import classification_report,confusion_matrix
from nlp import Engine, ROOT

engine=Engine();rows=json.loads((ROOT/'data/evaluation.json').read_text(encoding='utf-8'))
for lang in ('en','hi','mr'):
    selected=[r for r in rows if r['lang']==lang]
    actual=[r['category'] for r in selected]
    predicted=[engine.classify(r['text'])['category'] or 'unknown' for r in selected]
    print(f'\nLanguage: {lang} — only {len(selected)} authored test examples')
    print(classification_report(actual,predicted,zero_division=0))
    for row,p in zip(selected,predicted): print(f"{row['category']:10} -> {p:10} {row['text']}")
print('\nThis is a smoke check, not evidence of general-world accuracy. Collect independently labelled local feedback for a real evaluation.')
