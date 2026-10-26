"""Assignment-specific views of the existing JanSahay NLP algorithms.

No additional models are trained, no network requests are made, and demo runs
never write to the complaint tracker.
"""
from nlp import tokenize
from scripts.scrape import extract
from scripts.civic_assignment import summarize


def translated(en, hi, mr):
    return dict(en=en, hi=hi, mr=mr)


# The assignment numbering follows the user's original 11-item syllabus.
CATALOG = [
    dict(id=1, title=translated('Web scraping', 'वेब स्क्रैपिंग', 'वेब स्क्रॅपिंग'),
         feature=translated('Collect public civic guidance', 'सार्वजनिक नागरिक जानकारी एकत्र करना', 'सार्वजनिक नागरी माहिती गोळा करणे'),
         purpose=translated('Extract readable guidance from a public HTML page for local guidance search.', 'सार्वजनिक HTML पेज से पढ़ने योग्य जानकारी निकालकर स्थानीय खोज में उपयोग करें।', 'सार्वजनिक HTML पानावरील वाचनीय माहिती स्थानिक मार्गदर्शन शोधासाठी वापरा.'),
         method='Requests + robots.txt checks + BeautifulSoup → attributed data/scraped.json → LSA index after restart',
         limitation=translated('The browser demo extracts pasted HTML offline; it does not fetch a website. Run the shown terminal command on a permitted public page for live collection.', 'यह डेमो चिपकाए गए HTML पर ऑफलाइन चलता है। वेबसाइट से डेटा लाने के लिए अनुमति वाले सार्वजनिक पेज पर दिया गया टर्मिनल कमांड चलाएँ।', 'हा डेमो पेस्ट केलेल्या HTML वर ऑफलाइन चालतो. प्रत्यक्ष वेबसाइटवरील माहिती मिळवण्यासाठी परवानगी असलेल्या सार्वजनिक पानावर दिलेली टर्मिनल कमांड चालवा.'),
         files=['scripts/scrape.py', 'nlp.py: Engine.related']),
    dict(id=2, title=translated('Language, counts & tokenization', 'भाषा, गिनती और टोकन', 'भाषा, मोजणी आणि टोकन'),
         feature=translated('Understand civic complaint text', 'नागरिक शिकायत के पाठ को समझना', 'नागरी तक्रारीचा मजकूर समजून घेणे'),
         purpose=translated('Detect a language hint and count words/sentences while preserving Hindi and Marathi vowel marks.', 'भाषा का अनुमान, शब्द और वाक्य गिनें; हिन्दी और मराठी की मात्राएँ सुरक्षित रहें।', 'भाषेचा अंदाज, शब्द व वाक्यांची मोजणी करा; हिंदी व मराठीच्या मात्रा जतन करा.'),
         method='langdetect + Unicode NFC normalization + Unicode-aware tokenization',
         limitation=translated('HuffPost supplies the assignment methods only. This project analyzes JanSahay civic messages. A language hint can be wrong, especially for short or mixed text.', 'HuffPost केवल विधियों का संदर्भ है। यहाँ JanSahay के नागरिक संदेश हैं। छोटे या मिश्रित पाठ में भाषा का अनुमान गलत हो सकता है।', 'HuffPost हा केवळ पद्धतींचा संदर्भ आहे. येथे JanSahay चे नागरी संदेश आहेत. लहान किंवा मिश्र मजकुरातील भाषेचा अंदाज चुकू शकतो.'),
         files=['scripts/civic_assignment.py', 'nlp.py: tokenize, sentences, language_hint']),
    dict(id=3, title=translated('Stemming & lemmatization', 'स्टेमिंग और लेमेटाइज़ेशन', 'स्टेमिंग आणि लेमॅटायझेशन'),
         feature=translated('Inspect English word normalization', 'अंग्रेज़ी शब्दों का सामान्यीकरण', 'इंग्रजी शब्दांचे सामान्यीकरण'),
         purpose=translated('Compare original English words with Porter stems and WordNet lemmas in the educational lab.', 'लैब में मूल अंग्रेज़ी शब्दों की तुलना Porter stems और WordNet lemmas से करें।', 'लॅबमध्ये मूळ इंग्रजी शब्दांची Porter stems व WordNet lemmas सोबत तुलना करा.'),
         method='PorterStemmer + POS-aware WordNetLemmatizer',
         limitation=translated('English only. WordNet and POS require optional NLTK resources; missing results are never invented. Citizen complaint text is kept unchanged.', 'केवल अंग्रेज़ी। WordNet और POS के लिए वैकल्पिक NLTK संसाधन चाहिए। शिकायत का मूल पाठ नहीं बदला जाता।', 'फक्त इंग्रजी. WordNet व POS साठी ऐच्छिक NLTK साधने आवश्यक आहेत. तक्रारीचा मूळ मजकूर बदलत नाही.'),
         files=['nlp.py: english_analysis', 'scripts/download_nltk.py']),
    dict(id=4, title=translated('POS, embeddings & classification', 'POS, एम्बेडिंग और वर्गीकरण', 'POS, एम्बेडिंग आणि वर्गीकरण'),
         feature=translated('Explain complaint category prediction', 'शिकायत श्रेणी का अनुमान समझना', 'तक्रारीच्या वर्गाचा अंदाज समजून घेणे'),
         purpose=translated('Inspect word vectors and the separate English POS + embedding classifier; compare it with the public service classifier.', 'शब्द वेक्टर और अलग अंग्रेज़ी POS + embedding classifier देखें; सार्वजनिक सेवा classifier से तुलना करें।', 'शब्द व्हेक्टर व स्वतंत्र इंग्रजी POS + embedding classifier पाहा; मुख्य सेवा classifier सोबत तुलना करा.'),
         method='Word-context PPMI → 24D SVD vectors + POS ratios → logistic regression; public routing uses character TF-IDF',
         limitation=translated('English POS classifier requires NLTK resources and uses a small demo corpus. It is separate from the HF-trained multilingual routing model.', 'अंग्रेज़ी POS classifier के लिए NLTK चाहिए और यह छोटे डेमो डेटा पर है। यह HF-trained मुख्य मॉडल से अलग है।', 'इंग्रजी POS classifier साठी NLTK आवश्यक असून त्याचा डेमो डेटा लहान आहे. तो HF-trained मुख्य मॉडेलपेक्षा स्वतंत्र आहे.'),
         files=['nlp.py: Engine.embedding_classifier, Engine.inspect', 'service_model.py']),
    dict(id=5, title=translated('Named entity recognition', 'नामित इकाई पहचान', 'नामित घटक ओळख'),
         feature=translated('Spot places, dates & postal codes', 'स्थान, तारीख और पिन कोड पहचानना', 'ठिकाणे, तारखा आणि पिन कोड ओळखणे'),
         purpose=translated('Highlight possible entities in a complaint. The location entered by the citizen remains authoritative.', 'शिकायत में संभावित इकाइयाँ देखें। नागरिक द्वारा भरा गया स्थान ही अंतिम रहता है।', 'तक्रारीतील संभाव्य घटक पाहा. नागरिकाने दिलेले ठिकाणच अंतिम मानले जाते.'),
         method='NLTK English statistical NER when installed; labelled place gazetteer + regex baseline',
         limitation=translated('Hindi/Marathi use only a small gazetteer and regex; this is not a complete multilingual NER model.', 'हिन्दी/मराठी में छोटी स्थान-सूची और regex हैं; यह पूर्ण बहुभाषी NER मॉडल नहीं है।', 'हिंदी/मराठीसाठी छोटी स्थानसूची व regex आहेत; हे संपूर्ण बहुभाषिक NER मॉडेल नाही.'),
         files=['nlp.py: entities']),
    dict(id=6, title=translated('TF-IDF', 'TF-IDF', 'TF-IDF'),
         feature=translated('Represent complaint text for routing', 'श्रेणी के लिए शिकायत के पाठ का निरूपण', 'वर्गीकरणासाठी तक्रारीचे संख्यात्मक रूप'),
         purpose=translated('See the weighted character features used by the trained service classifier.', 'प्रशिक्षित सेवा classifier द्वारा उपयोग किए गए भारित character features देखें।', 'प्रशिक्षित सेवा classifier ने वापरलेली भारित character features पाहा.'),
         method='Character 2–5 grams → sublinear TF × smoothed IDF → L2 normalization → logistic regression',
         limitation=translated('TF-IDF features are not word embeddings. Displayed values are normalized query weights, not standalone importance or confidence.', 'TF-IDF features word embeddings नहीं हैं। दिखाए गए मान normalized query weights हैं, confidence नहीं।', 'TF-IDF features म्हणजे word embeddings नाहीत. दाखवलेली मूल्ये normalized query weights आहेत, confidence नाही.'),
         files=['service_model.py: fit_service', 'nlp.py: Engine.inspect']),
    dict(id=7, title=translated('N-gram models', 'N-gram मॉडल', 'N-gram मॉडेल'),
         feature=translated('Inspect local word-sequence patterns', 'स्थानीय शब्द-क्रम के पैटर्न', 'स्थानिक शब्दक्रमातील नमुने'),
         purpose=translated('Choose unigram, bigram or trigram and inspect learned counts and sentence boundaries.', 'Unigram, bigram या trigram चुनकर सीखे गए counts और वाक्य-सीमाएँ देखें।', 'Unigram, bigram किंवा trigram निवडून शिकलेली मोजणी व वाक्यसीमा पाहा.'),
         method='Same-language authored civic corpus → n-gram/context counts + Laplace smoothing (alpha = 1)',
         limitation=translated('An educational model built from 30 authored messages per language, not the larger routing corpus or a grammar checker.', 'प्रति भाषा 30 लिखे गए संदेशों पर शैक्षिक मॉडल; यह बड़ा routing corpus या grammar checker नहीं है।', 'प्रत्येक भाषेतील 30 लिहिलेल्या संदेशांवर शैक्षणिक मॉडेल; हा मोठा routing corpus किंवा grammar checker नाही.'),
         files=['nlp.py: NGramModel']),
    dict(id=8, title=translated('Sequence probability', 'शब्द-क्रम की प्रायिकता', 'शब्दक्रमाची संभाव्यता'),
         feature=translated('Explain probability step by step', 'प्रायिकता को चरण-दर-चरण समझना', 'संभाव्यता टप्प्याटप्प्याने समजून घेणे'),
         purpose=translated('Show conditional probabilities, the product, log probability and perplexity for the entered sentence.', 'दिए गए वाक्य की conditional probabilities, गुणनफल, log probability और perplexity देखें।', 'दिलेल्या वाक्याच्या conditional probabilities, गुणाकार, log probability व perplexity पाहा.'),
         method='P(sequence) = product P(word | context); log P = sum log P; perplexity = exp(−log P / scored tokens)',
         limitation=translated('Includes end-of-sentence and maps unseen words to <UNK>. Probability is not complaint quality, truth or urgency.', 'वाक्य का अंत शामिल है और अनदेखे शब्द <UNK> बनते हैं। यह शिकायत की गुणवत्ता, सत्यता या तात्कालिकता का माप नहीं है।', 'वाक्याचा शेवट समाविष्ट असून नवे शब्द <UNK> होतात. हा तक्रारीची गुणवत्ता, सत्यता किंवा तातडीचा मापदंड नाही.'),
         files=['nlp.py: NGramModel.score']),
    dict(id=9, title=translated('LSI / LDA topic modelling', 'LSI / LDA विषय मॉडलिंग', 'LSI / LDA विषय मॉडेलिंग'),
         feature=translated('Find related guidance & corpus themes', 'संबंधित मार्गदर्शन और विषय ढूँढना', 'संबंधित मार्गदर्शन व विषय शोधणे'),
         purpose=translated('Use LSA/LSI to retrieve same-language guidance and LDA to explore five themes in the demo corpus.', 'LSA/LSI से उसी भाषा का मार्गदर्शन खोजें और LDA से डेमो corpus के पाँच विषय देखें।', 'LSA/LSI ने त्याच भाषेतील मार्गदर्शन शोधा व LDA ने डेमो corpus मधील पाच विषय पाहा.'),
         method='Guides: TF-IDF → truncated SVD → cosine similarity; topics: word counts → LDA',
         limitation=translated('Topics are unsupervised and may reflect language. Demo guidance is authored, not official advice; imported pages carry their source.', 'विषय unsupervised हैं और भाषा भी दर्शा सकते हैं। डेमो मार्गदर्शन लिखा गया है, आधिकारिक सलाह नहीं है।', 'विषय unsupervised असून भाषा दर्शवू शकतात. डेमो मार्गदर्शन लिहिलेले आहे, अधिकृत सल्ला नाही.'),
         files=['nlp.py: Engine.related, Engine.topics']),
    dict(id=10, title=translated('Sentiment, emotions & opinion mining', 'भाव, भावना और राय विश्लेषण', 'भाव, भावना आणि मत विश्लेषण'),
         feature=translated('Explore feedback tone by topic', 'विषय के अनुसार प्रतिक्रिया का भाव', 'विषयानुसार अभिप्रायाचा भाव'),
         purpose=translated('Inspect lexical sentiment/emotion cues and aggregate tone counts for each LDA topic.', 'शब्द-आधारित sentiment/emotion संकेत और हर LDA विषय के tone counts देखें।', 'शब्दांवर आधारित sentiment/emotion संकेत व प्रत्येक LDA विषयाची भावमोजणी पाहा.'),
         method='Authored multilingual lexicons + limited negation rules; LDA topic × tone counts',
         limitation=translated('Not a trained sentiment model. Sarcasm and nuanced emotion are unsupported; sentiment never decides complaint urgency.', 'यह trained sentiment model नहीं है। व्यंग्य और जटिल भाव नहीं समझता; इससे शिकायत की प्राथमिकता तय नहीं होती।', 'हे trained sentiment model नाही. उपरोध व सूक्ष्म भावना समर्थित नाहीत; यावरून तक्रारीची तातडी ठरत नाही.'),
         files=['nlp.py: sentiment, Engine.topics']),
    dict(id=11, title=translated('Integrated NLP mini project', 'एकीकृत NLP मिनी प्रोजेक्ट', 'एकत्रित NLP मिनी प्रोजेक्ट'),
         feature=translated('Prepare a complaint & manage follow-ups', 'शिकायत तैयार करना और अनुवर्ती रिकॉर्ड रखना', 'तक्रार तयार करणे व पाठपुरावा नोंदवणे'),
         purpose=translated('Trace the real analysis pipeline, then use Report a problem to edit/save a complaint and My complaints for local tracking.', 'असली analysis pipeline देखें, फिर Report a problem से शिकायत संपादित/सहेजें और My complaints में स्थानीय रिकॉर्ड रखें।', 'प्रत्यक्ष analysis pipeline पाहा; नंतर Report a problem मधून तक्रार संपादित/जतन करा व My complaints मध्ये स्थानिक नोंद ठेवा.'),
         method='Language hint → guarded TF-IDF routing → same-language LSA guidance → authored complaint template → explicit local save',
         limitation=translated('This demo never saves or submits anything. Official submission is external and every tracker status is user-recorded.', 'यह डेमो कुछ सहेजता या जमा नहीं करता। आधिकारिक जमा बाहरी पोर्टल पर है और tracker की स्थिति उपयोगकर्ता दर्ज करता है।', 'हा डेमो काहीही जतन किंवा सादर करत नाही. अधिकृत सादरीकरण बाह्य पोर्टलवर होते व tracker स्थिती वापरकर्ता नोंदवतो.'),
         files=['app.py: analyze_data', 'workflow.py', 'static/app.js']),
]


