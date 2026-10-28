"""Module G & H: N-gram Analysis and Laplace-Smoothed Sequence Probability Language Models."""
import math
from collections import Counter
from engine.preprocessing import tokenize_words

class NGramLanguageModel:
    """Statistical N-gram Language Model with Laplace smoothing, UNK handling, and Perplexity."""
    
    def __init__(self, texts: list[str], n: int = 2, alpha: float = 1.0):
        if n not in (1, 2, 3):
            raise ValueError("N-gram order n must be 1, 2, or 3.")
        if alpha <= 0:
            raise ValueError("Smoothing parameter alpha must be positive.")
            
        self.n = n
        self.alpha = alpha
        self.counts = Counter()
        self.context_counts = Counter()
        
        # Tokenize training texts
        tokenized_docs = [tokenize_words(t) for t in texts if t.strip()]
        
        # Build vocabulary including UNK and EOS
        word_set = {w for doc in tokenized_docs for w in doc}
        self.vocab = word_set | {'<UNK>', '</s>'}
        self.vocab_size = len(self.vocab)
        
        # Count n-grams and context frequencies
        for doc in tokenized_docs:
            if not doc:
                continue
            padded = ['<s>'] * (n - 1) + doc + ['</s>']
            for i in range(n - 1, len(padded)):
                ctx = tuple(padded[i - n + 1:i]) if n > 1 else ()
                word = padded[i]
                ngram = ctx + (word,)
                self.counts[ngram] += 1
                self.context_counts[ctx] += 1
                
    def conditional_probability(self, context: tuple, word: str) -> float:
        """Calculate smoothed conditional probability P(word | context)."""
        ctx_tuple = tuple(context)
        ngram = ctx_tuple + (word,)
        count_ngram = self.counts.get(ngram, 0)
        count_ctx = self.context_counts.get(ctx_tuple, 0)
        
        prob = (count_ngram + self.alpha) / (count_ctx + self.alpha * self.vocab_size)
        return prob
        
    def score_sequence(self, text: str) -> dict:
        """Calculate step-by-step sequence probability, log-likelihood, and perplexity."""
        raw_tokens = tokenize_words(text)
        if not raw_tokens:
            return {
                'tokens': [],
                'probability': 0.0,
                'log_probability': -999.0,
                'perplexity': 9999.0,
                'steps': [],
                'explanation': 'Empty sequence.'
            }
            
        # Map unseen words to <UNK>
        tokens = [w if w in self.vocab else '<UNK>' for w in raw_tokens]
        padded = ['<s>'] * (self.n - 1) + tokens + ['</s>']
        
        steps = []
        total_log_prob = 0.0
        
        for i in range(self.n - 1, len(padded)):
            ctx = tuple(padded[i - self.n + 1:i]) if self.n > 1 else ()
            word = padded[i]
            orig_word = raw_tokens[i - (self.n - 1)] if (i - (self.n - 1)) < len(raw_tokens) else '</s>'
            is_unk = (word == '<UNK>')
            
            p = self.conditional_probability(ctx, word)
            log_p = math.log(p)
            total_log_prob += log_p
            
            steps.append({
                'step': len(steps) + 1,
                'context': list(ctx) if ctx else ['(none)'],
                'word': word,
                'original_word': orig_word,
                'is_unknown': is_unk,
                'probability': round(p, 6),
                'log_probability': round(log_p, 4)
            })
            
        num_terms = len(steps)
        sequence_prob = math.exp(total_log_prob)
        perplexity = math.exp(-total_log_prob / max(1, num_terms))
        
        return {
            'n': self.n,
            'model_type': f"{'Unigram' if self.n==1 else ('Bigram' if self.n==2 else 'Trigram')} Language Model",
            'smoothing': f"Laplace (alpha = {self.alpha})",
            'vocabulary_size': self.vocab_size,
            'tokens_evaluated': tokens + ['</s>'],
            'steps': steps,
            'sequence_probability': sequence_prob,
            'sequence_probability_scientific': f"{sequence_prob:.4e}",
            'total_log_probability': round(total_log_prob, 4),
            'perplexity': round(perplexity, 2),
            'pedagogical_note': (
                "Perplexity measures how surprised the N-gram language model is by this sentence. Lower perplexity means the sequence "
                "conforms more naturally to patterns observed in the civic training corpus. Conditional probability P(w|h) is computed at "
                "each token step with Laplace additive smoothing (+alpha) to prevent zero-probability for unseen transitions."
            )
        }

def extract_corpus_ngrams(texts: list[str], top_k: int = 15) -> dict:
    """Extract unigrams, bigrams, and trigrams across a collection of texts."""
    unigrams = Counter()
    bigrams = Counter()
    trigrams = Counter()
    
    for text in texts:
        tokens = tokenize_words(text)
        for i in range(len(tokens)):
            unigrams[tokens[i]] += 1
            if i + 1 < len(tokens):
                bigrams[f"{tokens[i]} {tokens[i+1]}"] += 1
            if i + 2 < len(tokens):
                trigrams[f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}"] += 1
                
    return {
        'unigrams': [{'phrase': p, 'count': c} for p, c in unigrams.most_common(top_k)],
        'bigrams': [{'phrase': p, 'count': c} for p, c in bigrams.most_common(top_k)],
        'trigrams': [{'phrase': p, 'count': c} for p, c in trigrams.most_common(top_k)]
    }
