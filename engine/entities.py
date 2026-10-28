"""Module E: Named Entity Recognition (Statistical NER, Gazetteer, and Pattern Matching)."""
from pathlib import Path
from collections import Counter
import regex as re
import nltk

ROOT = Path(__file__).resolve().parents[1]
nltk.data.path.insert(0, str(ROOT / 'nltk_data'))

# Civic gazetteer: Indian cities, regions, and known municipal/civic bodies
KNOWN_LOCATIONS = {
    # Cities & Metros
    'pune': 'Pune', 'mumbai': 'Mumbai', 'nagpur': 'Nagpur', 'nashik': 'Nashik',
    'delhi': 'Delhi', 'bengaluru': 'Bengaluru', 'bangalore': 'Bangalore', 'hyderabad': 'Hyderabad',
    'chennai': 'Chennai', 'kolkata': 'Kolkata', 'thane': 'Thane', 'aurangabad': 'Chhatrapati Sambhajinagar',
    'solapur': 'Solapur', 'kolhapur': 'Kolhapur', 'amravati': 'Amravati', 'nanded': 'Nanded',
    'dehradun': 'Dehradun', 'bhubaneswar': 'Bhubaneswar', 'lucknow': 'Lucknow', 'jaipur': 'Jaipur',
    # Devanagari
    'पुणे': 'Pune', 'पुण्यात': 'Pune', 'पुण्यातील': 'Pune',
    'मुंबई': 'Mumbai', 'मुंबईत': 'Mumbai',
    'नागपूर': 'Nagpur', 'नागपुर': 'Nagpur',
    'नाशिक': 'Nashik', 'नाशिकमध्ये': 'Nashik',
    'दिल्ली': 'Delhi', 'ठाणे': 'Thane',
    # Neighbourhoods & Localities (Pune & Mumbai focus)
    'kothrud': 'Kothrud', 'shivajinagar': 'Shivajinagar', 'hadapsar': 'Hadapsar',
    'viman nagar': 'Viman Nagar', 'hinjewadi': 'Hinjewadi', 'baner': 'Baner',
    'wakad': 'Wakad', 'pimpri': 'Pimpri', 'chinchwad': 'Chinchwad', 'aundh': 'Aundh',
    'katraj': 'Katraj', 'swargate': 'Swargate', 'camp': 'Pune Camp', 'deccan': 'Deccan Gymkhana',
    'kondhwa': 'Kondhwa', 'warje': 'Warje', 'bhosari': 'Bhosari', 'nigdi': 'Nigdi',
    'dharavi': 'Dharavi', 'bandra': 'Bandra', 'andheri': 'Andheri', 'dadar': 'Dadar',
    'borivali': 'Borivali', 'chembur': 'Chembur', 'kurla': 'Kurla',
    'कोथरुड': 'Kothrud', 'शिवाजीनगर': 'Shivajinagar', 'हडपसर': 'Hadapsar',
    'विमान नगर': 'Viman Nagar', 'हिंजवडी': 'Hinjewadi', 'बाणेर': 'Baner',
    'वाकड': 'Wakad', 'पिंपरी': 'Pimpri', 'चिंचवड': 'Chinchwad'
}

KNOWN_ORGS = {
    'pmc': 'Pune Municipal Corporation',
    'pcmc': 'Pimpri Chinchwad Municipal Corporation',
    'mcgm': 'Municipal Corporation of Greater Mumbai',
    'bmc': 'Brihanmumbai Municipal Corporation',
    'nmc': 'Nagpur/Nashik Municipal Corporation',
    'mseb': 'Maharashtra State Electricity Board',
    'mahadiscom': 'MSEDCL (Mahavitaran)',
    'msedcl': 'MSEDCL (Mahavitaran)',
    'pwd': 'Public Works Department',
    'police': 'Police Department',
    'fire brigade': 'Fire & Emergency Services',
    'जल बोर्ड': 'Water Board',
    'महापालिका': 'Municipal Corporation',
    'नगर निगम': 'Nagar Nigam'
}

