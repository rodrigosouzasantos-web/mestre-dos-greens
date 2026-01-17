import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier
from PIL import Image # Importante para abrir a logo

# --- CARREGA A LOGO ---
try:
    # Tenta carregar a imagem 'logo.jpg' que deve estar na mesma pasta
    logo = Image.open("logo.jpg.jpg") 
    icon_page = logo
except:
    # Se não achar a imagem, usa um emoji de bola como fallback
    logo = None
    icon_page = "⚽"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO",
    page_icon=icon_page, # Aqui define o ícone da aba do navegador
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS VISUAL ---
st.markdown("""
    <style>
    .metric-card {background-color: #1e2130; border: 1px solid #313547; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);}
    div[data-testid="stMetricValue"] { font-size: 20px; color: #00ff00; }
    div[data-testid="stMetricLabel"] { font-size: 14px; }
    /* Ajuste para centralizar a logo na sidebar se quiser */
    [data-testid="stSidebar"] > div:first-child { text-align: center; }
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
# 1. BANCO DE DADOS HISTÓRICO (DADOS PESADOS)
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

# ==============================================================================
# 2. BANCO DE DADOS ATUAL (DADOS "FRESCOS") - COLE SEUS LINKS AQUI
# ==============================================================================
URLS_ATUAIS = {
    # EXEMPLO: "Inglaterra Atual": "LINK_DA_PL_2025_ATUALIZADO.csv",
    # Cole aqui os links da temporada atual se tiver
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
    
    # Lista combinada de links (Histórico + Atual)
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
            
            # Mapeamento
            map_cols = {'homegoalcount': 'fthg', 'awaygoalcount': 'ftag', 'home_score': 'fthg', 'away_score': 'ftag',
                        'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
            df.rename(columns=map_cols, inplace=True)
            
            if 'date' not in df.columns and 'date_unix' in df.columns:
                df['date'] = pd.to_datetime(df['date_unix'], unit='s')
            
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
            
            # Remove " Atual" do nome se vier da lista nova, para manter consistência no Raio-X
            nome_limpo = nome.replace(" Atual", "")
            df['League_Custom'] = nome_limpo
            
            if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','Over05HT','Over15FT','Over25FT','BTTS','HomeWin','AwayWin','HC','AC']])
        except: pass
        my_bar.progress((i + 1) / len(TODAS_URLS))

    my_bar.empty()
    full_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    
    # --- FILTRO ANTI-DUPLICIDADE (CRUCIAL PARA V33) ---
    # Se você adicionar links atuais, pode ter jogo repetido. Isso remove a cópia mais antiga.
    full_df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last', inplace=True)
    
    # Filtro de Data (2023+)
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy()
    
    # Grade de Hoje com Odds Reais (V32 - DOCX)
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns: df_today['HomeTeam'], df_today['AwayTeam'] = df_today.iloc[:, 0], df_today.iloc[:, 1]
        
        cols_odds = [
            'odds_ft_1', 'odds_ft_x', 'odds_ft_2', 'odds_ft_over25', 'odds_btts_yes',
            'odds_ft_over15', 'odds_1st_half_over05', 'odds_corners_over_95'
        ]
        for c in cols_odds:
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

# --- APP PRINCIPAL ---
st.title("🧙‍♂️ Mestre dos Greens PRO - Versão 33.0 (Integrada)")

df_recent, df_today = load_data()

if not df_recent.empty:
    model, team_stats = treinar_ia(df_recent)
    
    # --- MOSTRA A LOGO NA SIDEBAR ---
    if logo:
        st.sidebar.image(logo, use_column_width=True)
        st.sidebar.markdown("---") # Uma linha separadora para ficar bonito
        
    st.sidebar.markdown("## 🧭 Navegação")
    menu = st.sidebar.radio("Selecione:", ["🎯 Grade & Oportunidades", "🔎 Analisador de Times", "🌍 Raio-X Ligas"])
    
    # ------------------------------------------------------------------
    # TAB 1: GRADE DO DIA
    # ------------------------------------------------------------------
    if menu == "🎯 Grade & Oportunidades":
        st.header("🎯 Grade do Dia & Oportunidades")
        
        if not df_today.empty:
            lista_visual = [] 
            dados_para_envio = {} 

            for idx, row in df_today.iterrows():
                h, a = row['HomeTeam'], row['AwayTeam']
                sh = df_recent[df_recent['HomeTeam'] == h]; sa = df_recent[df_recent['AwayTeam'] == a]
                if len(sh) < 3: sh = df_recent[(df_recent['HomeTeam']==h)|(df_recent['AwayTeam']==h)]
                if len(sa) < 3: sa = df_recent[(df_recent['HomeTeam']==a)|(df_recent['AwayTeam']==a)]

                if len(sh)>=3 and len(sa)>=3:
                    p_ia = model.predict_proba([[team_stats.get(h,0), team_stats.get(a,0)]])[0][1]*100 if model and h in team_stats and a in team_stats else 0
                    p_05ht = (sh['Over05HT'].mean() + sa['Over05HT'].mean())/2*100
                    p_15ft = (sh['Over15FT'].mean() + sa['Over15FT'].mean())/2*100
                    p_btts = (sh['BTTS'].mean() + sa['BTTS'].mean())/2*100
                    avg_corners = (sh['HC'].mean() + sa['AC'].mean())
                    wh = sh['HomeWin'].mean() * 100
                    wa = sa['AwayWin'].mean() * 100
                    wd = 100 - (wh + wa)
                    if wd < 0: wd = 0
                    
                    tips_list = []
                    if p_ia >= 60: tips_list.append("🤖 Over 2.5")
                    if p_15ft >= 80: tips_list.append("🛡️ Over 1.5")
                    if p_05ht >= 75: tips_list.append("⚡ 0.5 HT")
                    if p_btts >= 60: tips_list.append("🤝 BTTS")
                    if avg_corners >= 9.5: tips_list.append("🚩 Cantos")
                    
                    tips_str = " | ".join(tips_list) if tips_list else "⚠️ S/ Padrão"
                    
                    lista_visual.append({
                        "Liga": row.get('League','-'), "Jogo": f"{h} x {a}",
                        "Tip Visual": tips_str, "IA (2.5)": p_ia, "1.5 FT": p_15ft,
                        "0.5 HT": p_05ht, "BTTS": p_btts, "Cantos": avg_corners, "Score": p_ia
                    })
                    
                    dados_para_envio[f"{h} x {a}"] = {
                        "League": row.get('League','-'), "Time": row.get('Time','--:--'),
                        "Home": h, "Away": a, "Tips": tips_list,
                        "Prob_IA": p_ia, "Prob_15FT": p_15ft, "Prob_05HT": p_05ht, 
                        "Prob_BTTS": p_btts, "Avg_Corners": avg_corners,
                        "Prob_H": wh, "Prob_D": wd, "Prob_A": wa,
                        "Odd_Real_H": row.get('odds_ft_1', 0), "Odd_Real_D": row.get('odds_ft_x', 0), "Odd_Real_A": row.get('odds_ft_2', 0),
                        "Odd_Real_15FT": row.get('odds_ft_over15', 0), "Odd_Real_25FT": row.get('odds_ft_over25', 0),
                        "Odd_Real_BTTS": row.get('odds_btts_yes', 0), "Odd_Real_HT": row.get('odds_1st_half_over05', 0)
                    }

            df_show = pd.DataFrame(lista_visual).sort_values('Score', ascending=False)
            
            st.dataframe(
                df_show,
                column_config={
                    "Tip Visual": st.column_config.TextColumn("Destaques"),
                    "IA (2.5)": st.column_config.ProgressColumn("Over 2.5 (IA)", format="%.1f%%", min_value=0, max_value=100),
                    "1.5 FT": st.column_config.ProgressColumn("Over 1.5", format="%.1f%%", min_value=0, max_value=100),
                    "0.5 HT": st.column_config.ProgressColumn("Over 0.5 HT", format="%.1f%%", min_value=0, max_value=100),
                    "BTTS": st.column_config.ProgressColumn("Ambas Marcam", format="%.1f%%", min_value=0, max_value=100),
                    "Cantos": st.column_config.NumberColumn("Cantos (Média)", format="%.1f"),
                },
                use_container_width=True, hide_index=True
            )
            
            st.divider()
            st.markdown("### 📡 Disparar Alerta (Manual)")
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                jogos_disp = list(dados_para_envio.keys())
                jogo_alvo = st.selectbox("Selecione o jogo para enviar:", jogos_disp)
            
            with col_btn:
                st.write("") 
                st.write("")
                if st.button("🚀 Enviar para Telegram"):
                    if jogo_alvo in dados_para_envio:
                        d = dados_para_envio[jogo_alvo]
                        destaque_str = " | ".join(d['Tips']) if d['Tips'] else "Análise Manual"
                        header = "⚽ ANÁLISE PRÉ-JOGO (MANUAL)"
                        if d['Prob_A'] >= 50 and d['Prob_H'] <= 40: header = "🦓 ALERTA DE ZEBRA"
                        elif d['Prob_H'] >= 80: header = "🔥 SUPER FAVORITO (CASA)"
                        
                        def show_odd(real, fair_prob):
                            fair_odd = get_odd_justa(fair_prob)
                            if real > 1.0: return f"@{real:.2f}"
                            return f"Justa @{fair_odd:.2f}"

                        txt = f"{header}\n"
                        txt += f"🏆 *{d['League'].upper()}*\n\n"
                        txt += f"⚔️ *{d['Home']}* vs *{d['Away']}*\n"
                        txt += f"⏰ {d['Time']}\n\n"
                        txt += f"🎯 *Destaque:* {destaque_str}\n\n"
                        
                        txt += f"📊 *PROBABILIDADES (1x2):*\n"
                        txt += f"🏠 Casa: {show_odd(d['Odd_Real_H'], d['Prob_H'])} ({d['Prob_H']:.0f}%)\n"
                        txt += f"⚖️ Empate: {show_odd(d['Odd_Real_D'], d['Prob_D'])} ({d['Prob_D']:.0f}%)\n"
                        txt += f"✈️ Visitante: {show_odd(d['Odd_Real_A'], d['Prob_A'])} ({d['Prob_A']:.0f}%)\n\n"
                        
                        txt += f"⚽ *MERCADOS DE GOLS:*\n"
                        txt += f"⚡ 0.5 HT: {show_odd(d['Odd_Real_HT'], d['Prob_05HT'])} ({d['Prob_05HT']:.0f}%)\n"
                        txt += f"🛡️ 1.5 FT: {show_odd(d['Odd_Real_15FT'], d['Prob_15FT'])} ({d['Prob_15FT']:.0f}%)\n"
                        txt += f"🔥 2.5 FT: {show_odd(d['Odd_Real_25FT'], d['Prob_IA'])} (IA: {d['Prob_IA']:.0f}%)\n"
                        txt += f"🤝 Ambas: {show_odd(d['Odd_Real_BTTS'], d['Prob_BTTS'])} ({d['Prob_BTTS']:.0f}%)\n"
                        
                        if d['Avg_Corners'] >= 8.0:
                            txt += f"\n🚩 *CANTOS:* Avg {d['Avg_Corners']:.1f}\n"

                        txt += "--------------------------------\n"
                        txt += "⚠️ Aposte com Responsabilidade\n\n"
                        txt += "🤖 *Mestre dos Greens (Painel)*"
                        
                        if enviar_telegram(txt): st.success(f"Alerta de {d['Home']} x {d['Away']} enviado!")
                        else: st.error("Erro ao enviar.")
        else: st.warning("Aguardando dados da grade...")

    # ==============================================================================
    # 2. ANALISADOR DE TIMES
    # ==============================================================================
    elif menu == "🔎 Analisador de Times":
        st.header("🔎 Scout Profundo de Equipes")
        
        all_teams = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        sel_time = st.selectbox("Pesquise o Time:", all_teams, index=None, placeholder="Digite para filtrar...")
        
        if sel_time:
            df_home = df_recent[df_recent['HomeTeam'] == sel_time]
            df_away = df_recent[df_recent['AwayTeam'] == sel_time]
            df_all = pd.concat([df_home, df_away]).sort_values('Date', ascending=False)
            
            if not df_all.empty:
                st.markdown(f"### 📊 Raio-X: {sel_time}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("##### 🌍 Geral")
                    st.metric("Jogos (2023+)", len(df_all))
                    st.metric("Média Gols (Total)", f"{(df_all['FTHG'] + df_all['FTAG']).mean():.2f}")
                    st.metric("BTTS %", f"{((df_all['FTHG']>0) & (df_all['FTAG']>0)).mean() * 100:.1f}%")
                with c2:
                    st.markdown("##### 🏠 Em Casa")
                    if not df_home.empty:
                        st.write(f"⚽ Pró: {df_home['FTHG'].mean():.2f}")
                        st.write(f"🛡️ Sofridos: {df_home['FTAG'].mean():.2f}")
                        st.write(f"🚩 Cantos: {df_home['HC'].mean():.1f}")
                    else: st.info("-")
                with c3:
                    st.markdown("##### ✈️ Fora de Casa")
                    if not df_away.empty:
                        st.write(f"⚽ Pró: {df_away['FTAG'].mean():.2f}")
                        st.write(f"🛡️ Sofridos: {df_away['FTHG'].mean():.2f}")
                        st.write(f"🚩 Cantos: {df_away['AC'].mean():.1f}")
                    else: st.info("-")
                
                st.divider()
                st.subheader("📈 Comparativo: Casa x Fora")
                data_chart = pd.DataFrame({
                    'Situação': ['Casa', 'Casa', 'Fora', 'Fora'],
                    'Tipo': ['Gols Feitos', 'Gols Sofridos', 'Gols Feitos', 'Gols Sofridos'],
                    'Média': [df_home['FTHG'].mean() if not df_home.empty else 0, df_home['FTAG'].mean() if not df_home.empty else 0,
                              df_away['FTAG'].mean() if not df_away.empty else 0, df_away['FTHG'].mean() if not df_away.empty else 0]
                })
                fig = px.bar(data_chart, x='Situação', y='Média', color='Tipo', barmode='group', height=300, color_discrete_sequence=['#00ff00', '#ff4444'])
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📜 Últimas 10 Partidas")
                st.dataframe(df_all[['Date', 'League_Custom', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam']].head(10), hide_index=True, use_container_width=True)

    # ==============================================================================
    # 3. RAIO-X LIGAS
    # ==============================================================================
    elif menu == "🌍 Raio-X Ligas":
        st.header("🌎 Inteligência de Campeonatos")
        
        stats_liga = df_recent.groupby('League_Custom').apply(lambda x: pd.Series({
            'Jogos': len(x),
            'Média Gols': (x['FTHG']+x['FTAG']).mean(),
            'Over 2.5 (%)': ((x['FTHG']+x['FTAG']) > 2.5).mean() * 100,
            'BTTS (%)': ((x['FTHG']>0) & (x['FTAG']>0)).mean() * 100,
            'Média Cantos': (x['HC']+x['AC']).mean()
        })).reset_index()

        ligas_disponiveis = sorted(stats_liga['League_Custom'].unique())
        ligas_sel = st.multiselect("🔍 Filtrar Ligas:", ligas_disponiveis, placeholder="Selecione para comparar...")
        
        if ligas_sel:
            stats_liga = stats_liga[stats_liga['League_Custom'].isin(ligas_sel)]

        if not stats_liga.empty:
            tab_g, tab_c = st.tabs(["⚽ Gols", "🚩 Cantos"])
            with tab_g:
                fig_gols = px.bar(stats_liga.sort_values('Média Gols', ascending=False), x='League_Custom', y='Média Gols', color='Over 2.5 (%)', title="Média de Gols (Cor = % Over 2.5)", color_continuous_scale='RdYlGn')
                st.plotly_chart(fig_gols, use_container_width=True)
            with tab_c:
                fig_cantos = px.bar(stats_liga.sort_values('Média Cantos', ascending=False), x='League_Custom', y='Média Cantos', title="Média de Escanteios", color_discrete_sequence=['#00ccff'])
                st.plotly_chart(fig_cantos, use_container_width=True)

            st.dataframe(
                stats_liga.sort_values('Média Gols', ascending=False),
                column_config={
                    "League_Custom": st.column_config.TextColumn("Campeonato"),
                    "Média Gols": st.column_config.NumberColumn(format="%.2f ⚽"),
                    "Over 2.5 (%)": st.column_config.ProgressColumn("Over 2.5", format="%.1f%%", min_value=0, max_value=100),
                    "BTTS (%)": st.column_config.ProgressColumn("BTTS", format="%.1f%%", min_value=0, max_value=100),
                    "Média Cantos": st.column_config.NumberColumn(format="%.1f 🚩"),
                },
                hide_index=True, use_container_width=True
            )
        else:
            st.info("Selecione as ligas acima para visualizar os dados.")

else: st.info("Carregando Inteligência Global (2016-2025)...")
