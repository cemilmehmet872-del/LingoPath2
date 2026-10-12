import difflib
import json
import random
import re
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import streamlit as st

try:
    from streamlit_sortables import sort_items  # sürükle-bırak için: pip install streamlit-sortables
except ImportError:
    sort_items = None

st.set_page_config(page_title="LingoPath", page_icon="✏️", layout="centered")

SAVE = Path("lingopath_progress.json")
DAILY_GOAL = 30  # günlük XP hedefi
INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 15}  # kutu -> kaç gün sonra tekrar
LEVELS = ["Tümü", "Başlangıç", "Orta", "İleri"]

B, O, I = "Başlangıç", "Orta", "İleri"
WORDS = [
    # ---- Başlangıç ----
    ("apple", "elma", "I eat an apple.", B),
    ("borrow", "ödünç almak", "Can I borrow your pen?", B),
    ("quiet", "sessiz", "The library is quiet.", B),
    ("careful", "dikkatli", "Be careful when you cross the road.", B),
    ("journey", "yolculuk", "Learning English is a journey.", B),
    ("beautiful", "güzel", "The garden is beautiful.", B),
    ("delicious", "lezzetli", "This soup is delicious.", B),
    ("friendly", "arkadaş canlısı", "Our new teacher is friendly.", B),
    ("usually", "genellikle", "I usually walk to school.", B),
    ("remember", "hatırlamak", "Please remember my name.", B),
    ("water", "su", "I drink water every day.", B),
    ("book", "kitap", "This book is interesting.", B),
    ("house", "ev", "Our house has a small garden.", B),
    ("family", "aile", "I love my family.", B),
    ("morning", "sabah", "I wake up early in the morning.", B),
    ("night", "gece", "The stars shine at night.", B),
    ("happy", "mutlu", "She is happy today.", B),
    ("sad", "üzgün", "He looks sad.", B),
    ("big", "büyük", "They live in a big city.", B),
    ("small", "küçük", "I have a small bag.", B),
    ("fast", "hızlı", "The train is very fast.", B),
    ("slow", "yavaş", "The turtle is slow.", B),
    ("hot", "sıcak", "The tea is hot.", B),
    ("cold", "soğuk", "It is cold in winter.", B),
    ("open", "açmak", "Please open the window.", B),
    ("close", "kapatmak", "Close the door, please.", B),
    ("buy", "satın almak", "I want to buy a new phone.", B),
    ("sell", "satmak", "They sell fresh bread.", B),
    ("ask", "sormak", "You can ask me anything.", B),
    ("answer", "cevap", "I know the answer.", B),
    ("understand", "anlamak", "I understand the lesson.", B),
    ("walk", "yürümek", "We walk in the park.", B),
    ("run", "koşmak", "He runs every morning.", B),
    ("sleep", "uyumak", "Babies sleep a lot.", B),
    ("cook", "pişirmek", "My mother cooks dinner.", B),
    ("read", "okumak", "I read before bed.", B),
    ("write", "yazmak", "Write your name here.", B),
    ("listen", "dinlemek", "Listen to the teacher.", B),
    ("speak", "konuşmak", "Can you speak slowly?", B),
    ("weather", "hava durumu", "The weather is nice today.", B),
    ("city", "şehir", "Istanbul is a huge city.", B),
    ("street", "sokak", "The street is full of people.", B),
    ("kitchen", "mutfak", "She is in the kitchen.", B),
    ("birthday", "doğum günü", "Today is my birthday.", B),
    # ---- Orta ----
    ("improve", "geliştirmek", "I want to improve my English.", O),
    ("although", "her ne kadar", "Although it was late, we continued.", O),
    ("environment", "çevre", "We should protect the environment.", O),
    ("discover", "keşfetmek", "I want to discover new places.", O),
    ("challenge", "zorluk", "Learning a language is a challenge.", O),
    ("confident", "kendine güvenen", "I feel confident when I practise.", O),
    ("achieve", "başarmak", "You can achieve your goals.", O),
    ("curious", "meraklı", "Curious students ask questions.", O),
    ("important", "önemli", "Sleep is important for learning.", O),
    ("solution", "çözüm", "We found a solution to the problem.", O),
    ("protect", "korumak", "We must protect nature.", O),
    ("successful", "başarılı", "Practice helps you become successful.", O),
    ("experience", "deneyim", "She has a lot of experience.", O),
    ("decision", "karar", "It was a difficult decision.", O),
    ("popular", "popüler", "This song is very popular.", O),
    ("probably", "muhtemelen", "It will probably rain tomorrow.", O),
    ("recently", "yakın zamanda", "I recently started a new course.", O),
    ("strange", "garip", "I heard a strange noise.", O),
    ("prepare", "hazırlamak", "We prepare for the exam together.", O),
    ("explain", "açıklamak", "Can you explain this rule?", O),
    ("suggest", "önermek", "I suggest taking a short break.", O),
    ("depend", "bağlı olmak", "It depends on the weather.", O),
    ("manage", "idare etmek", "How do you manage your time?", O),
    ("avoid", "kaçınmak", "Try to avoid mistakes.", O),
    ("mistake", "hata", "Everyone makes mistakes.", O),
    ("compare", "karşılaştırmak", "Compare the two answers.", O),
    ("describe", "tanımlamak", "Describe your best friend.", O),
    ("develop", "gelişmek", "Children develop quickly.", O),
    ("patient", "sabırlı", "A good teacher is patient.", O),
    ("honest", "dürüst", "Please be honest with me.", O),
    ("generous", "cömert", "He is a generous man.", O),
    ("polite", "kibar", "She is always polite.", O),
    ("creative", "yaratıcı", "Children are very creative.", O),
    ("useful", "faydalı", "This app is useful.", O),
    ("common", "yaygın", "This is a common mistake.", O),
    ("allow", "izin vermek", "They do not allow phones here.", O),
    ("require", "gerektirmek", "This job requires patience.", O),
    ("provide", "sağlamak", "The school provides books.", O),
    ("increase", "artmak", "Prices increase every year.", O),
    ("reduce", "azaltmak", "We must reduce waste.", O),
    ("advice", "tavsiye", "Thank you for your advice.", O),
    ("society", "toplum", "Society is changing fast.", O),
    ("health", "sağlık", "Health is more important than money.", O),
    ("goal", "hedef", "My goal is to speak fluently.", O),
    ("habit", "alışkanlık", "Reading is a good habit.", O),
    ("schedule", "program", "I have a busy schedule.", O),
    # ---- İleri ----
    ("opportunity", "fırsat", "This is a great opportunity.", I),
    ("knowledge", "bilgi", "Knowledge grows when we learn.", I),
    ("independent", "bağımsız", "She is an independent learner.", I),
    ("achievement", "başarı", "Winning was a great achievement.", I),
    ("adequate", "yeterli", "The room is adequate for us.", I),
    ("ambitious", "hırslı", "She is an ambitious student.", I),
    ("consequence", "sonuç", "Every action has a consequence.", I),
    ("contribute", "katkıda bulunmak", "Everyone can contribute to the project.", I),
    ("determine", "belirlemek", "We need to determine the cause.", I),
    ("efficient", "verimli", "This method is very efficient.", I),
    ("fluent", "akıcı", "He is fluent in three languages.", I),
    ("inevitable", "kaçınılmaz", "Change is inevitable.", I),
    ("reliable", "güvenilir", "She is a reliable friend.", I),
    ("significant", "kayda değer", "There was a significant improvement.", I),
    ("sustainable", "sürdürülebilir", "We need sustainable energy.", I),
    ("thorough", "kapsamlı", "He did a thorough check.", I),
    ("overcome", "üstesinden gelmek", "You can overcome any obstacle.", I),
    ("obstacle", "engel", "Fear is the biggest obstacle.", I),
    ("perspective", "bakış açısı", "Try to see another perspective.", I),
    ("reluctant", "isteksiz", "He was reluctant to speak.", I),
    ("vague", "belirsiz", "Her answer was vague.", I),
    ("evidence", "kanıt", "There is no evidence yet.", I),
    ("emphasize", "vurgulamak", "Teachers emphasize practice.", I),
    ("tendency", "eğilim", "He has a tendency to be late.", I),
    ("willing", "istekli", "I am willing to help.", I),
]
WORDS = [dict(en=a, tr=b, example=c, level=d) for a, b, c, d in WORDS]
BY_EN = {w["en"]: w for w in WORDS}

PAGES = ["Bugün", "Kelimeler", "Tekrar", "Konuşma", "Test", "Oyunlar", "Macera",
         "Günlük Görev", "Rozetler", "İstatistik", "Günlük Konuşma", "AI Sohbet", "Defterim"]

