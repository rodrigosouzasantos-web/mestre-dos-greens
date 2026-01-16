import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS PREMIUM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .metric-card {
        background: linear-gradient(145deg, #1e2130, #161924);
        border: 1px solid #313547;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    h1, h2, h3 { color: #00e676; }
    .stProgress > div > div > div > div { background-color: #00e676; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO TELEGRAM (SIDEBAR) ---
with st.sidebar.expander("📲 Configuração Telegram"):
    TELEGRAM_TOKEN = st.text_input("Bot Token", type="password")
    TELEGRAM_CHAT_ID = st.text_input("Chat ID")

def enviar_telegram(mensagem):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=data)
            return True
        except: return False
    return False

# --- BANCO DE DADOS ---
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
    with st.spinner("🔄 Conectando satélites e baixando dados..."):
        for nome, url in URLS_LIGAS.items():
            try:
                r = requests.get(url)
                if r.status_code != 200: continue
                try: df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), low_memory=False)
                except: df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), sep=';', low_memory=False)
                
                df.columns = [c.strip().lower() for c in df.columns]
                rename = {'date':'Date','date_unix':'DateUnix','home_name':'HomeTeam','away_name':'AwayTeam',
                          'fthg':'FTHG','ftag':'FTAG','homegoalcount':'FTHG','awaygoalcount':'FTAG',
                          'team_a_corners':'HC','team_b_corners':'AC','corners_home':'HC','corners_away':'AC',
                          'ht_goals_team_a':'HTHG','ht_goals_team_b':'HTAG'}
                df.rename(columns=rename, inplace=True)
                
                if 'Date' not in df.columns and 'DateUnix' in df.columns:
                    df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
                
                df['League_Custom'] = nome
                
                # Tratamento de Nulos
                cols_num = ['FTHG','FTAG','HTHG','HTAG','HC','AC']
                for c in cols_num:
                    if c not in df.columns: df[c] = 0
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

                # Cria colunas calculadas para o histórico
                df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
                df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
                df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int) # Alvo para IA
                
                cols = ['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','HC','AC','Over05HT','Over15FT','Over25FT']
                all_dfs.append(df[cols])
            except: pass
            
    if not all_dfs: return None, None
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy().dropna()
    
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns:
            df_today['HomeTeam'] = df_today.iloc[:, 0]
            df_today['AwayTeam'] = df_today.iloc[:, 1]
    except: df_today = pd.DataFrame()
    
    return df_recent, df_today

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
st.title("🤖 Mestre dos Greens PRO AI")
df_recent, df_today = load_data()

