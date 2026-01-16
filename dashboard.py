import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Mestre dos Greens PRO", page_icon="⚽", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .metric-card {background-color: #1e2130; border: 1px solid #313547; padding: 20px; border-radius: 12px; text-align: center;}
    div[data-testid="stMetricValue"] { font-size: 20px; color: #00ff00; }
    </style>
""", unsafe_allow_html=True)

# --- DADOS ---
URLS_LIGAS = {
    "Argentina": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv",
    "Belgica": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Belgium_Pro_League_2016-2025.csv",
    "Brasileirao": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
    "Inglaterra": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
    "Franca": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/France_Ligue_1_2016-2025.csv",
    "Alemanha": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
    "Italia": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
    "Holanda": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
    "Portugal": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv",
    "Espanha": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
    "Turquia": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Turkey_S%C3%BCper_Lig_2016-2025.csv"
}
URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

@st.cache_data(ttl=3600)
def load_data():
    all_dfs = []
    for nome, url in URLS_LIGAS.items():
        try:
            r = requests.get(url)
            if r.status_code != 200: continue
            try: df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), low_memory=False)
            except: df = pd.read_csv(io.StringIO(r.content.decode('latin-1')), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            map_cols = {'homegoalcount': 'fthg', 'awaygoalcount': 'ftag', 'home_score': 'fthg', 'away_score': 'ftag',
                        'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
            df.rename(columns=map_cols, inplace=True)
            df.rename(columns={'date':'Date','home_name':'HomeTeam','away_name':'AwayTeam'}, inplace=True)
            
            for c in ['fthg','ftag','HTHG','HTAG','HC','AC']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                
            df.rename(columns={'fthg': 'FTHG', 'ftag': 'FTAG'}, inplace=True)
            
            df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
            df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            df['BTTS'] = ((df['FTHG'] > 0) & (df['FTAG'] > 0)).astype(int)
            df['League_Custom'] = nome
            
            if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','Over05HT','Over15FT','Over25FT','BTTS','HC','AC']])
        except: pass

    full_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    full_df['Date'] = pd.to_datetime(full_df['Date'], errors='coerce')
    df_recent = full_df.dropna()
    
    # Grade de Hoje
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns: df_today['HomeTeam'], df_today['AwayTeam'] = df_today.iloc[:, 0], df_today.iloc[:, 1]
        
        # Mapeamento de Odds (DOCX do Usuário)
        for c in ['odds_ft_1', 'odds_ft_x', 'odds_ft_2', 'odds_ft_over25', 'odds_btts_yes']:
            if c not in df_today.columns: df_today[c] = 0.0
            else: df_today[c] = pd.to_numeric(df_today[c], errors='coerce').fillna(0.0)
            
        df_today.drop_duplicates(subset=['HomeTeam', 'AwayTeam'], keep='first', inplace=True)
    except: df_today = pd.DataFrame()
    
    return df_recent, df_today

# --- IA ---
@st.cache_resource
def treinar_ia(df):
    team_stats = {}
    for team in pd.concat([df['HomeTeam'], df['AwayTeam']]).unique():
        games = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)]
        if len(games) < 3: continue
        team_stats[team] = (games['FTHG'].sum() + games['FTAG'].sum()) / len(games)
    model_data = []
    for idx, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        if h in team_stats and a in team_stats: model_data.append({'H': team_stats[h], 'A': team_stats[a], 'Target': row['Over25FT']})
    df_train = pd.DataFrame(model_data)
    if df_train.empty: return None, None
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(df_train[['H', 'A']], df_train['Target'])
    return model, team_stats

# --- APP LAYOUT ---
st.title("🧙‍♂️ Mestre dos Greens PRO - V29 Ultimate")
df_recent, df_today = load_data()

if not df_recent.empty:
    model, team_stats = treinar_ia(df_recent)
    
    tab1, tab2, tab3 = st.tabs(["🎯 Jogos de Hoje", "📊 Analisador de Times", "🌍 Raio-X Ligas"])
    
    # --- TAB 1: GRADE (Lógica V28/29) ---
    with tab1:
        st.subheader("Grade Inteligente")
        if not df_today.empty:
            lista = []
            for idx, row in df_today.iterrows():
                h, a = row['HomeTeam'], row['AwayTeam']
                sh = df_recent[df_recent['HomeTeam'] == h]; sa = df_recent[df_recent['AwayTeam'] == a]
                if len(sh) < 3: sh = df_recent[(df_recent['HomeTeam']==h)|(df_recent['AwayTeam']==h)]
                if len(sa) < 3: sa = df_recent[(df_recent['HomeTeam']==a)|(df_recent['AwayTeam']==a)]

                if len(sh)>=3 and len(sa)>=3:
                    p_ia = model.predict_proba([[team_stats.get(h,0), team_stats.get(a,0)]])[0][1]*100 if model and h in team_stats and a in team_stats else 0
                    p_25ft = (sh['Over25FT'].mean() + sa['Over25FT'].mean())/2*100
                    p_btts = (sh['BTTS'].mean() + sa['BTTS'].mean())/2*100
                    
                    lista.append({
                        "Liga": row.get('League','-'), 
                        "Jogo": f"{h} x {a}",
                        "Odd Casa": f"{row['odds_ft_1']:.2f}" if row['odds_ft_1'] > 1 else "-",
                        "IA (Over 2.5)": f"{p_ia:.1f}%",
                        "Stats BTTS": f"{p_btts:.0f}%",
                        "Score": p_ia
                    })
            
            st.dataframe(pd.DataFrame(lista).sort_values('Score', ascending=False), use_container_width=True)
        else: st.warning("Aguardando dados de hoje...")

    # --- TAB 2: ANALISADOR (Recuperado da V8) ---
    with tab2:
        st.subheader("🔎 Analisador de Times")
        times = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        sel_time = st.selectbox("Escolha um Time:", times)
        
        if sel_time:
            t_games = df_recent[(df_recent['HomeTeam'] == sel_time) | (df_recent['AwayTeam'] == sel_time)].sort_values('Date', ascending=False)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Média Gols Feitos", f"{((t_games[t_games['HomeTeam']==sel_time]['FTHG'].sum() + t_games[t_games['AwayTeam']==sel_time]['FTAG'].sum()) / len(t_games)):.2f}")
            col2.metric("Over 2.5 %", f"{(t_games['Over25FT'].mean()*100):.1f}%")
            col3.metric("BTTS %", f"{(t_games['BTTS'].mean()*100):.1f}%")
            col4.metric("Cantos Médios", f"{((t_games[t_games['HomeTeam']==sel_time]['HC'].sum() + t_games[t_games['AwayTeam']==sel_time]['AC'].sum()) / len(t_games)):.1f}")
            
            st.write("Últimos 5 Jogos:")
            st.dataframe(t_games[['Date','HomeTeam','AwayTeam','FTHG','FTAG']].head(5), hide_index=True)

    # --- TAB 3: RAIO-X LIGAS (Recuperado da V8) ---
    with tab3:
        st.subheader("🌍 Raio-X das Ligas")
        stats_league = df_recent.groupby('League_Custom')[['Over05HT','Over15FT','Over25FT','BTTS']].mean() * 100
        st.dataframe(stats_league.style.format("{:.1f}%").background_gradient(cmap='Greens'), use_container_width=True)

else: st.info("Carregando Banco de Dados...")