# ---------- Macera: Kayıp Pasaport ----------
def C(en, tr, to, needs=None):
    return {"en": en, "tr": tr, "to": to, "needs": needs}


ADV_ITEMS = {"map": "🗺️ Harita", "clue": "💡 İpucu", "crystal": "💎 Kristal"}
ADVENTURE = {
    "start": {
        "text": "You arrive at Heathrow Airport in London. The airport is big and busy. "
                "You open your bag, but your passport is not there!",
        "tr": "Londra'daki Heathrow Havalimanı'na varıyorsun. Havalimanı büyük ve kalabalık. "
              "Çantanı açıyorsun ama pasaportun orada değil!",
        "choices": [
            C("Check your coat pocket.", "Ceket cebine bak.", "coat"),
            C("Ask the officer for help.", "Görevliden yardım iste.", "officer"),
            C("Walk to the café.", "Kafeye yürü.", "cafe"),
        ],
    },
    "coat": {
        "text": "You check your coat. In the pocket there is a small map of the airport. "
                "There is no passport, but the map shows a Lost Property Office near Gate 5.",
        "tr": "Ceketini kontrol ediyorsun. Cebinde havalimanının küçük bir haritası var. Pasaport yok "
              "ama harita, 5 numaralı kapının yakınında bir Kayıp Eşya Ofisi gösteriyor.",
        "gives": "map",
        "choices": [
            C("Follow the map to the Lost Property Office.", "Haritayı izleyip Kayıp Eşya Ofisi'ne git.", "lost_office"),
            C("Ask the officer first.", "Önce görevliye sor.", "officer"),
        ],
    },
    "officer": {
        "text": "The officer is polite but very busy. 'Please be patient,' she says. 'The line is long.'",
        "tr": "Görevli kibar ama çok meşgul. 'Lütfen sabırlı ol,' diyor. 'Sıra uzun.'",
        "choices": [
            C("Wait in line.", "Sırada bekle.", "long_wait"),
            C("Walk to the café.", "Kafeye yürü.", "cafe"),
            C("Show your map and ask about the Lost Property Office.",
              "Haritanı göster ve Kayıp Eşya Ofisi'ni sor.", "lost_office", needs="map"),
        ],
    },
    "long_wait": {
        "text": "You wait for forty minutes. At last the officer says, 'Sorry, I can not help you here. "
                "Try the Lost Property Office.' You feel tired and sad.",
        "tr": "Kırk dakika bekliyorsun. Sonunda görevli, 'Üzgünüm, burada sana yardım edemem. "
              "Kayıp Eşya Ofisi'ni dene.' diyor. Yorgun ve üzgün hissediyorsun.",
        "choices": [
            C("Go to the Lost Property Office.", "Kayıp Eşya Ofisi'ne git.", "lost_office"),
            C("Give up and go home.", "Pes et ve eve dön.", "end_giveup"),
        ],
    },
    "cafe": {
        "text": "The café is warm and the coffee smells delicious. A friendly waiter smiles at you. "
                "'Can I help you?' he asks.",
        "tr": "Kafe sıcak ve kahve lezzetli kokuyor. Arkadaş canlısı bir garson sana gülümsüyor. "
              "'Yardım edebilir miyim?' diye soruyor.",
        "choices": [
            C("Ask about your passport.", "Pasaportunu sor.", "waiter"),
            C("Buy a coffee and sit down.", "Bir kahve al ve otur.", "coffee"),
        ],
    },
    "waiter": {
        "text": "The waiter thinks for a moment. 'Yes! A man found a passport near the door. "
                "Please be careful with your bag next time,' he says.",
        "tr": "Garson bir an düşünüyor. 'Evet! Bir adam kapının yanında bir pasaport buldu. "
              "Lütfen bir dahaki sefere çantana dikkat et.' diyor.",
        "quiz": "careful", "ok": "waiter_ok", "bad": "waiter_bad",
    },
    "waiter_ok": {
        "text": "The waiter smiles. 'Good! The man took the passport to the Lost Property Office at Gate 5,' "
                "he says. You thank him and feel confident.",
        "tr": "Garson gülümsüyor. 'Güzel! Adam pasaportu 5 numaralı kapıdaki Kayıp Eşya Ofisi'ne götürdü.' "
              "diyor. Ona teşekkür ediyorsun ve kendine güveniyorsun.",
        "gives": "clue",
        "choices": [C("Hurry to the Lost Property Office.", "Acele edip Kayıp Eşya Ofisi'ne git.", "lost_office")],
    },
    "waiter_bad": {
        "text": "You do not understand the waiter. He repeats the words slowly and then points to Gate 5.",
        "tr": "Garsonu anlamıyorsun. Kelimeleri yavaşça tekrar ediyor, sonra 5 numaralı kapıyı gösteriyor.",
        "choices": [C("Go to Gate 5.", "5 numaralı kapıya git.", "lost_office")],
    },
    "coffee": {
        "text": "You sit down with your coffee and breathe slowly. Then you remember something: "
                "in the arrivals hall you stopped at the bookshop!",
        "tr": "Kahvenle oturuyor ve yavaşça nefes alıyorsun. Sonra bir şey hatırlıyorsun: "
              "geliş salonunda kitapçıda durmuştun!",
        "choices": [
            C("Run to the bookshop.", "Kitapçıya koş.", "bookshop"),
            C("Go to the Lost Property Office.", "Kayıp Eşya Ofisi'ne git.", "lost_office"),
        ],
    },
    "bookshop": {
        "text": "The bookshop is very quiet. A sign on the wall says: 'Please be quiet.' "
                "Next to a red book you see something blue... your passport!",
        "tr": "Kitapçı çok sessiz. Duvardaki bir tabela diyor ki: 'Lütfen sessiz olun.' "
              "Kırmızı bir kitabın yanında mavi bir şey görüyorsun... pasaportun!",
        "quiz": "quiet", "ok": "end_secret", "bad": "bookshop_bad",
    },
    "bookshop_bad": {
        "text": "You do not know the word, so you shout 'My passport!' Everyone looks at you. "
                "The shop assistant says, 'Shh!'",
        "tr": "Kelimeyi bilmiyorsun ve 'Pasaportum!' diye bağırıyorsun. Herkes sana bakıyor. "
              "Tezgâhtar 'Şşş!' diyor.",
        "choices": [C("Say sorry and look again.", "Özür dile ve tekrar bak.", "bookshop")],
    },
    "lost_office": {
        "text": "A kind woman works at the Lost Property Office. 'Hello! Please describe your passport,' she says.",
        "tr": "Kayıp Eşya Ofisi'nde nazik bir kadın çalışıyor. 'Merhaba! Lütfen pasaportunu tarif et.' diyor.",
        "quiz": "describe", "ok": "lost_ok", "bad": "lost_bad",
    },
    "lost_ok": {
        "text": "You describe it well: 'It is blue and it has a small photo.' The woman opens a box and smiles. "
                "'I think we found it!'",
        "tr": "Pasaportunu iyi tarif ediyorsun: 'Mavi ve küçük bir fotoğrafı var.' Kadın bir kutu açıyor ve "
              "gülümsüyor. 'Sanırım onu bulduk!'",
        "choices": [C("Thank her and take the passport.", "Ona teşekkür et ve pasaportu al.", "end_good")],
    },
    "lost_bad": {
        "text": "You do not know what to say. The woman smiles and says, 'Take your time. Let's try again.'",
        "tr": "Ne diyeceğini bilmiyorsun. Kadın gülümsüyor ve 'Acele etme. Tekrar deneyelim.' diyor.",
        "choices": [C("Try again calmly.", "Sakin sakin tekrar dene.", "lost_office")],
    },
    "end_good": {
        "end": "good", "title": "Mutlu son", "xp": 20,
        "text": "You hold your passport in your hand. What a day! You smile and walk out of the airport. "
                "London is waiting for you.",
        "tr": "Pasaportun elinde. Ne gündü ama! Gülümseyip havalimanından çıkıyorsun. Londra seni bekliyor.",
    },
    "end_secret": {
        "end": "secret", "title": "Gizli son", "xp": 30,
        "text": "You take your passport from the shelf. A woman near you laughs. 'You are lucky!' she says. "
                "You smile, and you walk out into the London sunshine.",
        "tr": "Pasaportunu raftan alıyorsun. Yanındaki bir kadın gülüyor. 'Çok şanslısın!' diyor. "
              "Gülümseyip Londra'nın güneşine çıkıyorsun.",
    },
    "end_giveup": {
        "end": "giveup", "title": "Kötü son", "xp": 2,
        "text": "You sit down and do not try anymore. Without a passport, your trip is over before it begins.",
        "tr": "Oturuyorsun ve artık denemiyorsun. Pasaportsuz yolculuğun daha başlamadan bitiyor.",
    },
}
PASSPORT_END = {n["end"]: n["title"] for n in ADVENTURE.values() if "end" in n}

