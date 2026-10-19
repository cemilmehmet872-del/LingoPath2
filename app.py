"""LingoPath düzeltme betiği.

Kullanım:
    python patch_lingopath.py app.py
(app.py yerine kendi dosyanın adını yaz.)

Orijinal dosyayı <ad>.bak olarak yedekler, düzeltilmiş hâli aynı adla yazar.
"""
import re
import shutil
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("Kullanım: python patch_lingopath.py app.py")

src = Path(sys.argv[1])
text = src.read_text(encoding="utf-8")
shutil.copy(src, src.with_suffix(src.suffix + ".bak"))

ok, fail = [], []


def patch(name, old, new, count=1):
    global text
    n = text.count(old)
    if n != count:
        fail.append(f"{name} (bulunan: {n}, beklenen: {count})")
        return
    text = text.replace(old, new)
    ok.append(name)


# 1) Oyunlar zincirindeki if -> elif
patch("Hazine Avı elif", '    if game == "Hazine Avı":', '    elif game == "Hazine Avı":')

# 2) Günlük görev butonu (callback)
patch("Günlük görev butonu",
      '''    if st.button("Günlük görevleri gör"):
        go("Günlük Görev")
        st.rerun()''',
      '''    st.button("Günlük görevleri gör", on_click=go, args=("Günlük Görev",))''')

# 3) Kelime Avcısı
patch("Kelime Avcısı metin",
      "Süre dolmadan İngilizce kelimenin doğru Türkçe anlamını bul.",
      "İngilizce kelimenin doğru Türkçe anlamını bul.")
patch("Kelime Avcısı id",
      '{"word": w, "opts": opts, "answered": False, "correct": None}',
      '{"word": w, "opts": opts, "answered": False, "correct": None, "id": new_nonce()}')
patch("Kelime Avcısı tek cevap",
      '''            pick = st.radio("Doğru anlam hangisi?", r["opts"], key="word_hunt_pick", index=None)
            if st.button("Cevabı kilitle", key="word_hunt_check", disabled=pick is None):
                r["answered"] = True
                r["correct"] = pick == r["word"]["tr"]
                if r["correct"]:
                    award(2)
                save()
                st.rerun()''',
      '''            if not r["answered"]:
                pick = st.radio("Doğru anlam hangisi?", r["opts"], key=f"word_hunt_pick_{r['id']}", index=None)
                if st.button("Cevabı kilitle", key="word_hunt_check", disabled=pick is None):
                    r["answered"] = True
                    r["correct"] = pick == r["word"]["tr"]
                    if r["correct"]:
                        award(2)
                    save()
                    st.rerun()''')

# 4) Hızlı Doğru
patch("Hızlı Doğru id",
      '{"word": w, "shown": shown, "truth": is_true, "answered": False}',
      '{"word": w, "shown": shown, "truth": is_true, "answered": False, "id": new_nonce()}')
patch("Hızlı Doğru tek cevap",
      '''            pick = st.radio("Doğru mu?", ["Doğru", "Yanlış"], key="quick_true_pick", index=None, horizontal=True)
            if st.button("Kontrol et", key="quick_true_check", disabled=pick is None):
                r["answered"] = True
                r["correct"] = (pick == "Doğru") == r["truth"]
                if r["correct"]:
                    award(2)
                save()
                st.rerun()''',
      '''            if not r["answered"]:
                pick = st.radio("Doğru mu?", ["Doğru", "Yanlış"], key=f"quick_true_pick_{r['id']}", index=None, horizontal=True)
                if st.button("Kontrol et", key="quick_true_check", disabled=pick is None):
                    r["answered"] = True
                    r["correct"] = (pick == "Doğru") == r["truth"]
                    if r["correct"]:
                        award(2)
                    save()
                    st.rerun()''')

# 5) Karanlık tema: data-theme yerine prefers-color-scheme
new_css = """@media (prefers-color-scheme: dark) {
  :root { --ink:#f0eee8; --paper:#151922; --grid:#252c39; --margin:#e58b82; --mark:#51452a; --muted:#c1c8d6; --panel:rgba(21,25,34,.96); --button:#252c39; }
  [data-testid="stSidebar"] { background:#1d2330 !important; }
  [data-testid="stMetric"] { background:#202633; }
  div.stButton > button { border-color:#64708a; }
  div.stButton > button[kind="primary"] { background:#d8dfef; color:#151922; }
  [data-testid="stMarkdownContainer"], label, p, li { color:var(--ink); }
}
"""
text, n = re.subn(r"/\* Streamlit koyu tema.*?(?=</style>)", lambda m: new_css, text, count=1, flags=re.S)
(ok if n else fail).append("Karanlık tema CSS")

