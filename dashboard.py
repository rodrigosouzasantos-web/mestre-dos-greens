import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS PROFISSIONAL ---
st.markdown("""
    <style>
    .metric-card {background-color: #1e2130; border: 1px solid #313547; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);}
    .stProgress > div > div > div > div { background-color: #00ff00; }
    h1, h2, h3 { color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS (LINKS) ---
URLS_LIGAS = {
    "🇦🇷 Argentina Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv",
    "🇧🇪 Bélgica Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Belgium_Pro_League_2016-2025.csv",
    "🇧🇷 Brasileirão Série A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
    "🇨🇴 Colômbia Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Colombia_Primera_Liga_2016-2024.csv",
    "🇭🇷 Croácia HNL": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Croatia_HNL_2016-2025.csv",
    "🇩🇰 Dinamarca Superliga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Denmark_Superliga_2016-2025.csv",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
    "🇫🇮 Finlândia Veikkausliiga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Finland_Veikkausliiga_2016-2024.csv",
    "🇫🇷 França Ligue 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/France_Ligue_1_2016-2025.csv",
    "🇩🇪 Alemanha Bundesliga 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
    "🇩🇪 Alemanha Bundesliga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2_2016-2025.csv",
    "🇬🇷 Grécia Super League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Greece_Super_League_2016-2025.csv",
    "🇮🇹 Itália Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
    "🇮🇹 Itália Serie B": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_B_2016-2025.csv",
    "🇯🇵 Japão J1 League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Japan_J1_League_2016-2024.csv",
    "🇵🇹 Portugal 2ª Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/LigaPro_Portugal_2a_divisi%C3%B3n_2016-2025.csv",
    "🇵🇹 Portugal Primeira Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv",
    "🇲🇽 México Liga MX": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Mexico_Liga_MX_2016-2025.csv",
    "🇳🇱 Holanda Eredivisie": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
    "🇳🇴 Noruega Eliteserien": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Norway_Eliteserien_2016-2024.csv",
    "🇷🇺 Rússia Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Russian_Premier_League_2016-2025.csv",
    "🇸🇦 Arábia Saudita Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Saudi_Pro_League_2016-2025.csv",
    "🇰🇷 Coreia do Sul K-League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/South_Korea_K_League_1_2016-2024.csv",
    "🇪🇸 Espanha La Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
    "🇪🇸 Espanha La Liga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_Segunda_Divisi%C3%B3n_2016-2025.csv",
    "🇸🇪 Suécia Allsvenskan": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Sweden_Allsvenskan_2016-2024.csv",
    "🇹🇷 Turquia Süper Lig": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Turkey_S%C3%BCper_Lig_2016-2025.csv",
    "🇺🇸 USA MLS": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/USA_Major_League_Soccer_2016-2024.csv",
    "🇺🇾 Uruguai Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Uruguay_Primera_Divisi%C3%B3n_2016-2024.csv"
}

URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

# --- ENGINE DE DADOS (MOTOR V8) ---
@st.cache_data(ttl=7200) # Cache de 2 horas
def load_data():
    all_dfs = []
    
    # Barra de Progresso
    progress_text = "Conectando aos satélites..."
    my_bar = st.progress(0, text=progress_text)
    total_files = len(URLS_LIGAS)
    
    for i, (nome_amigavel, url) in enumerate(URLS_LIGAS.items()):
        try:
            # Download
            response = requests.get(url)
            if response.status_code != 200: continue
            
            content = response.content.decode('utf-8')
            try:
                df = pd.read_csv(io.StringIO(content), low_memory=False)
            except:
                df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
            
            # Padronização de Colunas
            df.columns = [c.strip().lower() for c in df.columns]
            rename_map = {
                'date': 'Date', 'date_unix': 'DateUnix',
                'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'home': 'HomeTeam', 'away': 'AwayTeam',
                'fthg': 'FTHG', 'ftag': 'FTAG', 'homegoalcount': 'FTHG', 'awaygoalcount': 'FTAG',
                'team_a_corners': 'HC', 'team_b_corners': 'AC', 'corners_home': 'HC', 'corners_away': 'AC'
            }
            df.rename(columns=rename_map, inplace=True)
            
            # Validação de Data
            if 'Date' not in df.columns:
                if 'DateUnix' in df.columns:
                    df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
                else:
                    continue # Pula se não tiver data
            
            # Adiciona Nome da Liga
            df['League_Custom'] = nome_amigavel
            
            # Seleciona Colunas Úteis
            cols_needed = ['Date', 'League_Custom', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HC', 'AC']
            for c in cols_needed:
                if c not in df.columns: df[c] = 0
            
            all_dfs.append(df[cols_needed])
            
        except Exception as e:
            pass # Segue o jogo
            
        # Atualiza barra
        pct = (i + 1) / total_files
        my_bar.progress(pct, text=f"Baixando: {nome_amigavel}...")
    
    my_bar.empty() # Some com a barra
    
    if not all_dfs: return None, None
    
    # Consolidação
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    
    # Filtro Recente (2023 em diante para performance)
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy()
    
    # Converte números
    for c in ['FTHG', 'FTAG', 'HC', 'AC']:
        df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)

    # Carrega Hoje
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        mapa_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
        df_today.rename(columns=mapa_today, inplace=True)
        if 'HomeTeam' not in df_today.columns:
             df_today['HomeTeam'] = df_today.iloc[:, 0]
             df_today['AwayTeam'] = df_today.iloc[:, 1]
    except:
        df_today = pd.DataFrame()
        
    return df_recent, df_today

# --- INÍCIO DO APP ---
st.title("🧙‍♂️ Mestre dos Greens PRO")

with st.spinner("Processando milhões de dados..."):
    df_recent, df_today = load_data()

if df_recent is not None:
    # Sidebar Info
    total_jogos = len(df_recent)
    total_ligas = len(df_recent['League_Custom'].unique())
    
    st.sidebar.markdown("### 📊 Status do Banco")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Ligas", total_ligas)
    col2.metric("Jogos", f"{total_jogos/1000:.1f}k")
    st.sidebar.divider()
    
    menu = st.sidebar.radio("Navegação", ["🎯 Jogos de Hoje", "🏆 Raio-X Ligas", "⚽ Analisador de Times"])

    # === LÓGICA DE PROBABILIDADES ===
    def calcular_probabilidades(home, away):
        # Busca Inteligente (Nome exato ou contém)
        stats_h = df_recent[df_recent['HomeTeam'] == home]
        if len(stats_h) < 3: stats_h = df_recent[df_recent['HomeTeam'].str.contains(home, case=False, na=False)]
        
        stats_a = df_recent[df_recent['AwayTeam'] == away]
        if len(stats_a) < 3: stats_a = df_recent[df_recent['AwayTeam'].str.contains(away, case=False, na=False)]
        
        if len(stats_h) < 3 or len(stats_a) < 3: return None
        
        # Métricas
        over25 = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2
        btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean()) / 2
        cantos = ((stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean()) / 2
        
        return {"Over25": over25*100, "BTTS": btts*100, "Cantos": cantos}

    # === ABA 1: JOGOS DE HOJE ===
    if menu == "🎯 Jogos de Hoje":
        st.header(f"📅 Jogos Encontrados: {len(df_today) if not df_today.empty else 0}")
        
        if not df_today.empty:
            lista_final = []
            barra = st.progress(0, text="Analisando partidas...")
            
            for idx, row in df_today.iterrows():
                h, a = row.get('HomeTeam', 'Casa'), row.get('AwayTeam', 'Fora')
                stats = calcular_probabilidades(h, a)
                
                if stats:
                    score = (stats['Over25']*0.4) + (stats['BTTS']*0.3) + (min(stats['Cantos'],12)/12*30)
                    lista_final.append({
                        "Liga": row.get('League', '-'),
                        "Horário": row.get('Time', '-'),
                        "Confronto": f"{h} x {a}",
                        "Over 2.5": stats['Over25'],
                        "BTTS": stats['BTTS'],
                        "Cantos": stats['Cantos'],
                        "Score": score
                    })
                barra.progress((idx+1)/len(df_today))
            
            barra.empty()
            
            if lista_final:
                df_front = pd.DataFrame(lista_final).sort_values('Score', ascending=False)
                
                # Filtros Visuais
                min_score = st.slider("⚖️ Filtrar por Poder do Green (Score)", 0, 100, 50)
                df_front = df_front[df_front['Score'] >= min_score]
                
                st.dataframe(
                    df_front,
                    column_config={
                        "Score": st.column_config.ProgressColumn("Poder", format="%.0f", min_value=0, max_value=100),
                        "Over 2.5": st.column_config.NumberColumn("Over 2.5", format="%.1f%%"),
                        "BTTS": st.column_config.NumberColumn("Ambas Marcam", format="%.1f%%"),
                        "Cantos": st.column_config.NumberColumn("Cantos", format="%.1f"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning("Jogos encontrados, mas sem histórico suficiente nas ligas carregadas.")
        else:
            st.info("Nenhum jogo na grade de hoje.")

    # === ABA 2: RAIO-X LIGAS ===
    elif menu == "🏆 Raio-X Ligas":
        st.subheader("🌎 Inteligência de Ligas")
        
        # Agrupa dados
        stats_liga = df_recent.groupby('League_Custom').apply(lambda x: pd.Series({
            'Jogos': len(x),
            'Média Gols': (x['FTHG']+x['FTAG']).mean(),
            'Over 2.5 (%)': ((x['FTHG']+x['FTAG']) > 2.5).mean() * 100,
            'BTTS (%)': ((x['FTHG']>0) & (x['FTAG']>0)).mean() * 100,
            'Média Cantos': (x['HC']+x['AC']).mean()
        })).sort_values('Média Gols', ascending=False).reset_index()
        
        # Gráfico Interativo
        fig = px.bar(stats_liga, x='League_Custom', y='Over 2.5 (%)', color='Média Gols',
                     title="Ligas com mais Gols (Over 2.5 + Média)", color_continuous_scale='Bluered')
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(stats_liga, hide_index=True, use_container_width=True)

    # === ABA 3: TIME ===
    elif menu == "⚽ Analisador de Times":
        st.subheader("🕵️‍♂️ Scout de Time")
        
        all_teams = sorted(list(set(df_recent['HomeTeam'].unique()) | set(df_recent['AwayTeam'].unique())))
        team_sel = st.selectbox("Digite o nome do time:", all_teams)
        
        if team_sel:
            df_t = df_recent[(df_recent['HomeTeam'] == team_sel) | (df_recent['AwayTeam'] == team_sel)].sort_values('Date', ascending=False)
            
            # KPIs
            total = len(df_t)
            vitorias = len(df_t[((df_t['HomeTeam']==team_sel)&(df_t['FTHG']>df_t['FTAG'])) | ((df_t['AwayTeam']==team_sel)&(df_t['FTAG']>df_t['FTHG']))])
            gols_marcados = df_t.apply(lambda x: x['FTHG'] if x['HomeTeam']==team_sel else x['FTAG'], axis=1).sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Partidas (Base)", total)
            c2.metric("Vitórias", vitorias)
            c3.metric("Gols Feitos", gols_marcados)
            
            st.markdown("#### 📜 Histórico Recente")
            st.dataframe(df_t[['Date', 'League_Custom', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam', 'HC', 'AC']].head(20), hide_index=True, use_container_width=True)

else:
    st.error("Erro crítico ao carregar a base de dados.")
