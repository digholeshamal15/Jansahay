"""Module D (Embeddings): Distributional Dense Word Embeddings (PPMI + TruncatedSVD)."""
from collections import Counter
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from engine.preprocessing import tokenize_words

class WordEmbeddingModel:
    """Distributional dense word vectors via Word-Context co-occurrence, PPMI and TruncatedSVD."""
    
    def __init__(self, texts: list[str], dimensions: int = 24, window_size: int = 2, random_state: int = 7):
        self.dimensions = dimensions
        self.window_size = window_size
        self.random_state = random_state
        
        # Tokenize corpus
        docs = [tokenize_words(t) for t in texts]
        word_counts = Counter(w for d in docs for w in d)
        # Keep words with minimum count >= 1
        self.words = sorted([w for w, c in word_counts.items() if c >= 1])
        self.word_to_id = {w: i for i, w in enumerate(self.words)}
        self.vocab_size = len(self.words)
        
        if self.vocab_size < 5:
            self.vectors = np.zeros((max(1, self.vocab_size), dimensions))
            return
            
        # Build co-occurrence matrix
        matrix = np.zeros((self.vocab_size, self.vocab_size), dtype=np.float64)
        for doc in docs:
            for i, target in enumerate(doc):
                if target not in self.word_to_id:
                    continue
                tid = self.word_to_id[target]
                start = max(0, i - window_size)
                end = min(len(doc), i + window_size + 1)
                for j in range(start, end):
                    if j != i and doc[j] in self.word_to_id:
                        cid = self.word_to_id[doc[j]]
                        matrix[tid, cid] += 1.0
                        
        # Positive Pointwise Mutual Information (PPMI)
        total = matrix.sum()
        if total > 0:
            row_sums = matrix.sum(axis=1, keepdims=True)
            col_sums = matrix.sum(axis=0, keepdims=True)
            expected = (row_sums * col_sums) / total
            with np.errstate(divide='ignore', invalid='ignore'):
                pmi = np.log((matrix * total) / (row_sums * col_sums + 1e-12) + 1e-12)
            ppmi = np.maximum(0, pmi)
        else:
            ppmi = matrix
            
        # Truncated SVD dimensionality reduction
        n_comp = min(dimensions, max(2, self.vocab_size - 1))
        self.svd = TruncatedSVD(n_components=n_comp, random_state=random_state)
        self.vectors = self.svd.fit_transform(ppmi)
        
        # Pad to dimensions if smaller
        if self.vectors.shape[1] < dimensions:
            padding = np.zeros((self.vocab_size, dimensions - self.vectors.shape[1]))
            self.vectors = np.hstack([self.vectors, padding])
            
        # Normalize vectors for cosine speed
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.normalized_vectors = self.vectors / norms
        
    def get_vector(self, word: str) -> np.ndarray | None:
        """Get the embedding vector for a given word."""
        w = word.lower()
        if w in self.word_to_id:
            return self.vectors[self.word_to_id[w]]
        return None
        
    def nearest_neighbors(self, word: str, top_k: int = 5) -> list[dict]:
        """Find the top_k most semantically similar words by cosine similarity."""
        w = word.lower()
        if w not in self.word_to_id:
            return []
        idx = self.word_to_id[w]
        vec = self.normalized_vectors[idx:idx+1]
        sims = cosine_similarity(vec, self.normalized_vectors)[0]
        
        ranked_indices = sims.argsort()[::-1]
        neighbors = []
        for i in ranked_indices:
            if i != idx and len(neighbors) < top_k:
                neighbors.append({
                    'word': self.words[i],
                    'similarity': round(float(sims[i]), 4)
                })
        return neighbors
        
    def document_vector(self, text: str) -> np.ndarray:
        """Compute the average word embedding for an entire document."""
        words = tokenize_words(text)
        known = [self.normalized_vectors[self.word_to_id[w]] for w in words if w in self.word_to_id]
        if not known:
            return np.zeros(self.dimensions)
        avg = np.mean(known, axis=0)
        norm = np.linalg.norm(avg)
        return avg / norm if norm > 0 else avg
        
    def word_similarity(self, word1: str, word2: str) -> float:
        """Compute cosine similarity between two words."""
        w1, w2 = word1.lower(), word2.lower()
        if w1 not in self.word_to_id or w2 not in self.word_to_id:
            return 0.0
        v1 = self.normalized_vectors[self.word_to_id[w1]:self.word_to_id[w1]+1]
        v2 = self.normalized_vectors[self.word_to_id[w2]:self.word_to_id[w2]+1]
        return round(float(cosine_similarity(v1, v2)[0, 0]), 4)
        
    def inspect_text_embeddings(self, text: str) -> dict:
        """Inspect embeddings of key words in the given text."""
        words = tokenize_words(text)
        samples = []
        seen = set()
        for w in words:
            if w in self.word_to_id and w not in seen:
                seen.add(w)
                vec = self.vectors[self.word_to_id[w]]
                samples.append({
                    'word': w,
                    'dimensions': len(vec),
                    'sample_values': [round(float(v), 4) for v in vec[:8]],
                    'neighbors': self.nearest_neighbors(w, top_k=4)
                })
                if len(samples) >= 6:
                    break
                    
        return {
            'vocabulary_size': self.vocab_size,
            'embedding_dimensions': self.dimensions,
            'method': 'Window-2 PPMI + TruncatedSVD Distributional Embeddings',
            'explanation': 'Dense embeddings capture contextual co-occurrence geometry (words appearing in similar linguistic contexts have close vector coordinates). Distinct from sparse TF-IDF which measures term uniqueness.',
            'words_sampled': samples
        }