# 6) Kayıt dosyası: sabit yol, atomik yazma, dialogue_done
patch("SAVE yolu", 'SAVE = Path("lingopath_progress.json")',
      'SAVE = Path(__file__).resolve().parent / "lingopath_progress.json"')
patch("PERSIST",
      '"streak", "endings", "treasure_hunt"]',
      '"streak", "endings", "treasure_hunt", "dialogue_done"]')
patch("save() get", 'data = {k: st.session_state[k] for k in PERSIST}',
      'data = {k: st.session_state.get(k, []) for k in PERSIST}')
patch("atomik yazma",
      '        SAVE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")',
      '''        tmp = SAVE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(SAVE)''')
patch("dialogue_done yükle",
      "\n\ninitialise_state()\n",
      '''

initialise_state()
if "dialogue_done" not in st.session_state:
    st.session_state.dialogue_done = list(load().get("dialogue_done", []))
''')
patch("Sıfırlama",
      '''                st.session_state.round = {"n": 0, "score": 0}
                save()''',
      '''                st.session_state.round = {"n": 0, "score": 0}
                st.session_state.treasure_hunt = {"room": "Beach", "found": [], "opened": [], "complete": False, "xp_claimed": False, "xp_rooms": []}
                st.session_state.dialogue_done = []
                save()''')

# 7) Hazine Avı kelimeleri defterde olsun
patch("Yeni kelimeler",
      '    ("birthday", "doğum günü", "Today is my birthday.", B),',
      '''    ("birthday", "doğum günü", "Today is my birthday.", B),
    ("green", "yeşil", "The grass is green.", B),
    ("swim", "yüzmek", "I can swim in the lake.", B),
    ("key", "anahtar", "I lost my key.", B),''')

# 8) Bulut platformu düşme sınırı
patch("Platform düşme", "if(player.y>520){over=true;", "if(player.y>480){over=true;")

# 9) Macera quiz açıklaması
patch("Quiz açıklaması",
      'st.caption("Türkçe çeviri, soruyu cevapladıktan sonra açılır.")',
      'st.caption("Bu sahnenin Türkçesi gizli. Soruyu cevaplayınca kelimenin anlamını göreceksin.")')

# 10) Gerçekten günlük görevler
patch("mark_daily yardımcı",
      "def add_learned(en):",
      '''def mark_daily(task):
    """Günlük görev tamamlandı olarak işaretle (gün değişince sıfırlanır)."""
    d = st.session_state.daily
    if d.get("date") != today():
        st.session_state.daily = d = {"date": today(), "xp": 0}
    d.setdefault("done", [])
    if task not in d["done"]:
        d["done"].append(task)
        save()


def add_learned(en):''')
patch("mark word",
      "        st.session_state.learned.append(en)\n",
      '        st.session_state.learned.append(en)\n        mark_daily("word")\n')
patch("mark quiz", '                rd["n"] += 1\n',
      '                rd["n"] += 1\n                mark_daily("quiz")\n')
patch("mark speak",
      "st.session_state.speaking_history = st.session_state.speaking_history[-20:]\n                save()",
      'st.session_state.speaking_history = st.session_state.speaking_history[-20:]\n                mark_daily("speak")\n                save()')
patch("done_today",
      "    daily_xp = today_xp()\n    mission_items = [",
      '''    daily_xp = today_xp()
    done_today = st.session_state.daily.get("done", []) if st.session_state.daily.get("date") == today() else []
    mission_items = [''')
patch("görev 1", '("Bir kelimeyi defterine ekle", len(set(st.session_state.learned)) > 0,',
      '("Bir kelimeyi defterine ekle", "word" in done_today,')
patch("görev 2", '("Bir test sorusu çöz", st.session_state.round.get("n", 0) > 0,',
      '("Bir test sorusu çöz", "quiz" in done_today,')
patch("görev 3", '("Bir konuşma denemesi yap", len(st.session_state.speaking_history) > 0,',
      '("Bir konuşma denemesi yap", "speak" in done_today,')

src.write_text(text, encoding="utf-8")
print(f"Uygulandı: {len(ok)} yama")
if fail:
    print("Uygulanamayanlar (dosyan farklıysa elle bak):")
    for f in fail:
        print(" -", f)
print(f"Yedek: {src.with_suffix(src.suffix + '.bak')}")
