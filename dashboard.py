import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .metric-card {background-color: #0e1117; border: 1px solid #262730; padding: 20px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 24px !important; font-weight: bold; color: #00ff00;}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=3600)
def load_data():
    URL_HISTORY = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/leagues-total/all_matches_combined.csv"
    URL_TODAY = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"
    
    # 1. Histórico
    try:
        s = requests.get(URL_HISTORY).content
        try:
            df = pd.read_csv(io.StringIO(s.decode('utf-8')), low_memory=False)
        except:
            df = pd.read_csv(io.StringIO(s.decode('utf-8')), sep=';', low_memory=False)
            
        df.columns = [c.strip() for c in df.columns]
        rename_map = {
            'date': 'Date', 'date_unix': 'DateUnix',
            'home_name': 'HomeTeam', 'away_name': 'AwayTeam',
            'homeGoalCount': 'FTHG', 'awayGoalCount': 'FTAG',
            'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG',
            'team_a_corners': 'HC', 'team_b_corners': 'AC'
        }
        for old, new in rename_map.items():
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)
        
        if 'Date' not in df.columns and 'DateUnix' in df.columns:
            df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
        else:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
        df_recent = df[df['Date'].dt.year >= 2024].copy()
        
        cols_stats = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HC', 'AC']
        for c in cols_stats:
            if c not in df_recent.columns: df_recent[c] = 0
            df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)
            
    except Exception as e:
        return None, None

    # 2. Jogos de Hoje
    try:
        df_today = pd.read_csv(URL_TODAY)
        rename_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
        df_today.rename(columns=rename_today, inplace=True)
        if 'HomeTeam' not in df_today.columns:
            df_today['HomeTeam'] = df_today.iloc[:, 0]
            df_today['AwayTeam'] = df_today.iloc[:, 1]
    except Exception as e:
        return None, None
        
    return df_recent, df_today

# --- PROCESSAMENTO ---
def process_matches(df_recent, df_today):
    results = []
    
    for index, row in df_today.iterrows():
        home = row.get('HomeTeam', 'Casa')
        away = row.get('AwayTeam', 'Fora')
        league = row.get('League', 'Liga')
        horario = row.get('Time', '--:--')
        
        stats_h = df_recent[df_recent['HomeTeam'] == home]
        stats_a = df_recent[df_recent['AwayTeam'] == away]
        
        if len(stats_h) >= 3 and len(stats_a) >= 3:
            prob_over15 = (((stats_h['FTHG']+stats_h['FTAG']) > 1.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 1.5).mean()) / 2
            prob_over25 = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2
            
            btts_h = ((stats_h['FTHG'] > 0) & (stats_h['FTAG'] > 0)).mean()
            btts_a = ((stats_a['FTHG'] > 0) & (stats_a['FTAG'] > 0)).mean()
            prob_btts = (btts_h + btts_a) / 2
            
            avg_corners = ( (stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean() ) / 2
            
            score = (prob_over25 * 40) + (prob_btts * 30) + (min(avg_corners, 12)/12 * 30)
            
            results.append({
                "Liga": league,
                "Horário": horario,
                "Mandante": home,
                "Visitante": away,
                "Over 1.5 (%)": round(prob_over15 * 100, 1),
                "Over 2.5 (%)": round(prob_over25 * 100, 1),
                "BTTS (%)": round(prob_btts * 100, 1),
                "Cantos (Média)": round(avg_corners, 1),
                "Score Geral": round(score, 1)
            })
            
    # CORREÇÃO DO ERRO: Se a lista estiver vazia, cria DF com colunas vazias
    if not results:
        return pd.DataFrame(columns=["Liga", "Horário", "Mandante", "Visitante", 
                                     "Over 1.5 (%)", "Over 2.5 (%)", "BTTS (%)", 
                                     "Cantos (Média)", "Score Geral"])
        
    return pd.DataFrame(results)

# --- INTERFACE ---
st.title("🧙‍♂️ Mestre dos Greens PRO")

with st.spinner('Analisando o mercado...'):
    df_recent, df_today = load_data()

if df_recent is not None and df_today is not None:
    df_final = process_matches(df_recent, df_today)
    
    # VERIFICAÇÃO SE HÁ DADOS
    if df_final.empty:
        st.warning("⚠️ O robô analisou os jogos de hoje, mas nenhum time tem histórico suficiente (mínimo 3 jogos em 2024/25) na nossa base de dados.")
        st.info("Isso é comum em dias com poucos jogos ou início de temporada.")
    else:
        # --- SIDEBAR ---
        st.sidebar.header("🔍 Filtros")
        ligas = ['Todas'] + sorted(df_final['Liga'].unique().tolist())
        liga_selecionada = st.sidebar.selectbox("Selecionar Liga", ligas)
        
        min_over25 = st.sidebar.slider("Mínimo Over 2.5 (%)", 0, 100, 50)
        min_btts = st.sidebar.slider("Mínimo BTTS (%)", 0, 100, 50)
        min_score = st.sidebar.slider("Score Mínimo", 0, 100, 0) # Mudei padrão para 0 para mostrar tudo
        
        # Filtros
        df_filtered = df_final.copy()
        if liga_selecionada != 'Todas':
            df_filtered = df_filtered[df_filtered['Liga'] == liga_selecionada]
            
        df_filtered = df_filtered[
            (df_filtered['Over 2.5 (%)'] >= min_over25) &
            (df_filtered['BTTS (%)'] >= min_btts) &
            (df_filtered['Score Geral'] >= min_score)
        ]
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Jogos Analisados", len(df_final))
        c2.metric("Jogos Filtrados", len(df_filtered))
        c3.metric("Melhor Chance Gols", f"{df_final['Over 2.5 (%)'].max()}%")
        
        st.divider()
        
        # Tabela
        if not df_filtered.empty:
            st.dataframe(
                df_filtered.sort_values(by='Score Geral', ascending=False),
                column_config={
                    "Score Geral": st.column_config.ProgressColumn("Poder do Green", format="%.1f", min_value=0, max_value=100),
                    "BTTS (%)": st.column_config.NumberColumn(format="%.1f%%"),
                    "Over 2.5 (%)": st.column_config.NumberColumn(format="%.1f%%"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Gráficos
            st.divider()
            st.subheader("📊 Raio-X")
            jogo = st.selectbox("Detalhar Jogo:", df_filtered['Mandante'] + " x " + df_filtered['Visitante'])
            if jogo:
                mandante, visitante = jogo.split(" x ")
                row = df_filtered[(df_filtered['Mandante']==mandante) & (df_filtered['Visitante']==visitante)].iloc[0]
                
                dat = pd.DataFrame({
                    'Métrica': ['Over 1.5', 'Over 2.5', 'BTTS'],
                    'Probabilidade': [row['Over 1.5 (%)'], row['Over 2.5 (%)'], row['BTTS (%)']]
                })
                fig = px.bar(dat, x='Métrica', y='Probabilidade', color='Probabilidade', range_y=[0,100], color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum jogo passou nos seus filtros. Tente diminuir a régua na barra lateral.")
else:
    st.error("Erro ao conectar com o banco de dados do GitHub.")
