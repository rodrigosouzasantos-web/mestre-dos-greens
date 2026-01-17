import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
from PIL import Image

# --- CARREGA A LOGO ---
try:
    logo = Image.open("logo.jpg") 
    icon_page = logo
except:
    logo = None
    icon_page = "⚽"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO - V44",
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
    div[data-testid="stMetricValue"] { font-size: 24px; color: #f1c40f; font-weight: 700; }
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
    "Suecia Allsvenskan": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Sweden_Allsvenskan_2016-2024.csv",
    "Turquia Super Lig": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Turkey_S%C3%BCper_Lig_2016-2025.csv",
    "USA MLS": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/USA_Major_League_Soccer_2016-2024.csv",
    "Uruguai Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Uruguay_Primera_Divisi%C3%B3n_2016-2024.csv"
}

URLS_ATUAIS = {
    "Argentina_Primera_División_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Argentina_Primera_Divisi%C3%B3n_2025.csv",
    "Belgium_Pro_League_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Belgium_Pro_League_2025-2026.csv",
    "Brasileirão_Série_A_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2025-2026.csv",
    "Colombia_Primera_Liga_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Colombia_Primera_Liga_2025.csv",
    "Croatia_HNL_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Croatia_HNL_2025-2026.csv",
    "Denmark_Superliga_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Denmark_Superliga_2025-2026.csv",
    "England_Premier_League_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/England_Premier_League_2025-2026.csv",
    "Finland_Veikkausliiga_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Finland_Veikkausliiga_2025.csv",
    "France_Ligue_1_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/France_Ligue_1_2025-2026.csv",
    "Germany_Bundesliga_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Germany_Bundesliga_2025-2026.csv",
    "Germany_Bundesliga_2_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Germany_Bundesliga_2_2025-2026.csv",
    "Greece_Super_League_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Greece_Super_League_2025-2026.csv",
    "Italy_Serie_A_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Italy_Serie_A_2025-2026.csv",
    "Italy_Serie_B_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Italy_Serie_B_2025-2026.csv",
    "Japan_J1_League_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Japan_J1_League_2025.csv",
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
    "Sweden_Allsvenskan_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Sweden_Allsvenskan_2025.csv",
    "Turkey_Süper_Lig_2025-2026": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Turkey_S%C3%BCper_Lig_2025-2026.csv",
    "USA_Major_League_Soccer_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/USA_Major_League_Soccer_2025.csv",
    "Uruguay_Primera_División_2025": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Uruguay_Primera_Divisi%C3%B3n_2025.csv"
}

URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

