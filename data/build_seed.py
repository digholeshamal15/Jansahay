"""Rebuild the small, authored demonstration corpus. Not real citizen data."""
import json
from pathlib import Path
root = Path(__file__).parent
# Separate examples rather than translations used as a substitute for language models.
examples = {
'water': {
'en':['There is no water supply in our building','The drinking water is dirty and smells bad','A water pipe is leaking near my house','Water pressure is very low every morning','The public tap is broken','Our area has not received water for two days'],
'hi':['हमारे घर में पानी नहीं आ रहा है','पीने का पानी गंदा है और बदबू आती है','सड़क पर पानी की पाइप लीक हो रही है','सुबह पानी का दबाव बहुत कम है','सार्वजनिक नल टूट गया है','हमारे मोहल्ले में दो दिन से पानी नहीं आया'],
'mr':['आमच्या घरी पाणी येत नाही','पिण्याचे पाणी घाण आहे आणि वास येतो','रस्त्यावर पाण्याची पाइप फुटली आहे','सकाळी पाण्याचा दाब खूप कमी असतो','सार्वजनिक नळ तुटला आहे','आमच्या भागात दोन दिवस पाणी आले नाही']},
'garbage': {
'en':['Garbage has not been collected from our street','There is a pile of waste near the bus stop','The dustbin is overflowing and smells bad','Please arrange regular garbage collection','People are dumping rubbish near the market','The garbage truck has not visited our lane'],
'hi':['हमारी गली से कचरा नहीं उठाया गया','बस स्टॉप के पास कूड़े का ढेर है','कूड़ेदान भर गया है और बदबू आ रही है','कृपया रोज कचरा उठाने की व्यवस्था करें','बाजार के पास लोग कूड़ा फेंक रहे हैं','कचरे की गाड़ी हमारी गली में नहीं आई'],
'mr':['आमच्या गल्लीतला कचरा उचलला नाही','बस थांब्याजवळ कचऱ्याचा ढीग आहे','कचरापेटी भरली आहे आणि वास येतो','कृपया नियमित कचरा उचलण्याची व्यवस्था करा','बाजाराजवळ लोक कचरा टाकत आहेत','कचरा गाडी आमच्या गल्लीत आली नाही']},
'roads': {
'en':['There are large potholes on the road','The road surface is broken near the school','Please repair the damaged footpath','Loose paving stones make walking difficult','A large hole in the street needs repair','The pavement is damaged outside our building'],
'hi':['सड़क पर बड़े गड्ढे हैं','स्कूल के पास सड़क टूट गई है','कृपया टूटे हुए फुटपाथ की मरम्मत करें','फुटपाथ के पत्थर उखड़ गए हैं','गली में बड़ा गड्ढा है इसे ठीक करें','हमारी इमारत के बाहर फुटपाथ खराब है'],
'mr':['रस्त्यावर मोठे खड्डे आहेत','शाळेजवळचा रस्ता खराब झाला आहे','कृपया तुटलेला पदपथ दुरुस्त करा','पदपथाचे दगड निखळले आहेत','गल्लीत मोठा खड्डा पडला आहे','आमच्या इमारतीसमोरचा पदपथ खराब आहे']},
'lights': {
'en':['The streetlight outside my house is not working','Our lane is dark because the street lamp is broken','Please repair the flickering public streetlight','Three street lights are off near the park','The road lamp has been off for a week','A streetlight pole needs maintenance'],
'hi':['मेरे घर के बाहर स्ट्रीट लाइट बंद है','गली की बत्ती खराब होने से अंधेरा है','सड़क की टिमटिमाती लाइट ठीक करें','पार्क के पास तीन स्ट्रीट लाइट बंद हैं','सड़क की बत्ती एक हफ्ते से बंद है','स्ट्रीट लाइट के खंभे की मरम्मत चाहिए'],
'mr':['माझ्या घराबाहेरचा पथदिवा बंद आहे','गल्लीतला दिवा खराब असल्याने अंधार आहे','रस्त्यावरचा लुकलुकणारा दिवा दुरुस्त करा','उद्यानाजवळ तीन पथदिवे बंद आहेत','रस्त्यावरील दिवा एक आठवडा बंद आहे','पथदिव्याच्या खांबाची दुरुस्ती हवी आहे']},
'drainage': {
'en':['The drain is blocked and sewage is overflowing','Dirty sewage water is entering our lane','Please clean the blocked gutter','The manhole cover is missing','Wastewater is overflowing from the drain','The sewer line is blocked near the market'],
'hi':['नाली बंद है और गंदा पानी बह रहा है','सीवर का पानी हमारी गली में आ रहा है','कृपया बंद नाली साफ करें','मैनहोल का ढक्कन गायब है','नाले से गंदा पानी बाहर आ रहा है','बाजार के पास सीवर लाइन जाम है'],
'mr':['गटार तुंबले आहे आणि सांडपाणी वाहत आहे','आमच्या गल्लीत सांडपाणी येत आहे','कृपया तुंबलेली नाली साफ करा','मॅनहोलचे झाकण गायब आहे','नाल्यातून घाण पाणी बाहेर येत आहे','बाजाराजवळ गटाराची लाइन तुंबली आहे']}}
rows=[dict(text=t,category=c,lang=l) for c,langs in examples.items() for l,items in langs.items() for t in items]
(root/'training.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
# Handwritten held-out smoke set: not a representative benchmark.
tests=[
('en','water','Water supply stopped yesterday in my apartment'),('hi','water','आज हमारे घर पानी की सप्लाई बंद है'),('mr','water','कालपासून आमच्या घरी पाणीपुरवठा बंद आहे'),
('en','garbage','Uncollected garbage is lying outside the shop'),('hi','garbage','दुकान के सामने कूड़े का ढेर लगा है'),('mr','garbage','दुकानासमोर कचरा साचला आहे'),
('en','roads','Potholes make the main road difficult to use'),('hi','roads','मुख्य सड़क पर बहुत सारे गड्ढे हो गए हैं'),('mr','roads','मुख्य रस्त्यावर अनेक खड्डे पडले आहेत'),
('en','lights','Street lamps near our houses have stopped working'),('hi','lights','हमारे मकान के पास सड़क की लाइट खराब है'),('mr','lights','आमच्या घराजवळ रस्त्याचा दिवा लागत नाही'),
('en','drainage','Sewage keeps coming out of the blocked drain'),('hi','drainage','बंद नाले से सीवर का पानी निकल रहा है'),('mr','drainage','तुंबलेल्या गटारातून सांडपाणी बाहेर पडते')]
(root/'evaluation.json').write_text(json.dumps([dict(lang=l,category=c,text=t) for l,c,t in tests],ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Wrote {len(rows)} training and {len(tests)} evaluation examples')
