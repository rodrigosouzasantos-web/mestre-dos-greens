import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
from PIL import Image
import itertools
from datetime import datetime, timedelta

# --- CARREGA A LOGO ---
try:
    logo = Image.open("logo.jpg") 
    icon_page = logo
except:
    logo = None
    icon_page = "⚽"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO - V66.8 (Final + Timezone)",
    page_icon=icon_page,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS VISUAL (ESTILO PREMIUM DARK/GOLD) ---
st.markdown("""
    <style>
    /* Fundo Geral */
    .stApp { background-color: #0e1117; }
    
    /* Cards de Métricas */
    .metric-card {background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; text-align: center;}
    
    /* Textos de Métricas */
    div[data-testid="stMetricValue"] { font-size: 20px; color: #f1c40f; font-weight: 700; }
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #8b949e; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #010409; }
    
    /* Botões */
    div.stButton > button { 
        width: 100%; border-radius: 6px; font-weight: bold; 
        background-color: #f1c40f; color: #0d1117; border: none;
        transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #d4ac0d; color: #fff; }

    /* Lista de Placares */
    .placar-row {
        background-color: #1f2937;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 3px solid #f1c40f;
    }
    .placar-score { font-size: 16px; font-weight: bold; color: #fff; }
    .placar-prob { font-size: 14px; color: #f1c40f; font-weight: bold; }
    .placar-odd { font-size: 12px; color: #cfcfcf; }
    
    /* Estilo do Bilhete */
    .ticket-card {
        background-color: #1c232b;
        border: 2px solid #f1c40f;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 10px;
    }
    .ticket-header { color: #f1c40f; font-size: 22px; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px;}
    .ticket-item { font-size: 16px; color: #e6edf3; margin-bottom: 8px; border-left: 3px solid #2ea043; padding-left: 10px; }
    .ticket-total { font-size: 20px; color: #2ea043; font-weight: bold; margin-top: 15px; text-align: right; }
    
    /* Cards Analisador (Força) */
    .strength-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        text-align: center;
        margin-bottom: 10px;
    }
    .strength-title { color: #8b949e; font-size: 14px; margin-bottom: 5px; }
    .strength-value { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
    .strength-context { font-size: 12px; color: #cfcfcf; }
    
    /* Badge Must Win */
    .badge-must-win-title {
        background-color: #2ea043; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-left: 10px;
    }
    .badge-must-win-relegation {
        background-color: #da3633; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-left: 10px;
    }
    .rank-badge {
        font-weight: bold; color: #f1c40f;
    }
    
    /* Tabela Alavancagem */
    .alavancagem-table {
        font-size: 14px;
        color: #e6edf3;
        border-collapse: collapse;
        width: 100%;
    }
    .alavancagem-table th, .alavancagem-table td {
        border: 1px solid #30363d;
        padding: 8px;
        text-align: center;
    }
    .alavancagem-table th {
        background-color: #161b22;
        color: #f1c40f;
    }
    .winrate-green { color: #2ea043; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO TELEGRAM ---
if "TELEGRAM_TOKEN" in st.secrets:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
else:
    TELEGRAM_TOKEN = st.sidebar.text_input("Token Telegram", type="password")
    TELEGRAM_CHAT_ID = st.sidebar.text_input("Chat ID")

def enviar_telegram(msg):
    try: 
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        return True
    except: return False

def get_odd_justa(prob):
    if prob <= 1: return 0.00
    return 100 / prob

# ==============================================================================
# 1. BANCO DE DADOS
# ==============================================================================
URLS_HISTORICAS = {
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
    "Sweden Allsvenskan": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Sweden_Allsvenskan_2025.csv",
    "Turquia Super Lig": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Turkey_S%C3%BCper_Lig_2025-2026.csv",
    "USA MLS": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/USA_Major_League_Soccer_2025.csv",
    "Uruguay Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Uruguay_Primera_Divisi%C3%B3n_2025.csv"
}

URLS_ATUAIS = {
    "Argentina Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Argentina_Primera_Divisi%C3%B3n_2025.csv",
    "Belgica Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Belgium_Pro_League_2025-2026.csv",
    "Brasileirao Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2025-2026.csv",
    "Colombia Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Colombia_Primera_Liga_2025.csv",
    "Croacia HNL": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Croatia_HNL_2025-2026.csv",
    "Dinamarca Superliga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Denmark_Superliga_2025-2026.csv",
    "Inglaterra Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/England_Premier_League_2025-2026.csv",
    "Finlandia Veikkausliiga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Finland_Veikkausliiga_2025.csv",
    "Franca Ligue 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/France_Ligue_1_2025-2026.csv",
    "Alemanha Bundesliga 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Germany_Bundesliga_2025-2026.csv",
    "Alemanha Bundesliga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Germany_Bundesliga_2_2025-2026.csv",
    "Grecia Super League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Greece_Super_League_2025-2026.csv",
    "Italia Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Italy_Serie_A_2025-2026.csv",
    "Italia Serie B": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Italy_Serie_B_2025-2026.csv",
    "Japao J1 League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Japan_J1_League_2025.csv",
    "LigaPro_Portugal_2a_división_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/LigaPro_Portugal_2a_divisi%C3%B3n_2025-2026.csv",
    "Liga_Portugal_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Liga_Portugal_2025-2026.csv",
    "Mexico_Liga_MX_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Mexico_Liga_MX_2025-2026.csv",
    "Netherlands_Eredivisie_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Netherlands_Eredivisie_2025-2026.csv",
    "Norway_Eliteserien_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Norway_Eliteserien_2025.csv",
    "Russian_Premier_League_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Russian_Premier_League_2025-2026.csv",
    "Saudi_Pro_League_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Saudi_Pro_League_2025-2026.csv",
    "South_Korea_K_League_1_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/South_Korea_K_League_1_2025.csv",
    "Spain_La_Liga_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Spain_La_Liga_2025-2026.csv",
    "Spain_Segunda_División_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Spain_Segunda_Divisi%C3%B3n_2025-2026.csv",
    "Sweden Allsvenskan": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Sweden_Allsvenskan_2025.csv",
    "Turkey_Süper_Lig_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Turkey_S%C3%BCper_Lig_2025-2026.csv",
    "USA_Major_League_Soccer_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/USA_Major_League_Soccer_2025.csv",
    "Uruguay Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Uruguay_Primera_Divisi%C3%B3n_2025.csv"
}

URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

@st.cache_data(ttl=3600)
def load_data():
    all_dfs = []
    current_season_dfs = []
    
    # 1. Carrega Histórico
    progress_text = "Carregando bases..."
    my_bar = st.progress(0, text=progress_text)
    
    total_files = len(URLS_HISTORICAS) + len(URLS_ATUAIS)
    idx = 0

    for name, url in URLS_HISTORICAS.items():
        try:
            r = requests.get(url); df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
            df.columns = [c.strip().lower() for c in df.columns]
            map_cols = {'homegoalcount': 'fthg', 'awaygoalcount': 'ftag', 'home_score': 'fthg', 'away_score': 'ftag', 'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
            df.rename(columns=map_cols, inplace=True)
            if 'date' not in df.columns and 'date_unix' in df.columns: df['date'] = pd.to_datetime(df['date_unix'], unit='s')
            df.rename(columns={'date':'Date','home_name':'HomeTeam','away_name':'AwayTeam'}, inplace=True)
            for c in ['fthg','ftag','HTHG','HTAG','HC','AC']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            df.rename(columns={'fthg': 'FTHG', 'ftag': 'FTAG'}, inplace=True)
            df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
            df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            df['BTTS'] = ((df['FTHG'] > 0) & (df['FTAG'] > 0)).astype(int)
            df['HomeWin'] = (df['FTHG'] > df['FTAG']).astype(int)
            df['AwayWin'] = (df['FTAG'] > df['FTHG']).astype(int)
            df['League_Custom'] = name
            df['Season_Type'] = 'Historic'
            if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','Over05HT','Over15FT','Over25FT','BTTS','HomeWin','AwayWin','HC','AC','Season_Type']])
        except: pass
        idx+=1; my_bar.progress(idx/total_files)

    # 2. Carrega Atual (Com Tag de Season)
    for name, url in URLS_ATUAIS.items():
        try:
            r = requests.get(url); df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
            df.columns = [c.strip().lower() for c in df.columns]
            map_cols = {'homegoalcount': 'fthg', 'awaygoalcount': 'ftag', 'home_score': 'fthg', 'away_score': 'ftag', 'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
            df.rename(columns=map_cols, inplace=True)
            if 'date' not in df.columns and 'date_unix' in df.columns: df['date'] = pd.to_datetime(df['date_unix'], unit='s')
            df.rename(columns={'date':'Date','home_name':'HomeTeam','away_name':'AwayTeam'}, inplace=True)
            for c in ['fthg','ftag','HTHG','HTAG','HC','AC']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            df.rename(columns={'fthg': 'FTHG', 'ftag': 'FTAG'}, inplace=True)
            df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
            df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            df['BTTS'] = ((df['FTHG'] > 0) & (df['FTAG'] > 0)).astype(int)
            df['HomeWin'] = (df['FTHG'] > df['FTAG']).astype(int)
            df['AwayWin'] = (df['FTAG'] > df['FTHG']).astype(int)
            df['League_Custom'] = name
            df['Season_Type'] = 'Current' 
            clean_df = df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','Over05HT','Over15FT','Over25FT','BTTS','HomeWin','AwayWin','HC','AC','Season_Type']]
            if 'HomeTeam' in df.columns: 
                all_dfs.append(clean_df)
                current_season_dfs.append(clean_df)
        except: pass
        idx+=1; my_bar.progress(idx/total_files)

    my_bar.empty()
    full_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    full_df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last', inplace=True)
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy()
    
    # 3. Dataframe SÓ da Temporada Atual (Para Standings)
    df_current_season = pd.concat(current_season_dfs, ignore_index=True) if current_season_dfs else pd.DataFrame()
    
    # 4. Jogos de Hoje (COM O AJUSTE DE DATA/HORA AQUI)
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns: df_today['HomeTeam'], df_today['AwayTeam'] = df_today.iloc[:, 0], df_today.iloc[:, 1]
        
        # --- INÍCIO DO AJUSTE DE HORÁRIO ---
        if 'date_unix' in df_today.columns:
            df_today['match_time'] = pd.to_datetime(df_today['date_unix'], unit='s') - pd.Timedelta(hours=3)
        elif 'date' in df_today.columns:
            df_today['match_time'] = pd.to_datetime(df_today['date']) - pd.Timedelta(hours=3)
        else:
            df_today['match_time'] = datetime.now()
            
        df_today['Hora'] = df_today['match_time'].dt.strftime('%H:%M')
        df_today = df_today.sort_values('match_time')
        # --- FIM DO AJUSTE DE HORÁRIO ---

        cols_odds = ['odds_ft_1', 'odds_ft_x', 'odds_ft_2', 'odds_ft_over25', 'odds_btts_yes', 'odds_ft_over15', 'odds_1st_half_over05', 'odds_corners_over_95']
        for c in cols_odds:
            if c not in df_today.columns: df_today[c] = 0.0
            else: df_today[c] = pd.to_numeric(df_today[c], errors='coerce').fillna(0.0)
        df_today.drop_duplicates(subset=['HomeTeam', 'AwayTeam'], keep='first', inplace=True)
    except: df_today = pd.DataFrame()
    
    return df_recent, df_today, full_df, df_current_season

# ==============================================================================
# MOTOR DE CLASSIFICAÇÃO (CÁLCULO REAL)
# ==============================================================================
def calculate_standings(df_league_matches):
    if df_league_matches.empty: return pd.DataFrame()
    
    teams = {}
    # Itera sobre todos os jogos da liga na temporada atual
    for i, row in df_league_matches.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        hg, ag = row['FTHG'], row['FTAG']
        
        if h not in teams: teams[h] = {'P':0, 'W':0, 'D':0, 'L':0, 'GF':0, 'GA':0, 'Pts':0}
        if a not in teams: teams[a] = {'P':0, 'W':0, 'D':0, 'L':0, 'GF':0, 'GA':0, 'Pts':0}
        
        # Home Stats
        teams[h]['P'] += 1
        teams[h]['GF'] += hg
        teams[h]['GA'] += ag
        
        # Away Stats
        teams[a]['P'] += 1
        teams[a]['GF'] += ag
        teams[a]['GA'] += hg
        
        if hg > ag: # Home Win
            teams[h]['W'] += 1; teams[h]['Pts'] += 3
            teams[a]['L'] += 1
        elif ag > hg: # Away Win
            teams[a]['W'] += 1; teams[a]['Pts'] += 3
            teams[h]['L'] += 1
        else: # Draw
            teams[h]['D'] += 1; teams[h]['Pts'] += 1
            teams[a]['D'] += 1; teams[a]['Pts'] += 1
            
    # Convert to DF
    df_rank = pd.DataFrame.from_dict(teams, orient='index').reset_index()
    df_rank.rename(columns={'index':'Team'}, inplace=True)
    df_rank['GD'] = df_rank['GF'] - df_rank['GA']
    
    # Sort: Points -> GD -> GF
    df_rank = df_rank.sort_values(by=['Pts', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    df_rank.index += 1 # 1st place
    df_rank['Rank'] = df_rank.index
    
    return df_rank

# ==============================================================================
# CÁLCULOS PONDERADOS
# ==============================================================================
def get_weighted_avg(full_df, venue_df, col_name):
    w_geral = full_df[col_name].mean()
    w_venue = venue_df[col_name].mean() if not venue_df.empty else w_geral
    w_10 = full_df.tail(10)[col_name].mean()
    w_5 = full_df.tail(5)[col_name].mean()
    return (w_geral * 0.10) + (w_venue * 0.40) + (w_10 * 0.20) + (w_5 * 0.30)

def calcular_xg_ponderado(df_historico, league, team_home, team_away, col_home_goal='FTHG', col_away_goal='FTAG'):
    df_league = df_historico[df_historico['League_Custom'] == league]
    if df_league.empty: return None, None, None, None
    avg_goals_home = df_league[col_home_goal].mean()
    avg_goals_away = df_league[col_away_goal].mean()
    df_h_all = df_historico[(df_historico['HomeTeam'] == team_home) | (df_historico['AwayTeam'] == team_home)].sort_values('Date')
    df_a_all = df_historico[(df_historico['HomeTeam'] == team_away) | (df_historico['AwayTeam'] == team_away)].sort_values('Date')
    df_h = df_historico[df_historico['HomeTeam'] == team_home].sort_values('Date')
    df_a = df_historico[df_historico['AwayTeam'] == team_away].sort_values('Date')
    if len(df_h_all) < 5 or len(df_a_all) < 5: return None, None, None, None
    att_h_pond = get_weighted_avg(df_h_all, df_h, col_home_goal)
    strength_att_h = att_h_pond / avg_goals_home if avg_goals_home > 0 else 1.0
    def_a_pond = get_weighted_avg(df_a_all, df_a, col_home_goal)
    strength_def_a = def_a_pond / avg_goals_home if avg_goals_home > 0 else 1.0
    xg_home = strength_att_h * strength_def_a * avg_goals_home
    att_a_pond = get_weighted_avg(df_a_all, df_a, col_away_goal)
    strength_att_a = att_a_pond / avg_goals_away if avg_goals_away > 0 else 1.0
    def_h_pond = get_weighted_avg(df_h_all, df_h, col_away_goal)
    strength_def_h = def_h_pond / avg_goals_away if avg_goals_away > 0 else 1.0
    xg_away = strength_att_a * strength_def_h * avg_goals_away
    return xg_home, xg_away, strength_att_h, strength_att_a

def calcular_cantos_esperados_e_probs(df_historico, team_home, team_away):
    df_h = df_historico[df_historico['HomeTeam'] == team_home]
    df_a = df_historico[df_historico['AwayTeam'] == team_away]
    if df_h.empty or df_a.empty: return 0.0, {}
    media_pro_a = df_h['HC'].mean()
    media_contra_b = df_a['HC'].mean() 
    exp_cantos_a = (media_pro_a + media_contra_b) / 2
    media_pro_b = df_a['AC'].mean()
    media_contra_a = df_h['AC'].mean() 
    exp_cantos_b = (media_pro_b + media_contra_a) / 2
    total_exp = exp_cantos_a + exp_cantos_b
    probs = { "Over 8.5": poisson.sf(8, total_exp) * 100, "Over 9.5": poisson.sf(9, total_exp) * 100, "Over 10.5": poisson.sf(10, total_exp) * 100 }
    return total_exp, probs

def gerar_matriz_poisson(xg_home, xg_away):
    matrix = []
    top_scores = []
    probs_dict = {"HomeWin":0,"Draw":0,"AwayWin":0,"Over15":0,"Over25":0,"Under35":0,"BTTS":0}
    for h in range(6):
        row = []
        for a in range(6):
            prob = poisson.pmf(h, xg_home) * poisson.pmf(a, xg_away)
            row.append(prob * 100)
            top_scores.append({'Placar': f"{h}x{a}", 'Prob': prob*100})
            if h > a: probs_dict["HomeWin"] += prob
            elif h < a: probs_dict["AwayWin"] += prob
            else: probs_dict["Draw"] += prob
            total_goals = h + a
            if total_goals > 1.5: probs_dict["Over15"] += prob
            if total_goals > 2.5: probs_dict["Over25"] += prob
            if total_goals < 3.5: probs_dict["Under35"] += prob
            if h > 0 and a > 0: probs_dict["BTTS"] += prob
        matrix.append(row)
    top_scores = sorted(top_scores, key=lambda x: x['Prob'], reverse=True)[:5]
    return matrix, probs_dict, top_scores

def exibir_matriz_visual(matriz, home_name, away_name):
    fig = go.Figure(data=go.Heatmap(z=matriz, x=['0','1','2','3','4','5+'], y=['0','1','2','3','4','5+'], text=matriz, texttemplate="<b>%{z:.1f}%</b>", colorscale=[[0,'#161b22'],[1,'#f1c40f']], showscale=False))
    fig.update_layout(title="🎲 Placar Exato", xaxis=dict(side="top"), yaxis=dict(autorange='reversed'), height=400, margin=dict(t=50, l=50, r=50, b=50), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# APP PRINCIPAL
# ==============================================================================
st.title("🧙‍♂️ Mestre dos Greens PRO - V66.8 (Golden Master)")

df_recent, df_today, full_df, df_current_season = load_data()

if not df_recent.empty:
    if logo:
        st.sidebar.image(logo, use_container_width=True)
        st.sidebar.markdown("---")
    
    if st.sidebar.button("🔄 Forçar Atualização"):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.markdown("---")
        
    menu = st.sidebar.radio("Selecione:", ["🎯 Grade do Dia", "📊 Winrate & Assertividade", "🏆 Classificação", "⚔️ Simulador Manual", "🎫 Bilhetes Prontos", "🚀 Alavancagem", "🔎 Analisador de Times", "🌍 Raio-X Ligas"])
    
    # 1. GRADE DO DIA
    if menu == "🎯 Grade do Dia":
        st.header("🎯 Grade do Dia")
        if not df_today.empty:
            # --- AJUSTE NA EXIBIÇÃO DA LISTA ---
            jogos_hoje = [f"{row['Hora']} ⏰ {row['HomeTeam']} x {row['AwayTeam']}" for i, row in df_today.iterrows()]
            jogo_selecionado = st.selectbox("👉 Selecione um jogo:", jogos_hoje, index=0)
            
            # --- LIMPEZA DA STRING ---
            clean_selection = jogo_selecionado.split(" ⏰ ")[1]
            times = clean_selection.split(" x ")
            home_sel, away_sel = times[0], times[1]
            # --------------------------
            
            # INFO DE CLASSIFICAÇÃO (CÁLCULO DINÂMICO)
            try:
                liga_match = df_recent[df_recent['HomeTeam'] == home_sel]['League_Custom'].mode()[0]
                df_league_matches = df_current_season[df_current_season['League_Custom'] == liga_match]
                df_rank = calculate_standings(df_league_matches)
                
                h_info = df_rank[df_rank['Team'] == home_sel]
                a_info = df_rank[df_rank['Team'] == away_sel]
                
                h_rank = h_info.iloc[0]['Rank'] if not h_info.empty else "-"
                a_rank = a_info.iloc[0]['Rank'] if not a_info.empty else "-"
                
                home_rank_str = f"({h_rank}º)"
                away_rank_str = f"({a_rank}º)"
                
                must_win_msg = ""
                if h_rank != "-":
                    if int(h_rank) <= 3: must_win_msg = f"🔥 {home_sel}: Briga por Título!"
                    elif int(h_rank) >= len(df_rank) - 3: must_win_msg = f"💀 {home_sel}: Fuga do Z4!"
                if must_win_msg: st.warning(must_win_msg)
                
            except: 
                liga_match = None
                home_rank_str = ""
                away_rank_str = ""

            if liga_match:
                xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, liga_match, home_sel, away_sel, 'FTHG', 'FTAG')
                xg_h_ht, xg_a_ht, _, _ = calcular_xg_ponderado(df_recent, liga_match, home_sel, away_sel, 'HTHG', 'HTAG')
                exp_cantos, probs_cantos = calcular_cantos_esperados_e_probs(df_recent, home_sel, away_sel)
                if xg_h is not None:
                    st.divider()
                    st.markdown(f"### 📊 Raio-X: {home_sel} {home_rank_str} vs {away_sel} {away_rank_str}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("⚽ xG Esperado (FT)", f"{xg_h+xg_a:.2f}")
                    c2.metric("🚩 Cantos Esperados", f"{exp_cantos:.1f}")
                    c3.metric("xG Casa", f"{xg_h:.2f}")
                    c4.metric("xG Fora", f"{xg_a:.2f}")
                    matriz, probs, top_scores = gerar_matriz_poisson(xg_h, xg_a)
                    prob_00_ht = poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht)
                    prob_over05_ht = (1 - prob_00_ht) * 100
                    col_matriz, col_probs = st.columns([1.5, 1])
                    with col_matriz:
                        exibir_matriz_visual(matriz, home_sel, away_sel)
                        if st.button("📤 Enviar Análise", key="btn_send_grade"):
                            msg = f"🔥 *ANÁLISE* {home_sel} x {away_sel}\n🏆 Liga: {liga_match}\n📊 Over 2.5: {probs['Over25']*100:.1f}%\n"
                            if must_win_msg: msg += f"\n⚠️ *CONTEXTO:* {must_win_msg}"
                            enviar_telegram(msg)
                        if st.button("📋 Ver Top Placares", key="btn_grade"):
                            st.subheader("Placares Mais Prováveis")
                            for score in top_scores:
                                odd_j = get_odd_justa(score['Prob'])
                                st.markdown(f"""<div class="placar-row"><span class="placar-score">{score['Placar']}</span><span class="placar-prob">{score['Prob']:.1f}%</span><span class="placar-odd">@{odd_j:.2f}</span></div>""", unsafe_allow_html=True)
                    with col_probs:
                        st.subheader("📈 Probabilidades Reais")
                        def visual_metric(label, value, target):
                            yellow_threshold = target - 10
                            if value >= target: st.success(f"🟢 {label}: {value:.1f}%") 
                            elif value >= yellow_threshold: st.warning(f"🟡 {label}: {value:.1f}%") 
                            else: st.error(f"🔴 {label}: {value:.1f}%") 
                        visual_metric("Over 0.5 HT", prob_over05_ht, 80)
                        visual_metric("Over 1.5 FT", probs['Over15']*100, 80)
                        visual_metric("Over 2.5 FT", probs['Over25']*100, 60)
                        visual_metric("BTTS", probs['BTTS']*100, 60)
                        visual_metric("Under 3.5 FT", probs['Under35']*100, 80)
                        st.markdown("---")
                        st.write(f"🏠 **{home_sel}**: {probs['HomeWin']*100:.1f}%")
                        st.write(f"✈️ **{away_sel}**: {probs['AwayWin']*100:.1f}%")
                else: st.warning("Dados insuficientes.")
            else: st.warning("Liga não encontrada.")
        else: st.info("Aguardando jogos...")

    # 2. WINRATE (ATUALIZADO V66.5 - DETALHADO + CALENDÁRIO)
    elif menu == "📊 Winrate & Assertividade":
        st.header("📊 Assertividade do Robô (Backtest Detalhado)")
        
        # Encontra a última data com jogos na base (para evitar tela vazia)
        last_db_date = df_recent['Date'].max()
        yesterday = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
        
        # Se a base estiver atrasada, sugere a última data disponível
        default_date = yesterday if yesterday <= last_db_date else last_db_date
        
        col_date, _ = st.columns([1, 3])
        with col_date:
            selected_date = st.date_input("Selecione a Data para Análise:", value=default_date)
        
        tab_dia, tab_mes = st.tabs([f"📅 Resultados do Dia ({selected_date.strftime('%d/%m')})", "🗓️ Acumulado do Mês"])
        
        def calculate_winrate(start, end):
            # Filtra jogos do período
            mask = (df_recent['Date'] >= pd.Timestamp(start)) & (df_recent['Date'] <= pd.Timestamp(end) + pd.Timedelta(hours=23, minutes=59))
            games = df_recent.loc[mask]
            
            if games.empty:
                st.warning(f"Sem jogos finalizados na base de dados para o período selecionado.")
                return

            market_stats = {
                'Over 0.5 HT': {'total':0, 'green':0}, 
                'Over 1.5 FT': {'total':0, 'green':0},
                'Over 2.5 FT': {'total':0, 'green':0}, 
                'BTTS': {'total':0, 'green':0},
                'Under 3.5 FT': {'total':0, 'green':0}
            }
            results = []
            
            # Barra de progresso visual
            prog_bar = st.progress(0); step = 1/len(games) if len(games)>0 else 1
            
            for i, row in games.iterrows():
                prog_bar.progress(min((i+1)*step, 1.0))
                h, a, l = row['HomeTeam'], row['AwayTeam'], row['League_Custom']
                
                xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, l, h, a)
                if xg_h is None: continue
                xg_h_ht, xg_a_ht, _, _ = calcular_xg_ponderado(df_recent, l, h, a, 'HTHG', 'HTAG')
                
                _, probs, _ = gerar_matriz_poisson(xg_h, xg_a)
                prob_ht = (1 - (poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht))) 

                # Lógica de Green/Red
                # 1. Over 0.5 HT (>= 80%)
                if prob_ht >= 0.80:
                    market_stats['Over 0.5 HT']['total'] += 1
                    if (row['HTHG'] + row['HTAG']) > 0: 
                        market_stats['Over 0.5 HT']['green'] += 1; res="✅"
                    else: res="🔻"
                    results.append({'Jogo':f"{h} x {a}", 'Mercado':'Over 0.5 HT', 'Resultado':res})

                # 2. Over 1.5 FT (>= 80%)
                if probs['Over15'] >= 0.80:
                    market_stats['Over 1.5 FT']['total'] += 1
                    if (row['FTHG'] + row['FTAG']) > 1.5: 
                        market_stats['Over 1.5 FT']['green'] += 1; res="✅"
                    else: res="🔻"
                    results.append({'Jogo':f"{h} x {a}", 'Mercado':'Over 1.5 FT', 'Resultado':res})

                # 3. Over 2.5 FT (> 60%)
                if probs['Over25'] >= 0.60:
                    market_stats['Over 2.5 FT']['total'] += 1
                    if (row['FTHG'] + row['FTAG']) > 2.5: 
                        market_stats['Over 2.5 FT']['green'] += 1; res="✅"
                    else: res="🔻"
                    results.append({'Jogo':f"{h} x {a}", 'Mercado':'Over 2.5 FT', 'Resultado':res})

                # 4. BTTS (> 60%)
                if probs['BTTS'] >= 0.60:
                    market_stats['BTTS']['total'] += 1
                    if (row['FTHG'] > 0 and row['FTAG'] > 0): 
                        market_stats['BTTS']['green'] += 1; res="✅"
                    else: res="🔻"
                    results.append({'Jogo':f"{h} x {a}", 'Mercado':'BTTS', 'Resultado':res})

                # 5. Under 3.5 FT (> 80%)
                if probs['Under35'] >= 0.80:
                    market_stats['Under 3.5 FT']['total'] += 1
                    if (row['FTHG'] + row['FTAG']) < 3.5: 
                        market_stats['Under 3.5 FT']['green'] += 1; res="✅"
                    else: res="🔻"
                    results.append({'Jogo':f"{h} x {a}", 'Mercado':'Under 3.5 FT', 'Resultado':res})

            prog_bar.empty()
            
            # Exibição dos Cards
            total_entradas = sum([d['total'] for d in market_stats.values()])
            total_greens = sum([d['green'] for d in market_stats.values()])
            
            if total_entradas > 0:
                wr_geral = (total_greens / total_entradas) * 100
                st.markdown("### 📈 Performance Global")
                c1, c2, c3 = st.columns(3)
                c1.metric("Entradas", total_entradas)
                c2.metric("Greens", total_greens)
                c3.metric("Winrate", f"{wr_geral:.1f}%")
                
                st.divider()
                st.markdown("### 🎯 Por Mercado")
                cols = st.columns(5)
                i=0
                for m, d in market_stats.items():
                    with cols[i]:
                        t = d['total']; g = d['green']
                        wr = (g/t*100) if t>0 else 0
                        color = "#2ea043" if wr >= 70 else "#f1c40f" if wr >= 50 else "#da3633"
                        st.markdown(f"""<div class="metric-card"><div style="color:#8b949e">{m}</div><div style="font-size:22px;font-weight:bold;color:{color}">{wr:.1f}%</div><div style="font-size:12px">{g}/{t}</div></div>""", unsafe_allow_html=True)
                    i+=1
                
                with st.expander("📝 Detalhes dos Jogos"):
                    st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("Nenhuma oportunidade encontrada para os critérios neste período.")

        with tab_dia:
            calculate_winrate(selected_date, selected_date)
            
        with tab_mes:
            first_day = selected_date.replace(day=1)
            calculate_winrate(first_day, selected_date)

    # 3. CLASSIFICAÇÃO
    elif menu == "🏆 Classificação":
        st.header("🏆 Classificação (Standings 2025/26)")
        if not df_current_season.empty:
            leagues_avail = sorted(df_current_season['League_Custom'].unique())
            sel_league = st.selectbox("Selecione a Liga:", leagues_avail)
            
            # FILTRA JOGOS DA LIGA ATUAL
            df_league_matches = df_current_season[df_current_season['League_Custom'] == sel_league]
            
            # CALCULA TABELA
            df_rank = calculate_standings(df_league_matches)
            
            if not df_rank.empty:
                st.markdown(f"### Tabela: {sel_league}")
                def color_standings(row):
                    rank = row['Rank']
                    if rank <= 4: return ['background-color: #1e3a8a; color: white'] * len(row) # Azul (Top)
                    elif rank >= len(df_rank) - 3: return ['background-color: #7f1d1d; color: white'] * len(row) # Vermelho (Z3)
                    else: return [''] * len(row)

                # Colunas para exibir
                cols_show = ['Rank', 'Team', 'P', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']
                st.dataframe(df_rank[cols_show].style.apply(color_standings, axis=1), use_container_width=True)
            else:
                st.warning("Nenhum jogo encontrado para esta liga nesta temporada.")
        else:
            st.warning("Base de dados da temporada atual vazia.")

    # 4. SIMULADOR MANUAL
    elif menu == "⚔️ Simulador Manual":
        st.header("⚔️ Simulador Manual")
        all_teams = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        c1, c2 = st.columns(2)
        team_a = c1.selectbox("Casa:", all_teams, index=None)
        team_b = c2.selectbox("Visitante:", all_teams, index=None)
        if team_a and team_b:
            try: liga_sim = df_recent[df_recent['HomeTeam'] == team_a]['League_Custom'].mode()[0]
            except: liga_sim = None
            if liga_sim:
                xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, liga_sim, team_a, team_b, 'FTHG', 'FTAG')
                xg_h_ht, xg_a_ht, _, _ = calcular_xg_ponderado(df_recent, liga_sim, team_a, team_b, 'HTHG', 'HTAG')
                exp_cantos, probs_cantos = calcular_cantos_esperados_e_probs(df_recent, team_a, team_b)
                if xg_h:
                    st.success(f"Liga Base: {liga_sim}")
                    matriz, probs, top_scores = gerar_matriz_poisson(xg_h, xg_a)
                    prob_over05_ht = (1 - (poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht))) * 100
                    exibir_matriz_visual(matriz, team_a, team_b)
                    
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("📤 Enviar para Telegram", key="btn_send_sim"):
                            msg = f"🔥 *SIMULAÇÃO* {team_a} x {team_b}\n📊 Over 2.5: {probs['Over25']*100:.1f}%"
                            if enviar_telegram(msg): st.success("Enviado!")
                    with c_btn2:
                        if st.button("📋 Ver Top Placares", key="btn_sim"):
                            for score in top_scores:
                                odd_j = get_odd_justa(score['Prob'])
                                st.markdown(f"""<div class="placar-row"><span class="placar-score">{score['Placar']}</span><span class="placar-prob">{score['Prob']:.1f}%</span><span class="placar-odd">@{odd_j:.2f}</span></div>""", unsafe_allow_html=True)
                    st.divider()
                    st.subheader("📊 Probabilidades de Resultado (1x2)")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("🏠 Vitória Casa", f"{probs['HomeWin']*100:.1f}%")
                    m2.metric("⚖️ Empate", f"{probs['Draw']*100:.1f}%")
                    m3.metric("✈️ Vitória Visitante", f"{probs['AwayWin']*100:.1f}%")
                    st.divider()
                    st.subheader("⚽ Probabilidades de Gols")
                    g1, g2, g3, g4 = st.columns(4)
                    g1.metric("⚡ Over 0.5 HT", f"{prob_over05_ht:.1f}%")
                    g2.metric("🛡️ Over 1.5 FT", f"{probs['Over15']*100:.1f}%")
                    g3.metric("🔥 Over 2.5 FT", f"{probs['Over25']*100:.1f}%")
                    g4.metric("🧱 Under 3.5 FT", f"{probs['Under35']*100:.1f}%")
                    st.divider()
                    st.subheader("🚩 Probabilidades de Escanteios")
                    c1, c2 = st.columns(2)
                    c1.metric("Cantos (Média Esp.)", f"{exp_cantos:.1f}")
                    c2.metric("Over 9.5 Cantos", f"{probs_cantos['Over 9.5']:.1f}%")

    # 5. BILHETES PRONTOS
    elif menu == "🎫 Bilhetes Prontos":
        st.header("🎫 Bilhetes Prontos (Segurança de Green)")
        if df_today.empty:
            st.info("Nenhum jogo disponível hoje para gerar bilhetes.")
        else:
            if st.button("🔄 Gerar Novos Bilhetes"):
                with st.spinner("Analisando todos os jogos e calculando probabilidades..."):
                    all_candidates = [] 
                    for i, row in df_today.iterrows():
                        home = row['HomeTeam']
                        away = row['AwayTeam']
                        try:
                            league = df_recent[df_recent['HomeTeam'] == home]['League_Custom'].mode()[0]
                            xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, league, home, away, 'FTHG', 'FTAG')
                            if xg_h is None: continue
                            _, probs_dict, _ = gerar_matriz_poisson(xg_h, xg_a)
                            
                            if probs_dict['Over15'] > 0.75:
                                all_candidates.append({'Jogo': f"{home} x {away}", 'Tipo': 'Over 1.5 Gols', 'Odd_Est': 1/probs_dict['Over15']})
                            if probs_dict['Under35'] > 0.80:
                                all_candidates.append({'Jogo': f"{home} x {away}", 'Tipo': 'Under 3.5 Gols', 'Odd_Est': 1/probs_dict['Under35']})
                            if probs_dict['Under35'] > 0.90: 
                                all_candidates.append({'Jogo': f"{home} x {away}", 'Tipo': 'Under 4.5 Gols', 'Odd_Est': 1.08})
                            prob_1x = probs_dict['HomeWin'] + probs_dict['Draw']
                            if prob_1x > 0.80:
                                all_candidates.append({'Jogo': f"{home} x {away}", 'Tipo': 'Casa ou Empate (1X)', 'Odd_Est': 1/prob_1x})
                            prob_x2 = probs_dict['AwayWin'] + probs_dict['Draw']
                            if prob_x2 > 0.80:
                                all_candidates.append({'Jogo': f"{home} x {away}", 'Tipo': 'Fora ou Empate (X2)', 'Odd_Est': 1/prob_x2})
                        except: continue
                    
                    found_dupla = False
                    for pair in itertools.combinations(all_candidates, 2):
                        odd_total = pair[0]['Odd_Est'] * pair[1]['Odd_Est']
                        if 1.45 <= odd_total <= 1.60:
                            st.markdown(f"""<div class="ticket-card"><div class="ticket-header">🎫 DUPLA SEGURA (Odd Total ~{odd_total:.2f})</div><div class="ticket-item">⚽ {pair[0]['Jogo']} <br> 🎯 {pair[0]['Tipo']} (@{pair[0]['Odd_Est']:.2f})</div><div class="ticket-item">⚽ {pair[1]['Jogo']} <br> 🎯 {pair[1]['Tipo']} (@{pair[1]['Odd_Est']:.2f})</div></div>""", unsafe_allow_html=True)
                            msg_dupla = f"🔥 *DUPLA SEGURA* 🔥\n🎯 Odd: ~{odd_total:.2f}\n1️⃣ {pair[0]['Jogo']} - {pair[0]['Tipo']}\n2️⃣ {pair[1]['Jogo']} - {pair[1]['Tipo']}"
                            if st.button("📤 Enviar Dupla", key="btn_dupla"): enviar_telegram(msg_dupla)
                            found_dupla = True
                            break 
                    if not found_dupla: st.warning("Nenhuma Dupla ideal encontrada.")

                    found_tripla = False
                    for trio in itertools.combinations(all_candidates, 3):
                        odd_total = trio[0]['Odd_Est'] * trio[1]['Odd_Est'] * trio[2]['Odd_Est']
                        if 1.65 <= odd_total <= 1.85:
                            st.markdown(f"""<div class="ticket-card"><div class="ticket-header">🎫 TRIPLA DE VALOR (Odd Total ~{odd_total:.2f})</div><div class="ticket-item">⚽ {trio[0]['Jogo']} <br> 🎯 {trio[0]['Tipo']} (@{trio[0]['Odd_Est']:.2f})</div><div class="ticket-item">⚽ {trio[1]['Jogo']} <br> 🎯 {trio[1]['Tipo']} (@{trio[1]['Odd_Est']:.2f})</div><div class="ticket-item">⚽ {trio[2]['Jogo']} <br> 🎯 {trio[2]['Tipo']} (@{trio[2]['Odd_Est']:.2f})</div></div>""", unsafe_allow_html=True)
                            msg_tripla = f"🚀 *TRIPLA DE VALOR* 🚀\n🎯 Odd: ~{odd_total:.2f}\n1️⃣ {trio[0]['Jogo']} - {trio[0]['Tipo']}\n2️⃣ {trio[1]['Jogo']} - {trio[1]['Tipo']}\n3️⃣ {trio[2]['Jogo']} - {trio[2]['Tipo']}"
                            if st.button("📤 Enviar Tripla", key="btn_tripla"): enviar_telegram(msg_tripla)
                            found_tripla = True
                            break
                    if not found_tripla: st.warning("Nenhuma Tripla ideal encontrada.")

    # 6. ALAVANCAGEM (NOVA VERSÃO - V66.6 - CICLOS)
    elif menu == "🚀 Alavancagem":
        st.header("🚀 Alavancagem Pro (Gestão de Ciclos)")
        st.markdown("""
        <div class="metric-card" style="text-align: left;">
            <h3 style="color: #f1c40f; margin-top: 0;">💎 Modelo de Alavancagem com Proteção</h3>
            <p style="font-size: 14px; color: #cfcfcf;">
            Estrutura de <b>5 Ciclos</b> com <b>2 Jogos por Ciclo</b> (Total: 10 Jogos).<br>
            Objetivo: Dobrar a stake do ciclo com lucro protegido (saques parciais).
            </p>
            <table class="alavancagem-table">
                <tr><th>Ciclo</th><th>Início (R$)</th><th>Meta (R$)</th><th>Saque (R$)</th><th>Próx. Ciclo (R$)</th></tr>
                <tr><td>1</td><td>50</td><td>100</td><td><span class="winrate-green">50</span> (Recupera)</td><td>50</td></tr>
                <tr><td>2</td><td>50</td><td>100</td><td><span class="winrate-green">25</span> (Lucro)</td><td>75</td></tr>
                <tr><td>3</td><td>75</td><td>150</td><td><span class="winrate-green">50</span> (Lucro)</td><td>100</td></tr>
                <tr><td>4</td><td>100</td><td>200</td><td><span class="winrate-green">50</span> (Lucro)</td><td>150</td></tr>
                <tr><td>5</td><td>150</td><td>300</td><td><span class="winrate-green">300</span> (Final)</td><td>---</td></tr>
            </table>
            <br>
            <b>Regra do Jogo:</b><br>
            • <b>Passo 1:</b> Jogo com Odd média <b>@1.50</b> (Over 1.5, BTTS, Win)<br>
            • <b>Passo 2:</b> Jogo com Odd média <b>@1.34</b> (Double Chance, Over 1.5, Under 3.5)<br>
            <i>O lucro do 1º jogo é reinvestido no 2º jogo para bater a dobra.</i>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        if st.button("🔄 Gerar Ciclo do Dia"):
            with st.spinner("Analisando Grade do Dia para encontrar a Combinação Perfeita..."):
                step1_candidates = []
                step2_candidates = []
                
                for i, row in df_today.iterrows():
                    h, a = row['HomeTeam'], row['AwayTeam']
                    # Busca Liga (mesma lógica da Grade)
                    try: l = df_recent[df_recent['HomeTeam'] == h]['League_Custom'].mode()[0]
                    except: 
                        if h in df_recent['HomeTeam'].unique(): l = df_recent[df_recent['HomeTeam'] == h].iloc[-1]['League_Custom']
                        else: continue
                    
                    xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, l, h, a)
                    if xg_h is None: continue
                    _, probs, _ = gerar_matriz_poisson(xg_h, xg_a)
                    
                    # --- FILTRO PASSO 1 (ODD ~1.50) ---
                    # Over 1.5 (65-75%), BTTS (60-70%), Win (60-70%)
                    if 0.65 <= probs['Over15'] <= 0.85:
                        odd = 1/probs['Over15']
                        if 1.40 <= odd <= 1.60:
                            step1_candidates.append({'Jogo': f"{h} x {a}", 'M': 'Over 1.5 Gols', 'Odd': odd, 'Prob': probs['Over15']})
                    
                    if 0.60 <= probs['BTTS'] <= 0.75:
                        odd = 1/probs['BTTS']
                        if 1.45 <= odd <= 1.65:
                            step1_candidates.append({'Jogo': f"{h} x {a}", 'M': 'Ambas Marcam', 'Odd': odd, 'Prob': probs['BTTS']})

                    # --- FILTRO PASSO 2 (ODD ~1.34) ---
                    # Over 1.5 (>75%), Under 3.5 (>75%), DC (>75%)
                    if probs['Over15'] > 0.75:
                        odd = 1/probs['Over15']
                        if 1.25 <= odd <= 1.42:
                            step2_candidates.append({'Jogo': f"{h} x {a}", 'M': 'Over 1.5 Gols', 'Odd': odd, 'Prob': probs['Over15']})
                            
                    if probs['Under35'] > 0.75:
                        odd = 1/probs['Under35']
                        if 1.25 <= odd <= 1.42:
                            step2_candidates.append({'Jogo': f"{h} x {a}", 'M': 'Under 3.5 Gols', 'Odd': odd, 'Prob': probs['Under35']})
                            
                    prob_1x = probs['HomeWin'] + probs['Draw']
                    if prob_1x > 0.75:
                        odd = 1/prob_1x
                        if 1.20 <= odd <= 1.40:
                             step2_candidates.append({'Jogo': f"{h} x {a}", 'M': 'Casa ou Empate', 'Odd': odd, 'Prob': prob_1x})

                # --- GERAR COMBINAÇÃO ---
                step1_candidates.sort(key=lambda x: x['Prob'], reverse=True)
                step2_candidates.sort(key=lambda x: x['Prob'], reverse=True)
                
                if step1_candidates and step2_candidates:
                    s1 = step1_candidates[0]
                    s2 = step2_candidates[0]
                    if s1['Jogo'] == s2['Jogo'] and len(step2_candidates) > 1: s2 = step2_candidates[1]
                    
                    st.success("✅ Ciclo Encontrado! (Siga a gestão)")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"""<div class="ticket-card"><div class="ticket-header">1️⃣ PASSO 1 (Stake Inicial)</div><div class="ticket-item">⚽ {s1['Jogo']}</div><div class="ticket-item">🎯 {s1['M']}</div><div class="ticket-total">Odd Justa: @{s1['Odd']:.2f}</div></div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div class="ticket-card" style="border-color: #2ea043;"><div class="ticket-header" style="color: #2ea043;">2️⃣ PASSO 2 (All-in Lucro)</div><div class="ticket-item">⚽ {s2['Jogo']}</div><div class="ticket-item">🎯 {s2['M']}</div><div class="ticket-total" style="color: #2ea043;">Odd Justa: @{s2['Odd']:.2f}</div></div>""", unsafe_allow_html=True)
                    
                    if st.button("📤 Enviar Ciclo para Telegram"):
                        msg = f"🚀 *CICLO DE ALAVANCAGEM* 🚀\n\n1️⃣ *PASSO 1* (Odd ~1.50)\n⚽ {s1['Jogo']}\n🎯 {s1['M']}\n\n2️⃣ *PASSO 2* (Odd ~1.34)\n⚽ {s2['Jogo']}\n🎯 {s2['M']}\n\n🍀 *Objetivo:* Dobrar a Stake do Ciclo!"
                        if enviar_telegram(msg): st.success("Enviado!")
                else:
                    st.warning("Não foram encontrados jogos com as probabilidades exatas para formar o ciclo hoje.")

    # 7. ANALISADOR DE TIMES
    elif menu == "🔎 Analisador de Times":
        st.header("🔎 Scout Profundo (Visual)")
        all_teams_db = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        sel_time = st.selectbox("Pesquise o time:", all_teams_db, index=None)
        if sel_time:
            # INFO EXTRA DA NOVA BASE
            try:
                liga_match = df_recent[df_recent['HomeTeam'] == sel_time]['League_Custom'].mode()[0]
                df_league_matches = df_current_season[df_current_season['League_Custom'] == liga_match]
                df_rank = calculate_standings(df_league_matches)
                team_info = df_rank[df_rank['Team'] == sel_time]
                rank_display = f"{team_info.iloc[0]['Rank']}º na Liga" if not team_info.empty else "Sem Rank"
            except: rank_display = "-"
            
            df_home = df_recent[df_recent['HomeTeam'] == sel_time].copy()
            df_away = df_recent[df_recent['AwayTeam'] == sel_time].copy()
            
            # --- FIX PARA CORRIGIR O ERRO "KeyError: 'TeamGoals_HT'" ---
            if not df_home.empty:
                df_home['TeamGoals_FT'] = df_home['FTHG']
                df_home['TeamGoals_HT'] = df_home['HTHG']
            
            if not df_away.empty:
                df_away['TeamGoals_FT'] = df_away['FTAG']
                df_away['TeamGoals_HT'] = df_away['HTAG']
            # -----------------------------------------------------------

            df_all = pd.concat([df_home, df_away]).sort_values('Date', ascending=False)
            
            if not df_all.empty:
                main_league = df_all['League_Custom'].mode()[0]
                df_league = df_recent[df_recent['League_Custom'] == main_league]
                avg_goals_league = (df_league['FTHG'] + df_league['FTAG']).mean() / 2 
                team_scored_avg = (df_home['FTHG'].mean() + df_away['FTAG'].mean()) / 2
                team_conceded_avg = (df_home['FTAG'].mean() + df_away['FTHG'].mean()) / 2
                att_strength = (team_scored_avg / avg_goals_league) * 100 if avg_goals_league > 0 else 0
                def_strength = (team_conceded_avg / avg_goals_league) * 100 if avg_goals_league > 0 else 0 
                
                st.markdown(f"### 📊 Raio-X: {sel_time} ({main_league})")
                st.markdown(f"#### 🏆 Posição Atual: **{rank_display}**")
                
                color_att = "#2ea043" if team_scored_avg > avg_goals_league else "#da3633"
                color_def = "#2ea043" if team_conceded_avg < avg_goals_league else "#da3633"
                
                c1, c2 = st.columns(2)
                with c1: st.markdown(f"""<div class="strength-card"><div class="strength-title">⚔️ Força de Ataque</div><div class="strength-value" style="color: {color_att}">{att_strength:.0f}%</div><div class="strength-context">Time: {team_scored_avg:.2f} vs Liga: {avg_goals_league:.2f}</div></div>""", unsafe_allow_html=True)
                with c2: st.markdown(f"""<div class="strength-card"><div class="strength-title">🛡️ Força Defensiva</div><div class="strength-value" style="color: {color_def}">{def_strength:.0f}%</div><div class="strength-context">Time: {team_conceded_avg:.2f} vs Liga: {avg_goals_league:.2f}</div></div>""", unsafe_allow_html=True)
                
                st.divider()
                st.subheader("⚽ Gols (Médias)")
                g1, g2, g3, g4 = st.columns(4)
                g1.metric("Marcados (Casa)", f"{df_home['FTHG'].mean():.2f}")
                g2.metric("Marcados (Fora)", f"{df_away['FTAG'].mean():.2f}")
                g3.metric("Sofridos (Casa)", f"{df_home['FTAG'].mean():.2f}")
                g4.metric("Sofridos (Fora)", f"{df_away['FTHG'].mean():.2f}")
                
                st.subheader("📈 Tendências de Over (Gols do Time)")
                team_score_ht = (df_all['TeamGoals_HT'] > 0).mean()
                team_score_15 = (df_all['TeamGoals_FT'] > 1.5).mean()
                team_score_25 = (df_all['TeamGoals_FT'] > 2.5).mean()
                team_btts = (df_all['BTTS'] == 1).mean()
                st.write(f"Time Marcou 0.5 HT ({team_score_ht*100:.0f}%)"); st.progress(float(team_score_ht))
                st.write(f"Time Marcou 1.5 FT ({team_score_15*100:.0f}%)"); st.progress(float(team_score_15))
                st.write(f"Time Marcou 2.5 FT ({team_score_25*100:.0f}%)"); st.progress(float(team_score_25))
                st.write(f"Ambas Marcam (BTTS) ({team_btts*100:.0f}%)"); st.progress(float(team_btts))
                
                st.divider()
                st.subheader("🚩 Escanteios (Média)")
                corners_pro = []; 
                if not df_home.empty: corners_pro.extend(df_home['HC'].tolist())
                if not df_away.empty: corners_pro.extend(df_away['AC'].tolist())
                media_geral_cantos = sum(corners_pro) / len(corners_pro) if corners_pro else 0
                c0, c1, c2, c3, c4 = st.columns(5)
                c0.metric("Média Geral (Pró)", f"{media_geral_cantos:.1f}")
                c1.metric("A Favor (Casa)", f"{df_home['HC'].mean():.1f}")
                c2.metric("Cedidos (Casa)", f"{df_home['AC'].mean():.1f}")
                c3.metric("A Favor (Fora)", f"{df_away['AC'].mean():.1f}")
                c4.metric("Cedidos (Fora)", f"{df_away['HC'].mean():.1f}")
                
                st.divider()
                st.subheader("🗓️ Últimos 10 Jogos")
                last_10 = df_all.head(10)[['Date', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam', 'HomeWin', 'AwayWin']].copy()
                def color_results(row):
                    color = ''
                    if row['HomeTeam'] == sel_time and row['HomeWin'] == 1: color = 'background-color: #2ea043; color: white'
                    elif row['AwayTeam'] == sel_time and row['AwayWin'] == 1: color = 'background-color: #2ea043; color: white'
                    elif row['FTHG'] == row['FTAG']: color = 'background-color: #6e7681; color: white'
                    else: color = 'background-color: #da3633; color: white'
                    return [color] * len(row)
                st.dataframe(last_10.style.apply(color_results, axis=1), use_container_width=True)

    # 8. RAIO-X LIGAS
    elif menu == "🌍 Raio-X Ligas":
        st.header("🌎 Inteligência Temporal de Ligas (Ano a Ano)")
        all_leagues = sorted(df_recent['League_Custom'].unique())
        options = ["Todas as Ligas"] + all_leagues
        selected_leagues = st.multiselect("Selecione:", options, default=[])
        if not selected_leagues or "Todas as Ligas" in selected_leagues:
            df_filtered = df_recent
        else:
            df_filtered = df_recent[df_recent['League_Custom'].isin(selected_leagues)]
        df_filtered['Year'] = df_filtered['Date'].dt.year
        
        stats_ano = df_filtered.groupby(['League_Custom', 'Year']).apply(lambda x: pd.Series({
            'Gols (Média)': (x['FTHG'] + x['FTAG']).mean(),
            'Over 0.5 HT %': x['Over05HT'].mean() * 100,
            'Over 1.5 FT %': x['Over15FT'].mean() * 100,
            'Over 2.5 FT %': ((x['FTHG'] + x['FTAG']) > 2.5).mean() * 100,
            'BTTS %': ((x['FTHG'] > 0) & (x['FTAG'] > 0)).mean() * 100,
            'Cantos (Média)': (x['HC'] + x['AC']).mean()
        })).reset_index()
        
        stats_ano_display = stats_ano.copy()
        stats_ano_display['Year'] = stats_ano_display['Year'].astype(str)
        stats_ano_display = stats_ano_display.round(2)
        st.subheader("📊 Tabela Detalhada (Ano a Ano)")
        st.dataframe(stats_ano_display, use_container_width=True)
        st.subheader("📈 Tendência de Gols (Evolução)")
        fig_evol = px.line(stats_ano, x='Year', y='Gols (Média)', color='League_Custom', markers=True)
        fig_evol.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_evol, use_container_width=True)

else: st.info("Carregando...")
