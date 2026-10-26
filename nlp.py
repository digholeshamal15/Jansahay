"""Transparent local NLP baselines; no remote model calls or automatic downloads."""
from pathlib import Path
from collections import Counter, defaultdict
import json
import math
import unicodedata
import regex as re
import numpy as np
import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD, LatentDirichletAllocation
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from langdetect import detect_langs, DetectorFactory, LangDetectException
from service_model import load_service, domain_terms_present

ROOT = Path(__file__).parent
nltk.data.path.insert(0, str(ROOT / 'nltk_data'))
DetectorFactory.seed = 7
# Combining marks are kept, so Devanagari vowel signs are not dropped.
TOKEN = re.compile(r"[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*|\p{N}+")
def tokenize(text):
    return TOKEN.findall(unicodedata.normalize('NFC', text).lower())
def sentences(text):
    return [s.strip() for s in re.split(r'[.!?।॥\n]+', text) if s.strip()]
def language_hint(text):
    if len(tokenize(text)) < 4:
        return {'code':'uncertain', 'note':'Too short for reliable language detection.'}
    try:
        guesses=detect_langs(text)
        return {'code':guesses[0].lang,'score':round(guesses[0].prob,3),'note':'Statistical hint; Hindi/Marathi and mixed text may be confused. Not calibrated confidence.'}
    except LangDetectException:
        return {'code':'uncertain','note':'Language could not be estimated.'}

class NGramModel:
    """Laplace-smoothed model. Vocabulary includes UNK and EOS, excludes BOS."""
    def __init__(self, texts, n=2, alpha=1.0):
        if n not in (1,2,3) or alpha <= 0:
            raise ValueError('n must be 1, 2 or 3; alpha must be positive')
        self.n=n; self.alpha=alpha; self.counts=Counter(); self.contexts=Counter()
        docs=[tokenize(t) for t in texts]
        self.vocab={t for d in docs for t in d}|{'<UNK>','</s>'}
        for doc in docs:
            padded=['<s>']*(n-1)+doc+['</s>']
            for i in range(n-1,len(padded)):
                context=tuple(padded[i-n+1:i]) if n>1 else ()
                self.counts[context+(padded[i],)]+=1
                self.contexts[context]+=1
    def conditional(self,context,word):
        return (self.counts[tuple(context)+(word,)]+self.alpha)/(self.contexts[tuple(context)]+self.alpha*len(self.vocab))
    def score(self,text):
        original=tokenize(text)
        tokens=[t if t in self.vocab else '<UNK>' for t in original]
        padded=['<s>']*(self.n-1)+tokens+['</s>']; terms=[]; logp=0.
        for i in range(self.n-1,len(padded)):
            context=tuple(padded[i-self.n+1:i]) if self.n>1 else ()
            p=self.conditional(context,padded[i]); logp+=math.log(p)
            terms.append({'context':list(context),'word':padded[i],'probability':round(p,7)})
        return {'n':self.n,'alpha':self.alpha,'vocabulary_size':len(self.vocab),'log_probability':logp,'probability':math.exp(logp),'perplexity':math.exp(-logp/len(terms)),'terms':terms,'note':'Includes end-of-sentence. Small demo corpus; not a grammar, truth or urgency score.'}

NEG=['bad','dirty','broken','blocked','overflowing','not working','no water','not received','not collected','potholes','गंदा','खराब','बंद','बदबू','जाम','नहीं','घाण','तुंब','खड्ड','तुट','येत नाही','वास']
POS=['thank','good','fixed','resolved','repaired','clean now','धन्यवाद','अच्छा','ठीक हो गया','दुरुस्त झाले','सुटली','स्वच्छ झाले','चांगल']
EMOTIONS={'frustration':['frustrat','again','still','बार बार','परेशान','त्रास','पुन्हा'],'anger':['angry','furious','गुस्सा','राग'],'relief':['thank','relief','धन्यवाद','सुटली','समाधान']}
def _matches(text,patterns):
    # Whole words/phrases for Latin; Indic fragments intentionally allow inflections.
    return [p for p in patterns if (re.search(r'(?<!\p{L})'+re.escape(p)+r'(?!\p{L})',text) if p.isascii() else p in text)]
def sentiment(text):
    t=text.lower(); neg=_matches(t,NEG); pos=_matches(t,POS)
    # Small explicit negation handling, documented as a lexical baseline.
    if 'not good' in t or 'not fixed' in t or 'not resolved' in t:
        pos=[p for p in pos if p not in ('good','fixed','resolved')]; neg.append('negated positive phrase')
    tone='mixed' if neg and pos else 'negative' if neg else 'positive' if pos else 'neutral'
    return {'tone':tone,'negative_cues':neg,'positive_cues':pos,'emotions':[e for e,p in EMOTIONS.items() if any(s in t for s in p)],'method':'Small hand-authored multilingual lexicon; no sarcasm or broad negation understanding. Emotion may be unspecified.'}