@st.cache_data(ttl=3600)
def load_data():
    all_dfs = []
    TODAS_URLS = {**URLS_HISTORICAS, **URLS_ATUAIS}
    progress_text = f"Carregando {len(TODAS_URLS)} fontes de dados..."
    my_bar = st.progress(0, text=progress_text)

    for i, (nome, url) in enumerate(TODAS_URLS.items()):
        try:
            r = requests.get(url)
            if r.status_code != 200: continue
            try: df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), low_memory=False)
            except: df = pd.read_csv(io.StringIO(r.content.decode('latin-1')), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            map_cols = {'homegoalcount': 'fthg', 'awaygoalcount': 'ftag', 'home_score': 'fthg', 'away_score': 'ftag',
                        'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
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
            
            nome_limpo = nome.replace(" Atual", "")
            df['League_Custom'] = nome_limpo
            
            if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','Over05HT','Over15FT','Over25FT','BTTS','HomeWin','AwayWin','HC','AC']])
        except: pass
        my_bar.progress((i + 1) / len(TODAS_URLS))

    my_bar.empty()
    full_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    full_df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last', inplace=True)
    
    # Filtro temporal (2023 em diante)
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy()
    
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
    
    return df_recent, df_today, full_df

# ==============================================================================
# CÁLCULOS PONDERADOS
# ==============================================================================
def calcular_xg_ponderado(df_historico, league, team_home, team_away, col_home_goal='FTHG', col_away_goal='FTAG'):
    df_league = df_historico[df_historico['League_Custom'] == league]
    if df_league.empty: return None, None, None, None
    
    avg_goals_home = df_league[col_home_goal].mean()
    avg_goals_away = df_league[col_away_goal].mean()
    
    df_h = df_historico[df_historico['HomeTeam'] == team_home].sort_values('Date')
    df_a = df_historico[df_historico['AwayTeam'] == team_away].sort_values('Date')
    df_h_all = df_historico[(df_historico['HomeTeam'] == team_home) | (df_historico['AwayTeam'] == team_home)].sort_values('Date')
    df_a_all = df_historico[(df_historico['HomeTeam'] == team_away) | (df_historico['AwayTeam'] == team_away)].sort_values('Date')

    if len(df_h_all) < 5 or len(df_a_all) < 5: return None, None, None, None

    def get_weighted_avg(full_df, venue_df, col_name):
        w_geral = full_df[col_name].mean()
        w_venue = venue_df[col_name].mean() if not venue_df.empty else w_geral
        w_10 = full_df.tail(10)[col_name].mean()
        w_5 = full_df.tail(5)[col_name].mean()
        return (w_geral * 0.10) + (w_venue * 0.40) + (w_10 * 0.20) + (w_5 * 0.30)

    # MANDANTE (ATAQUE)
    att_h_pond = get_weighted_avg(df_h_all, df_h, col_home_goal)
    strength_att_h = att_h_pond / avg_goals_home if avg_goals_home > 0 else 1.0
    
    # VISITANTE (DEFESA)
    def_a_pond = get_weighted_avg(df_a_all, df_a, col_home_goal)
    strength_def_a = def_a_pond / avg_goals_home if avg_goals_home > 0 else 1.0
    
    xg_home = strength_att_h * strength_def_a * avg_goals_home
    
    # VISITANTE (ATAQUE)
    att_a_pond = get_weighted_avg(df_a_all, df_a, col_away_goal)
    strength_att_a = att_a_pond / avg_goals_away if avg_goals_away > 0 else 1.0
    
    # MANDANTE (DEFESA)
    def_h_pond = get_weighted_avg(df_h_all, df_h, col_away_goal)
    strength_def_h = def_h_pond / avg_goals_away if avg_goals_away > 0 else 1.0
    
    xg_away = strength_att_a * strength_def_h * avg_goals_away
    
    return xg_home, xg_away, strength_att_h, strength_att_a

def calcular_cantos_esperados_e_probs(df_historico, team_home, team_away):
    # Fórmula Cruzada
    df_h = df_historico[df_historico['HomeTeam'] == team_home]
    df_a = df_historico[df_historico['AwayTeam'] == team_away]
    
    if df_h.empty or df_a.empty: return 0.0, {}

    # (Média Pró A + Média Contra B) / 2
    media_pro_a = df_h['HC'].mean()
    media_contra_b = df_a['HC'].mean() 
    exp_cantos_a = (media_pro_a + media_contra_b) / 2
    
    # (Média Pró B + Média Contra A) / 2
    media_pro_b = df_a['AC'].mean()
    media_contra_a = df_h['AC'].mean() 
    exp_cantos_b = (media_pro_b + media_contra_a) / 2
    
    total_exp = exp_cantos_a + exp_cantos_b
    
    # Cálculo Poisson para probabilidades
    # Over 8.5, 9.5, 10.5
    probs = {
        "Over 8.5": poisson.sf(8, total_exp) * 100,
        "Over 9.5": poisson.sf(9, total_exp) * 100,
        "Over 10.5": poisson.sf(10, total_exp) * 100
    }
    
    return total_exp, probs

def gerar_matriz_poisson(xg_home, xg_away):
    matrix = []
    probs_dict = {"HomeWin":0,"Draw":0,"AwayWin":0,"Over15":0,"Over25":0,"Under35":0,"BTTS":0}
    
    for h in range(6):
        row = []
        for a in range(6):
            prob = poisson.pmf(h, xg_home) * poisson.pmf(a, xg_away)
            row.append(prob * 100)
            
            if h > a: probs_dict["HomeWin"] += prob
            elif h < a: probs_dict["AwayWin"] += prob
            else: probs_dict["Draw"] += prob
            
            total_goals = h + a
            if total_goals > 1.5: probs_dict["Over15"] += prob
            if total_goals > 2.5: probs_dict["Over25"] += prob
            if total_goals < 3.5: probs_dict["Under35"] += prob
            if h > 0 and a > 0: probs_dict["BTTS"] += prob
            
        matrix.append(row)
    return matrix, probs_dict

def exibir_matriz_visual(matriz, home_name, away_name):
    # Layout LIMPO: Mandante à Direita (Eixo Y), Visitante em Cima (Eixo X)
    # Nomes apenas nos títulos, não nas células.
    colorscale = [[0, '#161b22'], [0.3, '#1f2937'], [0.6, '#d4ac0d'], [1, '#f1c40f']]
    
    # Eixos simples
    x_labels = ['0', '1', '2', '3', '4', '5+']
    y_labels = ['0', '1', '2', '3', '4', '5+']

    fig = go.Figure(data=go.Heatmap(
        z=matriz,
        x=x_labels,
        y=y_labels,
        text=matriz,
        texttemplate="<b>%{z:.1f}%</b>",
        textfont={"size":16, "color":"white"},
        colorscale=colorscale,
        showscale=False
    ))
    
    fig.update_layout(
        title=dict(text="🎲 Matriz de Probabilidades (Placar Exato)", font=dict(color='#f1c40f', size=20)),
        xaxis=dict(side="top", title=f"<b>{away_name}</b> (Visitante)", title_font=dict(size=18, color='#fff'), tickfont=dict(color='#cfcfcf', size=14)),
        yaxis=dict(side="right", title=f"<b>{home_name}</b> (Mandante)", title_font=dict(size=18, color='#fff'), tickfont=dict(color='#cfcfcf', size=14)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=500,
        margin=dict(t=100, l=20, r=100)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- APP PRINCIPAL ---
st.title("🧙‍♂️ Mestre dos Greens PRO - V44")

df_recent, df_today, full_df = load_data()

if not df_recent.empty:
    if logo:
        st.sidebar.image(logo, use_container_width=True)
        st.sidebar.markdown("---")
    
    if st.sidebar.button("🔄 Forçar Atualização"):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.markdown("---")
        
    st.sidebar.markdown("## 🧭 Navegação")
    menu = st.sidebar.radio("Selecione:", ["🎯 Grade do Dia", "⚔️ Simulador Manual", "🔎 Analisador de Times", "🌍 Raio-X Ligas"])
    
    # ==============================================================================
    # 1. GRADE DO DIA
    # ==============================================================================
    if menu == "🎯 Grade do Dia":
        st.header("🎯 Grade do Dia (Poisson V44)")
        if not df_today.empty:
            jogos_hoje = [f"{row['HomeTeam']} x {row['AwayTeam']}" for i, row in df_today.iterrows()]
            jogo_selecionado = st.selectbox("👉 Selecione um jogo:", jogos_hoje, index=0)
            
            times = jogo_selecionado.split(" x ")
            home_sel, away_sel = times[0], times[1]
            try: liga_match = df_recent[df_recent['HomeTeam'] == home_sel]['League_Custom'].mode()[0]
            except: liga_match = None
            
            if liga_match:
                # 1. Full Time xG
                xg_h, xg_a, _, _ = calcular_xg_ponderado(df_recent, liga_match, home_sel, away_sel, 'FTHG', 'FTAG')
                # 2. Half Time xG (Para calcular Over 0.5 HT)
                xg_h_ht, xg_a_ht, _, _ = calcular_xg_ponderado(df_recent, liga_match, home_sel, away_sel, 'HTHG', 'HTAG')
                # 3. Cantos & Probs
                exp_cantos, probs_cantos = calcular_cantos_esperados_e_probs(df_recent, home_sel, away_sel)
                
                if xg_h is not None:
                    st.divider()
                    st.markdown(f"### 📊 Raio-X: {home_sel} vs {away_sel}")
                    
                    # Métricas Principais
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("⚽ xG Esperado (FT)", f"{xg_h+xg_a:.2f}")
                    c2.metric("🚩 Cantos Esperados", f"{exp_cantos:.1f}")
                    c3.metric("xG Casa", f"{xg_h:.2f}")
                    c4.metric("xG Fora", f"{xg_a:.2f}")
                    
                    # Matriz e Probabilidades FT
                    matriz, probs = gerar_matriz_poisson(xg_h, xg_a)
                    
                    # Probabilidade HT
                    prob_00_ht = poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht)
                    prob_over05_ht = (1 - prob_00_ht) * 100
                    
                    col_matriz, col_probs = st.columns([1.5, 1])
                    with col_matriz:
                        exibir_matriz_visual(matriz, home_sel, away_sel)
                    
                    with col_probs:
                        st.subheader("📈 Probabilidades Reais")
                        st.success(f"⚡ Over 0.5 HT: {prob_over05_ht:.1f}%")
                        st.success(f"🛡️ Over 1.5 FT: {probs['Over15']*100:.1f}%")
                        st.success(f"🔥 Over 2.5 FT: {probs['Over25']*100:.1f}%")
                        st.info(f"🧱 Under 3.5 FT: {probs['Under35']*100:.1f}%")
                        st.warning(f"🤝 BTTS: {probs['BTTS']*100:.1f}%")
                        st.markdown("---")
                        st.markdown("🚩 **Probabilidades de Cantos:**")
                        st.write(f"• Over 8.5: **{probs_cantos['Over 8.5']:.1f}%**")
                        st.write(f"• Over 9.5: **{probs_cantos['Over 9.5']:.1f}%**")
                        st.write(f"• Over 10.5: **{probs_cantos['Over 10.5']:.1f}%**")

                else: st.warning("Dados insuficientes.")
            else: st.warning("Liga não encontrada.")
        else: st.info("Aguardando jogos...")

    # ==============================================================================
    # 2. SIMULADOR MANUAL
    # ==============================================================================
    elif menu == "⚔️ Simulador Manual":
        st.header("⚔️ Simulador Manual V44")
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
                    matriz, probs = gerar_matriz_poisson(xg_h, xg_a)
                    prob_over05_ht = (1 - (poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht))) * 100
                    
                    exibir_matriz_visual(matriz, team_a, team_b)
                    
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Vitória Casa", f"{probs['HomeWin']*100:.1f}%")
                    k2.metric("Over 0.5 HT", f"{prob_over05_ht:.1f}%")
                    k3.metric("Cantos (Avg)", f"{exp_cantos:.1f}")
                    k4.metric("Over 9.5 Cantos", f"{probs_cantos['Over 9.5']:.1f}%")

    # ==============================================================================
    # 3. ANALISADOR DE TIMES (COM GRÁFICOS)
    # ==============================================================================
    elif menu == "🔎 Analisador de Times":
        st.header("🔎 Scout Profundo (Visual)")
        all_teams_db = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        sel_time = st.selectbox("Pesquise o time:", all_teams_db, index=None)
        
        if sel_time:
            df_t_home = df_recent[df_recent['HomeTeam'] == sel_time]
            df_t_away = df_recent[df_recent['AwayTeam'] == sel_time]
            df_t_all = pd.concat([df_t_home, df_t_away]).sort_values('Date', ascending=False)
            
            if not df_t_all.empty:
                st.markdown(f"### 📊 Estatísticas: {sel_time}")
                
                # Gráfico 1: Gols Pró vs Sofridos (Bar Chart)
                goals_data = pd.DataFrame({
                    "Tipo": ["Gols Pró (Casa)", "Gols Sofridos (Casa)", "Gols Pró (Fora)", "Gols Sofridos (Fora)"],
                    "Média": [
                        df_t_home['FTHG'].mean() if not df_t_home.empty else 0,
                        df_t_home['FTAG'].mean() if not df_t_home.empty else 0,
                        df_t_away['FTAG'].mean() if not df_t_away.empty else 0,
                        df_t_away['FTHG'].mean() if not df_t_away.empty else 0
                    ]
                })
                fig_goals = px.bar(goals_data, x="Tipo", y="Média", color="Tipo", title="Média de Gols (Casa vs Fora)")
                
                # Gráfico 2: Resultados (Pie Chart)
                wins = df_t_all[(df_t_all['HomeTeam']==sel_time) & (df_t_all['HomeWin']==1)].shape[0] + \
                       df_t_all[(df_t_all['AwayTeam']==sel_time) & (df_t_all['AwayWin']==1)].shape[0]
                draws = len(df_t_all) - (wins + (len(df_t_all)-wins)) # Simplificação p/ exemplo, ideal seria calcular losses exatos
                losses = len(df_t_all) - wins # (Losses + Draws) na verdade. Ajustar p/ precisão:
                
                # Recalculando Losses exatos
                losses = df_t_all[(df_t_all['HomeTeam']==sel_time) & (df_t_all['AwayWin']==1)].shape[0] + \
                         df_t_all[(df_t_all['AwayTeam']==sel_time) & (df_t_all['HomeWin']==1)].shape[0]
                draws = len(df_t_all) - (wins + losses)
                
                fig_res = px.pie(values=[wins, draws, losses], names=["Vitórias", "Empates", "Derrotas"], 
                                 title="Resultados Gerais", color_discrete_sequence=['#2ecc71', '#95a5a6', '#e74c3c'])
                
                col_g1, col_g2 = st.columns(2)
                col_g1.plotly_chart(fig_goals, use_container_width=True)
                col_g2.plotly_chart(fig_res, use_container_width=True)
                
                st.dataframe(df_t_all[['Date','League_Custom','HomeTeam','FTHG','FTAG','AwayTeam']].head(10), hide_index=True, use_container_width=True)

    # ==============================================================================
    # 4. RAIO-X LIGAS (COM GRÁFICOS RESTAURADOS)
    # ==============================================================================
    elif menu == "🌍 Raio-X Ligas":
        st.header("🌎 Inteligência de Ligas")
        stats_liga = df_recent.groupby('League_Custom').apply(lambda x: pd.Series({
            'Média Gols': (x['FTHG']+x['FTAG']).mean(),
            'Over 2.5 %': ((x['FTHG']+x['FTAG'])>2.5).mean()*100,
            'BTTS %': ((x['FTHG']>0)&(x['FTAG']>0)).mean()*100,
            'Cantos': (x['HC']+x['AC']).mean()
        })).reset_index()
        
        # Gráfico de Barras Degradê
        fig_gols = px.bar(stats_liga.sort_values('Média Gols', ascending=False).head(20), 
                          x='League_Custom', y='Média Gols', 
                          color='Over 2.5 %', 
                          title="Top 20 Ligas: Gols & Over 2.5", 
                          color_continuous_scale='Spectral')
        st.plotly_chart(fig_gols, use_container_width=True)
        
        st.dataframe(stats_liga.sort_values('Média Gols', ascending=False), hide_index=True, use_container_width=True)

else: st.info("Carregando...")
