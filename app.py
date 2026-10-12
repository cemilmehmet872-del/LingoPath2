import difflib

import json

import random

import re

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="LingoPath", page_icon="✏️", layout="centered")

SAVE = Path("lingopath_progress.json")

WORDS = [

    ("apple", "elma", "I eat an apple.", "Başlangıç"),

    ("borrow", "ödünç almak", "Can I borrow your pen?", "Başlangıç"),

    ("quiet", "sessiz", "The library is quiet.", "Başlangıç"),

    ("careful", "dikkatli", "Be careful when you cross the road.", "Başlangıç"),

    ("journey", "yolculuk", "Learning English is a journey.", "Başlangıç"),

    ("beautiful", "güzel", "The garden is beautiful.", "Başlangıç"),

    ("improve", "geliştirmek", "I want to improve my English.", "Orta"),

    ("although", "her ne kadar", "Although it was late, we continued.", "Orta"),

    ("environment", "çevre", "We should protect the environment.", "Orta"),

    ("discover", "keşfetmek", "I want to discover new places.", "Orta"),

    ("challenge", "zorluk", "Learning a language is a challenge.", "Orta"),

    ("confident", "kendine güvenen", "I feel confident when I practise.", "Orta"),

    ("achieve", "başarmak", "You can achieve your goals.", "Orta"),

    ("curious", "meraklı", "Curious students ask questions.", "Orta"),

    ("opportunity", "fırsat", "This is a great opportunity.", "İleri"),

]

WORDS = [dict(en=a, tr=b, example=c, level=d) for a, b, c, d in WORDS]

BY_EN = {w["en"]: w for w in WORDS}

SENTENCES = [

    "I want to improve my English.",

    "Can I borrow your pen?",

    "The library is quiet.",

    "I eat an apple.",

    "Learning English is a journey.",

    "You can achieve your goals.",

]

PAGES = ["Bugün", "Kelimeler", "Konuşma", "Test", "Oyunlar", "Defterim"]

# ---------- kalıcı ilerleme ----------

def load():

    try:

        return json.loads(SAVE.read_text(encoding="utf-8"))

    except Exception:

        return {}

def save():

    data = {"xp": st.session_state.xp,

            "learned": st.session_state.learned,

            "spoken": st.session_state.spoken}

    try:

        SAVE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    except OSError:

        pass

if "xp" not in st.session_state:

    d = load()

    st.session_state.xp = d.get("xp", 0)

    st.session_state.learned = d.get("learned", [])

    st.session_state.spoken = d.get("spoken", [])

    st.session_state.page = "Bugün"

    st.session_state.q = None          # test sorusu

    st.session_state.round = {"n": 0, "score": 0}

    st.session_state.g = None          # eşleştirme oyunu

    st.session_state.s = None          # cümle oyunu

    st.session_state.nonce = 0

def award(n):

    st.session_state.xp += n

    save()

def go(page):

    st.session_state.page = page

def new_nonce():

    st.session_state.nonce += 1

    return st.session_state.nonce

def norm(t):

    return " ".join(re.sub(r"[^\w\s']", " ", t.lower()).split())

def make_question():

    w = random.choice(WORDS)

    wrong = random.sample([x["tr"] for x in WORDS if x["tr"] != w["tr"]], 3)

    opts = random.sample(wrong + [w["tr"]], 4)

    return {"word": w, "opts": opts, "done": False, "ok": None, "id": new_nonce()}

# ---------- görünüm: kareli defter ----------

