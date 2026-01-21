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
    page_title="Mestre dos Greens PRO - V66.1",
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
            df['Season_Type'] = 'Current' # TAG IMPORTANTE
            
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
    
    # 4. Jogos de Hoje
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns: df_today['HomeTeam'], df_today['AwayTeam'] = df_today.iloc[:, 0], df_today.iloc[:, 1]
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
    for i, row in df_league_matches.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        hg, ag = row['FTHG'], row['FTAG']
        
        if h not in teams: teams[h] = {'P':0, 'W':0, 'D':0, 'L':0, 'GF':0, 'GA':0, 'Pts':0}
        if a not in teams: teams[a] = {'P':0, 'W':0, 'D':0, 'L':0, 'GF':0, 'GA':0, 'Pts':0}
        
        teams[h]['P'] += 1; teams[h]['GF'] += hg; teams[h]['GA'] += ag
        teams[a]['P'] += 1; teams[a]['GF'] += ag; teams[a]['GA'] += hg
        
        if hg > ag: # Home Win
            teams[h]['W'] += 1; teams[h]['Pts'] += 3
            teams[a]['L'] += 1
        elif ag > hg: # Away Win
            teams[a]['W'] += 1; teams[a]['Pts'] += 3
            teams[h]['L'] += 1
        else: # Draw
            teams[h]['D'] += 1; teams[h]['Pts'] += 1
            teams[a]['D'] += 1; teams[a]['Pts'] += 1
            
    df_rank = pd.DataFrame.from_dict(teams, orient='index').reset_index()
    df_rank.rename(columns={'index':'Team'}, inplace=True)
    df_rank['GD'] = df_rank['GF'] - df_rank['GA']
    df_rank = df_rank.sort_values(by=['Pts', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    df_rank.index += 1 
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
    att_h = get_weighted_avg(df_h_all, df_h, col_home_goal)
    def_a = get_weighted_avg(df_a_all, df_a, col_home_goal)
    att_a = get_weighted_avg(df_a_all, df_a, col_away_goal)
    def_h = get_weighted_avg(df_h_all, df_h, col_away_goal)
    xg_home = (att_h / avg_goals_home) * (def_a / avg_goals_home) * avg_goals_home if avg_goals_home > 0 else 0
    xg_away = (att_a / avg_goals_away) * (def_h / avg_goals_away) * avg_goals_away if avg_goals_away > 0 else 0
    return xg_home, xg_away, 0, 0

def calcular_cantos_esperados_e_probs(df_historico, team_home, team_away):
    df_h = df_historico[df_historico['HomeTeam'] == team_home]
    df_a = df_historico[df_historico['AwayTeam'] == team_away]
    if df_h.empty or df_a.empty: return 0.0, {}
    total_exp = (df_h['HC'].mean() + df_a['AC'].mean() + df_a['HC'].mean() + df_h['AC'].mean()) / 2
    probs = { "Over 8.5": poisson.sf(8, total_exp) * 100, "Over 9.5": poisson.sf(9, total_exp) * 100, "Over 10.5": poisson.sf(10, total_exp) * 100 }
    return total_exp, probs

def gerar_matriz_poisson(xg_home, xg_away):
    top_scores = []
    probs = {"HomeWin":0,"Draw":0,"AwayWin":0,"Over15":0,"Over25":0,"Under35":0,"BTTS":0}
    matrix = []
    for h in range(6):
        row = []
        for a in range(6):
            p = poisson.pmf(h, xg_home) * poisson.pmf(a, xg_away)
            row.append(p*100)
            top_scores.append({'Placar': f"{h}x{a}", 'Prob': p*100})
            if h > a: probs["HomeWin"] += p
            elif a > h: probs["AwayWin"] += p
            else: probs["Draw"] += p
            if (h+a) > 1.5: probs["Over15"] += p
            if (h+a) > 2.5: probs["Over25"] += p
            if (h+a) < 3.5: probs["Under35"] += p
            if h > 0 and a > 0: probs["BTTS"] += p
        matrix.append(row)
    return matrix, probs, sorted(top_scores, key=lambda x: x['Prob'], reverse=True)[:5]

def exibir_matriz_visual(matriz, home_name, away_name):
    fig = go.Figure(data=go.Heatmap(z=matriz, x=['0','1','2','3','4','5+'], y=['0','1','2','3','4','5+'], text=matriz, texttemplate="<b>%{z:.1f}%</b>", colorscale=[[0,'#161b22'],[1,'#f1c40f']], showscale=False))
    fig.update_layout(title="🎲 Placar Exato", xaxis=dict(side="top"), yaxis=dict(autorange='reversed'), height=400, margin=dict(t=50, l=50, r=50, b=50), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# APP
# ==============================================================================
st.title("🧙‍♂️ Mestre dos Greens PRO - V66.1 (Full)")

if not df_recent.empty:
    if logo: st.sidebar.image(logo, use_container_width=True)
    if st.sidebar.button("🔄 Atualizar"): st.cache_data.clear(); st.rerun()
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Menu:", ["🎯 Grade do Dia", "📊 Winrate & Assertividade", "🏆 Classificação", "⚔️ Simulador", "🎫 Bilhetes", "🚀 Alavancagem", "🔎 Analisador"])

    # 1. GRADE DO DIA
    if menu == "🎯 Grade do Dia":
        st.header("🎯 Grade do Dia")
        if not df_today.empty:
            jogos = [f"{row['HomeTeam']} x {row['AwayTeam']}" for i, row in df_today.iterrows()]
            sel_jogo = st.selectbox("Jogo:", jogos)
            home, away = sel_jogo.split(" x ")
            
            try: 
                liga = df_recent[df_recent['HomeTeam'] == home]['League_Custom'].mode()[0]
                rank_df = calculate_standings(df_current_season[df_current_season['League_Custom'] == liga])
                hr = rank_df[rank_df['Team'] == home].iloc[0]['Rank'] if not rank_df.empty and home in rank_df['Team'].values else "-"
                ar = rank_df[rank_df['Team'] == away].iloc[0]['Rank'] if not rank_df.empty and away in rank_df['Team'].values else "-"
            except: liga = None; hr = "-"; ar = "-"

            if liga:
                xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, liga, home, away)
                xg_h_ht, xg_a_ht, _, _ = calcular_xg_ponderado(df_recent, liga, home, away, 'HTHG', 'HTAG')
                _, probs, top = gerar_matriz_poisson(xg_h, xg_a)
                prob_ht = (1 - (poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht))) * 100
                
                st.divider()
                st.markdown(f"### {home} ({hr}º) x {away} ({ar}º)")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("xG Jogo", f"{xg_h+xg_a:.2f}")
                c3.metric("xG Casa", f"{xg_h:.2f}")
                c4.metric("xG Fora", f"{xg_a:.2f}")
                
                c_mat, c_prob = st.columns([1.5, 1])
                with c_mat: 
                    exibir_matriz_visual(_, home, away)
                    if st.button("Enviar Telegram"): enviar_telegram(f"🔥 {home} x {away}\n📊 Over 2.5: {probs['Over25']*100:.1f}%")
                with c_prob:
                    def show_metric(label, val, target):
                        color = "green" if val >= target else "orange" if val >= target-10 else "red"
                        icon = "✅" if val >= target else "⚠️" if val >= target-10 else "🔻"
                        st.markdown(f"**{label}**: <span style='color:{color}'>{icon} {val:.1f}%</span>", unsafe_allow_html=True)
                    
                    show_metric("Over 0.5 HT", prob_ht, 80)
                    show_metric("Over 1.5 FT", probs['Over15']*100, 80)
                    show_metric("Over 2.5 FT", probs['Over25']*100, 60)
                    show_metric("BTTS", probs['BTTS']*100, 60)
                    show_metric("Under 3.5 FT", probs['Under35']*100, 80)

    # 2. WINRATE (LÓGICA CORRIGIDA 1x1 = GREEN)
    elif menu == "📊 Winrate & Assertividade":
        st.header("📊 Assertividade do Robô (Backtest)")
        
        tab_yesterday, tab_month = st.tabs(["📅 Ontem", "🗓️ Mês Atual"])
        
        def calculate_winrate(target_date_start, target_date_end, title):
            # Filtra jogos
            mask = (df_recent['Date'] >= target_date_start) & (df_recent['Date'] <= target_date_end)
            games = df_recent.loc[mask]
            
            if games.empty:
                st.warning("Sem jogos finalizados neste período para analisar.")
                return

            total_bets = 0
            hits = 0
            results = []
            
            progress_bar = st.progress(0)
            step = 1 / len(games) if len(games) > 0 else 1
            
            for i, row in games.iterrows():
                progress_bar.progress(min((i + 1) * step, 1.0)) 
                h, a, l = row['HomeTeam'], row['AwayTeam'], row['League_Custom']
                
                # Simula Previsão (Exatamente como na Grade)
                xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, l, h, a)
                if xg_h is None: continue
                _, probs, _ = gerar_matriz_poisson(xg_h, xg_a)
                
                # Checa Critérios e Resultados Reais
                bets = []
                
                # Over 1.5 (> 1.5 gols = 2 ou mais. 1x1 é Green)
                if probs['Over15'] >= 0.80:
                    real_total = row['FTHG'] + row['FTAG']
                    outcome = real_total > 1.5 # 1.51 é maior que 1.5, então 2 gols é Green.
                    bets.append({'Market': 'Over 1.5', 'Hit': outcome, 'Prob': probs['Over15']})
                
                # Over 2.5
                if probs['Over25'] >= 0.60:
                    real_total = row['FTHG'] + row['FTAG']
                    outcome = real_total > 2.5
                    bets.append({'Market': 'Over 2.5', 'Hit': outcome, 'Prob': probs['Over25']})
                    
                # BTTS
                if probs['BTTS'] >= 0.60:
                    outcome = (row['FTHG'] > 0 and row['FTAG'] > 0)
                    bets.append({'Market': 'BTTS', 'Hit': outcome, 'Prob': probs['BTTS']})
                
                # Under 3.5 (Menos de 4 gols)
                if probs['Under35'] >= 0.80:
                    real_total = row['FTHG'] + row['FTAG']
                    outcome = real_total < 3.5
                    bets.append({'Market': 'Under 3.5', 'Hit': outcome, 'Prob': probs['Under35']})

                if bets:
                    for b in bets:
                        total_bets += 1
                        if b['Hit']: hits += 1
                        results.append({
                            'Jogo': f"{h} {int(row['FTHG'])}x{int(row['FTAG'])} {a}",
                            'Aposta': b['Market'],
                            'Prob Robô': f"{b['Prob']*100:.1f}%",
                            'Resultado': "✅ GREEN" if b['Hit'] else "🔻 RED"
                        })
            
            progress_bar.empty()
            
            if total_bets > 0:
                wr = (hits / total_bets) * 100
                c1, c2, c3 = st.columns(3)
                c1.metric("Total de Entradas", total_bets)
                c2.metric("Greens ✅", hits)
                c3.metric("Winrate %", f"{wr:.1f}%", delta_color="normal")
                
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("Nenhuma entrada se encaixou nos critérios do Robô neste período.")

        with tab_yesterday:
            yesterday = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
            st.subheader(f"Resultados de Ontem ({yesterday.strftime('%d/%m')})")
            if st.button("Calcular Ontem"):
                calculate_winrate(yesterday, yesterday + pd.Timedelta(hours=23, minutes=59), "Ontem")
                
        with tab_month:
            first_day = pd.Timestamp.now().replace(day=1).normalize()
            st.subheader(f"Acumulado do Mês ({first_day.strftime('%B')})")
            if st.button("Calcular Mês"):
                calculate_winrate(first_day, pd.Timestamp.now(), "Mês")

    # 3. CLASSIFICAÇÃO (CÁLCULO REAL)
    elif menu == "🏆 Classificação":
        st.header("🏆 Classificação (Standings 2025/26)")
        if not df_current_season.empty:
            leagues = sorted(df_current_season['League_Custom'].unique())
            sel_league = st.selectbox("Liga:", leagues)
            df_rank = calculate_standings(df_current_season[df_current_season['League_Custom'] == sel_league])
            if not df_rank.empty:
                def color_standings(row):
                    rank = row['Rank']
                    if rank <= 4: return ['background-color: #1e3a8a; color: white'] * len(row)
                    elif rank >= len(df_rank) - 3: return ['background-color: #7f1d1d; color: white'] * len(row)
                    else: return [''] * len(row)
                st.dataframe(df_rank[['Rank','Team','P','W','D','L','GF','GA','GD','Pts']].style.apply(color_standings, axis=1), use_container_width=True)
            else: st.warning("Sem dados.")

    # 4. SIMULADOR (MANTIDO)
    elif menu == "⚔️ Simulador Manual":
        st.header("Simulador")
        teams = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        t1 = st.selectbox("Casa", teams)
        t2 = st.selectbox("Fora", teams)
        if t1 and t2:
            try: 
                l = df_recent[df_recent['HomeTeam'] == t1]['League_Custom'].mode()[0]
                xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, l, t1, t2)
                if xg_h:
                    _, probs, _ = gerar_matriz_poisson(xg_h, xg_a)
                    st.metric("Prob Casa", f"{probs['HomeWin']*100:.1f}%")
            except: st.error("Erro ao simular.")

    # 5. ALAVANCAGEM
    elif menu == "🚀 Alavancagem":
        st.header("🚀 Alavancagem")
        st.info("Aguardando definição dos critérios.")

    # 6. BILHETES (MANTIDO)
    elif menu == "🎫 Bilhetes Prontos":
        st.header("Bilhetes")
        st.info("Use o menu Grade do Dia para análises detalhadas.")

else: st.info("Carregando dados...")
