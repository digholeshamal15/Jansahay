"""Module B: Language detection, text statistics, tokenization, and cleaning."""
import unicodedata
from collections import Counter
import regex as re
from langdetect import detect_langs, DetectorFactory, LangDetectException

DetectorFactory.seed = 7

# Token regex keeps combining marks (\p{M}) so Devanagari vowel signs/matras are preserved
TOKEN_PATTERN = re.compile(r"[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*|\p{N}+")
SENTENCE_SPLIT = re.compile(r"[.!?।॥\n\r]+(?:[ \t\n\r]+|$)")

# Curated stop words for English, Hindi, and Marathi
STOP_WORDS = {
    'en': {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any',
        'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between',
        'both', 'but', 'by', 'can', 'could', 'did', 'do', 'does', 'doing', 'down', 'during',
        'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her',
        'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into',
        'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor',
        'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves',
        'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that',
        'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this',
        'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were',
        'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'you',
        'your', 'yours', 'yourself', 'yourselves', 'please', 'also', 'due'
    },
    'hi': {
        'का', 'के', 'की', 'को', 'में', 'से', 'पर', 'ने', 'और', 'है', 'हैं', 'था', 'थी', 'थे',
        'होता', 'होती', 'होते', 'हो', 'यह', 'वह', 'इस', 'उस', 'इन', 'उन', 'जो', 'तो', 'भी',
        'ही', 'तक', 'या', 'लिए', 'साथ', 'कर', 'रहा', 'रही', 'रहे', 'गया', 'गई', 'गए', 'करना',
        'होना', 'किया', 'दिया', 'दिया', 'गया', 'अपने', 'अपनी', 'अपना', 'द्वारा', 'हुए', 'हुआ'
    },
    'mr': {
        'आहे', 'आहेत', 'होता', 'होती', 'होते', 'झाला', 'झाली', 'झाले', 'आणि', 'व', 'किंवा',
        'नाही', 'नाहीत', 'मध्ये', 'वर', 'खाली', 'तून', 'कडून', 'ने', 'ना', 'चे', 'च्या', 'ची',
        'चा', 'या', 'तो', 'ती', 'ते', 'हे', 'ह्या', 'हा', 'ही', 'पण', 'तर', 'मात्र', 'सुद्धा',
        'देखील', 'आमच्या', 'माझ्या', 'त्यांच्या', 'आपल्या', 'केले', 'करावे', 'पाहिजे'
    }
}

def normalize_text(text: str) -> str:
    """Normalize text using Unicode NFC form."""
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize('NFC', text.strip())

def tokenize_words(text: str) -> list[str]:
    """Tokenize text into words preserving multilingual unicode marks."""
    norm = normalize_text(text)
    return TOKEN_PATTERN.findall(norm.casefold())

def tokenize_sentences(text: str) -> list[str]:
    """Split text into sentences respecting Latin (.!?) and Indic (। ॥) danda."""
    norm = normalize_text(text)
    if not norm:
        return []
    raw = SENTENCE_SPLIT.split(norm)
    return [s.strip() for s in raw if s and s.strip()]

def get_paragraphs(text: str) -> list[str]:
    """Split text into distinct non-empty paragraphs."""
    norm = normalize_text(text)
    if not norm:
        return []
    return [p.strip() for p in re.split(r'\n{2,}|\r\n{2,}', norm) if p.strip()]

def detect_language(text: str) -> dict:
    """Estimate language using langdetect with fallback handling."""
    words = tokenize_words(text)
    if len(words) < 4:
        return {
            'code': 'uncertain',
            'score': 0.0,
            'note': 'Text is too short (< 4 words) for reliable statistical language detection.'
        }
    try:
        guesses = detect_langs(text)
        top = guesses[0]
        # Language names
        lang_names = {'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi'}
        code = top.lang
        name = lang_names.get(code, code)
        return {
            'code': code,
            'language_name': name,
            'score': round(float(top.prob), 3),
            'note': f"Statistical hint: {name} ({round(float(top.prob)*100, 1)}% probability). Hindi, Marathi, and code-mixed text may be confused."
        }
    except LangDetectException:
        return {
            'code': 'uncertain',
            'score': 0.0,
            'note': 'Language could not be statistically estimated.'
        }

def analyze_text(text: str, declared_lang: str = 'en') -> dict:
    """Run Module B: Comprehensive linguistic statistics, tokenization, and cleaning."""
    norm = normalize_text(text)
    words = tokenize_words(norm)
    sentences = tokenize_sentences(norm)
    paragraphs = get_paragraphs(norm)
    
    lang_info = detect_language(norm)
    active_lang = declared_lang if declared_lang in ('en', 'hi', 'mr') else (lang_info['code'] if lang_info['code'] in ('en', 'hi', 'mr') else 'en')
    
    stops = STOP_WORDS.get(active_lang, STOP_WORDS['en'])
    stop_words_found = [w for w in words if w in stops]
    content_words = [w for w in words if w not in stops]
    
    # Cleaned text: normalized words with stop words removed and clean spacing
    cleaned_text = ' '.join(content_words)
    
    # Word frequency
    freq = Counter(words)
    content_freq = Counter(content_words)
    
    return {
        'original_text': text,
        'cleaned_text': cleaned_text,
        'character_count': len(norm),
        'character_count_no_spaces': len(re.sub(r'\s+', '', norm)),
        'word_count': len(words),
        'unique_word_count': len(freq),
        'sentence_count': len(sentences),
        'paragraph_count': max(1, len(paragraphs)),
        'average_word_length': round(sum(len(w) for w in words) / max(1, len(words)), 2),
        'average_sentence_length_words': round(len(words) / max(1, len(sentences)), 2),
        'language_detection': lang_info,
        'effective_language': active_lang,
        'tokens': words,
        'sentences': sentences,
        'stop_words_identified': {
            'total_count': len(stop_words_found),
            'unique_count': len(set(stop_words_found)),
            'stop_words': sorted(list(set(stop_words_found)))[:30]
        },
        'top_words': [{'word': w, 'count': c} for w, c in content_freq.most_common(12)]
    }
