import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mestre dos Greens PRO", page_icon="⚽", layout="wide")

# --- LISTA DE LIGAS ---
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

# --- CARREGAMENTO ROBUSTO ---
@st.cache_data(ttl=3600)
def load_data():
    all_dfs = []
    
    # Barra de progresso visual
    progress_text = "Conectando ao banco de dados..."
    my_bar = st.progress(0, text=progress_text)
    total = len(URLS_LIGAS)
    
    for i, (nome_liga, url) in enumerate(URLS_LIGAS.items()):
        try:
            # 1. Baixar
            response = requests.get(url)
            response.raise_for_status() # Garante que o link funcionou
            
            # 2. Ler CSV tentando diferentes separadores
            content = response.content.decode('utf-8')
            try:
                temp_df = pd.read_csv(io.StringIO(content), low_memory=False)
            except:
                temp_df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
            
            # 3. NORMALIZAÇÃO FORÇADA (Aqui corrige o erro!)
            # Transforma tudo em minúsculo para padronizar
            temp_df.columns = [c.strip().lower() for c in temp_df.columns]
            
            # Mapeamento para nomes padrão
            mapa = {
                'date': 'Date', 'date_unix': 'DateUnix',
                'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'home': 'HomeTeam', 'away': 'AwayTeam',
                'homegoalcount': 'FTHG', 'awaygoalcount': 'FTAG', 'fthg': 'FTHG', 'ftag': 'FTAG',
                'team_a_corners': 'HC', 'team_b_corners': 'AC', 'corners_home': 'HC', 'corners_away': 'AC'
            }
            temp_df.rename(columns=mapa, inplace=True)
            
            # Garante que temos a coluna Date
            if 'Date' not in temp_df.columns:
                if 'DateUnix' in temp_df.columns:
                    temp_df['Date'] = pd.to_datetime(temp_df['DateUnix'], unit='s')
                else:
                    # Se não tiver data, pula essa liga para não quebrar o app
                    continue 

            # Marca a liga
            temp_df['League_Custom'] = nome_liga
            
            # Seleciona apenas colunas essenciais para evitar conflitos
            cols_to_keep = ['Date', 'League_Custom', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HC', 'AC']
            # Cria as que faltam preenchidas com 0
            for c in cols_to_keep:
                if c not in temp_df.columns:
                    temp_df[c] = 0
            
            all_dfs.append(temp_df[cols_to_keep])
            
        except Exception as e:
            print(f"Aviso: Erro ao carregar {nome_liga}: {e}")
            
        my_bar.progress((i + 1) / total, text=f"Lendo {nome_liga}...")
            
    my_bar.empty()
    
    if not all_dfs:
        return None, None

    # Junta tudo
    df = pd.concat(all_dfs, ignore_index=True)
    
    # Tratamento final de Data
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    
    # Filtro de Data (Desde 2023)
    df_recent = df[df['Date'].dt.year >= 2023].copy()
    
    # Garante números
    for c in ['FTHG', 'FTAG', 'HC', 'AC']:
        df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)

    # --- JOGOS DE HOJE ---
    try:
        df_today = pd.read_csv(URL_HOJE)
        # Padroniza hoje também
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        mapa_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
        df_today.rename(columns=mapa_today, inplace=True)
        
        # Garante colunas
        if 'HomeTeam' not in df_today.columns:
            df_today['HomeTeam'] = df_today.iloc[:, 0]
            df_today['AwayTeam'] = df_today.iloc[:, 1]
    except:
        df_today = pd.DataFrame()
        
    return df_recent, df_today

# --- APP ---
df_recent, df_today = load_data()

if df_recent is not None:
    st.sidebar.title("⚽ Mestre dos Greens")
    st.sidebar.info(f"Dados carregados: {len(df_recent)} partidas.")
    
    menu = st.sidebar.radio("Navegação", ["🎯 Jogos de Hoje", "🏆 Raio-X Ligas", "📊 Analisador Times"])
    
    # --- FUNÇÃO DE CÁLCULO ---
    def get_stats(home, away):
        # Busca flexível (tenta conter o nome)
        stats_h = df_recent[df_recent['HomeTeam'] == home]
        stats_a = df_recent[df_recent['AwayTeam'] == away]
        
        if len(stats_h) < 3: # Tenta buscar parcial se não achar exato
            stats_h = df_recent[df_recent['HomeTeam'].str.contains(home, case=False, na=False)]
        
        if len(stats_h) < 3 or len(stats_a) < 3: return None
        
        prob_over = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2
        prob_btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean()) / 2
        avg_corn = ((stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean()) / 2
        
        return {"Over25": prob_over*100, "BTTS": prob_btts*100, "Cantos": avg_corn}

    if menu == "🎯 Jogos de Hoje":
        st.header("🎯 Jogos do Dia")
        if not df_today.empty:
            data_list = []
            for _, row in df_today.iterrows():
                # Proteção caso falte nome do time
                h, a = row.get('HomeTeam', 'Casa'), row.get('AwayTeam', 'Fora')
                stats = get_stats(h, a)
                
                if stats:
                    score = (stats['Over25']*0.4) + (stats['BTTS']*0.3) + (min(stats['Cantos'],12)/12*30)
                    data_list.append({
                        "Liga": row.get('League', '-'), "Horário": row.get('Time', '-'),
                        "Confronto": f"{h} x {a}",
                        "Over 2.5": f"{stats['Over25']:.1f}%",
                        "BTTS": f"{stats['BTTS']:.1f}%",
                        "Cantos": f"{stats['Cantos']:.1f}",
                        "Score": score
                    })
            
            if data_list:
                df_final = pd.DataFrame(data_list).sort_values("Score", ascending=False)
                st.dataframe(df_final, hide_index=True, use_container_width=True)
            else:
                st.warning("Jogos de hoje sem histórico suficiente na base.")
        else:
            st.info("Nenhum jogo na grade de hoje.")

    elif menu == "🏆 Raio-X Ligas":
        st.header("🏆 Comparativo")
        stats_ligas = []
        for league in df_recent['League_Custom'].unique():
            dfl = df_recent[df_recent['League_Custom'] == league]
            stats_ligas.append({
                "Liga": league,
                "Gols/Jogo": round((dfl['FTHG']+dfl['FTAG']).mean(), 2),
                "Over 2.5": round(((dfl['FTHG']+dfl['FTAG'])>2.5).mean()*100, 1),
                "BTTS": round(((dfl['FTHG']>0)&(dfl['FTAG']>0)).mean()*100, 1),
                "Cantos": round((dfl['HC']+dfl['AC']).mean(), 1)
            })
        st.dataframe(pd.DataFrame(stats_ligas).sort_values("Gols/Jogo", ascending=False), hide_index=True, use_container_width=True)

    elif menu == "📊 Analisador Times":
        st.header("🔎 Buscar Time")
        teams = sorted(list(set(df_recent['HomeTeam'].unique()) | set(df_recent['AwayTeam'].unique())))
        team = st.selectbox("Time:", teams)
        dft = df_recent[(df_recent['HomeTeam']==team)|(df_recent['AwayTeam']==team)].sort_values('Date', ascending=False)
        st.dataframe(dft[['Date', 'League_Custom', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam', 'HC', 'AC']].head(10), hide_index=True)

else:
    st.error("Falha na conexão com o Banco de Dados. Tente recarregar a página.")