def run_assignment(number, engine, text, lang, n=2, html='', corpus=False, pipeline=None):
    """Return only the evidence relevant to the selected syllabus assignment."""
    if number == 1:
        title, content = extract(html)
        return dict(mode='offline_html_extraction', title=title, extracted_text=content,
                    character_count=len(content), word_count=len(tokenize(content)),
                    live_command='python scripts/scrape.py "https://YOUR-PERMITTED-PAGE" --lang '+lang,
                    storage='data/scraped.json', network_request_made=False)
    if number == 2 and corpus:
        return summarize(engine_root()/'data/service_train.json')
    if number == 11:
        return pipeline
    if number in (7, 8):
        model = engine.ngrams[(lang, n)]
        if number == 8:
            result = model.score(text)
            result['probability_factors'] = ' × '.join(str(t['probability']) for t in result['terms'])
            return result
        counts = model.counts.most_common(18)
        return dict(n=n, alpha=model.alpha, language=lang,
                    training_messages=sum(r['lang']==lang for r in engine.rows),
                    vocabulary_size=len(model.vocab), unique_ngrams=len(model.counts),
                    input_ngrams=[dict(context=t['context'], word=t['word'], count=model.counts[tuple(t['context'])+(t['word'],)], probability=t['probability']) for t in model.score(text)['terms']],
                    ngram_counts=[dict(context=list(k[:-1]), word=k[-1], count=c,
                                       context_count=model.contexts[k[:-1]],
                                       smoothed_probability=round(model.conditional(k[:-1], k[-1]),7)) for k,c in counts])
    if number == 9:
        return dict(related_guidance=engine.related(text, lang), **engine.topics())
    data = engine.inspect(text, lang, n)
    if number == 2:
        return {k: data[k] for k in ('language','word_count','sentence_count','tokens')}
    if number == 3:
        return dict(english=data['english'])
    if number == 4:
        return dict(pos=data['english'].get('pos', []),
                    resource_note=data['english'].get('resource_note',''),
                    word_embedding=data['word_embedding'],
                    pos_embedding_classifier=data['pos_embedding_classifier'],
                    service_classifier=data['service_classifier'])
    if number == 5:
        return data['entities']
    if number == 6:
        return dict(formula='idf(t) = ln((1 + N) / (1 + df(t))) + 1; tf = 1 + ln(count); L2 normalized',
                    top_features=data['tfidf_top_character_features'],
                    training_messages=engine.training_info['training_messages'],
                    ranking=data['service_classifier']['ranking'])
    if number == 10:
        return dict(sentiment=data['sentiment'], topic_opinion=engine.topics())
    raise ValueError('Unknown assignment')


def engine_root():
    from nlp import ROOT
    return ROOT
