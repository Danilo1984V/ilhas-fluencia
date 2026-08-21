import streamlit as st
import speech_recognition as sr
from rapidfuzz import fuzz
from datetime import date, timedelta

# ============================================================
# CONFIGURAÇÃO E ESTADO DA SESSÃO (PERSISTÊNCIA TEMPORÁRIA)
# ============================================================
st.set_page_config(page_title="Ilhas de Fluência & Gamificação", page_icon="🔥", layout="wide")

# Inicializa variáveis do usuário na memória da sessão
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "streak" not in st.session_state:
    st.session_state.streak = 1
if "historico_dias" not in st.session_state:
    st.session_state.historico_dias = set([date.today()])
if "ilhas_concluidas" not in st.session_state:
    st.session_state.ilhas_concluidas = 0

# ============================================================
# BANCO DE DADOS DAS ILHAS DE FLUÊNCIA
# ============================================================
ilhas = {
    1: {
        "titulo": "Trabalho (Work)",
        "texto": "I work as a project coordinator for a tech company. My daily routine involves organizing meetings, replying to emails, and ensuring my team meets deadlines. I really enjoy solving problems and collaborating with my colleagues. It can be stressful sometimes, but seeing a project successfully completed is always rewarding."
    },
    2: {
        "titulo": "História do Passado (Past Story)",
        "texto": "A few years ago, I decided to travel alone to the mountains. On the second day, I got completely lost because my phone battery died. Luckily, I found a small coffee shop where a friendly local showed me the way back. It was scary at first, but it became an unforgettable adventure."
    },
    3: {
        "titulo": "Plano para o Futuro (Future Plan)",
        "texto": "In the next two years, I am planning to move to a bigger apartment closer to the city center. I also want to improve my English to apply for international jobs. To achieve this, I am saving money every month and practicing speaking every single day."
    },
    4: {
        "titulo": "Processo/Sequenciamento (How-To)",
        "texto": "To make a great cup of coffee, first, you need to boil fresh water. While it heats, grind your coffee beans to a medium size. Next, place a filter in your coffee maker and add the ground coffee. Finally, slowly pour the hot water over it and wait for it to brew. Now it is ready to enjoy!"
    },
    5: {
        "titulo": "Preferência e Comparação (Preferences)",
        "texto": "I definitely prefer working from home rather than working in a traditional office. When I stay at home, I save two hours of commuting time every day, which allows me to sleep more and exercise. Even though I miss chatting with coworkers face-to-face, the flexibility and extra free time are worth it."
    }
}

intervalos_srs = [1, 2, 4, 6, 8, 11, 14, 17, 22, 25, 29, 33, 37, 41, 45, 49]
espacamento_entrada = 2

def gerar_calendario():
    calendario = {}
    for id_ilha in ilhas.keys():
        dia_intro = 1 + (id_ilha - 1) * espacamento_entrada
        for intervalo in intervalos_srs:
            dia_rev = dia_intro + (intervalo - 1)
            calendario.setdefault(dia_rev, []).append(id_ilha)

    for dia in sorted(calendario.keys()):
        while len(calendario[dia]) > 2:
            excedente = calendario[dia].pop()
            prox = dia + 1
            while len(calendario.get(prox, [])) >= 2:
                prox += 1
            calendario.setdefault(prox, []).append(excedente)
    return calendario

# ============================================================
# INTERFACE GRÁFICA WEB COM GAMIFICAÇÃO
# ============================================================
st.title("🗣️ Ilhas de Fluência & Repetição Espaçada")

# Painel de Gamificação no Topo
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.metric(label="🔥 Ofensiva de Treino", value=f"{st.session_state.streak} dias")
with col_s2:
    st.metric(label="⚡ Pontos de Experiência (XP)", value=f"{st.session_state.xp} XP")
with col_s3:
    st.metric(label="🎯 Ilhas Concluídas", value=f"{st.session_state.ilhas_concluidas}")

st.markdown("---")

