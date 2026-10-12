            st.session_state.round = {"n": 0, "score": 0}
            st.session_state.q = None
            st.rerun()
    else:
        if st.session_state.q is None:
            st.session_state.q = make_question()
        question = st.session_state.q
        word = question["word"]
        st.caption(f"Soru {round_data['n'] + 1} / 5")
        st.markdown(f"<div class='word'>{word['en']}</div>", unsafe_allow_html=True)
        pick = st.radio("Türkçesi nedir?", question["opts"], index=None,
                        key=f"pick_{question['id']}", disabled=question["done"])
        if not question["done"]:
            if st.button("Cevapla", type="primary", disabled=pick is None):
                question["done"] = True
                question["ok"] = pick == word["tr"]
                round_data["n"] += 1
                if question["ok"]:
                    round_data["score"] += 1
                    award(5)
                st.rerun()
        else:
            st.success("Doğru. +5 XP") if question["ok"] else st.error(f"Doğrusu: {word['tr']}")
            if st.button("Devam"):
                st.session_state.q = None
                st.rerun()

elif page == "Oyunlar":
    st.title("Oyunlar")
    game = st.radio("Oyun", ["Eşleştirme", "Cümle kurma"], horizontal=True, label_visibility="collapsed")
    if game == "Eşleştirme":
        st.caption("Beş kelimeyi doğru anlamlarıyla eşle.")
        if st.session_state.g is None:
            if st.button("Başla", type="primary"):
                words = random.sample(WORDS, 5)
                st.session_state.g = {"ws": words, "tr": random.sample([x["tr"] for x in words], 5),
                                      "id": new_nonce(), "res": None}
                st.rerun()
        else:
            game_data = st.session_state.g
            answers = {}
            for word in game_data["ws"]:
                a, b = st.columns([1, 2])
                a.markdown(f"<div class='sentence'>{word['en']}</div>", unsafe_allow_html=True)
                answers[word["en"]] = b.selectbox(word["en"], ["—"] + game_data["tr"],
                    key=f"m_{game_data['id']}_{word['en']}", label_visibility="collapsed",
                    disabled=game_data["res"] is not None)
            if game_data["res"] is None:
                if st.button("Kontrol et", type="primary"):
                    game_data["res"] = sum(answers[word["en"]] == word["tr"] for word in game_data["ws"])
                    award(game_data["res"] * 3)
                    st.rerun()
            else:
                st.success(f"5 eşleşmeden {game_data['res']} doğru. +{game_data['res'] * 3} XP")
                for word in game_data["ws"]:
                    st.write(f"{word['en']} → {word['tr']}")
                if st.button("Yeni oyun"):
                    st.session_state.g = None
                    st.rerun()
    else:
        st.caption("Karışık kelimelerden cümleyi kur.")
        if st.session_state.s is None:
            if st.button("Başla", type="primary"):
                sentence = random.choice(SENTENCES)
                words = sentence.rstrip(".?!").split()
                shuffled = words[:]
                while shuffled == words:
                    random.shuffle(shuffled)
                st.session_state.s = {"sent": sentence, "sh": shuffled, "id": new_nonce(), "ok": None}
                st.rerun()
        else:
            game_data = st.session_state.s
            st.markdown(f"<p class='sentence'>{' / '.join(game_data['sh'])}</p>", unsafe_allow_html=True)
            answer = st.text_input("Cümlen", key=f"s_{game_data['id']}", disabled=game_data["ok"] is not None)
            if game_data["ok"] is None:
                if st.button("Kontrol et", type="primary", disabled=not answer.strip()):
                    game_data["ok"] = norm(answer) == norm(game_data["sent"])
                    if game_data["ok"]:
                        award(10)
                    st.rerun()
            else:
                st.success("Doğru. +10 XP") if game_data["ok"] else st.error(f"Doğrusu: {game_data['sent']}")
                if st.button("Başka cümle"):
                    st.session_state.s = None
                    st.rerun()

elif page == "Defterim":
    st.title("Defterim")
    learned = sorted(set(st.session_state.learned))
    a, b, c = st.columns(3)
    a.metric("XP", st.session_state.xp)
    b.metric("Seviye", 1 + st.session_state.xp // 100)
    c.metric("Kelime", len(learned))
    st.caption(f"Sonraki seviyeye {100 - st.session_state.xp % 100} XP.")
    st.subheader("Öğrendiklerim")
    if learned:
        for english in learned:
            st.markdown(f"**{english}** — {BY_EN[english]['tr']}")
    else:
        st.info("Henüz kelime yok. Kelimeler bölümünden ilkini ekle.")
    st.subheader("Konuşma çalışmam")
    history = st.session_state.speaking_history
    if history:
        st.write(f"Kaydedilen son deneme sayısı: {len(history)}")
        average = round(sum(x["similarity"] for x in history) / len(history))
        st.metric("Son denemelerin ortalama metin benzerliği", f"%{average}")
        st.caption("Bu, metin benzerliğinin ortalamasıdır; fonetik telaffuz puanı değildir.")
    else:
        st.info("Konuşma denemelerin burada görünecek.")
    with st.expander("İlerlemeyi sıfırla"):
        st.warning("XP, öğrenilen kelimeler ve konuşma geçmişin bu oturumun kayıt dosyasından silinir.")
        if st.checkbox("Onaylıyorum", key="reset_confirm") and st.button("Sıfırla"):
            st.session_state.xp = 0
            st.session_state.learned = []
            st.session_state.spoken = []
            st.session_state.speaking_history = []
            save()
            st.rerun()
