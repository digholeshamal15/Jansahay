"""Module C & D (Linguistics): Stemming, POS-aware Lemmatization, and POS Tagging."""
from pathlib import Path
from collections import Counter
import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer, SnowballStemmer

ROOT = Path(__file__).resolve().parents[1]
# Ensure local nltk_data is prioritized
nltk.data.path.insert(0, str(ROOT / 'nltk_data'))

PENN_TO_WORDNET = {
    'JJ': 'a', 'JJR': 'a', 'JJS': 'a',
    'VB': 'v', 'VBD': 'v', 'VBG': 'v', 'VBN': 'v', 'VBP': 'v', 'VBZ': 'v',
    'NN': 'n', 'NNS': 'n', 'NNP': 'n', 'NNPS': 'n',
    'RB': 'r', 'RBR': 'r', 'RBS': 'r'
}

SIMPLIFIED_POS = {
    'NN': 'Noun', 'NNS': 'Noun', 'NNP': 'Proper Noun', 'NNPS': 'Proper Noun',
    'VB': 'Verb', 'VBD': 'Verb', 'VBG': 'Verb (Gerund/Participle)', 'VBN': 'Verb (Past Participle)',
    'VBP': 'Verb (Present)', 'VBZ': 'Verb (3rd Person)',
    'JJ': 'Adjective', 'JJR': 'Comparative Adjective', 'JJS': 'Superlative Adjective',
    'RB': 'Adverb', 'RBR': 'Adverb', 'RBS': 'Adverb',
    'CD': 'Cardinal Number', 'PRP': 'Personal Pronoun', 'PRP$': 'Possessive Pronoun',
    'IN': 'Preposition/Conjunction', 'DT': 'Determiner', 'CC': 'Coordinating Conjunction',
    'MD': 'Modal', 'UH': 'Interjection', 'WDT': 'Wh-determiner', 'WP': 'Wh-pronoun', 'WRB': 'Wh-adverb'
}

def analyze_linguistics(words: list[str], lang: str = 'en') -> dict:
    """Analyze morphology (stemming & lemmatization) and syntax (POS tagging)."""
    if lang != 'en':
        return {
            'language': lang,
            'status': 'English-only morphology module. Indic languages (Hindi/Marathi) use native script preservation and statistical/n-gram features; rule-based English stemmers are not applied.',
            'stems': [],
            'lemmas': [],
            'pos_tags': [],
            'comparison_table': [],
            'explanations': []
        }
    
    porter = PorterStemmer()
    snowball = SnowballStemmer('english')
    lemmatizer = WordNetLemmatizer()
    
    tagged = None
    pos_error = None
    try:
        tagged = nltk.pos_tag(words)
    except (LookupError, OSError) as e:
        pos_error = str(e)
        tagged = [(w, 'NN') for w in words]
        
    stem_results = []
    lemma_results = []
    comparison_table = []
    differences = []
    pos_distribution = Counter()
    pos_items = []
    
    for idx, (word, tag) in enumerate(tagged):
        lower = word.lower()
        p_stem = porter.stem(lower)
        s_stem = snowball.stem(lower)
        
        wn_pos = PENN_TO_WORDNET.get(tag[:2], PENN_TO_WORDNET.get(tag, 'n'))
        try:
            lemma = lemmatizer.lemmatize(lower, pos=wn_pos)
        except LookupError:
            lemma = lower
            
        simple_category = SIMPLIFIED_POS.get(tag, 'Other')
        pos_distribution[simple_category] += 1
        
        stem_results.append({'word': word, 'stem': p_stem, 'snowball_stem': s_stem})
        lemma_results.append({'word': word, 'lemma': lemma, 'pos_used': wn_pos})
        pos_items.append({'word': word, 'tag': tag, 'category': simple_category})
        
        # Check if stem differs from lemma
        is_diff = (p_stem != lemma)
        row = {
            'original': word,
            'stem': p_stem,
            'lemma': lemma,
            'pos': tag,
            'category': simple_category,
            'is_different': is_diff
        }
        comparison_table.append(row)
        
        if is_diff and len(differences) < 8:
            differences.append({
                'word': word,
                'stem': p_stem,
                'lemma': lemma,
                'explanation': f"Stemming applies heuristic suffix stripping ('{word}' → '{p_stem}'), which may produce a non-dictionary root. Lemmatization uses WordNet vocabulary and grammatical POS context ({simple_category}) to return the canonical base form ('{word}' → '{lemma}')."
            })
            
    total_tagged = len(tagged) or 1
    pos_summary = [
        {'category': cat, 'count': count, 'percentage': round((count / total_tagged) * 100, 1)}
        for cat, count in pos_distribution.most_common()
    ]
    
    # Pedagogical explanation of stemming vs lemmatization
    concept_explanation = (
        "Stemming (Porter / Snowball) is an algorithmic heuristic that strips affixes (e.g., -ing, -ed, -s) using rule tables. "
        "It is fast but can produce non-words (e.g., 'operating' → 'oper') or suffer from over-stemming/under-stemming. "
        "Lemmatization (WordNet) performs full morphological analysis with dictionary lookup and POS awareness to return valid lemma forms "
        "(e.g., 'feet' → 'foot', 'better' → 'good', 'operating' → 'operate')."
    )
    
    return {
        'language': 'en',
        'has_pos_resources': (pos_error is None),
        'concept_explanation': concept_explanation,
        'pos_tags': pos_items,
        'pos_distribution': pos_summary,
        'comparison_table': comparison_table[:40],
        'notable_differences': differences,
        'total_analyzed': len(words)
    }
