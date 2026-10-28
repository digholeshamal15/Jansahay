"""Module J: Sentiment, Emotion Detection, and Target-Stance-Evidence Opinion Mining."""
import regex as re
from collections import Counter
from engine.preprocessing import tokenize_sentences

# Lexicons with weights
POSITIVE_CUES = {
    'resolved': 0.8, 'fixed': 0.8, 'thank': 0.7, 'thanks': 0.7, 'excellent': 0.9, 'good': 0.6,
    'clean': 0.6, 'improved': 0.7, 'prompt': 0.8, 'helpful': 0.7, 'appreciate': 0.7, 'satisfaction': 0.8,
    'relief': 0.7, 'repaired': 0.8, 'धन्यवाद': 0.8, 'अच्छा': 0.6, 'सुधार': 0.7, 'ठीक हो गया': 0.9,
    'दुरुस्त झाले': 0.9, 'समाधान': 0.8, 'स्वच्छ': 0.6, 'चांगले': 0.6
}

NEGATIVE_CUES = {
    'broken': -0.7, 'damaged': -0.8, 'dirty': -0.6, 'blocked': -0.7, 'overflowing': -0.8,
    'delayed': -0.7, 'severe': -0.8, 'danger': -0.9, 'dangerous': -0.9, 'hazard': -0.8,
    'waterlogging': -0.7, 'pothole': -0.6, 'potholes': -0.7, 'disrupted': -0.7, 'complaint': -0.4,
    'unresponsive': -0.8, 'refused': -0.8, 'crisis': -0.9, 'contamination': -0.8, 'accident': -0.9,
    'stagnant': -0.6, 'mosquitoes': -0.6, 'dark': -0.5, 'failure': -0.8, 'suffering': -0.8,
    'खराब': -0.7, 'गंदा': -0.7, 'बंद': -0.6, 'गड्ढे': -0.7, 'खड्डे': -0.7, 'तुंबले': -0.7,
    'घाण': -0.7, 'दुर्गंधी': -0.8, 'अपघात': -0.9, 'धोका': -0.8, 'दुर्लक्ष': -0.8, 'तक्रार': -0.4
}

NEGATIONS = {'not', 'no', 'never', 'neither', 'hardly', 'barely', 'nahi', 'नहीं', 'नाही', 'नव्हते'}

EMOTIONS = {
    'frustration': {
        'keywords': ['frustrat', 'again', 'repeated', 'still', 'multiple times', 'no response', 'बार बार', 'परेशान', 'त्रास', 'पुन्हा', 'दिरंगाई'],
        'description': 'Impatience or distress over unresolved recurring problems'
    },
    'concern': {
        'keywords': ['worry', 'risk', 'hazard', 'safety', 'danger', 'children', 'pedestrians', 'चिंता', 'धोका', 'भीती', 'काळजी'],
        'description': 'Anxiety regarding public safety, health hazards, or infrastructure breakdown'
    },
    'anger': {
        'keywords': ['angry', 'furious', 'outrage', 'unacceptable', 'bribe', 'corruption', 'negligence', 'गुस्सा', 'राग', 'संताप', 'लाच'],
        'description': 'Outrage over civic negligence, misconduct, or severe administrative delay'
    },
    'fear': {
        'keywords': ['panic', 'shock', 'electrocution', 'collapse', 'drown', 'accident', 'deadly', 'भीती', 'दहशत', 'अपघात'],
        'description': 'Alarm over life-threatening hazards (e.g. open high-voltage wires, deep open manholes)'
    },
    'sadness': {
        'keywords': ['suffering', 'helpless', 'miserable', 'loss', 'tragedy', 'बदहाल', 'दुःख', 'हवालदिल'],
        'description': 'Sorrow over damaged property, public hardship, or civic degradation'
    },
    'relief': {
        'keywords': ['thank', 'relief', 'resolved', 'appreciate', 'fixed', 'धन्यवाद', 'सुटली', 'समाधान', 'दुरुस्त'],
        'description': 'Reassurance and satisfaction after an issue has been addressed'
    }
}

TARGET_TOPICS = [
    ('Water Supply', ['water', 'tap', 'pipeline', 'leakage', 'drinking', 'pressure', 'पाणी', 'पानी']),
    ('Road & Transport', ['road', 'pothole', 'potholes', 'footpath', 'traffic', 'bus', 'vehicles', 'सड़क', 'रस्ता']),
    ('Flooding & Drainage', ['flood', 'flooding', 'rain', 'waterlogging', 'drain', 'gutter', 'sewage', 'पाणी तुंबणे', 'गटार']),
    ('Streetlights & Power', ['light', 'lights', 'lamp', 'power', 'electricity', 'blackout', 'दिवा', 'बत्ती', 'वीज']),
    ('Waste & Sanitation', ['garbage', 'waste', 'trash', 'dustbin', 'dump', 'smell', 'कचरा', 'कूड़ा']),
    ('Public Safety & Access', ['safety', 'emergency', 'ambulance', 'fire', 'hazard', 'accident', 'सुरक्षा', 'धोका']),
    ('Health & Disease', ['hospital', 'health', 'dengue', 'mosquito', 'doctor', 'disease', 'आरोग्य', 'दवाखाना']),
    ('Civic Administration', ['office', 'officer', 'delay', 'portal', 'complaint', 'response', 'प्रशासन', 'तक्रार'])
]

