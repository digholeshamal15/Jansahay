"""Assignment 2 adapted to JanSahay: language, counts and tokens for civic messages.
The original news exercise supplies the method; no news data is required.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nlp import tokenize, sentences, language_hint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = PROJECT_ROOT / 'data/service_train.json'
if not DEFAULT_CORPUS.exists():
    DEFAULT_CORPUS = PROJECT_ROOT / 'data/training.json'


def summarize(path, limit=0):
    """Accept a JSON array or JSONL with text, optional lang and category fields."""
    if limit < 0:
        raise ValueError('limit must be nonnegative')
    content = Path(path).read_text(encoding='utf-8-sig')
    if content.lstrip().startswith('['):
        rows = json.loads(content)
    else:
        rows = []
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append(None)
    detected = Counter()
    declared = Counter()
    categories = Counter()
    examples = []
    total = word_count = sentence_count = invalid = 0
    for item in rows:
        if not isinstance(item, dict) or not isinstance(item.get('text'), str) or not tokenize(item['text']):
            invalid += 1
            continue
        text = item['text']
        tokens = tokenize(text)
        sentence_list = sentences(text)
        hint = language_hint(text)
        language = item.get('lang', 'unspecified')
        category = item.get('category', 'unspecified')
        language = language if isinstance(language, str) else 'unspecified'
        category = category if isinstance(category, str) else 'unspecified'
        total += 1
        word_count += len(tokens)
        sentence_count += len(sentence_list)
        detected[hint['code']] += 1
        declared[language] += 1
        categories[category] += 1
        if len(examples) < 8:
            examples.append(dict(text=text, declared_language=language, category=category,
                                 tokens=tokens, word_count=len(tokens), sentence_count=len(sentence_list),
                                 language_hint=hint))
        if limit and total >= limit:
            break
    return dict(dataset='JanSahay civic messages', input_file=Path(path).name,
                message_count=total, word_count=word_count, sentence_count=sentence_count,
                detected_language_counts=dict(detected), declared_language_counts=dict(declared),
                category_counts=dict(categories), invalid_rows=invalid, examples=examples,
                notes=['Assignment 2 methods applied to civic messages: language detection, word count, sentence count and tokenization.',
                       'The prepared service training corpus combines selected external HF examples with an authored language supplement; see dataset_manifest.json for provenance.',
                       'Detected language is a statistical hint; declared language is a separate user/data label.',
                       'Short or mixed Hindi/Marathi messages may be misidentified; no language label is forced to match.',
                       'Sentence boundaries include English punctuation and Devanagari danda.',
                       'No news records, headline fields or historical date filters are used.',
                       'With --limit, invalid_rows counts only the scanned prefix.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default=str(DEFAULT_CORPUS), help='JSON array or JSONL civic messages; defaults to data/service_train.json when available')
    parser.add_argument('--limit', type=int, default=0, help='0 processes all messages')
    parser.add_argument('--output', default='civic_text_report.json')
    args = parser.parse_args()
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    try:
        report = summarize(args.path, args.limit)
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    except (OSError, ValueError) as error:
        parser.exit(1, f'Could not analyze civic messages: {error}\n')
    print(f"Processed {report['message_count']} civic messages. Report: {args.output}")