PLACES=['Pune','Mumbai','Nagpur','Nashik','Delhi','पुणे','पुण्यात','मुंबई','नागपूर','नागपुर','नाशिक','दिल्ली']
def entities(text,lang,tagged=None):
    found=[]
    for place in PLACES:
        if re.search(r'(?<![\p{L}\p{M}])'+re.escape(place)+r'(?![\p{L}\p{M}])',text,re.I):
            found.append({'text':place,'label':'PLACE','method':'gazetteer'})
    for p,label in [(r'\b\d{6}\b','PIN_CODE'),(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b','DATE')]:
        found.extend({'text':m.group(),'label':label,'method':'regex'} for m in re.finditer(p,text))
    status='Gazetteer + regex baseline. English statistical NER unavailable until NLTK resources are installed.'
    if lang=='en' and tagged:
        try:
            for chunk in nltk.ne_chunk(tagged):
                if hasattr(chunk,'label'):
                    found.append({'text':' '.join(w for w,_ in chunk.leaves()),'label':chunk.label(),'method':'NLTK statistical NER'})
            status='NLTK English statistical NER plus gazetteer / regex.'
        except LookupError:
            pass
    if lang!='en': status='Gazetteer + regex only; no Hindi/Marathi statistical NER model installed.'
    return {'items':found,'status':status}

def english_analysis(text):
    words=TOKEN.findall(unicodedata.normalize('NFC',text)); porter=PorterStemmer(); tagged=None
    result={'stems':[{'word':w,'stem':porter.stem(w)} for w in words]}
    try:
        tagged=nltk.pos_tag(words)
        result['pos']=[{'word':w,'tag':p} for w,p in tagged]
        mapper={'J':'a','V':'v','N':'n','R':'r'}; lemma=WordNetLemmatizer()
        result['lemmas']=[{'word':w,'lemma':lemma.lemmatize(w.lower(),mapper.get(p[:1],'n'))} for w,p in tagged]
    except LookupError:
        result['resource_note']='Run python scripts/download_nltk.py for English POS, WordNet and NER. No tags or lemmas are fabricated.'
    return result,tagged

class Engine:
    def __init__(self):
        self.rows=json.loads((ROOT/'data/training.json').read_text(encoding='utf-8'))
        self.texts=[r['text'] for r in self.rows]
        self.vectorizer,self.classifier,self.x,self.routing_rows,self.training_info=load_service()
        # Word-context SVD provides actual dense distributional word embeddings.
        self.words=sorted({w for t in self.texts for w in tokenize(t)})
        self.wi={w:i for i,w in enumerate(self.words)}
        matrix=np.zeros((len(self.words),len(self.words)),dtype=np.float64)
        for text in self.texts:
            ws=tokenize(text)
            for i,w in enumerate(ws):
                for j in range(max(0,i-2),min(len(ws),i+3)):
                    if j!=i: matrix[self.wi[w],self.wi[ws[j]]]+=1
        total=matrix.sum(); den=matrix.sum(1)[:,None]*matrix.sum(0)[None,:]
        ppmi=np.maximum(0,np.log((matrix*total+1e-12)/(den+1e-12)))
        self.word_svd=TruncatedSVD(n_components=24,random_state=7)
        self.embeddings=self.word_svd.fit_transform(ppmi)
        self.ngrams={(lang,n):NGramModel([r['text'] for r in self.rows if r['lang']==lang],n) for lang in ('en','hi','mr') for n in (1,2,3)}
        self.topic_vector=CountVectorizer(tokenizer=tokenize,token_pattern=None,lowercase=False,min_df=1)
        self.cx=self.topic_vector.fit_transform(self.texts)
        self.lda=LatentDirichletAllocation(n_components=5,random_state=7,max_iter=15).fit(self.cx)
        # Guide retrieval uses TF-IDF with document SVD (LSA), independently of word SVD.
        self.guide_rows=[]
        from i18n import CATEGORIES, COPY
        for category,langs in CATEGORIES.items():
            for lang,title in langs.items():
                sample=' '.join(r['text'] for r in self.rows if r['category']==category and r['lang']==lang)
                self.guide_rows.append(dict(title=title,text=sample,display=COPY[lang]['guidance_body'],category=category,lang=lang,source='authored demo guide'))
        extra=ROOT/'data/scraped.json'
        if extra.exists():
            for item in json.loads(extra.read_text(encoding='utf-8')):
                if item.get('lang') in ('en','hi','mr'):
                    self.guide_rows.append(item)
        self.guide_vector=TfidfVectorizer(analyzer='char',ngram_range=(2,4))
        gx=self.guide_vector.fit_transform([r['text'] for r in self.guide_rows])
        self.guide_svd=TruncatedSVD(n_components=min(10,gx.shape[0]-1,gx.shape[1]-1),random_state=7)
        self.guide_embeddings=self.guide_svd.fit_transform(gx)
        self._pos_model=None
    def classify(self,text):
        q=self.vectorizer.transform([text]); probs=self.classifier.predict_proba(q)[0]
        best=int(np.argmax(probs)); sim=float(cosine_similarity(q,self.x).max())
        order=sorted(zip(self.classifier.classes_,probs),key=lambda v:-v[1])
        # Heuristic abstention, not a calibrated certainty threshold.
        has_domain=domain_terms_present(text)
        unknown=not has_domain or sim<.12 or float(probs[best])<.30
        return {'category':None if unknown else str(self.classifier.classes_[best]),'ranking':[{'category':c,'model_score':round(float(p),3)} for c,p in order],'nearest_training_similarity':round(sim,3),'method':'Domain-word guard + character TF-IDF + logistic regression. Model scores are not calibrated confidence.','training':self.training_info}
    def related(self,text,lang):
        q=self.guide_svd.transform(self.guide_vector.transform([text]))
        scores=cosine_similarity(q,self.guide_embeddings)[0]
        indexes=sorted((i for i,g in enumerate(self.guide_rows) if g['lang']==lang),key=lambda i:-scores[i])
        return [{**{k:v for k,v in self.guide_rows[i].items() if k!='text'},'similarity':round(float(scores[i]),3)} for i in indexes[:3] if scores[i]>.12]
    def topics(self):
        names=self.topic_vector.get_feature_names_out()
        result=[]
        for i,weights in enumerate(self.lda.components_):
            dominant=self.lda.transform(self.cx).argmax(axis=1)
            subset=[r['text'] for j,r in enumerate(self.rows) if dominant[j]==i]
            tones=Counter(sentiment(t)['tone'] for t in subset)
            result.append({'topic':i+1,'words':[str(names[j]) for j in weights.argsort()[-8:][::-1]],'documents':len(subset),'tone_counts':dict(tones)})
        return {'method':'LDA on word counts; five topics chosen for demonstration. Topics are unsupervised and may reflect language as well as service. Tone counts use the lexical baseline.','topics':result}
    def embedding_classifier(self,text,lang):
        if lang!='en':
            return {'status':'English-only POS + embedding classifier. Multilingual service routing uses the separate character TF-IDF model.'}
        try:
            def features(t):
                ws=tokenize(t); tags=nltk.pos_tag(ws)
                vecs=[self.embeddings[self.wi[w]] for w in ws if w in self.wi]
                avg=np.mean(vecs,axis=0) if vecs else np.zeros(24)
                pos=np.array([sum(tag.startswith(p) for _,tag in tags)/max(1,len(tags)) for p in ['NN','VB','JJ','RB']])
                return np.concatenate([avg,pos])
            if self._pos_model is None:
                en=[r for r in self.rows if r['lang']=='en']
                x=np.vstack([features(r['text']) for r in en])
                self._pos_model=LogisticRegression(C=5,max_iter=1000,random_state=7).fit(x,[r['category'] for r in en])
            p=self._pos_model.predict_proba([features(text)])[0]
            return {'category':str(self._pos_model.classes_[p.argmax()]),'method':'Mean 24D PPMI-SVD word embeddings + normalized noun/verb/adjective/adverb counts → logistic regression. Toy corpus; English only.'}
        except LookupError:
            return {'status':'Unavailable. Run python scripts/download_nltk.py to install the English POS resource.'}
    def inspect(self,text,lang,n=2):
        words=tokenize(text); en,tagged=english_analysis(text) if lang=='en' else ({'resource_note':'English Porter/WordNet/POS intentionally not applied to Hindi or Marathi.'},None)
        q=self.vectorizer.transform([text]).toarray()[0]; names=self.vectorizer.get_feature_names_out()
        features=[{'feature':str(names[i]),'weight':round(float(q[i]),4)} for i in q.argsort()[-12:][::-1] if q[i]>0]
        word=next((w for w in words if w in self.wi),None)
        embedding=None
        if word:
            vec=self.embeddings[self.wi[word]]; sims=cosine_similarity([vec],self.embeddings)[0]
            near=[self.words[i] for i in sims.argsort()[::-1] if self.words[i]!=word][:5]
            embedding={'word':word,'dimensions':len(vec),'first_8_values':np.round(vec[:8],4).tolist(),'neighbours':near,'method':'Window-2 word co-occurrence → PPMI → SVD. Tiny-corpus distributional embeddings; not cross-lingually aligned.'}
        return {'language':language_hint(text),'word_count':len(words),'sentence_count':len(sentences(text)),'tokens':words,'english':en,'entities':entities(text,lang,tagged),'service_classifier':self.classify(text),'pos_embedding_classifier':self.embedding_classifier(text,lang),'sentiment':sentiment(text),'tfidf_top_character_features':features,'word_embedding':embedding,'ngram':self.ngrams[(lang,n)].score(text)}