aba = st.sidebar.radio("Navegação", ["🎙️ Praticar Ilha", "📅 Esteira de Agendamento", "🏆 Conquistas"])
calendario = gerar_calendario()

# --- ABA 1: PRÁTICA ---
if aba == "🎙️ Praticar Ilha":
    st.header("Sessão de Prática")
    
    ilha_selecionada = st.selectbox(
        "Escolha qual Ilha deseja praticar:",
        options=list(ilhas.keys()),
        format_func=lambda x: f"Ilha {x} - {ilhas[x]['titulo']}"
    )

    dados = ilhas[ilha_selecionada]
    st.subheader(dados["titulo"])
    st.info(dados["texto"])

    if st.button("🎤 Iniciar Gravação de Voz"):
        reconhecedor = sr.Recognizer()
        with st.spinner("Escutando... Fale o texto em inglês!"):
            try:
                with sr.Microphone() as fonte:
                    reconhecedor.adjust_for_ambient_noise(fonte, duration=1)
                    audio = reconhecedor.listen(fonte, timeout=5, phrase_time_limit=15)
                    texto_falado = reconhecedor.recognize_google(audio, language="en-US")
                    
                    similaridade = fuzz.ratio(dados["texto"].lower(), texto_falado.lower())

                    st.success("Gravação enviada!")
                    st.write(f"**O app entendeu:** *\"{texto_falado}\"*")
                    st.metric(label="Precisão da Pronúncia", value=f"{similaridade:.1f}%")

                    # Lógica de Recompensa (Gamificação)
                    xp_ganho = int(similaridade * 1.5)
                    st.session_state.xp += xp_ganho
                    st.session_state.ilhas_concluidas += 1
                    
                    # Atualiza dias de treino
                    st.session_state.historico_dias.add(date.today())

                    st.write(f"🎉 **Você ganhou +{xp_ganho} XP!**")

                    if similaridade >= 80:
                        st.balloons()
                        st.success("Excelente! Ilha dominada.")
                    elif similaridade >= 60:
                        st.warning("Bom resultado! Treine mais uma vez para subir a nota.")
                    else:
                        st.error("Pratique novamente para melhorar a articulação.")

            except Exception as e:
                st.error(f"Erro no microfone ou no reconhecimento de voz: {e}")

# --- ABA 2: CALENDÁRIO ---
elif aba == "📅 Esteira de Agendamento":
    st.header("Esteira de Treino (Máximo 2 ilhas por dia)")
    col1, col2 = st.columns(2)
    dias_ordenados = sorted(calendario.keys())
    
    for i, dia in enumerate(dias_ordenados):
        ilhas_do_dia = calendario[dia]
        coluna_atual = col1 if i % 2 == 0 else col2
        with coluna_atual:
            with st.expander(f"📌 Dia {dia:02d} ({len(ilhas_do_dia)} ilha/s)"):
                for id_i in ilhas_do_dia:
                    st.write(f"• **Ilha {id_i}:** {ilhas[id_i]['titulo']}")

# --- ABA 3: CONQUISTAS ---
elif aba == "🏆 Conquistas":
    st.header("Suas Níveis e Medalhas")
    
    st.subheader("Suba de Nível:")
    if st.session_state.xp < 200:
        st.write("🥉 **Nível:** Iniciante B1")
        st.progress(st.session_state.xp / 200)
    elif st.session_state.xp < 500:
        st.write("🥈 **Nível:** Orador Intermediário")
        st.progress(st.session_state.xp / 500)
    else:
        st.write("🥇 **Nível:** Mestre das Ilhas")
        st.progress(1.0)

    st.markdown("---")
    st.subheader("Medalhas Desbloqueadas:")
    if st.session_state.ilhas_concluidas >= 1:
        st.success("🏅 **Primeiros Passos:** Concluiu a primeira ilha com sucesso.")
    if st.session_state.xp >= 300:
        st.success("🔥 **Acumulador de XP:** Alcançou mais de 300 pontos de experiência.")
    if st.session_state.ilhas_concluidas >= 10:
        st.success("⚡ **Dedicado:** Completou 10 treinos de pronúncia.")