PATTERNS = [
    ('PIN_CODE', re.compile(r'\b[1-9][0-9]{5}\b')),
    ('DATE', re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:january|february|march|april|may|june|july|august|september|october|november|december|monday|tuesday|wednesday|thursday|friday|saturday|sunday|yesterday|today|tomorrow))\b', re.IGNORECASE)),
    ('TIME', re.compile(r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm|hrs|hours)\b', re.IGNORECASE)),
    ('QUANTITY', re.compile(r'\b\d+(?:\.\d+)?\s*(?:km|kms|meters|metres|feet|days|weeks|months|hours|liters|litres|tons)\b', re.IGNORECASE)),
    ('MONEY', re.compile(r'(?:rs\.?|inr|₹)\s*\d+(?:,\d+)*(?:\.\d+)?\b', re.IGNORECASE))
]

def extract_entities(text: str, lang: str = 'en') -> dict:
    """Extract Named Entities using statistical model, domain gazetteer, and pattern rules."""
    entities = []
    seen_spans = set()
    
    # 1. Regex pattern matches
    for label, pattern in PATTERNS:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if not any(span[0] >= s[0] and span[1] <= s[1] for s in seen_spans):
                seen_spans.add(span)
                entities.append({
                    'text': m.group(),
                    'label': label,
                    'method': 'regex_pattern',
                    'start': m.start(),
                    'end': m.end(),
                    'confidence': 0.95
                })
                
    # 2. Gazetteer location matches
    text_lower = text.lower()
    for key, canonical in KNOWN_LOCATIONS.items():
        pattern = r'(?<![\p{L}\p{M}])' + re.escape(key) + r'(?![\p{L}\p{M}])'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            span = (m.start(), m.end())
            if not any(span[0] >= s[0] and span[1] <= s[1] for s in seen_spans):
                seen_spans.add(span)
                entities.append({
                    'text': m.group(),
                    'canonical': canonical,
                    'label': 'GPE',
                    'method': 'civic_gazetteer',
                    'start': m.start(),
                    'end': m.end(),
                    'confidence': 0.90
                })
                
    # 3. Gazetteer organization matches
    for key, canonical in KNOWN_ORGS.items():
        pattern = r'(?<![\p{L}\p{M}])' + re.escape(key) + r'(?![\p{L}\p{M}])'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            span = (m.start(), m.end())
            if not any(span[0] >= s[0] and span[1] <= s[1] for s in seen_spans):
                seen_spans.add(span)
                entities.append({
                    'text': m.group(),
                    'canonical': canonical,
                    'label': 'ORG',
                    'method': 'civic_gazetteer',
                    'start': m.start(),
                    'end': m.end(),
                    'confidence': 0.92
                })

    # 4. Statistical NLTK NER for English
    stat_ner_status = 'Statistical NER unavailable for this language.'
    if lang == 'en':
        try:
            tokens = nltk.word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            chunks = nltk.ne_chunk(pos_tags)
            stat_ner_status = 'NLTK English MaxEnt statistical chunker applied.'
            
            # Extract tree chunks
            char_cursor = 0
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    chunk_text = ' '.join(c[0] for c in chunk)
                    label = chunk.label()
                    # Map NLTK label
                    mapped_label = 'LOC' if label in ('GPE', 'LOCATION', 'FACILITY') else ('ORG' if label == 'ORGANIZATION' else ('PERSON' if label == 'PERSON' else label))
                    
                    # Find span in text
                    found_idx = text_lower.find(chunk_text.lower(), char_cursor)
                    if found_idx != -1:
                        end_idx = found_idx + len(chunk_text)
                        span = (found_idx, end_idx)
                        char_cursor = end_idx
                        if not any(span[0] >= s[0] and span[1] <= s[1] for s in seen_spans):
                            seen_spans.add(span)
                            entities.append({
                                'text': text[found_idx:end_idx],
                                'label': mapped_label,
                                'method': 'nltk_statistical_ner',
                                'start': found_idx,
                                'end': end_idx,
                                'confidence': 0.82
                            })
        except (LookupError, OSError):
            stat_ner_status = 'NLTK statistical NER models not loaded; fallback to gazetteer & regex rules.'
            
    # Sort entities by start index
    entities.sort(key=lambda e: e['start'])
    
    # Summary by entity type
    summary = Counter(e['label'] for e in entities)
    by_type = {}
    for e in entities:
        by_type.setdefault(e['label'], []).append(e['text'])
        
    return {
        'entities': entities,
        'summary': dict(summary),
        'by_type': {k: sorted(list(set(v))) for k, v in by_type.items()},
        'status_note': stat_ner_status,
        'primary_location': next((e['text'] for e in entities if e['label'] in ('GPE', 'LOC')), None)
    }