FOREST = {
    "f_start": {
        "text": "You are a young wizard at the edge of the Enchanted Forest. A big stone gate stops you. "
                "A deep voice says: 'Speak the magic words!'",
        "tr": "Büyülü Orman'ın kıyısında genç bir büyücüsün. Büyük bir taş kapı yolunu kesiyor. "
              "Derin bir ses 'Sihirli sözleri söyle!' diyor.",
        "say": "Please open the gate.", "ok": "f_path", "bad": "f_gate_bad",
    },
    "f_gate_bad": {
        "text": "The gate stays closed. A small owl laughs. 'Speak slowly and clearly,' it says.",
        "tr": "Kapı kapalı kalıyor. Küçük bir baykuş gülüyor. 'Yavaş ve net konuş.' diyor.",
        "choices": [
            C("Try again.", "Tekrar dene.", "f_start"),
            C("Look for another way.", "Başka bir yol ara.", "f_river"),
        ],
    },
    "f_path": {
        "text": "The gate opens! You walk into the forest. The trees are tall and the air is cold. "
                "You see two paths.",
        "tr": "Kapı açılıyor! Ormana giriyorsun. Ağaçlar uzun ve hava soğuk. İki yol görüyorsun.",
        "choices": [
            C("Take the path to the river.", "Nehre giden yola gir.", "f_river"),
            C("Take the path to the cave.", "Mağaraya giden yola gir.", "f_cave"),
        ],
    },
    "f_river": {
        "text": "A friendly water spirit lives at the river. 'Who are you, and what do you want?' it asks.",
        "tr": "Nehirde arkadaş canlısı bir su ruhu yaşıyor. 'Sen kimsin ve ne istiyorsun?' diye soruyor.",
        "say": "I want to protect the forest.", "ok": "f_bridge", "bad": "f_river_bad",
    },
    "f_river_bad": {
        "text": "The spirit does not understand you. It shakes its head and points to the cave.",
        "tr": "Ruh seni anlamıyor. Başını sallıyor ve mağarayı gösteriyor.",
        "choices": [
            C("Go to the cave.", "Mağaraya git.", "f_cave"),
            C("Try to speak again.", "Tekrar konuşmayı dene.", "f_river"),
        ],
    },
    "f_bridge": {
        "text": "You cross the bridge of light. The spirit gives you a blue crystal. 'Take it to the cave,' it says.",
        "tr": "Işıktan köprüyü geçiyorsun. Ruh sana mavi bir kristal veriyor. 'Bunu mağaraya götür.' diyor.",
        "gives": "crystal",
        "choices": [C("Go to the cave.", "Mağaraya git.", "f_cave")],
    },
    "f_cave": {
        "text": "The cave is dark and cold. In the dark, a big dragon sleeps. It looks sad.",
        "tr": "Mağara karanlık ve soğuk. Karanlıkta büyük bir ejderha uyuyor. Üzgün görünüyor.",
        "choices": [
            C("Speak to the dragon.", "Ejderhayla konuş.", "f_dragon"),
            C("Walk away.", "Uzaklaş.", "f_end_flee"),
        ],
    },
    "f_dragon": {
        "text": "The dragon opens one eye. 'Who is there?' it asks in a low voice.",
        "tr": "Ejderha bir gözünü açıyor. 'Kim var orada?' diye alçak sesle soruyor.",
        "say": "I think you are thirsty.", "ok": "f_dragon_ok", "bad": "f_dragon_bad",
    },
    "f_dragon_ok": {
        "text": "The dragon smiles a little. 'Yes! I am very thirsty,' it says. 'The river is far away.'",
        "tr": "Ejderha hafifçe gülümsüyor. 'Evet! Çok susadım.' diyor. 'Nehir çok uzak.'",
        "choices": [
            C("Use the blue crystal to bring water.", "Su getirmek için mavi kristali kullan.",
              "f_end_hero", needs="crystal"),
            C("Promise to bring water tomorrow.", "Yarın su getireceğine söz ver.", "f_end_friend"),
        ],
    },
    "f_dragon_bad": {
        "text": "The dragon does not understand and gets angry. Smoke comes from its nose!",
        "tr": "Ejderha anlamıyor ve kızıyor. Burnundan duman çıkıyor!",
        "choices": [
            C("Run away!", "Kaç!", "f_end_flee"),
            C("Speak again, calmly.", "Sakin sakin tekrar konuş.", "f_dragon"),
        ],
    },
    "f_end_hero": {
        "end": "hero", "title": "Kahraman son", "xp": 30,
        "text": "The crystal fills a big bowl with cold water. The dragon drinks and smiles. "
                "The forest is safe, and you are the hero!",
        "tr": "Kristal büyük bir kaseyi soğuk suyla dolduruyor. Ejderha içiyor ve gülümsüyor. "
              "Orman güvende ve kahraman sensin!",
    },
    "f_end_friend": {
        "end": "friend", "title": "Dost son", "xp": 20,
        "text": "The dragon closes its eyes. 'Thank you for your promise,' it says. "
                "You walk out of the cave with a new friend.",
        "tr": "Ejderha gözlerini kapatıyor. 'Sözün için teşekkürler.' diyor. Yeni bir dostla mağaradan çıkıyorsun.",
    },
    "f_end_flee": {
        "end": "flee", "title": "Kaçış sonu", "xp": 3,
        "text": "You run out of the cave and into the forest. You are safe, but the story ends here.",
        "tr": "Mağaradan ormana koşuyorsun. Güvendesin ama hikâye burada bitiyor.",
    },
}
FOREST_END = {n["end"]: n["title"] for n in FOREST.values() if "end" in n}
ADVENTURE.update(FOREST)  # tüm sahneler tek sözlükte

STORIES = {
    "passport": {"title": "Kayıp Pasaport", "emoji": "🧳", "start": "start", "ends": PASSPORT_END,
                 "desc": "Londra'da pasaportunu kaybettin. Seçimler yap ve kelime sorularını çöz."},
    "forest": {"title": "Büyülü Orman", "emoji": "🐉", "start": "f_start", "ends": FOREST_END,
               "desc": "Fantastik bir dünyada büyücüsün. Engelleri İngilizce cümleleri sesli söyleyerek aş."},
}
ENDINGS = {**PASSPORT_END, **FOREST_END}


def today():
    return date.today().isoformat()


# ---------- Kalıcı ilerleme ----------
PERSIST = ["xp", "learned", "spoken", "speaking_history", "srs", "daily", "streak", "endings"]


