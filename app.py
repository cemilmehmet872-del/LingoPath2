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

PAGES = ["Bugün", "Kelimeler", "Tekrar", "Konuşma", "Test", "Oyunlar", "Defterim"]


def today():
    return date.today().isoformat()


# ---------- Kalıcı ilerleme ----------
PERSIST = ["xp", "learned", "spoken", "speaking_history", "srs", "daily", "streak"]


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
                             ("streak", {"last": None, "count": 0})]:
            st.session_state[key] = data.get(key, default)
    ses = {"page": "Bugün", "q": None, "round": {"n": 0, "score": 0}, "g": None,
           "s": None, "d": None, "nonce": 0, "rv_show": False}
    for key, default in ses.items():
        st.session_state.setdefault(key, default)
    for key, default in [("learned", []), ("spoken", []), ("speaking_history", []),
                         ("srs", {}), ("daily", {"date": today(), "xp": 0}),
                         ("streak", {"last": None, "count": 0})]:
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

    st.markdown("### Çalışmaya başla")
    cols = st.columns(4)
    for col, name in zip(cols, ["Kelimeler", "Konuşma", "Test", "Oyunlar"]):
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


# ---------- DEFTERİM ----------
elif page == "Defterim":
    st.title("Defterim")
    learned = sorted(set(st.session_state.learned))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("XP", st.session_state.xp)
    c2.metric("Seviye", 1 + st.session_state.xp // 100)
    c3.metric("Kelime", len(learned))
    c4.metric("Seri", f"{streak_count()} gün")
    st.caption(f"Sonraki seviyeye {100 - st.session_state.xp % 100} XP.")

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
                st.session_state.round = {"n": 0, "score": 0}
                save()
                st.rerun()