st.markdown("""

<style>

@import url('https://fonts.googleapis.com/css2?family=Young+Serif&family=Instrument+Sans:wght@400;500;600&family=Caveat:wght@600&display=swap');

:root { --ink:#1d2b4f; --paper:#fbfbf7; --grid:#dfe6ef; --margin:#d9534f; --mark:#fff0a8; }

.stApp {

    background-color: var(--paper);

    background-image:

        linear-gradient(var(--grid) 1px, transparent 1px),

        linear-gradient(90deg, var(--grid) 1px, transparent 1px);

    background-size: 28px 28px;

    color: var(--ink);

    font-family: 'Instrument Sans', sans-serif;

}

.block-container { padding-top: 2.5rem; max-width: 720px;

    border-left: 2px solid var(--margin); padding-left: 2.4rem !important;

    background: rgba(251,251,247,.86); }

h1, h2, h3 { font-family: 'Young Serif', serif !important; color: var(--ink) !important;

    font-weight: 400 !important; letter-spacing: 0; }

h1 { font-size: 2.3rem !important; }

p, li, label, span, div { font-family: 'Instrument Sans', sans-serif; }

[data-testid="stSidebar"] { background: #eef1f6; border-right: 1px solid var(--grid); }

[data-testid="stSidebar"] h1 { font-size: 1.6rem !important; }

.word { font-family: 'Caveat', cursive; font-size: 4rem; line-height: 1.1; color: var(--ink);

    display: inline-block; background: linear-gradient(transparent 58%, var(--mark) 58%);

    padding: 0 .3rem; transform: rotate(-1.2deg); margin: .4rem 0 .6rem; }

.sentence { font-family: 'Young Serif', serif; font-size: 1.5rem; line-height: 1.4; }

.note { border-left: 3px solid var(--ink); padding: .1rem 0 .1rem .9rem; margin: .8rem 0; }

.faint { color: #5b6786; font-size: .92rem; }

div.stButton > button { border-radius: 4px; border: 1.5px solid var(--ink); background: white;

    color: var(--ink); font-weight: 500; box-shadow: 2px 2px 0 var(--ink); }

div.stButton > button:hover { transform: translate(1px,1px); box-shadow: 1px 1px 0 var(--ink);

    border-color: var(--ink); color: var(--ink); }

div.stButton > button[kind="primary"] { background: var(--ink); color: white; }

[data-testid="stMetric"] { background: transparent; border: 0; border-bottom: 1.5px solid var(--ink);

    border-radius: 0; padding: 0 0 .4rem; }

[data-testid="stProgressBar"] > div > div { background: var(--ink); }

:focus-visible { outline: 2px solid var(--margin) !important; outline-offset: 2px; }

</style>

""", unsafe_allow_html=True)

# ---------- kenar çubuğu ----------

xp = st.session_state.xp

with st.sidebar:

    st.markdown("# LingoPath")

    st.radio("Bölüm", PAGES, key="page", label_visibility="collapsed")

    st.write("")

    st.caption(f"Seviye {1 + xp // 100} · {xp % 100}/100 XP")

    st.progress((xp % 100) / 100)

page = st.session_state.page

# ---------- BUGÜN ----------

if page == "Bugün":

    n = len(set(st.session_state.learned))

    st.title("Bugün ne çalışalım?")

    if n == 0:

        st.write("Henüz defterin boş. Bir kelimeyle başla, sonra cümleyi yüksek sesle oku.")

    else:

        st.write(f"Defterinde {n} kelime var. Kaldığın yerden devam edebilirsin.")

    todo = [w for w in WORDS if w["en"] not in st.session_state.learned]

    if todo:

        w = todo[0]

        st.markdown(f"<div class='word'>{w['en']}</div>", unsafe_allow_html=True)

        st.markdown(f"**{w['tr']}** — {w['example']}")

    st.write("")

    c = st.columns(4)

    c[0].button("Kelimeler", on_click=go, args=("Kelimeler",), use_container_width=True)

    c[1].button("Konuşma", on_click=go, args=("Konuşma",), use_container_width=True)

    c[2].button("Test", on_click=go, args=("Test",), use_container_width=True)

    c[3].button("Oyunlar", on_click=go, args=("Oyunlar",), use_container_width=True)

# ---------- KELİMELER ----------

elif page == "Kelimeler":

    st.title("Kelimeler")

    col1, col2 = st.columns([2, 1])

    q = col1.text_input("Ara", placeholder="journey, elma…")

    lvl = col2.selectbox("Seviye", ["Tümü", "Başlangıç", "Orta", "İleri"])

    q = q.strip().lower()

    items = [w for w in WORDS

             if (lvl == "Tümü" or w["level"] == lvl)

             and (not q or q in w["en"] or q in w["tr"])]

    if not items:

        st.warning("Eşleşen kelime yok. Aramayı kısaltmayı veya seviyeyi “Tümü” yapmayı dene.")

    else:

        w = st.selectbox("Kelime", items, format_func=lambda x: f"{x['en']} — {x['tr']}")

        st.markdown(f"<div class='word'>{w['en']}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='note'><b>{w['tr']}</b><br>{w['example']}"

                    f"<br><span class='faint'>{w['level']}</span></div>",

                    unsafe_allow_html=True)

        if w["en"] in st.session_state.learned:

            st.success("Defterinde.")

        elif st.button("Defterime ekle (+10 XP)", type="primary"):

            st.session_state.learned.append(w["en"])

            award(10)

            st.rerun()

# ---------- KONUŞMA ----------