def load():
    try:
        data = json.loads(SAVE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def save():
    data = {k: st.session_state[k] for k in PERSIST}
    try:
        SAVE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # uygulama çalışmaya devam eder, sadece dosyaya yazılamaz


def initialise_state():
    if "xp" not in st.session_state:
        data = load()
        st.session_state.xp = int(data.get("xp", 0) or 0)
        for key, default in [("learned", []), ("spoken", []), ("speaking_history", []),
                             ("srs", {}), ("daily", {"date": today(), "xp": 0}),
                             ("streak", {"last": None, "count": 0}), ("endings", [])]:
            st.session_state[key] = data.get(key, default)
    ses = {"page": "Bugün", "q": None, "round": {"n": 0, "score": 0}, "g": None,
           "s": None, "d": None, "nonce": 0, "rv_show": False, "adv": None}
    for key, default in ses.items():
        st.session_state.setdefault(key, default)
    for key, default in [("learned", []), ("spoken", []), ("speaking_history", []),
                         ("srs", {}), ("daily", {"date": today(), "xp": 0}),
                         ("streak", {"last": None, "count": 0}), ("endings", [])]:
        st.session_state.setdefault(key, default)


initialise_state()


# ---------- Yardımcılar ----------
def pool():
    """Kenar çubuğundaki seviye seçimine göre çalışma havuzu."""
    lvl = st.session_state.get("lvl", "Tümü")
    items = WORDS if lvl == "Tümü" else [w for w in WORDS if w["level"] == lvl]
    return items if len(items) >= 5 else WORDS


def award(amount):
    """XP ver, günlük hedefi ve seriyi güncelle."""
    ss = st.session_state
    before = ss.xp // 100
    ss.xp += amount
    if ss.daily.get("date") != today():
        ss.daily = {"date": today(), "xp": 0}
    ss.daily["xp"] += amount
    if ss.daily["xp"] >= DAILY_GOAL and ss.streak.get("last") != today():
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        ss.streak["count"] = ss.streak["count"] + 1 if ss.streak.get("last") == yesterday else 1
        ss.streak["last"] = today()
        st.toast("Günlük hedef tamam. Seri devam ediyor!", icon="🔥")
    if ss.xp // 100 > before:
        st.toast(f"Seviye {1 + ss.xp // 100} oldun!", icon="🎉")
    save()


def streak_count():
    last = st.session_state.streak.get("last")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return st.session_state.streak.get("count", 0) if last in (today(), yesterday) else 0


def today_xp():
    d = st.session_state.daily
    return d["xp"] if d.get("date") == today() else 0


def add_learned(en):
    if en not in st.session_state.learned:
        st.session_state.learned.append(en)
        st.session_state.srs[en] = {"box": 1, "due": (date.today() + timedelta(days=1)).isoformat()}
        award(10)


def due_words():
    return [en for en in dict.fromkeys(st.session_state.learned)
            if en in BY_EN and st.session_state.srs.get(en, {}).get("due", today()) <= today()]


def review(en, known):
    card = st.session_state.srs.setdefault(en, {"box": 1, "due": today()})
    card["box"] = min(card["box"] + 1, 5) if known else 1
    card["due"] = (date.today() + timedelta(days=INTERVALS[card["box"]])).isoformat()
    if known:
        award(2)
    else:
        save()


def go(page):
    st.session_state.page = page


def new_nonce():
    st.session_state.nonce += 1
    return st.session_state.nonce


def norm(text):
    return " ".join(re.sub(r"[^\w\s']", " ", str(text).lower()).split())


@st.cache_data(show_spinner=False)
def tts(text):
    from gtts import gTTS
    buf = BytesIO()
    gTTS(text=text, lang="en").write_to_fp(buf)
    return buf.getvalue()


def speak(text, label="🔊 Dinle", key=None):
    """Sesi çalar; gTTS yoksa ya da internet yoksa nazikçe uyarır."""
    if st.button(label, key=key):
        try:
            st.audio(tts(text), format="audio/mp3", autoplay=True)
        except ImportError:
            st.error("Ses için gTTS gerekli: python -m pip install gTTS")
        except Exception:
            st.error("Ses oluşturulamadı. İnternet bağlantını kontrol et.")


def make_question():
    word = random.choice(pool())
    wrong = random.sample([w["tr"] for w in WORDS if w["tr"] != word["tr"]], 3)
    return {"word": word, "opts": random.sample(wrong + [word["tr"]], 4),
            "done": False, "ok": None, "id": new_nonce()}


def make_speech_result(target, heard):
    t, h = norm(target), norm(heard)
    ratio = difflib.SequenceMatcher(None, t, h).ratio()
    tw, hw = t.split(), h.split()
    diffs = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, tw, hw).get_opcodes():
        if tag != "equal":
            diffs.append({"expected": " ".join(tw[i1:i2]) or "—", "heard": " ".join(hw[j1:j2]) or "—"})
    return ratio, diffs


def words_in(text):
    """Metindeki, kelime listemizde olan İngilizce kelimeler."""
    seen = []
    for tok in re.findall(r"[a-z]+", text.lower()):
        for cand in (tok, tok[:-1] if tok.endswith("s") else tok):
            if cand in BY_EN and cand not in seen:
                seen.append(cand)
                break
    return seen


SPEAK_PASS = 0.70  # bu benzerliğin üstünde kapı açılır


def transcribe(data):
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    with sr.AudioFile(BytesIO(data)) as source:
        recorded = recognizer.record(source)
    return recognizer.recognize_google(recorded, language="en-US")


def stt_error(error):
    if isinstance(error, ImportError):
        return "Paket eksik: python -m pip install SpeechRecognition"
    name = type(error).__name__
    if "UnknownValue" in name:
        return "Ses net anlaşılamadı. Daha sessiz bir ortamda, biraz daha yavaş tekrar dene."
    if "RequestError" in name:
        return "Tanıma servisine ulaşılamadı. İnternet bağlantını kontrol et ya da yazarak dene."
    return "Ses çözümlenemedi. Mikrofon iznini ve kaydı kontrol et."


def pron_hint(diffs):
    """Yanlış algılanan kelimeler için kısa telaffuz ipuçları."""
    tips = []
    for d in diffs:
        w = d["expected"]
        if w == "—":
            continue
        if d["heard"] == "—":
            tip = "bu kelime duyulmadı. Net ve biraz daha yüksek söyle."
        elif "th" in w:
            tip = "“th” sesi: dilinin ucunu dişlerinin arasına koy ve hafifçe üfle. s, t ya da f gibi söyleme."
        elif w.startswith("w"):
            tip = "“w” için dudaklarını yuvarla. “v” gibi söyleme."
        elif "r" in w:
            tip = "“r” sesinde dilin damağa değmesin, geride ve gevşek dursun."
        elif w.endswith("ed"):
            tip = "“-ed” sonu kelimeye göre t, d ya da id okunur. Sonu yutma."
        else:
            tip = "yavaş söyle ve heceleri ayır."
        tips.append(f"**{w}**: {tip}")
    return tips[:3]


def adv_enter(nid):
    """Sahneye geç: eşya ver, soru seçeneklerini hazırla, sonda XP ver."""
    a = st.session_state.adv
    node = ADVENTURE[nid]
    a["node"] = nid
    a["steps"] += 1
    a["opts"] = None
    a["tries"] = 0
    a["fail"] = None
    a["pick_id"] = new_nonce()
    if node.get("gives") and node["gives"] not in a["items"]:
        a["items"].append(node["gives"])
    if "quiz" in node:
        w = BY_EN[node["quiz"]]
        wrong = random.sample([x["tr"] for x in WORDS if x["tr"] != w["tr"]], 3)
        a["opts"] = random.sample(wrong + [w["tr"]], 4)
    if "end" in node:
        a["bonus"] = 3 * len(a["items"])
        if node["end"] not in st.session_state.endings:
            st.session_state.endings.append(node["end"])
        award(node["xp"] + a["bonus"])


def adv_start(story_id):
    st.session_state.adv = {"story": story_id, "node": STORIES[story_id]["start"], "items": [],
                            "passed": [], "opts": None, "pick_id": new_nonce(), "steps": 0,
                            "tries": 0, "fail": None, "flash": None, "bonus": 0}


def speak_attempt(nid, node, heard, typed=False):
    """Söylenen (ya da yazılan) cümleyi değerlendir; geçtiyse sahneyi ilerlet."""
    a = st.session_state.adv
    ratio, diffs = make_speech_result(node["say"], heard)
    if ratio >= SPEAK_PASS:
        gain = 0
        if nid not in a["passed"]:
            a["passed"].append(nid)
            gain = 2 if typed else (8 if ratio >= 0.95 else 5)
            award(gain)
        a["flash"] = ("ok", f"Büyü çalıştı! Benzerlik %{round(ratio * 100)}."
                      + (f" +{gain} XP" if gain else ""))
        adv_enter(node["ok"])
    else:
        a["tries"] += 1
        a["fail"] = {"heard": heard, "ratio": round(ratio * 100), "tips": pron_hint(diffs)}


