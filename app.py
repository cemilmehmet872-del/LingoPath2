import difflib
import json
import random
import re
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_sortables import sort_items  # sürükle-bırak için: pip install streamlit-sortables
except ImportError:
    sort_items = None

st.set_page_config(page_title="LingoPath", page_icon="✏️", layout="wide")

SAVE = Path("lingopath_progress.json")
DAILY_GOAL = 30  # günlük XP hedefi
INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 15}  # kutu -> kaç gün sonra tekrar
LEVELS = ["Tümü", "Başlangıç", "Orta", "İleri"]

B, O, I = "Başlangıç", "Orta", "İleri"
WORDS = [
    # ---- Başlangıç ----
    ("apple", "elma", "I eat an apple.", B),
    ("clock", "saat", "The clock is old.", B),
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
        "text": "After a long flight, you finally arrive at Heathrow Airport in London. Rain taps against the huge glass roof, suitcases roll across the floor, and announcements echo above the crowd. You are excited to begin your trip, but when you open your bag, your passport is missing. Your train leaves in two hours. You take a deep breath and decide not to give up.",
        "tr": "Londra'daki Heathrow Havalimanı'na varıyorsun. Havalimanı büyük ve kalabalık. "
              "Çantanı açıyorsun ama pasaportun orada değil!",
        "choices": [
            C("Check your coat pocket.", "Ceket cebine bak.", "coat"),
            C("Ask the officer for help.", "Görevliden yardım iste.", "officer"),
            C("Walk to the café.", "Kafeye yürü.", "cafe"),
        ],
    },
    "coat": {
        "text": "You check every pocket of your coat. At first you find only a receipt and an old ticket. Then your fingers touch a folded piece of paper: an airport map! There is still no passport, but a red circle marks the Lost Property Office near Gate 5. You remember that you hurried past that gate when you arrived. Maybe someone has found your passport.",
        "tr": "Ceketini kontrol ediyorsun. Cebinde havalimanının küçük bir haritası var. Pasaport yok "
              "ama harita, 5 numaralı kapının yakınında bir Kayıp Eşya Ofisi gösteriyor.",
        "gives": "map",
        "choices": [
            C("Follow the map through the terminal.", "Haritayı izleyerek terminalden geç.", "terminal_map"),
            C("Ask the officer first.", "Önce görevliye sor.", "officer"),
        ],
    },
    "officer": {
        "text": "You approach an information desk. The officer is polite, but three worried travelers are already waiting. A radio crackles beside her and a phone keeps ringing. 'I will help you as soon as I can,' she says. 'The line is long today.' You notice a sign pointing toward the security desk and another toward the café.",
        "tr": "Görevli kibar ama çok meşgul. 'Lütfen sabırlı ol,' diyor. 'Sıra uzun.'",
        "choices": [
            C("Wait in line.", "Sırada bekle.", "long_wait"),
            C("Walk to the café.", "Kafeye yürü.", "cafe"),
            C("Show your map and ask about the Lost Property Office.",
              "Haritanı göster ve Kayıp Eşya Ofisi'ni sor.", "terminal_map", needs="map"),
        ],
    },
    "long_wait": {
        "text": "You wait for forty minutes. At last the officer says, 'Sorry, I can not help you here. "
                "Try the Lost Property Office.' You feel tired and sad.",
        "tr": "Kırk dakika bekliyorsun. Sonunda görevli, 'Üzgünüm, burada sana yardım edemem. "
              "Kayıp Eşya Ofisi'ni dene.' diyor. Yorgun ve üzgün hissediyorsun.",
        "choices": [
            C("Ask a security guard for directions.", "Bir güvenlik görevlisinden yol tarifi iste.", "security_desk"),
            C("Give up and go home.", "Pes et ve eve dön.", "end_giveup"),
        ],
    },
    "cafe": {
        "text": "The café is warm, and the smell of fresh coffee reminds you that you have not eaten since the flight. A waiter with a green apron notices your worried face. 'You look as if you have lost something,' he says kindly. Outside the window, rain runs down the glass while travelers hurry past with their bags.",
        "tr": "Kafe sıcak ve kahve lezzetli kokuyor. Arkadaş canlısı bir garson sana gülümsüyor. "
              "'Yardım edebilir miyim?' diye soruyor.",
        "choices": [
            C("Ask about your passport.", "Pasaportunu sor.", "waiter"),
            C("Buy a coffee and sit down.", "Bir kahve al ve otur.", "coffee"),
            C("Ask the waiter if anyone called about a passport.", "Garsona pasaport hakkında arayan olup olmadığını sor.", "phone_call"),
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
        "text": "At Gate 5, you find a small office filled with umbrellas, coats, toys, and bags. A kind woman looks up from a computer. 'Hello. We have received several items today,' she says. 'Please describe your passport carefully. If we can identify it, I will check the secure drawer.' You feel nervous, but you are finally in the right place.",
        "tr": "Kayıp Eşya Ofisi'nde nazik bir kadın çalışıyor. 'Merhaba! Lütfen pasaportunu tarif et.' diyor.",
        "quiz": "describe", "ok": "lost_ok", "bad": "lost_bad",
    },
    "lost_ok": {
        "text": "You describe it well: 'It is blue and it has a small photo.' The woman opens a box and smiles. "
                "'I think we found it!'",
        "tr": "Pasaportunu iyi tarif ediyorsun: 'Mavi ve küçük bir fotoğrafı var.' Kadın bir kutu açıyor ve "
              "gülümsüyor. 'Sanırım onu bulduk!'",
        "choices": [C("Confirm your details and collect it.", "Bilgilerini doğrula ve pasaportu teslim al.", "identity_check")],
    },
    "lost_bad": {
        "text": "You do not know what to say. The woman smiles and says, 'Take your time. Let's try again.'",
        "tr": "Ne diyeceğini bilmiyorsun. Kadın gülümsüyor ve 'Acele etme. Tekrar deneyelim.' diyor.",
        "choices": [C("Try again calmly.", "Sakin sakin tekrar dene.", "lost_office")],
    },
    "terminal_map": {
        "text": "You follow the map past a row of shops and a huge departures board. The board changes with a loud beep, and for a moment you worry that you will miss your train. A cleaner points toward a quieter corridor. At the end, you see Gate 5 and a sign for Lost Property. You are closer, but you still need to explain your problem clearly.",
        "tr": "Haritayı izleyerek dükkânları ve büyük uçuş ekranını geçiyorsun. Ekran sesle değişiyor ve bir an trenini kaçırmaktan korkuyorsun. Bir temizlik görevlisi sessiz koridoru gösteriyor. Koridorun sonunda 5 numaralı kapıyı ve Kayıp Eşya tabelasını görüyorsun.",
        "gives": "map",
        "choices": [C("Enter the Lost Property Office.", "Kayıp Eşya Ofisi'ne gir.", "lost_office"), C("Ask the security guard to confirm the way.", "Güvenlik görevlisinden yolu doğrulamasını iste.", "security_desk")],
    },
    "security_desk": {
        "text": "A security guard listens carefully. He asks when you last saw the passport and whether your bag was open. You explain that you stopped near the bookshop after landing. He writes down the location and says, 'Check Lost Property first. If it is not there, come back and we will help you.' His calm advice gives you a plan.",
        "tr": "Bir güvenlik görevlisi seni dikkatle dinliyor. Pasaportu en son ne zaman gördüğünü ve çantanın açık olup olmadığını soruyor. İnişten sonra kitapçının yanında durduğunu anlatıyorsun. Konumu not edip önce Kayıp Eşya Ofisi'ne bakmanı söylüyor.",
        "choices": [C("Go to Lost Property.", "Kayıp Eşya Ofisi'ne git.", "lost_office"), C("Check the bookshop first.", "Önce kitapçıya bak.", "bookshop")],
    },
    "phone_call": {
        "text": "The waiter checks with the manager, who remembers a call from the Lost Property Office. Someone found a blue passport and reported it. The manager cannot promise it is yours, but he tells you to bring a description and your full name. For the first time, the problem feels solvable.",
        "tr": "Garson müdüre danışıyor. Müdür, Kayıp Eşya Ofisi'nden gelen bir telefonu hatırlıyor. Birisi mavi bir pasaport bulup bildirmiş. Bunun senin pasaportun olduğundan emin değil ama tarifini ve tam adını hazırlamanı söylüyor.",
        "gives": "clue",
        "choices": [C("Go to Lost Property with the clue.", "İpucuyla Kayıp Eşya Ofisi'ne git.", "lost_office")],
    },
    "identity_check": {
        "text": "The woman asks you to spell your surname and check the photograph. You answer slowly and carefully. She compares the details with her computer, then slides the passport across the counter. 'Please keep it somewhere safe,' she says. You promise you will. You have learned that asking for help in English can turn a frightening day around.",
        "tr": "Kadın soyadını harf harf söylemeni ve fotoğrafı kontrol etmeni istiyor. Yavaşça cevap veriyorsun. Bilgileri bilgisayarla karşılaştırıp pasaportu sana uzatıyor. Güvenli bir yerde tutmanı söylüyor. İngilizce yardım istemenin zor bir günü değiştirebildiğini öğreniyorsun.",
        "choices": [C("Thank her and leave the airport.", "Ona teşekkür et ve havalimanından ayrıl.", "end_good")],
    },
    "end_good": {
        "end": "good", "title": "Mutlu son", "xp": 20,
        "text": "The woman checks the passport number and asks you to confirm your name. At last, she returns it to you. Relief washes over you. You thank her, put the passport in a zipped pocket, and take a photo of the pocket as a reminder. The rain has stopped. Outside, London buses shine in the wet street, and your adventure can finally begin.",
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
        "text": "At sunrise, you reach the edge of the Enchanted Forest, carrying a small lantern and a letter from the village elder. For weeks, a strange silver mist has covered the trees, and the forest animals have stopped returning home. A giant stone gate blocks the path. Blue symbols glow across its surface. From somewhere inside, a deep voice asks, 'Who seeks to enter? Speak the magic words!'",
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
        "text": "The symbols flash, and the stone gate slowly opens with a sound like distant thunder. You step into the forest. The trees are so tall that their branches hide the sky, and pale lights drift between their roots. Your lantern flickers even though there is no wind. Ahead, two paths split around an ancient tree: one descends toward a river, and the other climbs toward a dark cave. A third, almost hidden trail leads to a ruined tower.",
        "tr": "Kapı açılıyor! Ormana giriyorsun. Ağaçlar uzun ve hava soğuk. İki yol görüyorsun.",
        "choices": [
            C("Take the path to the river.", "Nehre giden yola gir.", "f_river"),
            C("Take the path to the cave.", "Mağaraya giden yola gir.", "f_cave"),
            C("Explore the ruined tower.", "Yıkık kuleyi keşfet.", "f_tower"),
        ],
    },
    "f_river": {
        "text": "The river is bright as glass, but it makes no sound. A water spirit rises from the surface, its hair flowing like blue ribbons. 'The river is losing its song,' it says. 'The silver mist has stolen the heart of the forest. Who are you, and what do you want?' The spirit watches you carefully, waiting to hear whether you have come to help or to take something.",
        "tr": "Nehirde arkadaş canlısı bir su ruhu yaşıyor. 'Sen kimsin ve ne istiyorsun?' diye soruyor.",
        "say": "I want to protect the forest.", "ok": "f_bridge", "bad": "f_river_bad",
    },
    "f_river_bad": {
        "text": "The spirit does not understand you. It shakes its head and points to the cave.",
        "tr": "Ruh seni anlamıyor. Başını sallıyor ve mağarayı gösteriyor.",
        "choices": [
            C("Go to the cave.", "Mağaraya git.", "f_cave"),
            C("Ask the spirit about the ruined tower.", "Ruha yıkık kuleyi sor.", "f_tower"),
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
        "text": "The cave entrance is covered in scratch marks, and the air smells of rain and stone. Your lantern reveals old drawings on the walls: a dragon, a crystal, and a tree with silver leaves. Deep inside, a huge dragon sleeps with its head resting on its claws. It looks frightening at first, but its eyes are wet and its breathing is weak. A broken chain lies beside it.",
        "tr": "Mağara karanlık ve soğuk. Karanlıkta büyük bir ejderha uyuyor. Üzgün görünüyor.",
        "choices": [
            C("Speak to the dragon.", "Ejderhayla konuş.", "f_dragon"),
            C("Examine the drawings on the wall.", "Duvardaki çizimleri incele.", "f_wall"),
            C("Walk away.", "Uzaklaş.", "f_end_flee"),
        ],
    },
    "f_dragon": {
        "text": "A pebble slips beneath your boot. The dragon opens one golden eye, then slowly lifts its head. 'Who is there?' it asks. Its voice shakes dust from the ceiling. You notice an empty bowl beside it and a silver mark around its neck, matching the symbols on the gate. The dragon does not seem angry so much as exhausted and terribly thirsty.",
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
    "f_tower": {
        "text": "The ruined tower leans over the trees. Inside, dust covers broken shelves and a map of the forest lies beneath a cracked window. You discover a journal written by the last forest keeper. One sentence is still readable: 'The heart will wake when water, courage, and kindness meet.' A small silver key is tied to the page.",
        "tr": "Yıkık kule ağaçların üzerine eğilmiş. İçeride tozlu raflar ve çatlak pencerenin altında bir orman haritası var. Son orman koruyucusunun günlüğünü buluyorsun. Bir cümle okunuyor: 'Su, cesaret ve iyilik buluştuğunda kalp uyanacak.' Sayfaya küçük bir gümüş anahtar bağlanmış.",
        "gives": "clue",
        "choices": [C("Take the journal to the river spirit.", "Günlüğü nehir ruhuna götür.", "f_river"), C("Follow the map to the cave.", "Haritayı izleyerek mağaraya git.", "f_cave")],
    },
    "f_wall": {
        "text": "You brush dust from the wall. The drawings show the dragon guarding the forest heart before the silver mist appeared. The broken chain was not a prison chain; it was part of an old protective spell. A line of tiny words glows beneath the picture: 'Kindness breaks the mist.' You now understand that the dragon may be a guardian, not a monster.",
        "tr": "Duvardaki tozu siliyorsun. Çizimler, gümüş sis ortaya çıkmadan önce ejderhanın orman kalbini koruduğunu gösteriyor. Kırık zincir bir hapishane zinciri değil, eski bir koruma büyüsünün parçasıymış. Resmin altında küçük kelimeler parlıyor: 'İyilik sisi dağıtır.' Ejderhanın bir canavar değil, koruyucu olabileceğini anlıyorsun.",
        "gives": "clue",
        "choices": [C("Talk gently to the dragon.", "Ejderhayla nazikçe konuş.", "f_dragon"), C("Return to the river for help.", "Yardım için nehre dön.", "f_river")],
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

# ---------- Yeni maceralar ----------
NIGHT_TRAIN = {
    "nt_start": {"text": "The last train leaves at midnight. You board the old night train, but the carriage is empty except for a silver suitcase and a ticket with your name on it. The lights flicker. A conductor appears and whispers, 'Your stop is not on any map.'", "tr": "Gece yarısı trenine biniyorsun. Vagon boş; gümüş bir bavul ve üzerinde adının yazdığı bir bilet var. Kondüktör, 'Durağın hiçbir haritada yok,' diye fısıldıyor.", "choices": [C("Explore the next carriage first.", "Önce sonraki vagonu keşfet.", "nt_next_carriage"), C("Ask the conductor about the ticket.", "Kondüktöre bileti sor.", "nt_conductor")]},
    "nt_case": {"text": "Inside the suitcase lies an old photograph, a brass key, and a note: 'When the train stops, do not follow the lights.' Outside the window, tiny blue lights begin to move beside the tracks.", "tr": "Bavulda eski bir fotoğraf, pirinç bir anahtar ve 'Tren durunca ışıkları takip etme' yazan bir not var. Pencerenin dışında mavi ışıklar rayların yanında ilerliyor.", "gives": "clue", "choices": [C("Keep the note and stay on the train.", "Notu al ve trende kal.", "nt_safe"), C("Follow the blue lights.", "Mavi ışıkları takip et.", "nt_lights")]},
    "nt_conductor": {"text": "The conductor studies your ticket. 'Someone has been waiting for you for a hundred years,' he says. He points to a door at the end of the carriage. Behind it, you hear the sound of waves, though the train is far from the sea.", "tr": "Kondüktör biletine bakıyor. 'Biri seni yüz yıldır bekliyor,' diyor. Vagonun sonundaki kapıyı gösteriyor. Kapının arkasından, denizden çok uzakta olmanıza rağmen dalga sesi geliyor.", "choices": [C("Open the mysterious door.", "Gizemli kapıyı aç.", "nt_lights"), C("Return to your seat.", "Koltuğuna dön.", "nt_safe")]},
    "nt_lights": {"text": "You step into a moonlit station covered in ivy. A shadow waits beneath the clock. It looks like you, but older. 'You can stay and learn the truth,' it says, 'or return before the doors close.'", "tr": "Ay ışığındaki sarmaşıklarla kaplı istasyona adım atıyorsun. Saatin altında sana benzeyen yaşlı bir gölge bekliyor. 'Gerçeği öğrenebilir ya da kapılar kapanmadan dönebilirsin,' diyor.", "choices": [C("Stay and hear the truth.", "Kal ve gerçeği öğren.", "nt_truth"), C("Run back to the train.", "Trene geri koş.", "nt_safe")]},
    "nt_truth": {"end": "nt_truth", "title": "Zamanın sırrı", "xp": 25, "text": "The shadow gives you the key. The clock begins to move backwards, and you see memories of choices you have not made yet. When you return to the train, sunrise is waiting beyond the window.", "tr": "Gölge sana anahtarı veriyor. Saat geriye doğru çalışmaya başlıyor ve henüz yapmadığın seçimlerin anılarını görüyorsun. Trene döndüğünde pencerenin ardında güneş doğuyor."},
    "nt_safe": {"end": "nt_safe", "title": "Güvenli dönüş", "xp": 12, "text": "You stay on the train. At dawn, it arrives at a familiar station. The strange ticket has vanished, but the photograph remains in your pocket—a mystery for another night.", "tr": "Trende kalıyorsun. Şafakta tanıdık bir istasyona varıyorsun. Garip bilet kaybolmuş, ama fotoğraf cebinde duruyor. Bu gizem başka bir geceye kalıyor."},
    "nt_next_carriage": {"text": "The next carriage is filled with clocks, all showing different times. A little girl in a yellow coat sits beside a window that shows a sunny beach instead of the dark countryside. She says she has lost her teddy bear, and the train will not move until someone finds it.", "tr": "Sonraki vagon farklı saatler gösteren saatlerle dolu. Sarı paltolu küçük bir kız, karanlık kırlar yerine güneşli bir sahil gösteren pencerenin yanında oturuyor. Oyuncak ayısını kaybettiğini ve biri bulana kadar trenin ilerlemeyeceğini söylüyor.", "choices": [C("Help her search under the seats.", "Koltukların altını aramasına yardım et.", "nt_teddy"), C("Ask the conductor why time is broken.", "Kondüktöre zamanın neden bozulduğunu sor.", "nt_conductor")]},
    "nt_teddy": {"text": "You find the teddy bear beneath a clock whose hands are moving backwards. The girl hugs it and gives you a small brass token. 'Show this to the shadow at the station,' she says. For the first time, the train's lights become warm and steady.", "tr": "Geriye doğru çalışan bir saatin altında oyuncak ayıyı buluyorsun. Kız ayıcığına sarılıp sana küçük bir pirinç jeton veriyor. 'Bunu istasyondaki gölgeye göster,' diyor. Tren ışıkları ilk kez sıcak ve sabit yanıyor.", "gives": "clue", "choices": [C("Go to the mysterious station.", "Gizemli istasyona git.", "nt_lights"), C("Return to your seat and wait.", "Koltuğuna dön ve bekle.", "nt_safe")]},
}
LIBRARY = {
    "lib_start": {"text": "During a storm, you discover a narrow door behind a bookshelf in the town library. It opens into a staircase descending underground. A lantern glows below, and somewhere in the dark a page turns by itself.", "tr": "Fırtınalı bir gecede kütüphanede kitaplığın arkasında dar bir kapı buluyorsun. Kapı yer altına inen bir merdivene açılıyor. Aşağıda bir fener yanıyor ve karanlıkta bir sayfa kendi kendine çevriliyor.", "choices": [C("Go down the stairs.", "Merdivenlerden aşağı in.", "lib_hall"), C("Look for a clue in the bookshelf.", "Kitaplıkta ipucu ara.", "lib_clue")]},
    "lib_clue": {"text": "One book is warm to the touch. Its title reads 'The Names We Forget'. Inside, a handwritten message says: 'Speak the name of what you seek, and the locked room will answer.'", "tr": "Bir kitap dokununca sıcak. Başlığında 'Unuttuğumuz İsimler' yazıyor. İçindeki el yazısı notta, 'Aradığın şeyin adını söyle, kilitli oda cevap verecek' deniyor.", "gives": "clue", "choices": [C("Go down with the message.", "Notla birlikte aşağı in.", "lib_hall")]},
    "lib_hall": {"text": "At the bottom, thousands of books float in the air. A small door has no handle, only a blank nameplate. You remember the note and whisper, 'knowledge'. The nameplate glows, and the door slowly opens.", "tr": "Aşağıda binlerce kitap havada süzülüyor. Küçük kapıda kol yok; yalnızca boş bir isimlik var. Notu hatırlayıp 'knowledge' diye fısıldıyorsun. İsimlik parlıyor ve kapı yavaşça açılıyor.", "quiz": "knowledge", "ok": "lib_archive", "bad": "lib_bad"},
    "lib_bad": {"text": "The door remains shut. The floating books rearrange themselves, almost as if they are trying to help you remember the word.", "tr": "Kapı açılmıyor. Havada süzülen kitaplar, kelimeyi hatırlamana yardım eder gibi yeniden diziliyor.", "choices": [C("Try the word again.", "Kelimeyi tekrar dene.", "lib_hall")]},
    "lib_archive": {"text": "The door opens into a circular archive. Books whisper in dozens of languages, and a staircase winds around a tree growing through the centre of the room. A silver quill floats above a desk. Three books are glowing: one about forgotten names, one about lost cities, and one about a traveller who has not yet arrived.", "tr": "Kapı dairesel bir arşive açılıyor. Kitaplar onlarca dilde fısıldıyor; odanın ortasındaki ağacın çevresinde bir merdiven yükseliyor. Masanın üzerinde gümüş bir tüy kalem süzülüyor. Üç kitap parlıyor: unutulmuş isimler, kayıp şehirler ve henüz gelmemiş bir yolcu hakkında.", "choices": [C("Read the book about forgotten names.", "Unutulmuş isimler kitabını oku.", "lib_secret"), C("Touch the floating quill.", "Havada duran kaleme dokun.", "lib_quill")]},
    "lib_quill": {"text": "The quill writes your name on a blank page. Beneath it, a new sentence appears: 'A story survives when it is shared.' The archive asks you to choose one book to carry upstairs. You may take a story, but you must leave another for the next visitor.", "tr": "Kalem boş bir sayfaya adını yazıyor. Altında yeni bir cümle beliriyor: 'Bir hikâye paylaşıldığında yaşamaya devam eder.' Arşiv yukarı çıkarmak için bir kitap seçmeni istiyor. Bir hikâye alabilirsin ama sonraki ziyaretçi için bir başkasını bırakmalısın.", "choices": [C("Take the book of forgotten names.", "Unutulmuş isimler kitabını al.", "lib_secret"), C("Leave the books and protect the archive.", "Kitapları bırak ve arşivi koru.", "lib_guardian")]},
    "lib_guardian": {"end": "lib_guardian", "title": "Arşivin koruyucusu", "xp": 30, "text": "You place the quill back on the desk and promise to keep the hidden door safe. The books settle quietly, and a tiny key appears in your hand. You leave the archive as its new guardian, ready to return whenever another story needs help.", "tr": "Kalemi masaya bırakıp gizli kapıyı koruyacağına söz veriyorsun. Kitaplar sessizce yerlerine oturuyor ve elinde küçük bir anahtar beliriyor. Yeni koruyucu olarak arşivden ayrılıyorsun; başka bir hikâye yardıma ihtiyaç duyduğunda geri dönmeye hazırsın."},
    "lib_secret": {"end": "lib_secret", "title": "Kayıp arşiv", "xp": 25, "text": "Behind the door is a secret archive containing letters from people who lived centuries ago. One letter is addressed to you. It says that the library chooses curious readers to protect its stories. You take the letter upstairs, knowing the adventure has only begun.", "tr": "Kapının ardında yüzyıllar önce yaşamış insanlardan mektuplarla dolu gizli bir arşiv var. Bir mektup sana hitap ediyor. Kütüphanenin hikâyelerini korumak için meraklı okurları seçtiğini söylüyor. Maceranın yeni başladığını bilerek mektupla yukarı çıkıyorsun."},
}
LIGHTHOUSE = {
    "lh_start": {"text": "A storm has pushed your small boat toward a lonely island. At the top of a cliff, an abandoned lighthouse flashes once, then goes dark. You find wet footprints leading to its door and hear a bell ringing inside, even though the building looks empty.", "tr": "Fırtına küçük tekneni yalnız bir adaya sürükledi. Uçurumun tepesindeki terk edilmiş deniz feneri bir kez yanıp söndü ve karardı. Kapıya giden ıslak ayak izleri buluyorsun. İçeriden, bina boş görünmesine rağmen bir zil sesi geliyor.", "choices": [C("Enter the lighthouse.", "Deniz fenerine gir.", "lh_inside"), C("Follow the footprints around the cliff.", "Ayak izlerini uçurumun çevresinden takip et.", "lh_path")]},
    "lh_inside": {"text": "Dust covers the stairs, but one lantern is still warm. On a desk you find a logbook. The last entry says: 'The light must guide the lost ship home before sunrise.' Through the window, you see a tiny ship struggling against the waves.", "tr": "Merdivenler tozla kaplı ama bir fener hâlâ sıcak. Masada bir kayıt defteri buluyorsun. Son notta, 'Gün doğmadan ışık kayıp gemiye eve dönüş yolunu göstermeli' yazıyor. Pencereden dalgalarla boğuşan küçük bir gemi görüyorsun.", "gives": "clue", "choices": [C("Repair the lamp with the tools nearby.", "Yakındaki aletlerle lambayı tamir et.", "lh_repair"), C("Ring the old bell for help.", "Yardım için eski zili çal.", "lh_bell")]},
    "lh_path": {"text": "The footprints end at a narrow cave. Inside, a brass key rests beside a message in a bottle: 'The keeper is still watching.' You hear the lighthouse bell again, louder this time.", "tr": "Ayak izleri dar bir mağarada bitiyor. İçeride bir şişedeki mesajın yanında pirinç bir anahtar var: 'Fener bekçisi hâlâ izliyor.' Deniz fenerinin zili yeniden, bu kez daha yüksek sesle çalıyor.", "gives": "clue", "choices": [C("Return to the lighthouse.", "Deniz fenerine dön.", "lh_inside"), C("Wait in the cave until morning.", "Sabaha kadar mağarada bekle.", "lh_safe")]},
    "lh_repair": {"text": "You carefully clean the glass and turn the old wheel. The beam cuts through the storm. The distant ship answers with three flashes and changes course toward the island's safe harbor.", "tr": "Camı dikkatlice temizleyip eski çarkı çeviriyorsun. Işık fırtınayı yarıyor. Uzaktaki gemi üç ışıkla cevap veriyor ve adanın güvenli limanına yöneliyor.", "choices": [C("Study the strange signal from the ship.", "Gemiden gelen garip işareti incele.", "lh_signal"), C("Search the keeper's room.", "Bekçinin odasını ara.", "lh_secret")]},
    "lh_bell": {"text": "The bell echoes over the sea. A ghostly keeper appears at the top of the stairs. 'You heard the call,' she says. 'Now choose: save the ship, or learn why I never left.'", "tr": "Zil sesi denizde yankılanıyor. Merdivenlerin tepesinde hayalet bir bekçi beliriyor. 'Çağrıyı duydun,' diyor. 'Şimdi seç: gemiyi kurtar ya da neden hiç ayrılmadığımı öğren.'", "choices": [C("Save the ship first.", "Önce gemiyi kurtar.", "lh_good"), C("Ask about the keeper's secret.", "Bekçinin sırrını sor.", "lh_secret")]},
    "lh_signal": {"text": "Through the telescope, you see the ship flashing a pattern: three short lights, then one long light. The old logbook contains the same pattern beside a hand-drawn map of hidden rocks. You realise the ship is not asking for rescue alone—it is warning you about a dangerous reef between the vessel and the harbour.", "tr": "Dürbünden geminin üç kısa, bir uzun ışık yaktığını görüyorsun. Eski defterde aynı işaret, gizli kayalıkların çizildiği bir haritanın yanında bulunuyor. Gemi yalnızca yardım istemiyor; limanla gemi arasındaki tehlikeli kayalıklar için uyarı gönderiyor.", "choices": [C("Use the lamp to guide the ship around the reef.", "Gemiyi kayalıkların çevresinden yönlendirmek için lambayı kullan.", "lh_good"), C("Ring the bell to warn the harbour.", "Limanı uyarmak için zili çal.", "lh_bell")]},
    "lh_good": {"end": "lh_good", "title": "Fırtınadan kurtuluş", "xp": 22, "text": "The ship reaches the harbor just before sunrise. The keeper smiles and fades into the golden light. The lighthouse shines again, and the island no longer feels lonely.", "tr": "Gemi gün doğmadan hemen önce limana ulaşıyor. Bekçi gülümsüyor ve altın ışıkların içinde kayboluyor. Deniz feneri yeniden parlıyor; ada artık yalnız hissettirmiyor."},
    "lh_secret": {"end": "lh_secret", "title": "Bekçinin sırrı", "xp": 28, "text": "The keeper tells you she has guarded the island for a hundred years, waiting for someone brave enough to answer the bell. She gives you the lighthouse key and vanishes as the storm clears.", "tr": "Bekçi, zile cevap verecek kadar cesur birini bekleyerek yüz yıldır adayı koruduğunu anlatıyor. Sana deniz fenerinin anahtarını veriyor ve fırtına dindiğinde ortadan kayboluyor."},
    "lh_safe": {"end": "lh_safe", "title": "Güvenli sabah", "xp": 10, "text": "You stay in the cave until the storm passes. At dawn, a rescue boat finds you. The lighthouse is dark again, but you keep the strange message as a reminder of the island.", "tr": "Fırtına geçene kadar mağarada kalıyorsun. Gün doğarken bir kurtarma teknesi seni buluyor. Deniz feneri yeniden karanlık, ama adayı hatırlamak için gizemli mesajı saklıyorsun."},
}
LOST_CITY = {
    "city_start": {"text": "While hiking through a desert, you discover a stone arch half-buried in the sand. Beyond it lies a city that does not appear on any map. Blue symbols glow on the walls, and a dry fountain begins to flow when you step closer.", "tr": "Çölde yürürken kuma yarı gömülmüş taş bir kemer keşfediyorsun. Ötesinde hiçbir haritada görünmeyen bir şehir var. Duvarlarda mavi semboller parlıyor ve yaklaştığında kuru bir çeşme akmaya başlıyor.", "choices": [C("Visit the silent market.", "Sessiz pazarı ziyaret et.", "city_market"), C("Follow the water toward the palace.", "Suyu saraya doğru takip et.", "city_palace")]},
    "city_market": {"text": "The market is full of stalls, but no sellers are visible. Bowls of dates, blue glass lamps, and tiny carved animals sit untouched beneath striped awnings. A child made of sand points to a dry well and asks you to return a lost silver bell. In exchange, the child promises to reveal a safe path through the city.", "tr": "Pazar tezgâhlarla dolu ama ortada satıcı yok. Hurma kaseleri, mavi cam lambalar ve küçük oyma hayvanlar çizgili tentelerin altında duruyor. Kumdan yapılmış bir çocuk kuru kuyuyu gösterip kayıp gümüş zilini bulmanı istiyor. Karşılığında şehirde güvenli bir yol göstereceğine söz veriyor.", "choices": [C("Search the dry well for the bell.", "Zil için kuru kuyuyu ara.", "city_well"), C("Continue directly to the palace.", "Doğrudan saraya ilerle.", "city_palace")]},
    "city_well": {"text": "At the bottom of the well, you find the silver bell beside a mosaic showing the city before the desert covered it. When you ring it, water rises like a shining staircase. The sand-child smiles and gives you a map with a hidden entrance marked in blue.", "tr": "Kuyunun dibinde, çöl şehri örtmeden önceki hâlini gösteren bir mozaiğin yanında gümüş zili buluyorsun. Zili çalınca su, parlayan bir merdiven gibi yükseliyor. Kumdan çocuk gülümsüyor ve gizli girişi maviyle işaretlenmiş bir harita veriyor.", "gives": "map", "choices": [C("Use the hidden entrance to study the symbols.", "Sembolleri incelemek için gizli girişi kullan.", "city_symbols"), C("Take the map to the palace guardian.", "Haritayı saray muhafızına götür.", "city_palace")]},
    "city_symbols": {"text": "The symbols form a warning: 'Only a truthful traveler may enter.' A stone door opens just enough to reveal a small mirror and a silver coin.", "tr": "Semboller bir uyarı oluşturuyor: 'Yalnızca dürüst bir yolcu içeri girebilir.' Taş kapı aralanıyor; içeride küçük bir ayna ve gümüş bir madeni para var.", "gives": "clue", "choices": [C("Take the mirror and enter.", "Aynayı al ve içeri gir.", "city_trial"), C("Leave everything and go to the palace.", "Her şeyi bırakıp saraya git.", "city_palace")]},
    "city_palace": {"text": "At the palace, a stone guardian blocks the entrance. 'What do you bring that cannot be stolen?' it asks. You remember that the city seems to react to every honest choice.", "tr": "Sarayda taş bir muhafız girişi kapatıyor. 'Çalınamayacak ne getirdin?' diye soruyor. Şehrin her dürüst seçime tepki verdiğini hatırlıyorsun.", "choices": [C("Answer: my memories.", "'Anılarımı' diye cevap ver.", "city_good"), C("Offer the silver coin.", "Gümüş parayı teklif et.", "city_trial")]},
    "city_trial": {"text": "The mirror shows a memory you had forgotten: someone once helped you when you were lost. The guardian lowers its head. 'Remember kindness, and the city will remember you.'", "tr": "Ayna unuttuğun bir anıyı gösteriyor: Kaybolduğunda biri sana yardım etmişti. Muhafız başını eğiyor. 'İyiliği hatırla, şehir de seni hatırlasın.'", "choices": [C("Promise to protect the city.", "Şehri koruyacağına söz ver.", "city_good"), C("Take a treasure and leave quickly.", "Bir hazine alıp hızla ayrıl.", "city_bad")]},
    "city_good": {"end": "city_good", "title": "Şehrin koruyucusu", "xp": 26, "text": "The blue symbols brighten. The guardian gives you a small crystal that can guide lost travelers. The hidden city welcomes you as its new friend, and the desert path home appears beneath the stars.", "tr": "Mavi semboller parlıyor. Muhafız sana kaybolan yolculara rehberlik eden küçük bir kristal veriyor. Gizli şehir seni yeni dostu olarak kabul ediyor ve yıldızların altında eve giden yol beliriyor."},
    "city_bad": {"end": "city_bad", "title": "Kumların sırrı", "xp": 8, "text": "The treasure turns to sand in your hands. The city closes its gates, but you escape before the desert swallows the path. You leave with a lesson instead of gold.", "tr": "Hazine ellerinde kuma dönüşüyor. Şehir kapılarını kapatıyor ama çöl yolu yutmadan kaçıyorsun. Altın yerine bir dersle ayrılıyorsun."},
}
ADVENTURE.update(LIGHTHOUSE)
ADVENTURE.update(LOST_CITY)
LIGHTHOUSE_END = {n["end"]: n["title"] for n in LIGHTHOUSE.values() if "end" in n}
CITY_END = {n["end"]: n["title"] for n in LOST_CITY.values() if "end" in n}

ADVENTURE.update(NIGHT_TRAIN)
ADVENTURE.update(LIBRARY)
NIGHT_END = {n["end"]: n["title"] for n in NIGHT_TRAIN.values() if "end" in n}
LIBRARY_END = {n["end"]: n["title"] for n in LIBRARY.values() if "end" in n}

# Yeni eklenen alternatif sonları da macera kayıtlarına dahil et.
NIGHT_END = {n["end"]: n["title"] for n in NIGHT_TRAIN.values() if "end" in n}
LIBRARY_END = {n["end"]: n["title"] for n in LIBRARY.values() if "end" in n}
LIGHTHOUSE_END = {n["end"]: n["title"] for n in LIGHTHOUSE.values() if "end" in n}
CITY_END = {n["end"]: n["title"] for n in LOST_CITY.values() if "end" in n}

# ---------- Yeni bulmacalı macera: Saat Kulesinin Sırrı ----------
CLOCK_TOWER = {
    "clock_start": {"text": "At the edge of a quiet town stands a clock tower that has been silent for twenty years. Tonight, every clock in town stops at 11:11. A letter slips under your door: 'Bring back the missing minute before midnight, or morning will never come.' You take your coat and walk toward the tower. The streets are empty, and a pale blue light shines behind its locked entrance.", "tr": "Sessiz bir kasabanın kenarında yirmi yıldır durmuş bir saat kulesi var. Bu gece kasabadaki bütün saatler 11.11'de duruyor. Kapının altından bir mektup geliyor: 'Gece yarısından önce kayıp dakikayı geri getir, yoksa sabah hiç gelmeyecek.'", "choices": [C("Search the square for clues.", "Meydanda ipuçları ara.", "clock_square"), C("Try the tower door.", "Kule kapısını dene.", "clock_door")]},
    "clock_square": {"text": "Near the dry fountain, you find a folded town map. Someone has drawn a circle around the old clockmaker's shop and written: 'The hands remember what people forget.' A cold wind carries the sound of a tiny bell from the shop's direction.", "tr": "Kuru çeşmenin yanında katlanmış bir kasaba haritası buluyorsun. Haritada eski saatçinin dükkânı daire içine alınmış. Notta 'Akrep ve yelkovan, insanların unuttuğunu hatırlar' yazıyor.", "gives": "map", "choices": [C("Follow the map to the clockmaker's shop.", "Haritayla saatçinin dükkânına git.", "clock_shop"), C("Return to the tower with the map.", "Haritayla kuleye dön.", "clock_door", needs="map")]},
    "clock_door": {"text": "The tower door has three empty slots and a riddle carved into the stone: 'I have a face but no eyes. I have hands but no arms. What am I?' A small panel beside it waits for an answer. You can hear gears turning deep inside the wall.", "tr": "Kule kapısında üç boş yuva ve taşa kazınmış bir bilmece var: 'Yüzüm var ama gözüm yok. Ellerim var ama kollarım yok. Ben neyim?'", "quiz": "clock", "ok": "clock_inside", "bad": "clock_riddle_bad"},
    "clock_riddle_bad": {"text": "The panel flashes red, but a hidden drawer opens. Inside is a note from the clockmaker: 'A clock can open a door, but only a memory can turn it.' The answer is written on the back in small letters.", "tr": "Panel kırmızı yanıyor ama gizli bir çekmece açılıyor. İçinde saatçinin notu var. Cevap arka tarafta küçük harflerle yazılmış.", "gives": "clue", "choices": [C("Read the note and try again.", "Notu oku ve tekrar dene.", "clock_door"), C("Search the clockmaker's shop.", "Saatçinin dükkânını ara.", "clock_shop")]},
    "clock_shop": {"text": "The clockmaker's shop is full of silent clocks. On the desk lies a brass key beside a diary. The last entry says the tower stopped when the clockmaker erased the memory of his daughter to protect her from a terrible accident. A tiny music box plays when you touch the diary.", "tr": "Saatçinin dükkânı sessiz saatlerle dolu. Masada pirinç bir anahtar ve günlük var. Son notta, kızını korkunç bir kazadan korumak için anısını sildiği ve o anda kulenin durduğu yazıyor.", "gives": "clue", "choices": [C("Take the diary and return to the tower.", "Günlüğü alıp kuleye dön.", "clock_inside"), C("Study the music box carefully.", "Müzik kutusunu dikkatle incele.", "clock_music")]},
    "clock_music": {"text": "The music box plays a melody you somehow know. Under its velvet lining, you discover a tiny crystal that glows when the melody reaches its final note. The clockmaker's diary says the crystal can restore one forgotten memory.", "tr": "Müzik kutusu garip biçimde tanıdık gelen bir melodi çalıyor. Kadifenin altında son nota çalınca parlayan küçük bir kristal buluyorsun. Günlük, kristalin unutulmuş bir anıyı geri getirebileceğini söylüyor.", "gives": "crystal", "choices": [C("Carry the crystal to the tower.", "Kristali kuleye götür.", "clock_inside", needs="crystal"), C("Read the diary before deciding.", "Karar vermeden önce günlüğü oku.", "clock_shop")]},
    "clock_inside": {"text": "The door opens with a deep metallic sigh. Inside, stairs spiral around a giant clock mechanism. A ghostly girl stands on a landing, holding a paper star. 'I remember the song,' she says, 'but not the face of the person who taught it to me.' The minute hand is trapped behind a glass case.", "tr": "Kapı metalik bir sesle açılıyor. İçeride dev bir saat mekanizmasının çevresinde dönen merdivenler var. Hayalet bir kız elinde kâğıt yıldız tutuyor. Şarkıyı hatırladığını ama kendisine öğreten kişinin yüzünü unuttuğunu söylüyor.", "choices": [C("Show her the crystal and restore the memory.", "Kristali göster ve anıyı geri getir.", "clock_memory", needs="crystal"), C("Use the clue from the diary to speak to her.", "Günlükteki ipucuyla onunla konuş.", "clock_talk", needs="clue"), C("Climb to the clock mechanism.", "Saat mekanizmasına tırman.", "clock_mechanism")]},
    "clock_talk": {"text": "You explain that the clockmaker erased the memory out of fear, not cruelty. The girl lowers her paper star. 'Then I can forgive him,' she whispers. A hidden latch clicks open, revealing the glass case keyhole.", "tr": "Saatçinin anıyı kötülükten değil korkudan sildiğini anlatıyorsun. Kız kâğıt yıldızını indiriyor. 'O zaman onu affedebilirim,' diye fısıldıyor. Gizli bir kilit açılıyor.", "choices": [C("Climb to the clock mechanism.", "Saat mekanizmasına tırman.", "clock_mechanism"), C("Ask the girl to sing the melody.", "Kızdan melodiyi söylemesini iste.", "clock_memory")]},
    "clock_memory": {"text": "The crystal shines. The girl remembers her father's face and sings the music-box melody. The tower trembles, and the glass case opens by itself. You can return the minute hand gently—or force the mechanism to move before the memory fades.", "tr": "Kristal parlıyor. Kız babasının yüzünü hatırlıyor ve müzik kutusundaki melodiyi söylüyor. Kule titriyor ve cam kutu kendi kendine açılıyor.", "choices": [C("Restore the clock carefully.", "Saati dikkatlice onar.", "clock_good"), C("Turn the mechanism quickly.", "Mekanizmayı hızla çevir.", "clock_rush")]},
    "clock_mechanism": {"text": "You reach the giant gears. Without the girl's help, the machine is difficult to understand. The map shows a narrow maintenance path, while the note warns you to move the minute hand only when the bell rings.", "tr": "Dev dişlilere ulaşıyorsun. Kızın yardımı olmadan makineyi anlamak zor. Harita dar bir bakım yolunu gösteriyor; not ise yelkovanı yalnızca zil çaldığında hareket ettirmeni söylüyor.", "choices": [C("Use the map and wait for the bell.", "Haritayı kullan ve zili bekle.", "clock_good", needs="map"), C("Move the gears immediately.", "Dişli çarkları hemen hareket ettir.", "clock_rush")]},
    "clock_good": {"end": "clock_good", "title": "Kayıp dakikanın dönüşü", "xp": 35, "text": "The bell rings once. You place the minute hand in its proper position, and the missing minute returns to every clock in town. Dawn spills over the rooftops. The girl reunites with her father as a memory, no longer trapped in the tower. Before you leave, the clockmaker gives you a small token for your courage.", "tr": "Zil bir kez çalıyor. Yelkovanı doğru yerine yerleştiriyorsun ve kayıp dakika kasabadaki bütün saatlere geri dönüyor. Şafak çatılara yayılıyor. Kız artık kulede hapsolmuş değil; babasıyla anısı yeniden birleşiyor."},
    "clock_rush": {"end": "clock_rush", "title": "Sonsuz gece", "xp": 8, "text": "You pull the gears too quickly. The clock strikes thirteen, and the tower fills with blue light. You escape before the door closes, but the town remains frozen at 11:11. You keep the map and promise to return when you understand the clock's warning.", "tr": "Dişlileri çok hızlı çekiyorsun. Saat on üç kez çalıyor ve kule mavi ışıkla doluyor. Kapı kapanmadan kaçıyorsun ama kasaba 11.11'de donmuş kalıyor. Haritayı yanında tutup uyarıyı anlayınca geri dönmeye söz veriyorsun."},
}
ADVENTURE.update(CLOCK_TOWER)
CLOCK_END = {n["end"]: n["title"] for n in CLOCK_TOWER.values() if "end" in n}

STORIES = {
    "passport": {"title": "Kayıp Pasaport", "emoji": "🧳", "start": "start", "ends": PASSPORT_END,
                 "desc": "Londra'da pasaportunu kaybettin. İpuçlarını topla, insanlarla konuş ve farklı sonlara ulaş.", "image": "kayip_pasaport.png"},
    "forest": {"title": "Büyülü Orman", "emoji": "🐉", "start": "f_start", "ends": FOREST_END,
               "desc": "Gümüş sisin sırrını çöz, nehir ruhuyla ve ejderhayla konuş. İngilizce büyülerle ormanı kurtar.", "image": "buyulu_orman.png"},
    "night_train": {"title": "Gece Treni", "emoji": "🚂", "start": "nt_start", "ends": NIGHT_END,
                    "desc": "Gece yarısı giden trende zamanın sırrını çöz."},
    "library": {"title": "Unutulmuş Kütüphane", "emoji": "📚", "start": "lib_start", "ends": LIBRARY_END,
                "desc": "Gizli bir arşivi keşfet ve kayıp hikâyeleri bul."},
    "lighthouse": {"title": "Fırtınalı Deniz Feneri", "emoji": "🌊", "start": "lh_start", "ends": LIGHTHOUSE_END,
                   "desc": "Issız bir adada fırtınaya yakalan. Gizemli bekçiyi bul ve kayıp gemiyi kurtar."},
    "lost_city": {"title": "Kayıp Şehir", "emoji": "🏜️", "start": "city_start", "ends": CITY_END,
                  "desc": "Çölde haritalarda olmayan bir şehir keşfet. Dürüst seçimlerin gizli kapıları açacak."},
    "clock_tower": {"title": "Saat Kulesinin Sırrı", "emoji": "🕰️", "start": "clock_start", "ends": CLOCK_END,
                    "desc": "Duran kasabayı kurtar, ipuçları topla ve saat kulesinin gizemini çöz."},
}
ENDINGS = {**PASSPORT_END, **FOREST_END, **NIGHT_END, **LIBRARY_END, **LIGHTHOUSE_END, **CITY_END, **CLOCK_END}


def today():
    return date.today().isoformat()


# ---------- Kalıcı ilerleme ----------
PERSIST = ["xp", "learned", "spoken", "speaking_history", "srs", "daily", "streak", "endings", "treasure_hunt"]


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
                             ("streak", {"last": None, "count": 0}), ("endings", []),
                             ("treasure_hunt", {"room": "Beach", "found": [], "opened": [], "complete": False, "xp_claimed": False})]:
            st.session_state[key] = data.get(key, default)
    ses = {"page": "Bugün", "q": None, "round": {"n": 0, "score": 0}, "g": None,
           "s": None, "d": None, "nonce": 0, "rv_show": False, "adv": None}
    for key, default in ses.items():
        st.session_state.setdefault(key, default)
    for key, default in [("learned", []), ("spoken", []), ("speaking_history", []),
                         ("srs", {}), ("daily", {"date": today(), "xp": 0}),
                         ("streak", {"last": None, "count": 0}), ("endings", []),
                         ("treasure_hunt", {"room": "Beach", "found": [], "opened": [], "complete": False, "xp_claimed": False})]:
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
    """Kelimeyi deftere ekle ve tekrar planını başlat; kelime eklemek XP vermez."""
    if en not in st.session_state.learned:
        st.session_state.learned.append(en)
        st.session_state.srs[en] = {"box": 1, "due": (date.today() + timedelta(days=1)).isoformat()}
        save()


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
    """WAV kaydını birkaç İngilizce tanıma ayarıyla çözmeyi dener."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    with sr.AudioFile(BytesIO(data)) as source:
        recorded = recognizer.record(source)

    # Farklı İngilizce varyantları bazen farklı sonuç verebilir.
    last_error = None
    for language in ("en-US", "en-GB"):
        try:
            text = recognizer.recognize_google(recorded, language=language).strip()
            if text:
                return text
        except sr.UnknownValueError as error:
            last_error = error
        except sr.RequestError:
            # Servis/bağlantı hatasında diğer dil ayarı da aynı servisi kullanacağı için dur.
            raise
    if last_error:
        raise last_error
    raise sr.UnknownValueError()


def stt_error(error):
    if isinstance(error, ImportError):
        return "Ses tanıma paketi eksik. Terminalde: python -m pip install SpeechRecognition"
    name = type(error).__name__
    if "UnknownValue" in name:
        return ("Kayıttaki sözler çözümlenemedi. Mikrofonu ağzına biraz yaklaştır, "
                "örnek cümleyi dinle ve daha yavaş, tam cümle hâlinde tekrar kaydet. "
                "İstersen aşağıdaki yazıyla kontrol seçeneğini kullan.")
    if "RequestError" in name:
        return "Google ses tanıma servisine ulaşılamadı. İnternet bağlantısını kontrol et veya aşağıdaki yazıyla kontrol seçeneğini kullan."
    if "AudioData" in name or "AudioFile" in name or "ValueError" in name:
        return "Ses dosyası okunamadı. Kaydı yeniden başlatıp tekrar dene."
    return "Ses çözümlenemedi. Mikrofon iznini kontrol edip yeniden kayıt yapmayı dene."


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
    """Sahneye geç: eşya ver, haritaya kaydet, soru seçeneklerini hazırla."""
    a = st.session_state.adv
    node = ADVENTURE[nid]
    a["node"] = nid
    a.setdefault("visited", [])
    a.setdefault("map_labels", {})
    if nid not in a["visited"]:
        a["visited"].append(nid)
    a["map_labels"].setdefault(nid, node.get("title", nid.replace("_", " ").title()))
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
    start = STORIES[story_id]["start"]
    st.session_state.adv = {"story": story_id, "node": start, "items": [],
                            "passed": [], "opts": None, "pick_id": new_nonce(), "steps": 0,
                            "tries": 0, "fail": None, "flash": None, "bonus": 0,
                            "visited": [], "map_labels": {start: "Başlangıç"}}
    adv_enter(start)


def choice_icon(label):
    """Tıklanabilir macera nesneleri için metne uygun basit simge seç."""
    t = label.lower()
    for words, emoji in [
        (("door", "kapı", "open"), "🚪"), (("map", "harita", "direction", "directions"), "🗺️"),
        (("book", "kitap", "read", "library"), "📚"), (("key", "anahtar", "lock"), "🗝️"),
        (("ask", "talk", "sor", "konuş", "officer", "conductor", "waiter"), "💬"),
        (("look", "search", "check", "ara", "incele", "explore"), "🔎"),
        (("walk", "follow", "go", "return", "git", "yürü", "follow"), "👣"),
        (("light", "lantern", "fener", "candle"), "🕯️"), (("train", "tren", "carriage", "vagon"), "🚂"),
        (("water", "river", "nehir", "sea", "deniz"), "🌊"), (("wait", "bekle", "sit", "otur"), "⏳"),
        (("take", "al", "keep", "tut"), "🎒"), (("dragon", "ejderha", "forest", "orman"), "🐉"),
    ]:
        if any(word in t for word in words):
            return emoji
    return "✨"


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
:root { --ink:#1d2b4f; --paper:#fbfbf7; --grid:#dfe6ef; --margin:#d9534f; --mark:#fff0a8; --muted:#5b6786; --panel:rgba(251,251,247,.94); --button:#ffffff; }
.stApp { background-color:var(--paper); background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px); background-size:28px 28px; color:var(--ink); font-family:'Instrument Sans',sans-serif; }
.block-container { padding-top:2rem; max-width:1180px; border-left:2px solid var(--margin); padding-left:2rem !important; background:var(--panel); }
h1,h2,h3 { font-family:'Young Serif',serif !important; color:var(--ink) !important; font-weight:400 !important; }
h1 { font-size:2.3rem !important; }
p,li,label,span,div { font-family:'Instrument Sans',sans-serif; }
[data-testid="stSidebar"] { background:#eef1f6; border-right:1px solid var(--grid); }
[data-testid="stSidebar"] h1 { font-size:1.6rem !important; }
.word { font-family:'Caveat',cursive; font-size:3.8rem; line-height:1.1; color:var(--ink); display:inline-block; background:linear-gradient(transparent 58%,var(--mark) 58%); padding:0 .3rem; margin:.4rem 0 .6rem; }
.sentence { font-family:'Young Serif',serif; font-size:1.35rem; line-height:1.65; color:var(--ink) !important; }
.note { border-left:3px solid var(--ink); padding:.1rem 0 .1rem .9rem; margin:.8rem 0; }
.faint { color:var(--muted) !important; font-size:.92rem; }
.tally { font-family:'Caveat',cursive; font-size:2rem; letter-spacing:.15rem; color:var(--margin); }
div.stButton > button { border-radius:6px; border:1.5px solid var(--ink); background:var(--button); color:var(--ink); font-weight:600; box-shadow:2px 2px 0 var(--ink); }
div.stButton > button:hover { border-color:var(--margin); color:var(--ink); }
div.stButton > button[kind="primary"] { background:var(--ink); color:#fff; }
[data-testid="stMetric"] { background:rgba(255,255,255,.55); color:var(--ink); border:0; border-bottom:1.5px solid var(--ink); padding:.5rem; }
[data-testid="stProgressBar"] > div > div { background:var(--ink); }
:focus-visible { outline:2px solid var(--margin) !important; outline-offset:2px; }
div[data-testid="stAlert"] { border-radius:6px; }
/* Streamlit koyu tema seçildiğinde metin ve kart kontrastını koru */
html[data-theme="dark"], [data-theme="dark"] { --ink:#f0eee8; --paper:#151922; --grid:#252c39; --margin:#e58b82; --mark:#51452a; --muted:#c1c8d6; --panel:rgba(21,25,34,.96); --button:#252c39; }
html[data-theme="dark"] .stApp, [data-theme="dark"] .stApp { background-color:var(--paper) !important; color:var(--ink) !important; }
html[data-theme="dark"] .block-container, [data-theme="dark"] .block-container { background:var(--panel) !important; }
html[data-theme="dark"] h1,html[data-theme="dark"] h2,html[data-theme="dark"] h3,html[data-theme="dark"] p,html[data-theme="dark"] li,html[data-theme="dark"] label,html[data-theme="dark"] [data-testid="stMarkdownContainer"], [data-theme="dark"] h1,[data-theme="dark"] h2,[data-theme="dark"] h3,[data-theme="dark"] p,[data-theme="dark"] li,[data-theme="dark"] label,[data-theme="dark"] [data-testid="stMarkdownContainer"] { color:var(--ink); }
html[data-theme="dark"] [data-testid="stSidebar"], [data-theme="dark"] [data-testid="stSidebar"] { background:#1d2330 !important; }
html[data-theme="dark"] div.stButton > button, [data-theme="dark"] div.stButton > button { background:var(--button); color:var(--ink); border-color:#64708a; }
html[data-theme="dark"] div.stButton > button[kind="primary"], [data-theme="dark"] div.stButton > button[kind="primary"] { background:#d8dfef; color:#151922; }
html[data-theme="dark"] [data-testid="stMetric"], [data-theme="dark"] [data-testid="stMetric"] { background:#202633; color:var(--ink); }
html[data-theme="dark"] input,html[data-theme="dark"] textarea,html[data-theme="dark"] [data-baseweb="select"], [data-theme="dark"] input,[data-theme="dark"] textarea,[data-theme="dark"] [data-baseweb="select"] { color:var(--ink); }
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
        if st.button("Defterime ekle", type="primary"):
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
        elif st.button("Defterime ekle", type="primary"):
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
                with st.spinner("Söylediklerin yazıya çevriliyor…"):
                    heard = transcribe(audio.getvalue())

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
                st.error(stt_error(error))
                if type(error).__name__ not in ("UnknownValueError", "RequestError", "ImportError"):
                    st.caption(f"Teknik ayrıntı: {error}")

    st.markdown("#### 3. Mikrofon çalışmazsa yazıyla kontrol et")
    st.caption("Bu seçenek mikrofon yerine yazdığın cümleyi karşılaştırır; konuşma XP'si vermez.")
    typed_speech = st.text_input(
        "İngilizce cümleyi buraya yaz", key=f"typed_speech_{target}",
        placeholder="Örnek: I like learning English."
    )
    if st.button("Yazdığım cümleyi kontrol et", key=f"typed_check_{target}",
                 disabled=not typed_speech.strip(), use_container_width=True):
        ratio, diffs = make_speech_result(target, typed_speech)
        st.markdown(f"**Beklenen:** {target}")
        st.markdown(f"**Yazdığın:** {typed_speech.strip()}")
        st.progress(ratio)
        st.caption(f"Metin benzerliği: %{round(ratio * 100)}. Bu bir telaffuz puanı değildir.")
        if norm(target) == norm(typed_speech):
            st.success("Cümleyi doğru yazdın!")
        else:
            st.info("Farklı olan kelimeleri aşağıda görebilirsin:")
            for d in diffs:
                st.write(f"Beklenen: **{d['expected']}** → Yazdığın: **{d['heard']}**")

    st.caption("Gizlilik: Mikrofon kaydı yazıya çevrilmek için Google'ın çevrim içi servisine gönderilir. Yazıyla kontrol seçeneği ses kaydı göndermez.")


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
    game = st.radio("Oyun", ["Eşleştirme", "Cümle kurma", "Dinle ve yaz", "Hazine Avı", "☁️ Bulut Platformu", "⚡ Kelime Avcısı", "🎯 Hızlı Doğru"], horizontal=True,
                    label_visibility="collapsed")

    if game == "☁️ Bulut Platformu":
        st.subheader("☁️ Bulut Platformu: Gökyüzü Yolculuğu")
        st.write("Ok tuşlarıyla veya ekrandaki tuşlarla ilerle. Doğru cevap bulutuna zıplayınca bulutlar platforma dönüşür. Yanlış cevapta düşersin. Yıldızları topla, hareketli engellerden kaç ve kontrol noktalarına ulaş!")
        st.caption("Bilgisayar: ← → hareket, ↑ veya Boşluk zıplama. Telefon: alttaki tuşlara dokun. Oyunu başlatmak için oyun alanına bir kez tıkla.")
        platform_html = r"""
        <div id="lp-game" style="font-family:system-ui,sans-serif;color:#16324f;max-width:900px;margin:auto">
          <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-weight:700;margin-bottom:8px">
            <span id="status">⭐ Yıldız: 0/5</span><span id="level">Bölüm 1/4</span><span id="hint">← → hareket · ↑ zıpla</span>
          </div>
          <canvas id="sky" width="850" height="440" style="width:100%;height:auto;border-radius:18px;border:2px solid #9bc8ed;display:block;background:#8bd3ff;touch-action:none"></canvas>
          <div style="display:flex;justify-content:center;gap:12px;margin:12px 0">
            <button id="left" style="font-size:24px;padding:10px 22px;border:0;border-radius:12px;background:#d8ecff">⬅️</button>
            <button id="jump" style="font-size:22px;padding:10px 24px;border:0;border-radius:12px;background:#ffe6a8">⬆️ Zıpla</button>
            <button id="right" style="font-size:24px;padding:10px 22px;border:0;border-radius:12px;background:#d8ecff">➡️</button>
            <button id="restart" style="font-size:16px;padding:10px 14px;border:0;border-radius:12px;background:#e5e7eb">↻ Baştan</button>
          </div>
          <div id="message" style="font-weight:700;text-align:center;min-height:28px">Gökyüzüne hazır mısın? Başlamak için hareket et!</div>
        </div>
        <script>
        (() => {
          const c=document.getElementById('sky'), x=c.getContext('2d');
          const status=document.getElementById('status'), levelEl=document.getElementById('level'), msg=document.getElementById('message');
          const questions=[
            {q:'“Apple” ne demek?',a:['Elma','Kitap','Kedi'],ok:0},
            {q:'“Blue” hangi renktir?',a:['Kırmızı','Mavi','Yeşil'],ok:1},
            {q:'“I am happy” ne demek?',a:['Üzgünüm','Yorgunum','Mutluyum'],ok:2},
            {q:'“Cat” hangisidir?',a:['Kedi','Köpek','Kuş'],ok:0}
          ];
          let player, clouds, stars, level, collected, won, lost, keys, hazards, checkpoint, frame;
          function reset(){level=0;collected=0;won=false;lost=false;keys={};checkpoint=0;frame=0;makeLevel();msg.textContent='Gökyüzüne hazır mısın? Sağ-sol tuşlarıyla ilerle!';}
          function makeLevel(){
            player={x:42,y:330,w:28,h:36,vx:0,vy:0,ground:false};
            const qIndex=level%questions.length, q=questions[qIndex];
            document.getElementById('hint').textContent=q.q;
            const answers=q.a.slice();
            while(answers.length<3) answers.push('???');
            clouds=[
              {x:185,y:320,w:105,h:24,type:'quiz',q:qIndex,option:0,active:true,label:answers[0]},
              {x:405,y:250,w:105,h:24,type:'quiz',q:qIndex,option:1,active:true,label:answers[1]},
              {x:625,y:320,w:105,h:24,type:'quiz',q:qIndex,option:2,active:true,label:answers[2]},
              {x:765,y:350,w:78,h:24,type:'goal',active:true}
            ];
            stars=[{x:125,y:285,taken:false},{x:350,y:215,taken:false},{x:560,y:285,taken:false},{x:700,y:250,taken:false},{x:790,y:305,taken:false}];
            hazards=[{x:380,y:390,w:42,h:18,base:380,range:80,speed:1.7}];
          }
          function jump(){if(player.ground&&!won&&!lost){player.vy=-11.8;player.ground=false;}}
          function bindHold(id,key){const b=document.getElementById(id);b.addEventListener('pointerdown',e=>{e.preventDefault();keys[key]=true;if(key==='up')jump();});['pointerup','pointerleave','pointercancel'].forEach(ev=>b.addEventListener(ev,()=>keys[key]=false));}
          bindHold('left','left');bindHold('right','right');bindHold('jump','up');
          document.getElementById('restart').onclick=reset;
          window.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp',' ','a','d','w'].includes(e.key)){e.preventDefault();if(e.key==='ArrowLeft'||e.key==='a')keys.left=true;if(e.key==='ArrowRight'||e.key==='d')keys.right=true;if(e.key==='ArrowUp'||e.key===' '||e.key==='w')jump();}});
          window.addEventListener('keyup',e=>{if(e.key==='ArrowLeft'||e.key==='a')keys.left=false;if(e.key==='ArrowRight'||e.key==='d')keys.right=false;});
          function question(cloud){
            const q=questions[cloud.q];
            if(cloud.option===q.ok){
              clouds.filter(p=>p.type==='quiz').forEach(p=>{p.type='platform';p.active=false;});
              checkpoint=player.x;msg.textContent='✅ Doğru bulut! Bütün bulutlar platforma dönüştü. Yıldızları toplayıp bitişe ulaş!';
            } else {lost=true;msg.textContent='💨 Yanlış bulut! Gökyüzünden düştün. “Baştan” ile tekrar dene.';}
          }
          function drawCloud(p){
            x.fillStyle=p.type==='goal'?'#ffd166':p.type==='platform'?'#55c995':'#fff';
            x.beginPath();x.arc(p.x+25,p.y+5,18,0,Math.PI*2);x.arc(p.x+48,p.y-2,24,0,Math.PI*2);x.arc(p.x+72,p.y+6,18,0,Math.PI*2);x.fill();
            x.fillStyle='#244b6b';x.font='bold 12px system-ui';x.textAlign='center';
            if(p.type==='quiz'){x.fillStyle='#16324f';x.font='bold 13px system-ui';x.fillText(p.label,p.x+52,p.y-22);}
            if(p.type==='platform')x.fillText('PLATFORM',p.x+52,p.y+32);
            if(p.type==='goal')x.fillText('BİTİŞ ⭐',p.x+39,p.y+32);
          }
          function loop(){
            frame++;x.clearRect(0,0,c.width,c.height);
            const sky=x.createLinearGradient(0,0,0,440);sky.addColorStop(0,'#5ab8ff');sky.addColorStop(1,'#e3f7ff');x.fillStyle=sky;x.fillRect(0,0,850,440);
            x.fillStyle='rgba(255,255,255,.8)';[[80,65],[340,95],[690,65]].forEach(([a,b])=>{x.beginPath();x.arc(a,b,22,0,7);x.arc(a+25,b-8,29,0,7);x.arc(a+55,b,20,0,7);x.fill();});
            // Ana başlangıç zemini
            x.fillStyle='#75c66b';x.fillRect(0,390,105,50);
            x.fillStyle='#48a85b';for(let i=0;i<105;i+=28)x.fillRect(i,390,16,5);
            if(!won&&!lost){
              player.vx=(keys.left?-4:0)+(keys.right?4:0);player.x+=player.vx;player.x=Math.max(0,Math.min(822,player.x));
              player.vy+=0.52;player.y+=player.vy;player.ground=false;
              clouds.forEach(p=>{
                if(player.vy>=0&&player.x+player.w>p.x&&player.x<p.x+p.w&&player.y+player.h>=p.y-3&&player.y+player.h<=p.y+20){
                  player.y=p.y-player.h;player.vy=0;player.ground=true;
                  if(p.type==='quiz'&&p.active)question(p);
                  if(p.type==='goal'){level++;if(level>=4){won=true;msg.textContent='🏆 Harika! Dört gökyüzü bölümünü tamamladın! Yıldızları topladın ve İngilizce sorularını çözdün.';}else{makeLevel();msg.textContent='🌤️ Yeni bölüm! Bu kez yıldızları ve cevap bulutlarını bul.';}}
                }
              });
              hazards.forEach(h=>{h.x=h.base+Math.sin(frame*h.speed/35)*h.range;x.fillStyle='#ef476f';x.beginPath();x.moveTo(h.x,h.y+h.h);x.lineTo(h.x+h.w/2,h.y);x.lineTo(h.x+h.w,h.y+h.h);x.fill();if(player.x<h.x+h.w&&player.x+player.w>h.x&&player.y<h.y+h.h&&player.y+player.h>h.y){lost=true;msg.textContent='💥 Hareketli engele çarptın! Baştan deneyebilirsin.';}});
              stars.forEach(s=>{if(!s.taken){x.fillStyle='#ffbf00';x.font='25px sans-serif';x.fillText('★',s.x,s.y);if(Math.abs(player.x+14-s.x)<22&&Math.abs(player.y+15-s.y)<25){s.taken=true;collected++;}}});
              if(player.y>450){lost=true;msg.textContent='💨 Düştün! Yanlış bulut seçmiş veya platformu kaçırmış olabilirsin. Baştan deneyebilirsin.';}
            }
            clouds.forEach(drawCloud);
            // Sevimli oyuncu
            x.fillStyle='#ff8c42';x.fillRect(player.x,player.y,player.w,player.h);x.fillStyle='#fff';x.fillRect(player.x+5,player.y+8,6,7);x.fillRect(player.x+17,player.y+8,6,7);x.fillStyle='#19324d';x.fillRect(player.x+7,player.y+10,3,4);x.fillRect(player.x+19,player.y+10,3,4);x.fillStyle='#b85d32';x.fillRect(player.x+8,player.y+25,13,3);
            status.textContent='⭐ Yıldız: '+collected+'/5';levelEl.textContent='Bölüm '+Math.min(level+1,4)+'/4'+(won?' · TAMAMLANDI':'');
            requestAnimationFrame(loop);
          }
          reset();loop();
        })();
        </script>
        """
        components.html(platform_html, height=570, scrolling=False)

    elif game == "⚡ Kelime Avcısı":
        st.subheader("⚡ Kelime Avcısı")
        st.write("Süre dolmadan İngilizce kelimenin doğru Türkçe anlamını bul. Her turda yeni kelime gelir.")
        if "word_hunt_round" not in st.session_state:
            st.session_state.word_hunt_round = None
        if st.session_state.word_hunt_round is None:
            if st.button("Kelime avını başlat", key="word_hunt_start", type="primary"):
                w = random.choice(pool())
                opts = [w["tr"]] + [x["tr"] for x in random.sample([x for x in WORDS if x["tr"] != w["tr"]], 2)]
                random.shuffle(opts)
                st.session_state.word_hunt_round = {"word": w, "opts": opts, "answered": False, "correct": None}
                st.rerun()
        else:
            r = st.session_state.word_hunt_round
            st.markdown(f"## 🔤 {r['word']['en']}")
            pick = st.radio("Doğru anlam hangisi?", r["opts"], key="word_hunt_pick", index=None)
            if st.button("Cevabı kilitle", key="word_hunt_check", disabled=pick is None):
                r["answered"] = True
                r["correct"] = pick == r["word"]["tr"]
                if r["correct"]:
                    award(2)
                save()
                st.rerun()
            if r["answered"]:
                if r["correct"]:
                    st.success(f"Doğru! {r['word']['en']} = {r['word']['tr']} · +2 XP")
                else:
                    st.info(f"Doğru cevap: {r['word']['tr']}. Bir sonraki turda tekrar dene!")
                if st.button("Sonraki kelime", key="word_hunt_next"):
                    st.session_state.word_hunt_round = None
                    st.rerun()

    elif game == "🎯 Hızlı Doğru":
        st.subheader("🎯 Hızlı Doğru")
        st.write("İngilizce cümleyi oku ve Türkçe anlamının doğru olup olmadığına karar ver.")
        if "quick_true_round" not in st.session_state:
            st.session_state.quick_true_round = None
        if st.session_state.quick_true_round is None:
            if st.button("Turu başlat", key="quick_true_start", type="primary"):
                w = random.choice(pool())
                is_true = random.choice([True, False])
                shown = w["tr"] if is_true else random.choice([x["tr"] for x in WORDS if x["tr"] != w["tr"]])
                st.session_state.quick_true_round = {"word": w, "shown": shown, "truth": is_true, "answered": False}
                st.rerun()
        else:
            r = st.session_state.quick_true_round
            st.markdown(f"### {r['word']['en']}")
            st.info(f"Bu kelimenin anlamı: **{r['shown']}**")
            pick = st.radio("Doğru mu?", ["Doğru", "Yanlış"], key="quick_true_pick", index=None, horizontal=True)
            if st.button("Kontrol et", key="quick_true_check", disabled=pick is None):
                r["answered"] = True
                r["correct"] = (pick == "Doğru") == r["truth"]
                if r["correct"]:
                    award(2)
                save()
                st.rerun()
            if r["answered"]:
                st.success("Doğru karar! +2 XP" if r["correct"] else f"Bu kez olmadı. Doğru anlam: {r['word']['tr']}")
                if st.button("Yeni tur", key="quick_true_next"):
                    st.session_state.quick_true_round = None
                    st.rerun()

    if game == "Hazine Avı":
        st.subheader("🏝️ Hazine Avı: Kayıp Ada")
        st.write("Adayı keşfet, sandıkları bul ve basit İngilizce sorularını çöz. Her oda küçük bir keşif içerir.")
        hunt = st.session_state.treasure_hunt
        rooms = {
            "Beach": {"emoji": "🏖️", "tr": "Sahil", "clue": "Look under the sand.", "q": "What is this? 🍎", "opts": ["Apple", "Book", "Door"], "answer": "Apple", "word": "apple", "meaning": "elma"},
            "Forest": {"emoji": "🌳", "tr": "Orman", "clue": "The trees are green.", "q": "What color are the trees?", "opts": ["Blue", "Green", "Red"], "answer": "Green", "word": "green", "meaning": "yeşil"},
            "Cave": {"emoji": "🪨", "tr": "Mağara", "clue": "It is dark inside.", "q": "Choose the opposite of 'hot'.", "opts": ["Cold", "Big", "Fast"], "answer": "Cold", "word": "cold", "meaning": "soğuk"},
            "Lake": {"emoji": "💧", "tr": "Göl", "clue": "The water is clear.", "q": "I can ___ in water.", "opts": ["swim", "read", "sleeping"], "answer": "swim", "word": "swim", "meaning": "yüzmek"},
            "Temple": {"emoji": "🏛️", "tr": "Tapınak", "clue": "The treasure is near!", "q": "What do you use to open a door?", "opts": ["A key", "A cloud", "A fish"], "answer": "A key", "word": "key", "meaning": "anahtar"},
        }
        unlocked = {"Beach": True, "Forest": "Beach" in hunt["opened"], "Cave": "Forest" in hunt["opened"], "Lake": "Cave" in hunt["opened"], "Temple": "Lake" in hunt["opened"]}
        st.caption(f"Bölüm: {len(hunt['opened'])}/5 · Bulunan kelime: {len(hunt['found'])}/5")
        map_cols = st.columns(5)
        for col, (room_name, room) in zip(map_cols, rooms.items()):
            disabled = not unlocked[room_name]
            label = ("✅ " if room_name in hunt["opened"] else room["emoji"] + " ") + room["tr"]
            if col.button(label, key=f"hunt_room_{room_name}", disabled=disabled, use_container_width=True):
                hunt["room"] = room_name
                save()
                st.rerun()
        current = hunt.get("room", "Beach")
        if current not in rooms or not unlocked.get(current, False):
            current = "Beach"
            hunt["room"] = current
        room = rooms[current]
        st.markdown(f"### {room['emoji']} {room['tr']} / {current}")
        st.info(f"**İpucu:** {room['clue']}  \n\nTürkçesi: { {'Beach':'Kumun altına bak.','Forest':'Ağaçlar yeşildir.','Cave':'İçerisi karanlık.','Lake':'Su berrak.','Temple':'Hazine çok yakın!'}[current] }")
        if current in hunt["opened"]:
            st.success("Bu bölümü zaten keşfettin. Haritadan başka bir yere gidebilirsin.")
            st.write(f"Kelime: **{room['word']}** — {room['meaning']}")
        else:
            st.write("🧰 **Sandık bulundu!** Açmak için İngilizce soruyu cevapla.")
            pick = st.radio(room["q"], room["opts"], index=None, key=f"hunt_pick_{current}")
            if st.button("Sandığı aç", type="primary", key=f"hunt_open_{current}", disabled=pick is None):
                if pick == room["answer"]:
                    hunt["opened"].append(current)
                    if room["word"] not in hunt["found"]:
                        hunt["found"].append(room["word"])
                    # Kelimeyi görmek/toplamak XP vermez; yalnızca ilk doğru çözüm küçük oyun ödülü verir.
                    if current not in hunt.get("xp_rooms", []):
                        hunt.setdefault("xp_rooms", []).append(current)
                        award(3)
                    if len(hunt["opened"]) == len(rooms):
                        hunt["complete"] = True
                    save()
                    st.success(f"Doğru! {room['word']} = {room['meaning']}. +3 XP")
                    st.rerun()
                else:
                    st.error("Henüz olmadı. İngilizce ipucunu tekrar oku ve yeniden dene!")
        if hunt.get("complete"):
            st.balloons()
            st.success("🏆 Hazineyi buldun! Harika iş çıkardın.")
            if st.button("Hazine Avı'nı yeniden başlat", key="hunt_reset"):
                st.session_state.treasure_hunt = {"room": "Beach", "found": [], "opened": [], "complete": False, "xp_claimed": False, "xp_rooms": []}
                save()
                st.rerun()

    elif game == "Eşleştirme":
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
        asset_dir = Path(__file__).resolve().parent / "lingopath_assets"
        for sid, s in STORIES.items():
            with st.container(border=True):
                image_path = asset_dir / s.get("image", "")
                if image_path.is_file():
                    st.image(str(image_path), use_container_width=True)
                st.subheader(f"{s['emoji']} {s['title']}")
                st.write(s["desc"])
                st.caption("Sonlar: " + " · ".join(
                    (f"✅ {t}" if k in found else "▫️ ???") for k, t in s["ends"].items()))
                if st.button("Maceraya başla", key=f"adv_start_{sid}", type="primary", use_container_width=True):
                    adv_start(sid)
                    st.rerun()
    else:
        story = STORIES[a["story"]]
        nid = a["node"]
        node = ADVENTURE[nid]
        st.title(f"{story['emoji']} {story['title']}")

        top1, top2 = st.columns([3, 1])
        top1.caption(f"Bölüm {a['steps']} · Keşfedilen yer: {len(a.get('visited', []))} · Sonlar: {sum(k in found for k in story['ends'])}/{len(story['ends'])}")
        with st.expander("🗺️ Keşif haritam", expanded=False):
            st.caption("Daha önce ziyaret ettiğin sahnelere geri dönebilirsin. Bitmiş sonlar haritadan tekrar açılamaz.")
            map_nodes = [n for n in a.get("visited", []) if n != nid and "end" not in ADVENTURE.get(n, {})]
            if map_nodes:
                map_cols = st.columns(2)
                for idx, map_nid in enumerate(map_nodes[-8:]):
                    map_label = a.get("map_labels", {}).get(map_nid, map_nid.replace("_", " ").title())
                    if map_cols[idx % 2].button(f"📍 {map_label}", key=f"adv_map_{a['pick_id']}_{map_nid}", use_container_width=True):
                        adv_enter(map_nid)
                        st.rerun()
            else:
                st.info("Haritanda henüz geri dönebileceğin başka bir yer yok. Bir seçeneğe tıklayarak keşfe başla.")
        with st.expander(f"🎒 Envanter ({len(a['items'])} eşya)", expanded=bool(a["items"])):
            if a["items"]:
                for item_id in a["items"]:
                    st.markdown(f"- {ADV_ITEMS.get(item_id, item_id)}")
                st.caption("Bazı seçenekler yalnızca gerekli eşyayı bulduğunda açılır.")
            else:
                st.write("Henüz eşya toplamadın. Çevreyi araştır ve ipuçlarını kaçırma.")
        if top2.button("↩️ Baştan", use_container_width=True):
            st.session_state.adv = None
            st.rerun()

        if a.get("flash"):
            kind, msg = a["flash"]
            (st.success if kind == "ok" else st.warning)(msg)
            a["flash"] = None

        asset_dir = Path(__file__).resolve().parent / "lingopath_assets"
        story_image = asset_dir / story.get("image", "")
        if story_image.is_file():
            st.image(str(story_image), use_container_width=True)
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
                    elif c2.button("Defterime ekle", key=f"adv_add_{en}_{a['steps']}"):
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
            st.markdown("#### 👆 Sahnedeki yerlere ve nesnelere tıkla")
            st.caption("Her seçenek yeni bir olay, ipucu veya bölge açabilir.")
            available_choices = [c for c in node["choices"] if not c["needs"] or c["needs"] in a["items"]]
            for row_start in range(0, len(available_choices), 2):
                cols = st.columns(2)
                for offset, c in enumerate(available_choices[row_start:row_start + 2]):
                    i = row_start + offset
                    label = c["en"] + (f"  ({ADV_ITEMS[c['needs']]})" if c["needs"] else "")
                    with cols[offset]:
                        with st.container(border=True):
                            st.markdown(f"<div style='font-size:2rem'>{choice_icon(c['en'] + ' ' + c['tr'])}</div>", unsafe_allow_html=True)
                            st.markdown(f"**{c['en']}**")
                            st.caption(c["tr"])
                            if st.button("Burayı araştır →", key=f"adv_c_{a['steps']}_{i}", help=c["tr"], use_container_width=True):
                                a.setdefault("map_labels", {})[c["to"]] = c["tr"]
                                adv_enter(c["to"])
                                st.rerun()


# ---------- DEFTERİM ----------
elif page == "Defterim":
    st.title("📘 İngilizce Kelime Defterim")
    st.write("Öğrendiğin kelimeleri, anlamlarını ve örnek cümlelerini gerçek bir defter gibi burada bulabilirsin.")

    learned = sorted(set(st.session_state.learned))
    c1, c2 = st.columns(2)
    c1.metric("Defterdeki kelimeler", len(learned))
    c2.metric("Tekrarı gelen kelimeler", len(due_words()))
    st.caption("Kelimeyi deftere eklemek XP kazandırmaz.")

    query = st.text_input("🔎 Defterimde ara", placeholder="İngilizce kelime veya Türkçe anlamı…").strip().casefold()
    level_filter = st.selectbox("Seviye filtresi", LEVELS, key="notebook_level_filter")
    notebook_words = [BY_EN[en] for en in learned if en in BY_EN]
    if query:
        notebook_words = [w for w in notebook_words if query in w["en"].casefold() or query in w["tr"].casefold() or query in w["example"].casefold()]
    if level_filter != "Tümü":
        notebook_words = [w for w in notebook_words if w["level"] == level_filter]

    st.markdown(f"**Defter sayfası · {len(notebook_words)} kelime**")
    if notebook_words:
        for index, word in enumerate(notebook_words, start=1):
            srs_card = st.session_state.srs.get(word["en"], {})
            box_num = srs_card.get("box", 1)
            card_html = f"""<div style="position:relative; margin:12px 0; padding:18px 18px 16px 56px;
            border:1px solid #d6d9df; border-radius:5px; color:#202b45;
            background-color:#fffdf5;
            background-image:linear-gradient(to bottom, transparent 31px, #d9e4f2 32px);
            background-size:100% 32px; box-shadow:2px 3px 0 rgba(30,40,60,.08);">
            <div style="position:absolute; left:36px; top:0; bottom:0; border-left:2px solid #dc8d8d;"></div>
            <div style="font-family:Georgia,serif; font-size:23px; line-height:32px; color:#1f3b67;"><b>{index}. {word['en']}</b></div>
            <div style="line-height:32px; font-size:17px;"><b>Türkçe:</b> {word['tr']}</div>
            <div style="line-height:32px; font-style:italic;">{word['example']}</div>
            <div style="line-height:25px; color:#69758b; font-size:13px;">{word['level']} seviye · Tekrar kutusu {box_num}/5</div>
            </div>"""
            st.markdown(card_html, unsafe_allow_html=True)
            col_a, col_b = st.columns([1, 1])
            with col_a:
                speak(word["en"], "🔊 Kelimeyi dinle", key=f"notebook_word_audio_{word['en']}")
            with col_b:
                speak(word["example"], "🔊 Örnek cümleyi dinle", key=f"notebook_example_audio_{word['en']}")
    else:
        st.info("Henüz burada gösterilecek kelime yok. Kelimeler bölümünden öğrendiğin kelimeleri defterine ekleyebilirsin.")

    st.divider()
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