def analyze_sentiment_and_emotions(text: str) -> dict:
    """Perform lexicon-based sentiment analysis with negation handling and emotion detection."""
    text_lower = text.lower()
    sentences = tokenize_sentences(text)
    
    pos_cues_found = []
    neg_cues_found = []
    total_score = 0.0
    
    # Process by sentence to handle local negations
    for s in sentences:
        s_lower = s.lower()
        words = re.findall(r"[\p{L}\p{M}]+", s_lower)
        negation_active = False
        
        for i, w in enumerate(words):
            if w in NEGATIONS:
                negation_active = True
                continue
                
            # Check window around negation
            is_negated = negation_active
            
            # Check positive cues
            for cue, weight in POSITIVE_CUES.items():
                if cue in s_lower and w == cue.split()[0]:
                    if is_negated:
                        neg_cues_found.append(f"not {cue}")
                        total_score -= weight * 0.9
                    else:
                        pos_cues_found.append(cue)
                        total_score += weight
                        
            # Check negative cues
            for cue, weight in NEGATIVE_CUES.items():
                if cue in s_lower and w == cue.split()[0]:
                    if is_negated:
                        pos_cues_found.append(f"not {cue}")
                        total_score += abs(weight) * 0.7
                    else:
                        neg_cues_found.append(cue)
                        total_score += weight
                        
    # Deduplicate cues
    pos_cues_found = sorted(list(set(pos_cues_found)))
    neg_cues_found = sorted(list(set(neg_cues_found)))
    
    # Normalize polarity score to [-1.0, 1.0]
    raw_magnitude = len(pos_cues_found) + len(neg_cues_found)
    polarity = max(-1.0, min(1.0, total_score / max(1, raw_magnitude * 0.8))) if raw_magnitude > 0 else 0.0
    
    if polarity <= -0.15:
        tone = 'negative'
    elif polarity >= 0.15:
        tone = 'positive'
    else:
        tone = 'mixed' if (pos_cues_found and neg_cues_found) else 'neutral'
        
    # Detect emotions with evidence cues
    emotions_detected = []
    for emotion_name, meta in EMOTIONS.items():
        matched_cues = []
        for kw in meta['keywords']:
            if kw in text_lower:
                matched_cues.append(kw)
        if matched_cues:
            emotions_detected.append({
                'emotion': emotion_name,
                'description': meta['description'],
                'evidence_keywords': matched_cues,
                'confidence': round(min(0.95, 0.4 + 0.2 * len(matched_cues)), 2)
            })
            
    # Opinion Mining: Target Entity -> Expressed Stance -> Sentiment -> Exact Sentence
    opinions = []
    for s in sentences:
        s_lower = s.lower()
        for topic_name, keywords in TARGET_TOPICS:
            matched_kw = [k for k in keywords if k in s_lower]
            if matched_kw:
                # Find sentiment of this specific sentence
                s_neg = [c for c in neg_cues_found if c in s_lower]
                s_pos = [c for c in pos_cues_found if c in s_lower]
                s_tone = 'negative' if s_neg else ('positive' if s_pos else 'neutral')
                
                # Associated emotion for sentence
                s_emotions = [e['emotion'] for e in emotions_detected if any(k in s_lower for k in e['evidence_keywords'])]
                
                opinions.append({
                    'target_issue': topic_name,
                    'matched_entity': matched_kw[0],
                    'opinion_stance': s.strip(),
                    'sentence_sentiment': s_tone,
                    'emotions': s_emotions or ['unspecified'],
                    'evidence_sentence': s.strip()
                })
                break  # match primary target per sentence
                
    return {
        'tone': tone,
        'polarity_score': round(polarity, 3),
        'subjectivity': round(min(1.0, raw_magnitude / max(1, len(sentences) * 2)), 2),
        'positive_cues': pos_cues_found,
        'negative_cues': neg_cues_found,
        'emotions': emotions_detected,
        'primary_emotion': emotions_detected[0]['emotion'] if emotions_detected else 'unspecified',
        'opinions_mined': opinions,
        'method': 'Lexicon-based sentiment with local negation inversion, contextual emotion cue matching, and sentence-level opinion extraction.'
    }
