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

# --- ESTILO CSS PERSONALIZADO (Tema Escuro/Verde) ---
st.markdown("""
    <style>
    .metric-card {background-color: #0e1117; border: 1px solid #262730; padding: 20px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 24px !important; font-weight: bold; color: #00ff00;}
    .header-style {font-size: 20px; font-weight: bold; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE CARREGAMENTO (CACHED) ---
@st.cache_data(ttl=3600) # Cache por 1 hora para não ficar baixando toda hora
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
            
        # Limpeza e Renomeação (Mesma lógica do Bot)
        df.columns = [c.strip() for c in df.columns]
        rename_map = {
            'date': 'Date', 'date_unix': 'DateUnix',
            'home_name': 'HomeTeam', 'away_name': 'AwayTeam',
            'homeGoalCount': 'FTHG', 'awayGoalCount': 'FTAG',
            'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG',
            'team_a_corners': 'HC', 'team_b_corners': 'AC',
            'team_a_cards_num': 'HY', 'team_b_cards_num': 'AY'
        }
        for old, new in rename_map.items():
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)
        
        if 'Date' not in df.columns and 'DateUnix' in df.columns:
            df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
        else:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
        df_recent = df[df['Date'].dt.year >= 2024].copy()
        
        # Garante números
        cols_stats = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HC', 'AC']
        for c in cols_stats:
            if c not in df_recent.columns: df_recent[c] = 0
            df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)
            
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
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
        st.error(f"Erro ao carregar agenda: {e}")
        return None, None
        
    return df_recent, df_today

# --- PROCESSAMENTO DOS DADOS ---
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
            # Cálculos
            prob_over15 = (((stats_h['FTHG']+stats_h['FTAG']) > 1.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 1.5).mean()) / 2
            prob_over25 = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2
            
            btts_h = ((stats_h['FTHG'] > 0) & (stats_h['FTAG'] > 0)).mean()
            btts_a = ((stats_a['FTHG'] > 0) & (stats_a['FTAG'] > 0)).mean()
            prob_btts = (btts_h + btts_a) / 2
            
            avg_corners = ( (stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean() ) / 2
            
            # Score de Confiança (IA Simples)
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
            
    return pd.DataFrame(results)

# --- INTERFACE PRINCIPAL ---
st.title("🧙‍♂️ Mestre dos Greens PRO")
st.markdown("### Painel de Inteligência Esportiva")

with st.spinner('Baixando dados do universo...'):
    df_recent, df_today = load_data()

if df_recent is not None and df_today is not None:
    # Processa os dados
    df_final = process_matches(df_recent, df_today)
    
    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("🔍 Filtros de Busca")
    
    # Filtro de Liga
    ligas = ['Todas'] + sorted(df_final['Liga'].unique().tolist())
    liga_selecionada = st.sidebar.selectbox("Selecionar Liga", ligas)
    
    # Filtros Deslizantes
    min_over25 = st.sidebar.slider("Mínimo Over 2.5 (%)", 0, 100, 50)
    min_btts = st.sidebar.slider("Mínimo BTTS (%)", 0, 100, 50)
    min_score = st.sidebar.slider("Score Mínimo (IA)", 0, 100, 60)
    
    # Aplicar Filtros
    df_filtered = df_final.copy()
    if liga_selecionada != 'Todas':
        df_filtered = df_filtered[df_filtered['Liga'] == liga_selecionada]
        
    df_filtered = df_filtered[
        (df_filtered['Over 2.5 (%)'] >= min_over25) &
        (df_filtered['BTTS (%)'] >= min_btts) &
        (df_filtered['Score Geral'] >= min_score)
    ]
    
    # --- KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jogos Hoje", len(df_final))
    col2.metric("Jogos Filtrados", len(df_filtered))
    col3.metric("Melhor Chance Gols", f"{df_final['Over 2.5 (%)'].max()}%" if not df_final.empty else "0%")
    col4.metric("Melhor Chance Cantos", f"{df_final['Cantos (Média)'].max()}" if not df_final.empty else "0")
    
    st.divider()
    
    # --- TABELA DE OPORTUNIDADES ---
    if not df_filtered.empty:
        st.subheader(f"📋 Lista de Oportunidades ({len(df_filtered)} jogos)")
        
        # Formatação Condicional (Highlight)
        st.dataframe(
            df_filtered.sort_values(by='Score Geral', ascending=False),
            column_config={
                "Score Geral": st.column_config.ProgressColumn(
                    "Poder do Green 🟢",
                    help="Pontuação baseada em Gols e Cantos",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "BTTS (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Over 2.5 (%)": st.column_config.NumberColumn(format="%.1f%%"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("Nenhum jogo atende aos critérios selecionados. Tente baixar a régua nos filtros laterais!")
        
    # --- ANÁLISE DETALHADA ---
    st.divider()
    st.subheader("📊 Raio-X da Partida")
    
    jogo_selecionado = st.selectbox("Escolha um jogo para ver detalhes:", df_final['Mandante'] + " x " + df_final['Visitante'])
    
    if jogo_selecionado:
        mandante, visitante = jogo_selecionado.split(" x ")
        row_game = df_final[(df_final['Mandante'] == mandante) & (df_final['Visitante'] == visitante)].iloc[0]
        
        c1, c2, c3 = st.columns([1, 2, 1])
        
        with c1:
            st.markdown(f"<h3 style='text-align: center; color: #4CAF50;'>{mandante}</h3>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<h1 style='text-align: center;'>VS</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>{row_game['Liga']} | {row_game['Horário']}</p>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<h3 style='text-align: center; color: #2196F3;'>{visitante}</h3>", unsafe_allow_html=True)

        # Gráfico Radar ou Barras
        stats_data = pd.DataFrame({
            'Métrica': ['Prob Over 2.5', 'Prob BTTS', 'Score Geral'],
            'Valor': [row_game['Over 2.5 (%)'], row_game['BTTS (%)'], row_game['Score Geral']]
        })
        
        fig = px.bar(stats_data, x='Métrica', y='Valor', color='Valor', 
                     color_continuous_scale=['red', 'yellow', 'green'], range_y=[0,100], title="Termômetro da Partida")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Não foi possível carregar os dados. Verifique a conexão com o GitHub.")
