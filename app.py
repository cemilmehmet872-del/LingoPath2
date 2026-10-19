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