if df_recent is not None:
    # Treino silencioso
    model, team_stats = treinar_ia(df_recent)
    
    st.sidebar.markdown("## 🧭 Navegação")
    menu = st.sidebar.radio("", ["🎯 Jogos de Hoje (+ Tips)", "⚽ Analisador de Times", "🏆 Raio-X Ligas", "📡 Disparar Telegram"])

    # === MÓDULO 1: JOGOS DE HOJE + TIPS/IA ===
    if menu == "🎯 Jogos de Hoje (+ Tips)":
        st.header("🎯 Grade do Dia & Inteligência Artificial")
        if not df_today.empty and model:
            preds = []
            for idx, row in df_today.iterrows():
                h, a = row.get('HomeTeam', 'Casa'), row.get('AwayTeam', 'Fora')
                
                # Busca estatísticas
                stats_h = df_recent[df_recent['HomeTeam'] == h]
                stats_a = df_recent[df_recent['AwayTeam'] == a]
                if len(stats_h) < 3: stats_h = df_recent[df_recent['HomeTeam'].str.contains(h, case=False, na=False)]
                if len(stats_a) < 3: stats_a = df_recent[df_recent['AwayTeam'].str.contains(a, case=False, na=False)]

                if h in team_stats and a in team_stats and len(stats_h) >= 3 and len(stats_a) >= 3:
                    # IA: Probabilidade Over 2.5
                    prob_ia = model.predict_proba([[team_stats[h], team_stats[a]]])[0][1] * 100
                    fair_odd = 100 / prob_ia if prob_ia > 0 else 0
                    
                    # Estatísticas Históricas: Over 0.5 HT e 1.5 FT
                    prob_05ht = ((stats_h['Over05HT'].mean() + stats_a['Over05HT'].mean()) / 2) * 100
                    prob_15ft = ((stats_h['Over15FT'].mean() + stats_a['Over15FT'].mean()) / 2) * 100
                    
                    preds.append({
                        "Liga": row.get('League','-'), 
                        "Jogo": f"{h} x {a}",
                        "Over 2.5 (IA)": prob_ia, 
                        "Odd Justa": fair_odd,
                        "Over 0.5 HT": prob_05ht,
                        "Over 1.5 FT": prob_15ft
                    })
            
            if preds:
                df_p = pd.DataFrame(preds).sort_values("Over 2.5 (IA)", ascending=False)
                
                # Filtros
                col_f1, col_f2 = st.columns(2)
                min_prob = col_f1.slider("🤖 Mínimo Confiança IA (%)", 0, 100, 50)
                
                df_show = df_p[df_p['Over 2.5 (IA)'] >= min_prob]
                
                st.dataframe(df_show, column_config={
                    "Over 2.5 (IA)": st.column_config.ProgressColumn("Over 2.5 (IA)", format="%.1f%%", min_value=0, max_value=100),
                    "Over 0.5 HT": st.column_config.ProgressColumn("Gol 1º Tempo (HT)", format="%.1f%%", min_value=0, max_value=100),
                    "Over 1.5 FT": st.column_config.ProgressColumn("Over 1.5 (FT)", format="%.1f%%", min_value=0, max_value=100),
                    "Odd Justa": st.column_config.NumberColumn(format="%.2f")
                }, hide_index=True, use_container_width=True)
                
                st.info("💡 **Legenda:**\n- **Over 2.5 (IA):** Previsão do Robô baseada em Machine Learning.\n- **Gol 1º Tempo (HT):** Média histórica de jogos com gol no 1º tempo.\n- **Over 1.5 (FT):** Média histórica de jogos com pelo menos 2 gols.")
            else: st.warning("IA sem dados suficientes para os times de hoje.")
        else: st.info("Sem jogos hoje.")

    # === MÓDULO 2: ANALISADOR VISUAL ===
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
                c1.metric("Média Gols (Total)", f"{(df_all['FTHG']+df_all['FTAG']).mean():.2f}")
                c2.metric("Gols Feitos (Casa)", f"{df_home['FTHG'].mean() if not df_home.empty else 0:.2f}")
                c3.metric("Gols Feitos (Fora)", f"{df_away['FTAG'].mean() if not df_away.empty else 0:.2f}")
                
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

    # === MÓDULO 3: RAIO-X LIGAS ===
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
        with c1: st.plotly_chart(px.bar(stats, x='League_Custom', y='Média Gols', color='Over 2.5 (%)', title="Gols por Liga"), use_container_width=True)
        with c2: st.plotly_chart(px.bar(stats, x='League_Custom', y='Cantos', title="Cantos por Liga"), use_container_width=True)
        
        st.dataframe(stats, hide_index=True, use_container_width=True)

    # === MÓDULO 4: TELEGRAM ===
    elif menu == "📡 Disparar Telegram":
        st.header("📲 Enviar Sinal")
        with st.form("telegram"):
            msg = st.text_area("Mensagem:", height=150, value="🔥 *ALERTA GREEN*\n\n⚽ Jogo:\n📈 Entrada:\n💰 Odd:")
            if st.form_submit_button("Enviar"):
                if enviar_telegram(msg): st.success("Enviado!")
                else: st.error("Erro. Verifique token.")

else: st.error("Erro no banco de dados.")