# ---------- Görünüm: kareli defter ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Young+Serif&family=Instrument+Sans:wght@400;500;600&family=Caveat:wght@600&display=swap');
:root { --ink:#1d2b4f; --paper:#fbfbf7; --grid:#dfe6ef; --margin:#d9534f; --mark:#fff0a8; }
.stApp { background-color: var(--paper);
    background-image: linear-gradient(var(--grid) 1px, transparent 1px),
                      linear-gradient(90deg, var(--grid) 1px, transparent 1px);
    background-size: 28px 28px; color: var(--ink); font-family: 'Instrument Sans', sans-serif; }
.block-container { padding-top: 2.5rem; max-width: 760px; border-left: 2px solid var(--margin);
    padding-left: 2.4rem !important; background: rgba(251,251,247,.9); }
h1, h2, h3 { font-family: 'Young Serif', serif !important; color: var(--ink) !important;
    font-weight: 400 !important; letter-spacing: 0; }
h1 { font-size: 2.3rem !important; }
p, li, label, span, div { font-family: 'Instrument Sans', sans-serif; }
[data-testid="stSidebar"] { background: #eef1f6; border-right: 1px solid var(--grid); }
[data-testid="stSidebar"] h1 { font-size: 1.6rem !important; }
.word { font-family: 'Caveat', cursive; font-size: 3.8rem; line-height: 1.1; color: var(--ink);
    display: inline-block; background: linear-gradient(transparent 58%, var(--mark) 58%);
    padding: 0 .3rem; transform: rotate(-1deg); margin: .4rem 0 .6rem; }
.sentence { font-family: 'Young Serif', serif; font-size: 1.4rem; line-height: 1.5; }
.note { border-left: 3px solid var(--ink); padding: .1rem 0 .1rem .9rem; margin: .8rem 0; }
.faint { color: #5b6786; font-size: .92rem; }
.tally { font-family: 'Caveat', cursive; font-size: 2rem; letter-spacing: .15rem; color: var(--margin); }
div.stButton > button { border-radius: 4px; border: 1.5px solid var(--ink); background: white;
    color: var(--ink); font-weight: 500; box-shadow: 2px 2px 0 var(--ink); }
div.stButton > button:hover { transform: translate(1px,1px); box-shadow: 1px 1px 0 var(--ink);
    border-color: var(--ink); color: var(--ink); }
div.stButton > button[kind="primary"] { background: var(--ink); color: white; }
[data-testid="stMetric"] { background: rgba(255,255,255,.5); border: 0;
    border-bottom: 1.5px solid var(--ink); border-radius: 0; padding: .3rem .2rem .5rem; }
[data-testid="stProgressBar"] > div > div { background: var(--ink); }
:focus-visible { outline: 2px solid var(--margin) !important; outline-offset: 2px; }
div[data-testid="stAlert"] { border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ---------- Kenar çubuğu ----------
xp = st.session_state.xp
with st.sidebar:
    st.markdown("# ✏️ LingoPath")
    st.caption("Küçük adımlar, büyük ilerleme.")
    st.radio("Bölüm", PAGES, key="page", label_visibility="collapsed")
    st.selectbox("Çalışma seviyesi", LEVELS, key="lvl",
                 help="Test, oyunlar ve konuşma pratiği bu seviyeden kelime/cümle seçer.")
    st.write("")
    st.caption(f"Seviye {1 + xp // 100} · {xp % 100}/100 XP")
    st.progress((xp % 100) / 100)
    st.caption(f"Bugün: {min(today_xp(), DAILY_GOAL)}/{DAILY_GOAL} XP · Seri: {streak_count()} gün")
    st.progress(min(today_xp() / DAILY_GOAL, 1.0))
    n_due = len(due_words())
    if n_due:
        st.caption(f"Tekrar bekleyen: {n_due} kelime")

page = st.session_state.page


# ---------- BUGÜN ----------
if page == "Bugün":
    st.title("Bugün ne çalışalım?")
    st.write("Kısa bir çalışma seç. Birkaç dakikalık düzenli pratik bile fark yaratır.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("XP", st.session_state.xp)
    m2.metric("Kelime", f"{len(set(st.session_state.learned))}/{len(WORDS)}")
    m3.metric("Seri", f"{streak_count()} gün")
    m4.metric("Bugün", f"{min(today_xp(), DAILY_GOAL)}/{DAILY_GOAL}")

    streak = streak_count()
    if streak:
        st.markdown(f"<div class='tally'>{'||||/ ' * (streak // 5)}{'|' * (streak % 5)}</div>",
                    unsafe_allow_html=True)

    if due_words():
        st.info(f"{len(due_words())} kelime tekrar için hazır.")
        st.button("Tekrara başla", on_click=go, args=("Tekrar",), type="primary")

    todo = [w for w in pool() if w["en"] not in st.session_state.learned]
    if todo:
        word = todo[0]
        st.markdown("### Bugünün kelimesi")
        st.markdown(f"<div class='word'>{word['en']}</div>", unsafe_allow_html=True)
        st.markdown(f"**{word['tr']}** — {word['example']}")
        speak(word["en"], key="today_audio")
        if st.button("Defterime ekle (+10 XP)", type="primary"):
            add_learned(word["en"])
            st.rerun()
    else:
        st.success("Bu seviyedeki tüm kelimeleri defterine ekledin. Başka bir seviye seçebilirsin.")

    st.markdown("### 🎯 Günün görevi")
    st.caption(f"Bugün {min(today_xp(), DAILY_GOAL)}/{DAILY_GOAL} XP kazandın. Günlük görevler bölümünden hedeflerini kontrol et.")
    if st.button("Günlük görevleri gör"):
        go("Günlük Görev")
        st.rerun()

    st.markdown("### Çalışmaya başla")
    cols = st.columns(5)
    for col, name in zip(cols, ["Kelimeler", "Konuşma", "Test", "Oyunlar", "Macera"]):
        col.button(name, on_click=go, args=(name,), use_container_width=True)


# ---------- KELİMELER ----------
elif page == "Kelimeler":
    st.title("Kelimeler")
    st.write("Kelimeyi ara, örnek cümlesini oku ve öğrendiklerini defterine ekle.")
    col1, col2 = st.columns([2, 1])
    query = col1.text_input("Ara", placeholder="journey, elma…").strip().lower()
    level = col2.selectbox("Seviye", LEVELS, key="word_level")
    items = [w for w in WORDS
             if (level == "Tümü" or w["level"] == level)
             and (not query or query in w["en"].lower() or query in w["tr"].lower())]
    st.caption(f"{len(items)} kelime bulundu.")
    if not items:
        st.warning("Eşleşen kelime yok. Aramayı kısaltmayı veya seviyeyi “Tümü” yapmayı dene.")
    else:
        word = st.selectbox("Kelime", items, format_func=lambda w: f"{w['en']} — {w['tr']}")
        st.markdown(f"<div class='word'>{word['en']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='note'><b>{word['tr']}</b><br>{word['example']}<br>"
                    f"<span class='faint'>{word['level']}</span></div>", unsafe_allow_html=True)
        a, b = st.columns(2)
        with a:
            speak(word["en"], "🔊 Kelimeyi dinle", key="w_audio")
        with b:
            speak(word["example"], "🔊 Cümleyi dinle", key="s_audio")
        if word["en"] in st.session_state.learned:
            st.success("Bu kelime defterinde.")
        elif st.button("Defterime ekle (+10 XP)", type="primary"):
            add_learned(word["en"])
            st.rerun()


# ---------- TEKRAR ----------
elif page == "Tekrar":
    st.title("Tekrar")
    st.write("Öğrendiğin kelimeler aralıklı tekrarla geri gelir. Bildikçe aralık uzar, unutursan başa döner.")
    queue = due_words()
    if not st.session_state.learned:
        st.info("Tekrar edilecek kelime yok. Önce Kelimeler bölümünden birkaç kelime ekle.")
    elif not queue:
        nxt = sorted(c["due"] for c in st.session_state.srs.values())
        st.success("Bugünlük tekrar bitti." + (f" Sıradaki tekrar: {nxt[0]}." if nxt else ""))
    else:
        en = queue[0]
        w = BY_EN[en]
        st.caption(f"Kalan: {len(queue)} · Kutu {st.session_state.srs.get(en, {}).get('box', 1)}/5")
        st.markdown(f"<div class='word'>{en}</div>", unsafe_allow_html=True)
        speak(en, key=f"rv_audio_{en}")
        if not st.session_state.rv_show:
            if st.button("Anlamını göster", type="primary"):
                st.session_state.rv_show = True
                st.rerun()
        else:
            st.markdown(f"<div class='note'><b>{w['tr']}</b><br>{w['example']}</div>",
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("Biliyordum (+2 XP)", type="primary", use_container_width=True):
                review(en, True)
                st.session_state.rv_show = False
                st.rerun()
            if c2.button("Hatırlamadım", use_container_width=True):
                review(en, False)
                st.session_state.rv_show = False
                st.rerun()


# ---------- KONUŞMA ----------
elif page == "Konuşma":
    st.title("🎙️ Konuşma pratiği")
    st.write("Önce örnek cümleyi dinle, sonra mikrofonla kendi sesini kaydet ve sonucu kontrol et.")
    sentences = [w["example"] for w in pool()]
    target = st.selectbox("Çalışılacak cümle", sentences, key="speech_target")
    st.markdown(f"<p class='sentence'>{target}</p>", unsafe_allow_html=True)
    speak(target, "🔊 Örneği dinle", key="speech_example")
    st.info("Tarayıcı mikrofon izni isterse İzin ver'e bas. Sessiz bir ortam seç.")

    st.markdown("#### 1. Mikrofonla kaydet")
    audio = st.audio_input("🎤 Kaydı başlatmak için mikrofon düğmesine bas", key=f"audio_{target}")

    if audio is not None:
        st.audio(audio, format="audio/wav")
        if st.button("Kaydımı kontrol et", type="primary", use_container_width=True):
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.AudioFile(BytesIO(audio.getvalue())) as source:
                    recorded = recognizer.record(source)
                with st.spinner("Söylediklerin yazıya çevriliyor…"):
                    heard = recognizer.recognize_google(recorded, language="en-US")

                ratio, diffs = make_speech_result(target, heard)
                exact = norm(target) == norm(heard)
                st.session_state.speaking_history.append(
                    {"target": target, "heard": heard, "similarity": round(ratio * 100), "exact": exact})
                st.session_state.speaking_history = st.session_state.speaking_history[-20:]
                save()

                st.markdown("#### 2. Sonuç")
                c1, c2 = st.columns(2)
                c1.caption("Beklenen")
                c1.write(f"**{target}**")
                c2.caption("Duyulan")
                c2.write(f"**{heard}**")
                st.progress(ratio)
                st.caption(f"Metin benzerliği %{round(ratio * 100)}. Bu gerçek bir telaffuz puanı değildir.")

                if exact:
                    st.success("Cümle doğru tanındı!")
                    if target not in st.session_state.spoken:
                        st.session_state.spoken.append(target)
                        award(5)
                        st.success("+5 XP")
                    else:
                        st.caption("Bu cümlenin XP ödülünü daha önce aldın.")
                else:
                    st.warning("Bazı kelimeler farklı algılandı. Bu her zaman yanlış telaffuz demek değildir.")
                    for d in diffs:
                        st.write(f"Beklenen: **{d['expected']}** → Algılanan: **{d['heard']}**")
                    st.caption("Biraz yavaş söyle, kelimeler arasında kısa duraklama yap.")
            except ImportError:
                st.error("Paket eksik: python -m pip install SpeechRecognition")
            except Exception as error:
                name = type(error).__name__
                if "UnknownValue" in name:
                    st.error("Ses net anlaşılamadı. Daha sessiz bir ortamda tekrar dene.")
                elif "RequestError" in name:
                    st.error("Tanıma servisine ulaşılamadı. İnternet bağlantını kontrol et.")
                else:
                    st.error("Ses çözümlenemedi. Mikrofon iznini ve kaydı kontrol et.")
                    st.caption(f"Ayrıntı: {error}")

    st.caption("Gizlilik: Ses kaydı, yazıya çevrilmek için Google'ın çevrim içi servisine gönderilir.")


# ---------- TEST ----------
elif page == "Test":
    st.title("Kendini test et")
    st.write("İngilizce kelimenin Türkçe anlamını seç. Her doğru cevap 5 XP.")
    rd = st.session_state.round
    if rd["n"] >= 5:
        st.markdown(f"<p class='sentence'>5 sorudan {rd['score']} doğru.</p>", unsafe_allow_html=True)
        st.progress(rd["score"] / 5)
        if st.button("Yeni tur", type="primary"):
            st.session_state.round = {"n": 0, "score": 0}
            st.session_state.q = None
            st.rerun()
    else:
        if st.session_state.q is None:
            st.session_state.q = make_question()
        q = st.session_state.q
        word = q["word"]
        st.caption(f"Soru {rd['n'] + 1} / 5")
        st.progress(rd["n"] / 5)
        st.markdown(f"<div class='word'>{word['en']}</div>", unsafe_allow_html=True)
        pick = st.radio("Türkçesi nedir?", q["opts"], index=None,
                        key=f"pick_{q['id']}", disabled=q["done"])
        if not q["done"]:
            if st.button("Cevapla", type="primary", disabled=pick is None):
                q["done"] = True
                q["ok"] = pick == word["tr"]
                rd["n"] += 1
                if q["ok"]:
                    rd["score"] += 1
                    award(5)
                elif word["en"] in st.session_state.srs:
                    # Yanlış bilinen kelime tekrar listesine hemen döner.
                    st.session_state.srs[word["en"]].update(box=1, due=today())
                    save()
                st.rerun()
        else:
            st.success("Doğru! +5 XP") if q["ok"] else st.error(f"Doğrusu: {word['tr']}")
            if st.button("Devam"):
                st.session_state.q = None
                st.rerun()


# ---------- OYUNLAR ----------
elif page == "Oyunlar":
    st.title("Oyunlar")
    game = st.radio("Oyun", ["Eşleştirme", "Cümle kurma", "Dinle ve yaz"], horizontal=True,
                    label_visibility="collapsed")

    if game == "Eşleştirme":
        g = st.session_state.g
        if g is None:
            st.caption("Beş kelimeyi doğru anlamlarıyla eşleştir.")
            if st.button("Oyunu başlat", type="primary"):
                ws = random.sample(pool(), 5)
                st.session_state.g = {"ws": ws, "tr": random.sample([w["tr"] for w in ws], 5),
                                      "id": new_nonce(), "res": None, "shown": {}}
                st.rerun()
        else:
            answers = {}
            if g["res"] is None:
                if sort_items is not None:
                    st.caption("Türkçe anlamları sürükleyip doğru İngilizce kelimenin kutusuna bırak. "
                               "Her kutuya bir anlam koy.")
                    containers = [{"header": "Anlamlar", "items": list(g["tr"])}] + \
                                 [{"header": w["en"], "items": []} for w in g["ws"]]
                    result = sort_items(containers, multi_containers=True, direction="vertical",
                                        key=f"sort_{g['id']}")
                    placed = {c["header"]: c["items"] for c in result}
                    for w in g["ws"]:
                        answers[w["en"]] = placed.get(w["en"], [])
                else:
                    st.caption("Beş kelimeyi doğru anlamlarıyla eşleştir.")
                    st.info("Sürükle-bırak için: python -m pip install streamlit-sortables")
                    for w in g["ws"]:
                        a, b = st.columns([1, 2])
                        a.markdown(f"<div class='sentence'>{w['en']}</div>", unsafe_allow_html=True)
                        pick = b.selectbox(w["en"], ["—"] + g["tr"], key=f"m_{g['id']}_{w['en']}",
                                           label_visibility="collapsed")
                        answers[w["en"]] = [] if pick == "—" else [pick]

                if st.button("Cevapları kontrol et", type="primary"):
                    g["res"] = sum(answers[w["en"]] == [w["tr"]] for w in g["ws"])
                    g["shown"] = {en: (v[0] if len(v) == 1 else ("—" if not v else " + ".join(v)))
                                  for en, v in answers.items()}
                    award(g["res"] * 3)
                    st.rerun()
            else:
                st.success(f"5 eşleşmeden {g['res']} doğru. +{g['res'] * 3} XP")
                for w in g["ws"]:
                    mine = g["shown"].get(w["en"], "—")
                    if mine == w["tr"]:
                        st.write(f"✅ {w['en']} → {w['tr']}")
                    else:
                        st.write(f"❌ {w['en']} → {w['tr']}  (senin cevabın: {mine})")
                if st.button("Yeni oyun"):
                    st.session_state.g = None
                    st.rerun()

    elif game == "Cümle kurma":
        st.caption("Karışık kelimelerden doğru İngilizce cümleyi kur.")
        s = st.session_state.s
        if s is None:
            if st.button("Oyunu başlat", type="primary"):
                sent = random.choice([w["example"] for w in pool()])
                words = sent.rstrip(".?!").split()
                sh = words[:]
                random.shuffle(sh)
                if sh == words:
                    sh = sh[1:] + sh[:1]
                st.session_state.s = {"sent": sent, "sh": sh, "id": new_nonce(), "ok": None}
                st.rerun()
        else:
            st.markdown(f"<p class='sentence'>{' / '.join(s['sh'])}</p>", unsafe_allow_html=True)
            ans = st.text_input("Cümlen", key=f"s_{s['id']}", disabled=s["ok"] is not None,
                                placeholder="Cümleyi buraya yaz…")
            if s["ok"] is None:
                if st.button("Cümleyi kontrol et", type="primary", disabled=not ans.strip()):
                    s["ok"] = norm(ans) == norm(s["sent"])
                    if s["ok"]:
                        award(10)
                    st.rerun()
            else:
                st.success("Doğru! +10 XP") if s["ok"] else st.error(f"Doğru cümle: {s['sent']}")
                if st.button("Başka cümle"):
                    st.session_state.s = None
                    st.rerun()

    else:
        st.caption("Kelimeyi dinle, nasıl yazıldığını bul. Sesi tekrar tekrar çalabilirsin.")
        d = st.session_state.d
        if d is None:
            if st.button("Oyunu başlat", type="primary"):
                st.session_state.d = {"w": random.choice(pool()), "id": new_nonce(), "ok": None}
                st.rerun()
        else:
            speak(d["w"]["en"], "🔊 Kelimeyi çal", key=f"d_audio_{d['id']}")
            ans = st.text_input("Duyduğun kelime", key=f"d_{d['id']}", disabled=d["ok"] is not None)
            if d["ok"] is None:
                if st.button("Kontrol et", type="primary", disabled=not ans.strip()):
                    d["ok"] = norm(ans) == norm(d["w"]["en"])
                    if d["ok"]:
                        award(5)
                    st.rerun()
            else:
                if d["ok"]:
                    st.success(f"Doğru: {d['w']['en']} ({d['w']['tr']}). +5 XP")
                else:
                    st.error(f"Doğrusu: {d['w']['en']} ({d['w']['tr']})")
                if st.button("Sonraki kelime"):
                    st.session_state.d = None
                    st.rerun()


# ---------- GÜNLÜK GÖREV ----------
elif page == "Günlük Görev":
    st.title("🎯 Günün görevi")
    st.write("Bugün küçük bir hedef seç ve tamamladıkça ilerlemeni takip et.")
    daily_xp = today_xp()
    mission_items = [
        ("Bir kelimeyi defterine ekle", len(set(st.session_state.learned)) > 0, "Kelimeler bölümünden yeni bir kelime ekle."),
        ("Bir test sorusu çöz", st.session_state.round.get("n", 0) > 0, "Test bölümünde bir soru cevapla."),
        ("Bir konuşma denemesi yap", len(st.session_state.speaking_history) > 0, "Konuşma bölümünde mikrofonla dene."),
        ("En az 30 XP kazan", daily_xp >= DAILY_GOAL, f"Bugünkü XP: {daily_xp}/{DAILY_GOAL}."),
    ]
    done_count = sum(1 for _, done, _ in mission_items if done)
    st.progress(done_count / len(mission_items))
    st.caption(f"{done_count}/{len(mission_items)} görev tamamlandı")
    for title, done, detail in mission_items:
        st.write(("✅" if done else "⬜") + f" **{title}** — {detail}")
    if done_count == len(mission_items):
        st.success("Harika! Günlük görevlerin hepsi tamamlandı.")

# ---------- ROZETLER ----------
elif page == "Rozetler":
    st.title("🏅 Başarı rozetleri")
    learned_count = len(set(st.session_state.learned))
    endings_count = len(st.session_state.endings)
    badges = [
        ("🌱 İlk Adım", "İlk kelimeni defterine ekle.", learned_count >= 1),
        ("📚 Kelime Avcısı", "10 kelime öğren.", learned_count >= 10),
        ("🧠 Kelime Ustası", "25 kelime öğren.", learned_count >= 25),
        ("⚡ XP Biriktirici", "100 XP kazan.", st.session_state.xp >= 100),
        ("🔥 İstikrarlı", "3 günlük seri yakala.", streak_count() >= 3),
        ("🎙️ Konuşkan", "İlk konuşma denemeni kaydet.", len(st.session_state.speaking_history) >= 1),
        ("🗺️ Hikâye Kaşifi", "Bir macera sonu keşfet.", endings_count >= 1),
        ("🏆 Çoklu Son", "3 farklı macera sonu keşfet.", endings_count >= 3),
    ]
    unlocked = sum(1 for _, _, ok in badges if ok)
    st.progress(unlocked / len(badges))
    st.caption(f"{unlocked}/{len(badges)} rozet açıldı")
    for title, desc, ok in badges:
        with st.container(border=True):
            st.write(f"{'🏅' if ok else '🔒'} **{title}**")
            st.caption(desc)
            st.write("Açıldı ✅" if ok else "Henüz açılmadı")

# ---------- İSTATİSTİK ----------
elif page == "İstatistik":
    st.title("📊 Gelişim istatistikleri")
    learned_count = len(set(st.session_state.learned))
    history = st.session_state.speaking_history
    avg_similarity = round(sum(x.get("similarity", 0) for x in history) / len(history)) if history else 0
    c1, c2 = st.columns(2)
    c1.metric("Toplam XP", st.session_state.xp)
    c2.metric("Seviye", 1 + st.session_state.xp // 100)
    c1.metric("Öğrenilen kelime", f"{learned_count}/{len(WORDS)}")
    c2.metric("Bulunan macera sonu", f"{len(set(st.session_state.endings))}/{len(ENDINGS)}")
    c1.metric("Konuşma denemesi", len(history))
    c2.metric("Ortalama metin benzerliği", f"%{avg_similarity}")
    st.subheader("Seviyelere göre kelime ilerlemesi")
    for level_name in ("Başlangıç", "Orta", "İleri"):
        total = sum(1 for w in WORDS if w["level"] == level_name)
        count = sum(1 for en in set(st.session_state.learned) if en in BY_EN and BY_EN[en]["level"] == level_name)
        st.write(f"**{level_name}:** {count}/{total}")
        st.progress(count / total if total else 0)
    st.caption("Konuşma benzerliği yalnızca yazıya çevrilen metinleri karşılaştırır; gerçek telaffuz puanı değildir.")

# ---------- GÜNLÜK KONUŞMA ----------
elif page == "Günlük Konuşma":
    st.title("💬 Günlük konuşma senaryoları")
    scenarios = {
        "Kafede sipariş": {
            "npc": "Barista: Hello! What would you like to drink?",
            "prompt": "İçecek sipariş et. Örnek: I'd like a tea, please.",
            "keywords": ["tea", "coffee", "water", "juice", "like", "please"],
            "next": "Barista: Sure! Would you like anything to eat?"
        },
        "Yeni biriyle tanışma": {
            "npc": "Alex: Hi! What's your name, and where are you from?",
            "prompt": "Adını ve nereli olduğunu söyle. Örnek: My name is Alex. I'm from Turkey.",
            "keywords": ["my name", "i am", "i'm", "from"],
            "next": "Alex: Nice to meet you! What do you like doing?"
        },
        "Yol tarifi sorma": {
            "npc": "Stranger: Hello! Can I help you?",
            "prompt": "Bir yere nasıl gideceğini sor. Örnek: How can I get to the station, please?",
            "keywords": ["where", "how", "station", "street", "get to", "please"],
            "next": "Stranger: Go straight ahead and turn left."
        },
        "Otelde giriş": {
            "npc": "Receptionist: Good evening! Do you have a reservation?",
            "prompt": "Rezervasyonun olduğunu veya oda istediğini söyle.",
            "keywords": ["reservation", "room", "yes", "no", "book", "name"],
            "next": "Receptionist: Could I have your name, please?"
        },
    }
    chosen = st.selectbox("Senaryo seç", list(scenarios))
    scenario = scenarios[chosen]
    st.markdown(f"**{scenario['npc']}**")
    st.caption(scenario["prompt"])
    reply = st.text_input("İngilizce cevabın", key="daily_dialogue_reply")
    if st.button("Cevabımı kontrol et", type="primary", disabled=not reply.strip()):
        low = reply.lower()
        if any(k in low for k in scenario["keywords"]):
            st.success("Güzel cevap! Diyalog devam ediyor.")
            st.write(f"**{scenario['next']}**")
            st.write("İpucu: Tam cümle kurmaya ve kibar ifadeler kullanmaya çalış.")
            if "dialogue_done" not in st.session_state:
                st.session_state.dialogue_done = []
            if chosen not in st.session_state.dialogue_done:
                st.session_state.dialogue_done.append(chosen)
                award(5)
                st.success("+5 XP")
        else:
            st.warning("Bir kez daha dene. İpucundaki kelimelerden birini kullanabilir veya örnek cümleden yararlanabilirsin.")
    st.caption("Bu bölüm hazır senaryolar ve kelime ipuçlarıyla çalışır; serbest yapay zekâ sohbeti değildir.")

# ---------- AI SOHBET ----------
elif page == "AI Sohbet":
    st.title("🤖 Yapay zekâ ile İngilizce sohbet")
    st.write("Kendi OpenAI API anahtarınla serbest sohbet edebilirsin. Anahtar bu oturumda kullanılır; dosyaya kaydedilmez.")
    api_key = st.text_input("OpenAI API anahtarı", type="password", help="API kullanımı ücretlendirmeye tabi olabilir.")
    level = st.selectbox("Sohbet seviyen", ["Başlangıç", "Orta", "İleri"], key="ai_chat_level")
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []
    for msg in st.session_state.ai_messages[-20:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    user_msg = st.chat_input("İngilizce yaz veya soru sor…")
    if user_msg:
        st.session_state.ai_messages.append({"role": "user", "content": user_msg})
        if not api_key:
            st.warning("Gerçek yapay zekâ yanıtı için API anahtarını girmen gerekiyor.")
        else:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                with st.spinner("Yanıt hazırlanıyor…"):
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "system", "content": (
                            f"You are a friendly English tutor for a Turkish learner at {level} level. "
                            "Reply mainly in simple English, then briefly explain corrections in Turkish. "
                            "Be encouraging and keep answers concise."
                        )}] + st.session_state.ai_messages[-12:]
                    )
                answer = response.choices[0].message.content or "Let's try another question!"
                st.session_state.ai_messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except ImportError:
                st.error("OpenAI paketi eksik. Kurmak için: python -m pip install openai")
            except Exception as error:
                st.error("Sohbet servisine bağlanılamadı. API anahtarını ve internet bağlantını kontrol et.")
                st.caption(f"Hata türü: {type(error).__name__}")
    if st.button("Sohbet geçmişini temizle"):
        st.session_state.ai_messages = []
        st.rerun()

# ---------- MACERA ----------
elif page == "Macera":
    a = st.session_state.adv
    found = st.session_state.endings

    if a is None:
        st.title("🗺️ Macera")
        st.write("İngilizce okuyarak ilerle. Bazı engelleri kelime sorularıyla, bazılarını da "
                 "cümleleri sesli söyleyerek aşarsın.")
        for sid, s in STORIES.items():
            st.subheader(f"{s['emoji']} {s['title']}")
            st.write(s["desc"])
            st.caption("Sonlar: " + " · ".join(
                (f"✅ {t}" if k in found else "▫️ ???") for k, t in s["ends"].items()))
            if st.button("Başla", key=f"adv_start_{sid}", type="primary"):
                adv_start(sid)
                st.rerun()
    else:
        story = STORIES[a["story"]]
        nid = a["node"]
        node = ADVENTURE[nid]
        st.title(f"{story['emoji']} {story['title']}")

        top1, top2 = st.columns([3, 1])
        top1.caption("Çanta: " + (", ".join(ADV_ITEMS[i] for i in a["items"]) or "boş")
                     + f" · Sonlar: {sum(k in found for k in story['ends'])}/{len(story['ends'])}")
        if top2.button("↩️ Baştan", use_container_width=True):
            st.session_state.adv = None
            st.rerun()

        if a.get("flash"):
            kind, msg = a["flash"]
            (st.success if kind == "ok" else st.warning)(msg)
            a["flash"] = None

        st.markdown(f"<p class='sentence'>{node['text']}</p>", unsafe_allow_html=True)

        is_quiz, is_speak, is_end = "quiz" in node, "say" in node, "end" in node
        if is_quiz:
            st.caption("Türkçe çeviri, soruyu cevapladıktan sonra açılır.")
        else:
            with st.expander("Türkçesi"):
                st.write(node["tr"])

        gloss = [e for e in words_in(node["text"]) if e != node.get("quiz")][:5]
        if gloss:
            with st.expander("📖 Bu sahnedeki kelimeler"):
                for en in gloss:
                    c1, c2 = st.columns([3, 2])
                    c1.markdown(f"**{en}** — {BY_EN[en]['tr']}")
                    if en in st.session_state.learned:
                        c2.caption("Defterinde")
                    elif c2.button("Ekle (+10 XP)", key=f"adv_add_{en}_{a['steps']}"):
                        add_learned(en)
                        st.rerun()

        if is_end:
            total = node["xp"] + a.get("bonus", 0)
            st.success(f"🏁 {node['title']} · +{total} XP"
                       + (f" (eşya bonusu: +{a['bonus']})" if a.get("bonus") else ""))
            st.caption(f"Bu hikâyede bulunan sonlar: "
                       f"{sum(k in found for k in story['ends'])}/{len(story['ends'])}")
            c1, c2 = st.columns(2)
            if c1.button("Yeniden oyna", type="primary", use_container_width=True):
                adv_start(a["story"])
                st.rerun()
            if c2.button("Hikâye listesi", use_container_width=True):
                st.session_state.adv = None
                st.rerun()

        elif is_quiz:
            w = BY_EN[node["quiz"]]
            st.markdown(f"**Soru:** “{w['en']}” ne demek?")
            pick = st.radio("Anlamı", a["opts"], index=None, key=f"adv_pick_{a['pick_id']}",
                            label_visibility="collapsed")
            if st.button("Cevapla", type="primary", disabled=pick is None):
                ok = pick == w["tr"]
                if ok and nid not in a["passed"]:
                    a["passed"].append(nid)
                    award(5)
                    a["flash"] = ("ok", f"Doğru! {w['en']} = {w['tr']}. +5 XP")
                elif ok:
                    a["flash"] = ("ok", f"Doğru! {w['en']} = {w['tr']}.")
                else:
                    a["flash"] = ("bad", f"Olmadı. {w['en']} = {w['tr']}")
                adv_enter(node["ok"] if ok else node["bad"])
                st.rerun()

        elif is_speak:
            st.markdown("#### 🎙️ Sihirli sözleri söyle")
            st.markdown(f"<p class='sentence'>“{node['say']}”</p>", unsafe_allow_html=True)
            speak(node["say"], "🔊 Örneği dinle", key=f"adv_say_{a['pick_id']}")
            st.caption(f"Kapının açılması için metin benzerliği en az %{round(SPEAK_PASS * 100)} olmalı.")

            if a.get("fail"):
                f = a["fail"]
                st.warning(f"Kapı açılmadı. Duyulan: “{f['heard']}” · benzerlik %{f['ratio']}")
                for tip in f["tips"]:
                    st.markdown(f"- {tip}")

            audio = st.audio_input("🎤 Kaydı başlatmak için mikrofon düğmesine bas",
                                   key=f"adv_audio_{a['pick_id']}_{a['tries']}")
            if audio is not None and st.button("Söyle ve kontrol et", type="primary",
                                               use_container_width=True):
                try:
                    with st.spinner("Söylediklerin yazıya çevriliyor…"):
                        heard = transcribe(audio.getvalue())
                except Exception as error:
                    st.error(stt_error(error))
                else:
                    speak_attempt(nid, node, heard)
                    st.rerun()

            with st.expander("Mikrofon çalışmıyor mu? Yazarak dene"):
                typed = st.text_input("Cümleyi yaz", key=f"adv_txt_{a['pick_id']}_{a['tries']}")
                if st.button("Yazdığımı kontrol et", disabled=not typed.strip()):
                    speak_attempt(nid, node, typed, typed=True)
                    st.rerun()
                st.caption("Yazarak geçersen sadece +2 XP alırsın.")

            if a["tries"] >= 2:
                st.caption("Birkaç kez denedin. İstersen başka bir yol seçebilirsin.")
                if st.button("Başka yol dene"):
                    adv_enter(node["bad"])
                    st.rerun()

        else:
            for i, c in enumerate(node["choices"]):
                if c["needs"] and c["needs"] not in a["items"]:
                    continue
                label = c["en"] + (f"  ({ADV_ITEMS[c['needs']]})" if c["needs"] else "")
                if st.button(label, key=f"adv_c_{a['steps']}_{i}", help=c["tr"], use_container_width=True):
                    adv_enter(c["to"])
                    st.rerun()


# ---------- DEFTERİM ----------
elif page == "Defterim":
    st.title("Defterim")
    learned = sorted(set(st.session_state.learned))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("XP", st.session_state.xp)
    c2.metric("Seviye", 1 + st.session_state.xp // 100)
    c3.metric("Kelime", len(learned))
    c4.metric("Seri", f"{streak_count()} gün")
    st.caption(f"Sonraki seviyeye {100 - st.session_state.xp % 100} XP. "
               f"Macerada bulunan son: {len(st.session_state.endings)}/{len(ENDINGS)}.")

    st.subheader("Öğrendiklerim")
    if learned:
        for en in learned:
            if en in BY_EN:
                box = st.session_state.srs.get(en, {}).get("box", 1)
                st.markdown(f"**{en}** — {BY_EN[en]['tr']} <span class='faint'>(kutu {box}/5)</span>",
                            unsafe_allow_html=True)
    else:
        st.info("Henüz kelime yok. Kelimeler bölümünden ilkini ekle.")

    st.subheader("Konuşma geçmişi")
    hist = st.session_state.speaking_history
    if hist:
        for item in reversed(hist[-10:]):
            with st.expander(f"%{item.get('similarity', 0)} benzerlik · {item.get('target', 'Cümle')}"):
                st.write("**Beklenen:**", item.get("target", ""))
                st.write("**Algılanan:**", item.get("heard", ""))
                if item.get("exact"):
                    st.success("Metin eşleşti")
                else:
                    st.caption("Metinler farklı algılandı. Bu tek başına telaffuz hatası kanıtı değildir.")
    else:
        st.info("Konuşma pratiği yaptığında denemelerin burada görünür.")

    with st.expander("İlerlemeyi sıfırla"):
        st.warning("XP, kelimeler, seri ve konuşma geçmişi silinir.")
        if st.checkbox("Sıfırlamak istediğimi onaylıyorum", key="confirm_reset"):
            if st.button("İlerlemeyi sıfırla", type="primary"):
                st.session_state.xp = 0
                st.session_state.learned = []
                st.session_state.spoken = []
                st.session_state.speaking_history = []
                st.session_state.srs = {}
                st.session_state.daily = {"date": today(), "xp": 0}
                st.session_state.streak = {"last": None, "count": 0}
                st.session_state.q = st.session_state.g = st.session_state.s = st.session_state.d = None
                st.session_state.endings = []
                st.session_state.adv = None
                st.session_state.round = {"n": 0, "score": 0}
                save()
                st.rerun()
