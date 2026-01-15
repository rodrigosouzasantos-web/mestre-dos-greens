import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mestre dos Greens PRO", page_icon="⚽", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .metric-card {background-color: #0e1117; border: 1px solid #262730; padding: 15px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 20px !important; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAMENTO (CACHED) ---
@st.cache_data(ttl=3600)
def load_data():
    # Links do Repositório
    URL_HISTORY = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/leagues-total/all_matches_combined.csv"
    URL_TODAY = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"
    
    try:
        # 1. Carregar Histórico
        s = requests.get(URL_HISTORY).content
        try:
            df = pd.read_csv(io.StringIO(s.decode('utf-8')), low_memory=False)
        except:
            df = pd.read_csv(io.StringIO(s.decode('utf-8')), sep=';', low_memory=False)
            
        # Limpeza de nomes das colunas
        df.columns = [c.strip() for c in df.columns]
        rename_map = {
            'date': 'Date', 'date_unix': 'DateUnix', 'league': 'League',
            'home_name': 'HomeTeam', 'away_name': 'AwayTeam',
            'homeGoalCount': 'FTHG', 'awayGoalCount': 'FTAG',
            'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG',
            'team_a_corners': 'HC', 'team_b_corners': 'AC',
            'team_a_cards_num': 'HY', 'team_b_cards_num': 'AY'
        }
        for old, new in rename_map.items():
            if old in df.columns: df.rename(columns={old: new}, inplace=True)
        
        # Tratamento de Data (Mais robusto)
        if 'Date' in df.columns:
            # Tenta converter forçando dia primeiro (padrão europeu/BR)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        elif 'DateUnix' in df.columns:
            df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
            
        # --- ALTERAÇÃO AQUI: Baixamos para 2023 para pegar mais ligas ---
        df_recent = df[df['Date'].dt.year >= 2023].copy()
        
        # Garante colunas numéricas (substitui erro por 0)
        cols_stats = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HC', 'AC', 'HY', 'AY']
        for c in cols_stats:
            if c not in df_recent.columns: df_recent[c] = 0
            df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)

        # 2. Carregar Jogos de Hoje
        try:
            df_today = pd.read_csv(URL_TODAY)
            rename_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
            df_today.rename(columns=rename_today, inplace=True)
            if 'HomeTeam' not in df_today.columns:
                df_today['HomeTeam'] = df_today.iloc[:, 0]
                df_today['AwayTeam'] = df_today.iloc[:, 1]
        except:
            df_today = pd.DataFrame() # Se der erro hoje, cria vazio para não quebrar o histórico
            
        return df_recent, df_today
    except Exception as e:
        st.error(f"Erro crítico ao carregar dados: {e}")
        return None, None