elif page == "Konuşma":

    st.title("🎙️ Konuşma pratiği")
    st.write("Önce örnek cümleyi dinle, ardından mikrofonla kendi sesini kaydet ve kontrol et.")

    target = st.selectbox("Çalışılacak cümle", SENTENCES)
    st.markdown(f"<p class='sentence'>{target}</p>", unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        if st.button("🔊 Örneği dinle", use_container_width=True):
            try:
                from gtts import gTTS
                from io import BytesIO

                audio_buffer = BytesIO()
                gTTS(text=target, lang="en", slow=False).write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                st.audio(audio_buffer, format="audio/mp3")
            except ImportError:
                st.error("Sesli örnek için gTTS kurulmamış. Terminalde: python -m pip install gTTS")
            except Exception:
                st.error("Örnek ses oluşturulamadı. İnternet bağlantını kontrol edip tekrar dene.")

    with right:
        st.info("İpucu: Tarayıcı mikrofon izni isterse **İzin ver** seçeneğine bas.")

    st.markdown("#### 1. Mikrofonla kaydet")
    audio = st.audio_input("🎤 Kaydı başlatmak için mikrofon düğmesine bas", key=f"audio_{target}")

    if audio is not None:
        st.audio(audio, format="audio/wav")
        if st.button("✅ Kaydımı kontrol et", type="primary", use_container_width=True):
            try:
                import speech_recognition as sr
                from io import BytesIO

                rec = sr.Recognizer()
                audio_bytes = BytesIO(audio.getvalue())
                with sr.AudioFile(audio_bytes) as audio_source:
                    data = rec.record(audio_source)

                with st.spinner("Söylediklerin yazıya çevriliyor…"):
                    heard = rec.recognize_google(data, language="en-US")

                target_norm = norm(target)
                heard_norm = norm(heard)
                ratio = difflib.SequenceMatcher(None, target_norm, heard_norm).ratio()

                st.markdown("#### 2. Sonuç")
                st.write("**Beklenen cümle:**", target)
                st.write("**Duyulan cümle:**", heard)
                st.progress(ratio)
                st.caption(f"Metin benzerliği: %{round(ratio * 100)}. Bu değer gerçek bir fonetik telaffuz puanı değildir.")

                if target_norm == heard_norm:
                    st.success("Cümle doğru tanındı! Güzel iş. 🎉")
                    if target not in st.session_state.spoken:
                        st.session_state.spoken.append(target)
                        award(5)
                        st.success("+5 XP kazandın.")
                else:
                    st.warning("Bazı kelimeler farklı algılanmış olabilir.")
                    expected_words = target_norm.split()
                    heard_words = heard_norm.split()
                    matcher = difflib.SequenceMatcher(None, expected_words, heard_words)
                    differences = []
                    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                        if tag != "equal":
                            expected = " ".join(expected_words[i1:i2]) or "—"
                            recognized = " ".join(heard_words[j1:j2]) or "—"
                            differences.append((expected, recognized))
                    if differences:
                        st.markdown("**Tekrar çalışabileceğin kısımlar:**")
                        for expected, recognized in differences:
                            st.write(f"• Beklenen: **{expected}** → Duyulan: **{recognized}**")
                    st.caption("Gürültüsüz bir ortamda, cümleyi biraz yavaş söyleyip tekrar deneyebilirsin.")

            except ImportError:
                st.error("Gerekli paket kurulu değil. Terminalde: python -m pip install SpeechRecognition")
            except Exception as e:
                st.error("Ses çözümlenemedi. Mikrofon iznini, internet bağlantını ve kaydı kontrol et.")
                st.caption(f"Hata ayrıntısı: {e}")

    st.caption("Not: Ses tanıma için kayıt Google'ın çevrim içi konuşma tanıma servisine gönderilir. Bu özellik sesleri karşılaştırır; tek başına bilimsel bir telaffuz değerlendirmesi değildir.")

# ---------- TEST ----------

elif page == "Test":

    st.title("Test")

    r = st.session_state.round

    if r["n"] >= 5:

        st.markdown(f"<p class='sentence'>5 sorudan {r['score']} doğru.</p>",

                    unsafe_allow_html=True)

        if st.button("Yeni tur", type="primary"):

            st.session_state.round = {"n": 0, "score": 0}

            st.session_state.q = None

            st.rerun()

    else:

        if st.session_state.q is None:

            st.session_state.q = make_question()

        q = st.session_state.q

        w = q["word"]

        st.caption(f"Soru {r['n'] + 1} / 5")

        st.markdown(f"<div class='word'>{w['en']}</div>", unsafe_allow_html=True)

        pick = st.radio("Türkçesi nedir?", q["opts"], index=None,

                        key=f"pick_{q['id']}", disabled=q["done"])

        if not q["done"]:

            if st.button("Cevapla", type="primary", disabled=pick is None):

                q["done"] = True

                q["ok"] = pick == w["tr"]

                r["n"] += 1

                if q["ok"]:

                    r["score"] += 1

                    award(5)

                st.rerun()

        else:

            if q["ok"]:

                st.success("Doğru. +5 XP")

            else:

                st.error(f"Doğrusu: {w['tr']}")

            if st.button("Devam"):

                st.session_state.q = None

                st.rerun()

# ---------- OYUNLAR ----------

elif page == "Oyunlar":

    st.title("Oyunlar")

    game = st.radio("Oyun", ["Eşleştirme", "Cümle kurma"], horizontal=True,

                    label_visibility="collapsed")

    if game == "Eşleştirme":

        st.caption("Beş kelimeyi doğru anlamlarıyla eşle.")

        if st.session_state.g is None:

            if st.button("Başla", type="primary"):

                ws = random.sample(WORDS, 5)

                st.session_state.g = {"ws": ws, "tr": random.sample([x["tr"] for x in ws], 5),

                                      "id": new_nonce(), "res": None}

                st.rerun()

        else:

            g = st.session_state.g

            answers = {}

            for w in g["ws"]:

                a, b = st.columns([1, 2])

                a.markdown(f"<div class='sentence'>{w['en']}</div>", unsafe_allow_html=True)

                answers[w["en"]] = b.selectbox(w["en"], ["—"] + g["tr"], key=f"m_{g['id']}_{w['en']}",

                                               label_visibility="collapsed")

            if g["res"] is None:

                if st.button("Kontrol et", type="primary"):

                    g["res"] = sum(answers[w["en"]] == w["tr"] for w in g["ws"])

                    award(g["res"] * 3)

                    st.rerun()

            else:

                st.success(f"5 eşleşmeden {g['res']} doğru. +{g['res'] * 3} XP")

                for w in g["ws"]:

                    st.write(f"{w['en']} → {w['tr']}")

                if st.button("Yeni oyun"):

                    st.session_state.g = None

                    st.rerun()

    else:

        st.caption("Karışık kelimelerden cümleyi kur.")

        if st.session_state.s is None:

            if st.button("Başla", type="primary"):

                sent = random.choice(SENTENCES)

                words = sent.rstrip(".?!").split()

                sh = words[:]

                while sh == words:

                    random.shuffle(sh)

                st.session_state.s = {"sent": sent, "sh": sh, "id": new_nonce(), "ok": None}

                st.rerun()

        else:

            s = st.session_state.s

            st.markdown(f"<p class='sentence'>{' / '.join(s['sh'])}</p>", unsafe_allow_html=True)

            ans = st.text_input("Cümlen", key=f"s_{s['id']}", disabled=s["ok"] is not None)

            if s["ok"] is None:

                if st.button("Kontrol et", type="primary", disabled=not ans.strip()):

                    s["ok"] = norm(ans) == norm(s["sent"])

                    if s["ok"]:

                        award(10)

                    st.rerun()

            else:

                if s["ok"]:

                    st.success("Doğru. +10 XP")

                else:

                    st.error(f"Doğrusu: {s['sent']}")

                if st.button("Başka cümle"):

                    st.session_state.s = None

                    st.rerun()

# ---------- DEFTERİM ----------

elif page == "Defterim":

    st.title("Defterim")

    learned = sorted(set(st.session_state.learned))

    a, b, c = st.columns(3)

    a.metric("XP", xp)

    b.metric("Seviye", 1 + xp // 100)

    c.metric("Kelime", len(learned))

    st.caption(f"Sonraki seviyeye {100 - xp % 100} XP.")

    st.subheader("Öğrendiklerim")

    if learned:

        for en in learned:

            st.markdown(f"**{en}** — {BY_EN[en]['tr']}")

    else:

        st.info("Henüz kelime yok. Kelimeler bölümünden ilkini ekle.")

    with st.expander("İlerlemeyi sıfırla"):

        st.warning("XP ve kelimelerin kalıcı olarak silinir.")

        if st.checkbox("Onaylıyorum") and st.button("Sıfırla"):

            st.session_state.xp = 0

            st.session_state.learned = []

            st.session_state.spoken = []

            save()

            st.rerun()
