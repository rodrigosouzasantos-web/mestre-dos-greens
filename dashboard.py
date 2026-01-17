import streamlit as st
import pandas as pd
import requests
import io
import math
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
    page_title="Mestre dos Greens PRO - V40",
    page_icon=icon_page,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS VISUAL ---
st.markdown("""
    <style>
    .metric-card {background-color: #1e2130; border: 1px solid #313547; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);}
    div[data-testid="stMetricValue"] { font-size: 20px; color: #00ff00; }
    div[data-testid="stMetricLabel"] { font-size: 14px; }
    [data-testid="stSidebar"] > div:first-child { text-align: center; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .poisson-cell { text-align: center; padding: 8px; border: 1px solid #444; }
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
            
            if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','Over05HT','Over15FT','Over25FT','BTTS','HomeWin','AwayWin','HC','AC']])
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
# CÁLCULOS PONDERADOS (PDF V40)
# ==============================================================================
def calcular_xg_ponderado(df_historico, league, team_home, team_away):
    # 1. Filtra dados da Liga (para Médias da Liga)
    df_league = df_historico[df_historico['League_Custom'] == league]
    if df_league.empty: return None, None, None, None
    
    # Médias da Liga
    avg_goals_home = df_league['FTHG'].mean()
    avg_goals_away = df_league['FTAG'].mean()
    
    # 2. Dados dos Times
    df_h = df_historico[df_historico['HomeTeam'] == team_home].sort_values('Date')
    df_a = df_historico[df_historico['AwayTeam'] == team_away].sort_values('Date')
    df_h_all = df_historico[(df_historico['HomeTeam'] == team_home) | (df_historico['AwayTeam'] == team_home)].sort_values('Date')
    df_a_all = df_historico[(df_historico['HomeTeam'] == team_away) | (df_historico['AwayTeam'] == team_away)].sort_values('Date')

    if len(df_h_all) < 5 or len(df_a_all) < 5: return None, None, None, None

    # Função Auxiliar de Pesos
    def get_weighted_avg(full_df, venue_df, col_name):
        # 10% Geral
        w_geral = full_df[col_name].mean()
        # 40% Venue (Casa ou Fora)
        w_venue = venue_df[col_name].mean() if not venue_df.empty else w_geral
        # 20% Last 10
        w_10 = full_df.tail(10)[col_name].mean()
        # 30% Last 5
        w_5 = full_df.tail(5)[col_name].mean()
        
        return (w_geral * 0.10) + (w_venue * 0.40) + (w_10 * 0.20) + (w_5 * 0.30)

    # CÁLCULO MANDANTE (HOME)
    # Ataque Ponderado (GF)
    att_h_pond = get_weighted_avg(df_h_all, df_h, 'FTHG')
    # Força de Ataque (Ataque Ponderado / Média Liga Home)
    strength_att_h = att_h_pond / avg_goals_home if avg_goals_home > 0 else 1.0
    
    # CÁLCULO VISITANTE (AWAY) - DEFESA
    # Defesa Ponderada (Goals Against - FTHG quando ele é visitante)
    # Nota: Quando o visitante joga fora, os gols que ele sofre são os FTHG do mandante adversário.
    # No dataframe, se o time é AwayTeam, os gols sofridos são 'FTHG'.
    def_a_pond = get_weighted_avg(df_a_all, df_a, 'FTHG') # Usa FTHG pois é o gol que ele tomou fora
    # Força de Defesa (Defesa Ponderada / Média Liga Home) - Compara com o ataque médio dos mandantes
    strength_def_a = def_a_pond / avg_goals_home if avg_goals_home > 0 else 1.0
    
    # xG FINAL MANDANTE
    xg_home = strength_att_h * strength_def_a * avg_goals_home
    
    # ---------------------------------------------------------
    
    # CÁLCULO VISITANTE (AWAY) - ATAQUE
    att_a_pond = get_weighted_avg(df_a_all, df_a, 'FTAG')
    strength_att_a = att_a_pond / avg_goals_away if avg_goals_away > 0 else 1.0
    
    # CÁLCULO MANDANTE (HOME) - DEFESA
    # Quando o mandante joga em casa, os gols que ele sofre são 'FTAG'
    def_h_pond = get_weighted_avg(df_h_all, df_h, 'FTAG')
    strength_def_h = def_h_pond / avg_goals_away if avg_goals_away > 0 else 1.0
    
    # xG FINAL VISITANTE
    xg_away = strength_att_a * strength_def_h * avg_goals_away
    
    return xg_home, xg_away, strength_att_h, strength_att_a

def gerar_matriz_poisson(xg_home, xg_away):
    # Gera probabilidades para placares de 0x0 até 5x5
    matrix = []
    probs_dict = {
        "HomeWin": 0, "Draw": 0, "AwayWin": 0,
        "Over15": 0, "Over25": 0, "BTTS": 0,
        "Exact_1x0": 0, "Exact_0x1": 0, "Exact_1x1": 0
    }
    
    for h in range(6):
        row = []
        for a in range(6):
            prob = poisson.pmf(h, xg_home) * poisson.pmf(a, xg_away)
            row.append(prob * 100) # Em porcentagem
            
            if h > a: probs_dict["HomeWin"] += prob
            elif h < a: probs_dict["AwayWin"] += prob
            else: probs_dict["Draw"] += prob
            
            if (h + a) > 1.5: probs_dict["Over15"] += prob
            if (h + a) > 2.5: probs_dict["Over25"] += prob
            if h > 0 and a > 0: probs_dict["BTTS"] += prob
            
            if h==1 and a==0: probs_dict["Exact_1x0"] = prob
            if h==0 and a==1: probs_dict["Exact_0x1"] = prob
            if h==1 and a==1: probs_dict["Exact_1x1"] = prob
            
        matrix.append(row)
        
    return matrix, probs_dict

# --- APP PRINCIPAL ---
st.title("🧙‍♂️ Mestre dos Greens PRO - V40")

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
    menu = st.sidebar.radio("Selecione:", ["🎯 Grade do Dia & Detalhes", "⚔️ Simulador Manual (H2H)", "🔎 Analisador de Times"])
    
    # ==============================================================================
    # 1. GRADE DO DIA & DETALHES (COM MATRIZ)
    # ==============================================================================
    if menu == "🎯 Grade do Dia & Detalhes":
        st.header("🎯 Grade do Dia")
        
        if not df_today.empty:
            jogos_hoje = [f"{row['HomeTeam']} x {row['AwayTeam']}" for i, row in df_today.iterrows()]
            jogo_selecionado = st.selectbox("👉 Selecione um jogo para ver a MATRIZ DE POISSON:", jogos_hoje, index=0)
            
            # Encontrar dados do jogo selecionado
            times = jogo_selecionado.split(" x ")
            home_sel, away_sel = times[0], times[1]
            row_sel = df_today[(df_today['HomeTeam'] == home_sel) & (df_today['AwayTeam'] == away_sel)].iloc[0]
            liga_sel = row_sel.get('League', '')
            
            # Tentar encontrar a liga no histórico (pode ter nome levemente diferente, faremos busca simples)
            try:
                liga_match = df_recent[df_recent['HomeTeam'] == home_sel]['League_Custom'].mode()[0]
            except:
                liga_match = None
            
            if liga_match:
                # CÁLCULO PODERADO V40
                xg_h, xg_a, str_h, str_a = calcular_xg_ponderado(df_recent, liga_match, home_sel, away_sel)
                
                if xg_h is not None:
                    st.divider()
                    st.markdown(f"### 📊 Raio-X: {home_sel} vs {away_sel}")
                    
                    # Exibir Forças e xG
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("⚔️ Força Ataque Casa", f"{str_h:.2f}")
                    c2.metric("🛡️ Força Defesa Visitante", f"{str_a:.2f}") # (Conceitual, aqui é força relativa)
                    c3.metric("⚽ xG Esperado (Casa)", f"{xg_h:.2f}", delta="Gols previstos")
                    c4.metric("⚽ xG Esperado (Fora)", f"{xg_a:.2f}", delta="Gols previstos")
                    
                    # MATRIZ DE POISSON
                    matriz, probs = gerar_matriz_poisson(xg_h, xg_a)
                    
                    st.subheader("🎲 Matriz de Probabilidades (Placar Exato)")
                    
                    # Criar Heatmap com Plotly
                    z_data = matriz
                    x_labels = ['0', '1', '2', '3', '4', '5+'] # Gols Visitante
                    y_labels = ['0', '1', '2', '3', '4', '5+'] # Gols Casa
                    
                    fig = px.imshow(z_data,
                                    labels=dict(x="Gols Visitante", y="Gols Mandante", color="Probabilidade (%)"),
                                    x=x_labels,
                                    y=y_labels,
                                    text_auto='.1f',
                                    color_continuous_scale='Viridis') # Escala de cor profissional
                    fig.update_layout(width=600, height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Probabilidades Consolidadas
                    st.subheader("📈 Probabilidades Reais (Baseadas na Matriz)")
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Vitória Casa", f"{probs['HomeWin']*100:.1f}%", f"Odd Justa: @{get_odd_justa(probs['HomeWin']*100):.2f}")
                    k2.metric("Empate", f"{probs['Draw']*100:.1f}%", f"Odd Justa: @{get_odd_justa(probs['Draw']*100):.2f}")
                    k3.metric("Vitória Visitante", f"{probs['AwayWin']*100:.1f}%", f"Odd Justa: @{get_odd_justa(probs['AwayWin']*100):.2f}")
                    
                    k4, k5, k6 = st.columns(3)
                    k4.metric("Over 2.5 Gols", f"{probs['Over25']*100:.1f}%", f"Odd Justa: @{get_odd_justa(probs['Over25']*100):.2f}")
                    k5.metric("Ambas Marcam (BTTS)", f"{probs['BTTS']*100:.1f}%", f"Odd Justa: @{get_odd_justa(probs['BTTS']*100):.2f}")
                    k6.metric("Placar Mais Provável", "Ver Matriz 👆")

                else:
                    st.warning("Dados históricos insuficientes para calcular xG Ponderado deste confronto.")
            else:
                st.warning(f"Não foi possível encontrar o histórico da liga para esses times. Verifique se a liga '{row_sel['League']}' está mapeada.")
        else:
            st.info("Aguardando jogos do dia...")

    # ==============================================================================
    # 2. SIMULADOR MANUAL
    # ==============================================================================
    elif menu == "⚔️ Simulador Manual (H2H)":
        st.header("⚔️ Simulador Manual V40 (Poisson)")
        all_teams = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        
        c1, c2, c3 = st.columns(3)
        team_a = c1.selectbox("Casa:", all_teams, index=None)
        team_b = c2.selectbox("Visitante:", all_teams, index=None)
        # Liga é necessária para a média. Tentar inferir.
        if team_a:
            try: liga_sim = df_recent[df_recent['HomeTeam'] == team_a]['League_Custom'].mode()[0]
            except: liga_sim = None
        
        if team_a and team_b and liga_sim:
            xg_h, xg_a, str_h, str_a = calcular_xg_ponderado(df_recent, liga_sim, team_a, team_b)
            if xg_h:
                st.success(f"Simulação baseada na liga: {liga_sim}")
                matriz, probs = gerar_matriz_poisson(xg_h, xg_a)
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.metric("xG Casa", f"{xg_h:.2f}")
                    st.metric("Vitória Casa %", f"{probs['HomeWin']*100:.1f}%")
                with col_res2:
                    st.metric("xG Visitante", f"{xg_a:.2f}")
                    st.metric("Over 2.5 %", f"{probs['Over25']*100:.1f}%")
                
                # Plot rápido
                z_data = matriz
                fig = px.imshow(z_data, x=['0','1','2','3','4','5+'], y=['0','1','2','3','4','5+'], text_auto='.1f', color_continuous_scale='Magma')
                st.plotly_chart(fig, use_container_width=True)

    # ==============================================================================
    # 3. ANALISADOR DE TIMES
    # ==============================================================================
    elif menu == "🔎 Analisador de Times":
        st.header("🔎 Scout de Equipes")
        st.info("Use a Grade do Dia para ver a análise avançada V40.")

else: st.info("Carregando bases de dados...")