# --- LÓGICA DE PROCESSAMENTO ---
def process_today(df_recent, df_today):
    results = []
    if df_today.empty: return pd.DataFrame()
    
    for index, row in df_today.iterrows():
        home = row.get('HomeTeam', 'Casa')
        away = row.get('AwayTeam', 'Fora')
        league = row.get('League', 'Liga')
        horario = row.get('Time', '--:--')
        
        stats_h = df_recent[df_recent['HomeTeam'] == home]
        stats_a = df_recent[df_recent['AwayTeam'] == away]
        
        if len(stats_h) >= 3 and len(stats_a) >= 3:
            prob_over25 = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2
            btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean()) / 2
            avg_corn = ((stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean()) / 2
            score = (prob_over25 * 40) + (btts * 30) + (min(avg_corn, 12)/12 * 30)
            
            results.append({
                "Liga": league, "Horário": horario, "Mandante": home, "Visitante": away,
                "Over 2.5 (%)": round(prob_over25*100, 1), "BTTS (%)": round(btts*100, 1),
                "Cantos": round(avg_corn, 1), "Score": round(score, 1)
            })
            
    return pd.DataFrame(results)

# --- INTERFACE VISUAL ---
df_recent, df_today = load_data()

if df_recent is not None:
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4128/4128176.png", width=100)
    st.sidebar.title("Mestre dos Greens")
    
    # Mostra total de ligas carregadas para conferência
    qtd_ligas = len(df_recent['League'].unique())
    st.sidebar.markdown(f"📊 **Base de Dados:**\n{len(df_recent)} jogos de {qtd_ligas} ligas carregadas (desde 2023).")
    
    menu = st.sidebar.radio("Navegação", ["🎯 Jogos de Hoje", "🏆 Raio-X das Ligas", "⚽ Analisador de Times"])
    
    # === MÓDULO 1: JOGOS DE HOJE ===
    if menu == "🎯 Jogos de Hoje":
        st.header("🎯 Oportunidades do Dia")
        if not df_today.empty:
            df_final = process_today(df_recent, df_today)
            if not df_final.empty:
                min_score = st.slider("Filtrar por Score", 0, 100, 50)
                df_show = df_final[df_final['Score'] >= min_score].sort_values('Score', ascending=False)
                
                st.dataframe(
                    df_show,
                    column_config={
                        "Score": st.column_config.ProgressColumn("Score", format="%.1f", min_value=0, max_value=100),
                        "Over 2.5 (%)": st.column_config.NumberColumn(format="%.1f%%"),
                        "BTTS (%)": st.column_config.NumberColumn(format="%.1f%%")
                    }, use_container_width=True, hide_index=True
                )
            else:
                st.info("Hoje não há jogos com dados suficientes na base histórica.")
        else:
            st.warning("A grade de jogos de hoje está vazia ou inacessível no momento.")

    # === MÓDULO 2: RAIO-X DAS LIGAS ===
    elif menu == "🏆 Raio-X das Ligas":
        st.header("🏆 Estatísticas por Campeonato")
        
        # Agrupamento
        ligas_stats = []
        for league in sorted(df_recent['League'].unique()):
            df_l = df_recent[df_recent['League'] == league]
            # Reduzi o filtro para 5 jogos para aparecer mais ligas
            if len(df_l) >= 5: 
                total_goals = (df_l['FTHG'] + df_l['FTAG']).mean()
                over25 = ((df_l['FTHG'] + df_l['FTAG']) > 2.5).mean()
                btts = ((df_l['FTHG'] > 0) & (df_l['FTAG'] > 0)).mean()
                corners = (df_l['HC'] + df_l['AC']).mean()
                
                ligas_stats.append({
                    "Liga": league, 
                    "Jogos": len(df_l),
                    "Média Gols": round(total_goals, 2),
                    "Over 2.5 (%)": round(over25*100, 1),
                    "BTTS (%)": round(btts*100, 1),
                    "Cantos": round(corners, 1)
                })
        
        if ligas_stats:
            df_leagues = pd.DataFrame(ligas_stats)
            liga_escolhida = st.selectbox("Selecione uma Liga:", df_leagues['Liga'].unique())
            
            row = df_leagues[df_leagues['Liga'] == liga_escolhida].iloc[0]
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Jogos Analisados", row['Jogos'])
            c2.metric("Média Gols", row['Média Gols'])
            c3.metric("Chance BTTS", f"{row['BTTS (%)']}%")
            c4.metric("Média Cantos", row['Cantos'])
            
            # Gráficos
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.subheader("Gols por Jogo")
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = row['Média Gols'],
                    gauge = {'axis': {'range': [0, 5]}, 'bar': {'color': "#00ff00"}}
                ))
                st.plotly_chart(fig, use_container_width=True)
            with col_g2:
                st.subheader("Probabilidades")
                fig2 = px.bar(x=['Over 2.5', 'BTTS'], y=[row['Over 2.5 (%)'], row['BTTS (%)']], 
                              labels={'x':'Mercado', 'y':'%'}, color_discrete_sequence=['#00ccff'])
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Nenhuma liga encontrada com mais de 5 jogos desde 2023.")

    # === MÓDULO 3: ANALISADOR DE TIMES ===
    elif menu == "⚽ Analisador de Times":
        st.header("⚽ Scout de Equipes")
        
        all_teams = sorted(list(set(df_recent['HomeTeam'].unique()) | set(df_recent['AwayTeam'].unique())))
        
        if all_teams:
            team = st.selectbox("Pesquise o Time:", all_teams)
            df_t = df_recent[(df_recent['HomeTeam'] == team) | (df_recent['AwayTeam'] == team)].sort_values('Date', ascending=False)
            
            if not df_t.empty:
                st.write(f"Histórico recente: {len(df_t)} partidas encontradas")
                
                # KPIs do Time
                vitorias = len(df_t[((df_t['HomeTeam']==team) & (df_t['FTHG']>df_t['FTAG'])) | ((df_t['AwayTeam']==team) & (df_t['FTAG']>df_t['FTHG']))])
                media_gols = (df_t['FTHG'] + df_t['FTAG']).mean()
                
                k1, k2 = st.columns(2)
                k1.metric("Vitórias", vitorias)
                k2.metric("Média de Gols nos Jogos", round(media_gols, 2))
                
                st.dataframe(df_t[['Date', 'League', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam']].head(10), hide_index=True, use_container_width=True)
        else:
            st.warning("Nenhum time encontrado na base de dados.")

else:
    st.info("Aguarde... Conectando ao banco de dados do GitHub.")
