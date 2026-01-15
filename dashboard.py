import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mestre dos Greens PRO", page_icon="⚽", layout="wide")

# --- LISTA DE LIGAS (ADICIONE SUAS LIGAS AQUI!) ---
# Dica: Vá no GitHub, abra o CSV da liga, clique em 'Raw' e copie o link.
URLS_LIGAS = {
    "🇬🇧 Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/england/premier-league/matches.csv",
    "🇪🇸 La Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/spain/laliga/matches.csv",
    "🇮🇹 Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/italy/serie-a/matches.csv",
    "🇩🇪 Bundesliga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/germany/bundesliga/matches.csv",
    "🇫🇷 Ligue 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/france/ligue-1/matches.csv",
    "🇧🇷 Brasileirão A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/brazil/serie-a/matches.csv"
}

URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .metric-card {background-color: #0e1117; border: 1px solid #262730; padding: 15px; border-radius: 10px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAMENTO INTELIGENTE (MULTI-LINKS) ---
@st.cache_data(ttl=3600)
def load_data():
    all_dfs = []
    
    # 1. Loop para baixar todas as ligas
    progress_text = "Baixando ligas..."
    my_bar = st.progress(0, text=progress_text)
    
    total_links = len(URLS_LIGAS)
    for i, (nome_liga, url) in enumerate(URLS_LIGAS.items()):
        try:
            s = requests.get(url).content
            try:
                temp_df = pd.read_csv(io.StringIO(s.decode('utf-8')), low_memory=False)
            except:
                temp_df = pd.read_csv(io.StringIO(s.decode('utf-8')), sep=';', low_memory=False)
            
            # Adiciona coluna manual com nome da liga (para garantir)
            temp_df['League_Name_Custom'] = nome_liga
            all_dfs.append(temp_df)
            
        except Exception as e:
            print(f"Erro ao baixar {nome_liga}: {e}")
        
        # Atualiza barra de progresso
        my_bar.progress((i + 1) / total_links, text=f"Baixando {nome_liga}...")
            
    my_bar.empty() # Remove barra quando acabar
    
    if not all_dfs:
        return None, None

    # Juntar tudo num DataFrame só
    df = pd.concat(all_dfs, ignore_index=True)

    # 2. Limpeza e Padronização
    df.columns = [c.strip() for c in df.columns]
    rename_map = {
        'date': 'Date', 'date_unix': 'DateUnix', 
        'home_name': 'HomeTeam', 'away_name': 'AwayTeam',
        'homeGoalCount': 'FTHG', 'awayGoalCount': 'FTAG',
        'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG',
        'team_a_corners': 'HC', 'team_b_corners': 'AC'
    }
    for old, new in rename_map.items():
        if old in df.columns: df.rename(columns={old: new}, inplace=True)
    
    # Tratamento de Data
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    elif 'DateUnix' in df.columns:
        df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
        
    # Filtro de Data (Últimos 2 anos para ter histórico bom)
    df_recent = df[df['Date'].dt.year >= 2023].copy()
    
    # Numéricos
    cols_stats = ['FTHG', 'FTAG', 'HC', 'AC']
    for c in cols_stats:
        if c not in df_recent.columns: df_recent[c] = 0
        df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)

    # 3. Carregar Jogos de Hoje
    try:
        df_today = pd.read_csv(URL_HOJE)
        rename_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
        df_today.rename(columns=rename_today, inplace=True)
        if 'HomeTeam' not in df_today.columns:
            df_today['HomeTeam'] = df_today.iloc[:, 0]
            df_today['AwayTeam'] = df_today.iloc[:, 1]
    except:
        df_today = pd.DataFrame()
        
    return df_recent, df_today

# --- INTERFACE ---
df_recent, df_today = load_data()

if df_recent is not None:
    st.sidebar.title("⚽ Mestre dos Greens")
    st.sidebar.success(f"Base carregada: {len(df_recent)} jogos.")
    
    menu = st.sidebar.radio("Menu", ["🎯 Jogos de Hoje", "🏆 Raio-X Ligas", "📊 Analisador Times"])
    
    # === PROCESSAMENTO LÓGICO ===
    def get_stats(home, away):
        stats_h = df_recent[df_recent['HomeTeam'] == home]
        stats_a = df_recent[df_recent['AwayTeam'] == away]
        if len(stats_h) < 3 or len(stats_a) < 3: return None
        
        prob_over = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2
        prob_btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean()) / 2
        avg_corn = ((stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean()) / 2
        
        return {"Over25": prob_over*100, "BTTS": prob_btts*100, "Cantos": avg_corn}

    # === MENU 1: JOGOS HOJE ===
    if menu == "🎯 Jogos de Hoje":
        st.header("🎯 Jogos do Dia")
        if not df_today.empty:
            data_list = []
            for _, row in df_today.iterrows():
                stats = get_stats(row.get('HomeTeam'), row.get('AwayTeam'))
                if stats:
                    score = (stats['Over25']*0.4) + (stats['BTTS']*0.3) + (min(stats['Cantos'],12)/12*30)
                    data_list.append({
                        "Liga": row.get('League'), "Horário": row.get('Time'),
                        "Jogo": f"{row.get('HomeTeam')} x {row.get('AwayTeam')}",
                        "Over 2.5": f"{stats['Over25']:.1f}%",
                        "BTTS": f"{stats['BTTS']:.1f}%",
                        "Cantos": f"{stats['Cantos']:.1f}",
                        "Score": score
                    })
            
            if data_list:
                df_final = pd.DataFrame(data_list).sort_values("Score", ascending=False)
                st.dataframe(df_final, hide_index=True, use_container_width=True)
            else:
                st.warning("Jogos de hoje sem histórico suficiente.")
        else:
            st.info("Sem jogos na grade hoje.")

    # === MENU 2: RAIO-X LIGAS ===
    elif menu == "🏆 Raio-X Ligas":
        st.header("🏆 Comparativo de Ligas")
        # Usa o nome customizado que criamos
        col_liga = 'League_Name_Custom' if 'League_Name_Custom' in df_recent.columns else 'League'
        
        stats_ligas = []
        for league in df_recent[col_liga].unique():
            dfl = df_recent[df_recent[col_liga] == league]
            stats_ligas.append({
                "Liga": league,
                "Média Gols": round((dfl['FTHG']+dfl['FTAG']).mean(), 2),
                "Over 2.5 (%)": round(((dfl['FTHG']+dfl['FTAG'])>2.5).mean()*100, 1),
                "Cantos": round((dfl['HC']+dfl['AC']).mean(), 1)
            })
        
        st.dataframe(pd.DataFrame(stats_ligas).sort_values("Média Gols", ascending=False), hide_index=True, use_container_width=True)

    # === MENU 3: ANALISADOR TIMES ===
    elif menu == "📊 Analisador Times":
        st.header("🔎 Buscar Time")
        teams = sorted(list(set(df_recent['HomeTeam'].unique()) | set(df_recent['AwayTeam'].unique())))
        team = st.selectbox("Escolha o time:", teams)
        
        dft = df_recent[(df_recent['HomeTeam']==team)|(df_recent['AwayTeam']==team)].sort_values('Date', ascending=False)
        st.write(f"Últimos {len(dft)} jogos:")
        st.dataframe(dft[['Date', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam', 'HC', 'AC']].head(10), hide_index=True)

else:
    st.error("Erro ao carregar dados.")
