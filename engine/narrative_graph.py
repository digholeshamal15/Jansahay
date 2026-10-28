"""EchoTrace AI Engine: Narrative & Connection Graph and Claim/Contradiction Analysis."""
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from engine.preprocessing import tokenize_words, tokenize_sentences

class NarrativeGraphEngine:
    """Builds the EchoTrace multi-entity connection graph and detects candidate contradictions."""
    
    def __init__(self, documents: list[dict]):
        self.documents = documents
        
    def build_graph(self) -> dict:
        """Construct nodes and edges connecting documents, locations, entities, and topics."""
        nodes = []
        edges = []
        seen_node_ids = set()
        
        def add_node(node_id: str, label: str, node_type: str, metadata: dict = None):
            if node_id not in seen_node_ids:
                seen_node_ids.add(node_id)
                nodes.append({
                    'id': node_id,
                    'label': label,
                    'type': node_type,
                    'metadata': metadata or {}
                })
                
        def add_edge(source: str, target: str, relationship: str, reason: str, weight: float = 1.0):
            edges.append({
                'source': source,
                'target': target,
                'relationship': relationship,
                'reason': reason,
                'weight': round(float(weight), 3)
            })
            
        # 1. Document nodes & attribute nodes
        for idx, doc in enumerate(self.documents):
            doc_id = str(doc.get('id', f"doc_{idx}"))
            title = doc.get('title') or (doc.get('text', '')[:45] + '...')
            category = doc.get('category', 'other')
            lang = doc.get('lang', 'en')
            loc = doc.get('location')
            
            add_node(doc_id, title, 'document', {
                'category': category,
                'location': loc,
                'lang': lang,
                'snippet': doc.get('text', '')[:120]
            })
            
            # Category node
            if category:
                cat_node_id = f"cat_{category}"
                add_node(cat_node_id, category.replace('_', ' ').title(), 'category')
                add_edge(doc_id, cat_node_id, 'BELONGS_TO', f"Document classified under {category}")
                
            # Location node
            if loc and loc != '—' and loc != 'unknown':
                loc_node_id = f"loc_{loc.lower().strip()}"
                add_node(loc_node_id, loc.strip(), 'location')
                add_edge(doc_id, loc_node_id, 'REPORTED_AT', f"Incident reported at {loc}")
                
            # Entity nodes from analysis if available
            entities = doc.get('entities', [])
            for ent in entities:
                ent_text = ent.get('text', '').strip()
                ent_label = ent.get('label', '')
                if ent_text and len(ent_text) > 2 and ent_label in ('GPE', 'LOC', 'ORG'):
                    ent_node_id = f"ent_{ent_text.lower()}"
                    add_node(ent_node_id, ent_text, ent_label.lower())
                    add_edge(doc_id, ent_node_id, 'MENTIONS', f"Mentions {ent_label} '{ent_text}'")
                    
        # 2. Document-to-Document edges based on TF-IDF cosine similarity
        if len(self.documents) >= 2:
            texts = [d.get('text', '') for d in self.documents]
            try:
                vectorizer = TfidfVectorizer(tokenizer=tokenize_words, token_pattern=None, min_df=1, max_df=0.90)
                tfidf_matrix = vectorizer.fit_transform(texts)
                sim_matrix = cosine_similarity(tfidf_matrix)
                
                n_docs = len(self.documents)
                for i in range(n_docs):
                    for j in range(i + 1, n_docs):
                        score = float(sim_matrix[i, j])
                        if score >= 0.28:  # Significant textual similarity
                            doc_i_id = str(self.documents[i].get('id', f"doc_{i}"))
                            doc_j_id = str(self.documents[j].get('id', f"doc_{j}"))
                            shared_cat = self.documents[i].get('category') == self.documents[j].get('category')
                            reason = f"High textual similarity ({round(score, 2)})" + (" in the same category." if shared_cat else ".")
                            add_edge(doc_i_id, doc_j_id, 'RELATED_REPORT', reason, score)
            except Exception:
                pass
                
        return {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'summary': f"Generated {len(nodes)} graph nodes and {len(edges)} contextual relationships across {len(self.documents)} records."
        }

    def detect_contradictions(self) -> list[dict]:
        """Detect candidate conflicting claims between reports in similar domains/locations."""
        if len(self.documents) < 2:
            return []
            
        contradictions = []
        
        # Group documents by location and/or category
        groups = defaultdict(list)
        for idx, doc in enumerate(self.documents):
            cat = doc.get('category', 'other')
            loc = (doc.get('location') or '').lower().strip()
            if loc and loc not in ('—', 'unknown'):
                groups[(cat, loc)].append((idx, doc))
            groups[cat].append((idx, doc))
            
        positive_keywords = {'restored', 'fixed', 'resolved', 'repaired', 'normal', 'operational', 'working fine', 'दुरुस्त', 'ठीक'}
        negative_keywords = {'no water', 'broken', 'stopped', 'not working', 'unresolved', 'delayed', 'off for', 'waterlogging', 'बंद', 'खराब', 'नाही'}
        
        evaluated_pairs = set()
        
        for key, doc_list in groups.items():
            if len(doc_list) < 2:
                continue
                
            for i in range(len(doc_list)):
                for j in range(i + 1, len(doc_list)):
                    idx_a, doc_a = doc_list[i]
                    idx_b, doc_b = doc_list[j]
                    pair_key = tuple(sorted((idx_a, idx_b)))
                    if pair_key in evaluated_pairs:
                        continue
                    evaluated_pairs.add(pair_key)
                    
                    text_a = doc_a.get('text', '').lower()
                    text_b = doc_b.get('text', '').lower()
                    
                    # Check for opposing sentiment/status cues
                    has_pos_a = any(k in text_a for k in positive_keywords)
                    has_neg_a = any(k in text_a for k in negative_keywords)
                    has_pos_b = any(k in text_b for k in positive_keywords)
                    has_neg_b = any(k in text_b for k in negative_keywords)
                    
                    # Direct conflict: A claims positive/resolved while B reports ongoing outage/failure
                    if (has_pos_a and has_neg_b) or (has_neg_a and has_pos_b):
                        claim_a = next((s for s in tokenize_sentences(doc_a.get('text', '')) if any(k in s.lower() for k in (positive_keywords if has_pos_a else negative_keywords))), doc_a.get('text', '')[:100])
                        claim_b = next((s for s in tokenize_sentences(doc_b.get('text', '')) if any(k in s.lower() for k in (negative_keywords if has_neg_b else positive_keywords))), doc_b.get('text', '')[:100])
                        
                        contradictions.append({
                            'id': f"contra_{idx_a}_{idx_b}",
                            'topic': str(key if isinstance(key, str) else f"{key[0]} in {key[1].title()}"),
                            'status': 'Candidate Divergence Requiring Verification',
                            'severity': 'Medium',
                            'reason': 'Conflicting operational claims: one document reports resolution/restoration while the other reports persistent failure or disruption in the same thematic domain.',
                            'report_a': {
                                'id': doc_a.get('id', idx_a),
                                'title': doc_a.get('title', f"Report #{idx_a+1}"),
                                'source': doc_a.get('source', 'Citizen Report'),
                                'claim': claim_a,
                                'stance': 'Resolved / Restored' if has_pos_a else 'Persistent Outage / Issue'
                            },
                            'report_b': {
                                'id': doc_b.get('id', idx_b),
                                'title': doc_b.get('title', f"Report #{idx_b+1}"),
                                'source': doc_b.get('source', 'Citizen Report'),
                                'claim': claim_b,
                                'stance': 'Persistent Outage / Issue' if has_neg_b else 'Resolved / Restored'
                            }
                        })
                        
        return contradictions
