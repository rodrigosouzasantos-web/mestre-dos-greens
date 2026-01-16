import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS (VISUAL V8) ---
st.markdown("""
    <style>
    .metric-card {background-color: #1e2130; border: 1px solid #313547; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);}
    .stProgress > div > div > div > div { background-color: #00ff00; }
    div[data-testid="stMetricValue"] { font-size: 22px; color: #00ff00; }
    div[data-testid="stMetricLabel"] { font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO TELEGRAM (AUTO-LOGIN) ---
# Tenta pegar dos Segredos (Secrets) do Streamlit
if "TELEGRAM_TOKEN" in st.secrets and "TELEGRAM_CHAT_ID" in st.secrets:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
    telegram_status = "✅ Conectado via Secrets"
else:
    # Se não tiver secrets, pede manual
    with st.sidebar.expander("📲 Configuração Telegram"):
        TELEGRAM_TOKEN = st.text_input("Bot Token", type="password")
        TELEGRAM_CHAT_ID = st.text_input("Chat ID")
    telegram_status = "⚠️ Aguardando Configuração"

def enviar_telegram(mensagem):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=data)
            return True
        except: return False
    return False

# --- BANCO DE DADOS (LINKS) ---
URLS_LIGAS = {
    "Argentina Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv",
    "Belgica Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Belgium_Pro_League_2016-2025.csv",
    "Brasileirao Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
    "Colombia Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Colombia_Primera_Liga_2016-2024.csv",
    "Croacia HNL": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Croatia_HNL_2016-2025.csv",
    "Dinamarca Superliga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Denmark_Superliga_2016-2025.csv",
    "Inglaterra Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
    "Finlandia Veikkausliiga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Finland_Veikkausliiga_2016-2024.csv",
    "Franca Ligue 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/France_Ligue_1_2016-2025.csv",
    "Alemanha Bundesliga 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
    "Alemanha Bundesliga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2_2016-2025.csv",
    "Grecia Super League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Greece_Super_League_2016-2025.csv",
    "Italia Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
    "Italia Serie B": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_B_2016-2025.csv",
    "Japao J1 League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Japan_J1_League_2016-2024.csv",
    "Portugal 2 Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/LigaPro_Portugal_2a_divisi%C3%B3n_2016-2025.csv",
    "Portugal Primeira Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv",
    "Mexico Liga MX": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Mexico_Liga_MX_2016-2025.csv",
    "Holanda Eredivisie": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
    "Noruega Eliteserien": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Norway_Eliteserien_2016-2024.csv",
    "Russia Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Russian_Premier_League_2016-2025.csv",
    "Arabia Saudita Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Saudi_Pro_League_2016-2025.csv",
    "Coreia do Sul K-League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/South_Korea_K_League_1_2016-2024.csv",
    "Espanha La Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
    "Espanha La Liga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_Segunda_Divisi%C3%B3n_2016-2025.csv",
    "Suecia Allsvenskan": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Sweden_Allsvenskan_2016-2024.csv",
    "Turquia Super Lig": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Turkey_S%C3%BCper_Lig_2016-2025.csv",
    "USA MLS": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/USA_Major_League_Soccer_2016-2024.csv",
    "Uruguai Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Uruguay_Primera_Divisi%C3%B3n_2016-2024.csv"
}

URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

# --- CARREGAMENTO ---
@st.cache_data(ttl=7200)
def load_data():
    all_dfs = []
    progress_text = "Carregando inteligência global..."
    my_bar = st.progress(0, text=progress_text)
    total_files = len(URLS_LIGAS)
    
    for i, (nome_amigavel, url) in enumerate(URLS_LIGAS.items()):
        try:
            response = requests.get(url)
            if response.status_code != 200: continue
            content = response.content.decode('utf-8')
            try: df = pd.read_csv(io.StringIO(content), low_memory=False)
            except: df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            rename_map = {
                'date': 'Date', 'date_unix': 'DateUnix', 'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'home': 'HomeTeam', 'away': 'AwayTeam',
                'fthg': 'FTHG', 'ftag': 'FTAG', 'homegoalcount': 'FTHG', 'awaygoalcount': 'FTAG',
                'team_a_corners': 'HC', 'team_b_corners': 'AC', 'corners_home': 'HC', 'corners_away': 'AC',
                'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG'
            }
            df.rename(columns=rename_map, inplace=True)
            if 'Date' not in df.columns:
                if 'DateUnix' in df.columns: df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
                else: continue
            
            df['League_Custom'] = nome_amigavel
            
            # Tratamento de Nulos
            cols_num = ['FTHG','FTAG','HTHG','HTAG','HC','AC']
            for c in cols_num:
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            # Colunas Calculadas
            df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
            df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)

            cols_needed = ['Date', 'League_Custom', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HTHG', 'HTAG', 'HC', 'AC', 'Over05HT', 'Over15FT', 'Over25FT']
            for c in cols_needed: 
                if c not in df.columns: df[c] = 0
            all_dfs.append(df[cols_needed])
        except Exception: pass
        my_bar.progress((i + 1) / total_files)
    
    my_bar.empty()
    if not all_dfs: return None, None
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy()
    
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        mapa_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
        df_today.rename(columns=mapa_today, inplace=True)
        if 'HomeTeam' not in df_today.columns:
             df_today['HomeTeam'] = df_today.iloc[:, 0]
             df_today['AwayTeam'] = df_today.iloc[:, 1]
    except: df_today = pd.DataFrame()
        
    return df_recent, df_today

# --- FUNÇÃO DE TIPS (V8) ---
def gerar_tip_visual(stats):
    tips = []
    if stats['Over25'] >= 70: tips.append("⚽ Over 2.5")
    elif stats['Over25'] <= 30: tips.append("🛡️ Under 2.5")
    if stats['BTTS'] >= 65: tips.append("🤝 BTTS")
    if stats['Cantos'] >= 10.5: tips.append("🚩 +10 Cantos")
    elif stats['Cantos'] <= 8.0: tips.append("📉 -9 Cantos")
    if not tips: return "⚠️ Sem Padrão Claro"
    return " | ".join(tips)

# --- IA ENGINE 🧠 ---
@st.cache_resource
def treinar_ia(df):
    team_stats = {}
    for team in pd.concat([df['HomeTeam'], df['AwayTeam']]).unique():
        games = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)]
        if len(games) < 5: continue
        avg_goals = (games['FTHG'].sum() + games['FTAG'].sum()) / len(games)
        team_stats[team] = avg_goals
        
    model_data = []
    for idx, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        if h in team_stats and a in team_stats:
            model_data.append({'H': team_stats[h], 'A': team_stats[a], 'Target': row['Over25FT']})
            
    df_train = pd.DataFrame(model_data)
    if df_train.empty: return None, None
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(df_train[['H', 'A']], df_train['Target'])
    return model, team_stats

# --- APP ---
st.title("🧙‍♂️ Mestre dos Greens PRO")

with st.spinner("Analisando dados globais..."):
    df_recent, df_today = load_data()

if df_recent is not None:
    # Treino IA (Silencioso)
    model, team_stats = treinar_ia(df_recent)

    st.sidebar.markdown(f"## 🧭 Navegação\nStatus: {telegram_status}")
    menu = st.sidebar.radio("", ["🎯 Jogos de Hoje (+ Tips)", "⚽ Analisador de Times", "🏆 Raio-X Ligas", "📡 Disparar Telegram"])
    
    # ----------------------------------------------------
    # MÓDULO 1: JOGOS DE HOJE + TIPS + IA
    # ----------------------------------------------------
    if menu == "🎯 Jogos de Hoje (+ Tips)":
        st.header("🎯 Grade do Dia & Tips da IA")
        if not df_today.empty:
            lista_final = []
            for idx, row in df_today.iterrows():
                h, a = row.get('HomeTeam', 'Casa'), row.get('AwayTeam', 'Fora')
                
                stats_h = df_recent[df_recent['HomeTeam'] == h]
                stats_a = df_recent[df_recent['AwayTeam'] == a]
                if len(stats_h) < 3: stats_h = df_recent[df_recent['HomeTeam'].str.contains(h, case=False, na=False)]
                if len(stats_a) < 3: stats_a = df_recent[df_recent['AwayTeam'].str.contains(a, case=False, na=False)]
                
                if len(stats_h) >= 3 and len(stats_a) >= 3:
                    over25 = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2 * 100
                    btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean()) / 2 * 100
                    cantos = ((stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean()) / 2
                    
                    prob_05ht = ((stats_h['Over05HT'].mean() + stats_a['Over05HT'].mean()) / 2) * 100
                    prob_15ft = ((stats_h['Over15FT'].mean() + stats_a['Over15FT'].mean()) / 2) * 100

                    prob_ia = 0
                    if model and h in team_stats and a in team_stats:
                        prob_ia = model.predict_proba([[team_stats[h], team_stats[a]]])[0][1] * 100

                    score = (over25*0.4) + (btts*0.3) + (min(cantos,12)/12*30)
                    tip_txt = gerar_tip_visual({'Over25': over25, 'BTTS': btts, 'Cantos': cantos})
                    
                    lista_final.append({
                        "Liga": row.get('League', '-'), "Hora": row.get('Time', '-'),
                        "Jogo": f"{h} x {a}", 
                        "Indicação (Tip)": tip_txt,
                        "Over 2.5 (IA)": prob_ia,
                        "Over 0.5 HT": prob_05ht,
                        "Over 1.5 FT": prob_15ft,
                        "BTTS": btts, 
                        "Cantos": cantos, 
                        "Score": score
                    })
            
            if lista_final:
                df_front = pd.DataFrame(lista_final).sort_values('Score', ascending=False)
                min_score = st.slider("⚖️ Filtrar Confiança (Score)", 0, 100, 50)
                df_show = df_front[df_front['Score'] >= min_score]
                
                st.dataframe(
                    df_show,
                    column_config={
                        "Score": st.column_config.ProgressColumn("Confiança", format="%.0f", min_value=0, max_value=100),
                        "Over 2.5 (IA)": st.column_config.ProgressColumn("Over 2.5 (IA)", format="%.1f%%", min_value=0, max_value=100),
                        "Over 0.5 HT": st.column_config.NumberColumn(format="%.1f%%"),
                        "Over 1.5 FT": st.column_config.NumberColumn(format="%.1f%%"),
                        "BTTS": st.column_config.NumberColumn(format="%.1f%%"),
                        "Cantos": st.column_config.NumberColumn(format="%.1f"),
                    }, hide_index=True, use_container_width=True
                )
            else: st.info("Jogos encontrados, mas sem histórico suficiente.")
        else: st.warning("Sem jogos na grade hoje.")

    # ----------------------------------------------------
    # MÓDULO 2: ANALISADOR VISUAL (V8)
    # ----------------------------------------------------
    elif menu == "⚽ Analisador de Times":
        st.header("🕵️‍♂️ Scout Detalhado")
        all_teams = sorted(list(set(df_recent['HomeTeam'].unique()) | set(df_recent['AwayTeam'].unique())))
        team = st.selectbox("🔍 Pesquise o Time:", all_teams, index=None, placeholder="Digite o nome...")
        
        if team:
            df_home = df_recent[df_recent['HomeTeam'] == team]
            df_away = df_recent[df_recent['AwayTeam'] == team]
            df_all = pd.concat([df_home, df_away]).sort_values('Date', ascending=False)
            if not df_all.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("Geral", f"{(df_all['FTHG']+df_all['FTAG']).mean():.2f} Gols")
                c2.metric("Casa", f"{df_home['FTHG'].mean() if not df_home.empty else 0:.2f} Gols")
                c3.metric("Fora", f"{df_away['FTAG'].mean() if not df_away.empty else 0:.2f} Gols")
                
                st.subheader("📈 Casa vs Fora")
                data_chart = pd.DataFrame({
                    'Situação': ['Casa', 'Casa', 'Fora', 'Fora'],
                    'Tipo': ['Gols Feitos', 'Gols Sofridos', 'Gols Feitos', 'Gols Sofridos'],
                    'Média': [df_home['FTHG'].mean() if not df_home.empty else 0, df_home['FTAG'].mean() if not df_home.empty else 0,
                              df_away['FTAG'].mean() if not df_away.empty else 0, df_away['FTHG'].mean() if not df_away.empty else 0]
                })
                fig = px.bar(data_chart, x='Situação', y='Média', color='Tipo', barmode='group', height=300)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_all.head(10), hide_index=True, use_container_width=True)

    # ----------------------------------------------------
    # MÓDULO 3: RAIO-X LIGAS (V8)
    # ----------------------------------------------------
    elif menu == "🏆 Raio-X Ligas":
        st.header("🌎 Estatísticas de Ligas")
        stats = df_recent.groupby('League_Custom').apply(lambda x: pd.Series({
            'Jogos': len(x), 'Média Gols': (x['FTHG']+x['FTAG']).mean(),
            'Over 2.5 (%)': ((x['FTHG']+x['FTAG'])>2.5).mean()*100,
            'BTTS (%)': ((x['FTHG']>0)&(x['FTAG']>0)).mean()*100,
            'Cantos': (x['HC']+x['AC']).mean()
        })).sort_values('Média Gols', ascending=False).reset_index()
        
        sel_ligas = st.multiselect("Filtrar Ligas:", sorted(stats['League_Custom'].unique()))
        if sel_ligas: stats = stats[stats['League_Custom'].isin(sel_ligas)]
        
        c1, c2 = st.tabs(["Gols", "Cantos"])
        with c1: st.plotly_chart(px.bar(stats, x='League_Custom', y='Média Gols', color='Over 2.5 (%)'), use_container_width=True)
        with c2: st.plotly_chart(px.bar(stats, x='League_Custom', y='Cantos'), use_container_width=True)
        st.dataframe(stats, hide_index=True, use_container_width=True)

    # ----------------------------------------------------
    # MÓDULO 4: TELEGRAM
    # ----------------------------------------------------
    elif menu == "📡 Disparar Telegram":
        st.header("📲 Enviar Sinal")
        with st.form("telegram"):
            msg = st.text_area("Mensagem:", height=150, value="🔥 *ALERTA GREEN*\n\n⚽ Jogo:\n📈 Entrada:\n💰 Odd:")
            if st.form_submit_button("Enviar"):
                if enviar_telegram(msg): st.success("Enviado!")
                else: st.error("Erro. Verifique token.")

else: st.error("Erro crítico ao carregar dados.")
