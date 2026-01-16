import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go

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
    .metric-card {background-color: #1e2130; border: 1px solid #313547; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);}
    .stProgress > div > div > div > div { background-color: #00ff00; }
    div[data-testid="stMetricValue"] { font-size: 22px; color: #00ff00; }
    div[data-testid="stMetricLabel"] { font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS (LINKS) ---
URLS_LIGAS = {
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

URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

# --- CARREGAMENTO ---
@st.cache_data(ttl=7200)
def load_data():
    all_dfs = []
    progress_text = "Carregando inteligência global..."
    my_bar = st.progress(0, text=progress_text)
    total_files = len(URLS_LIGAS)
    
    for i, (nome_amigavel, url) in enumerate(URLS_LIGAS.items()):
        try:
            response = requests.get(url)
            if response.status_code != 200: continue
            content = response.content.decode('utf-8')
            try: df = pd.read_csv(io.StringIO(content), low_memory=False)
            except: df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            rename_map = {
                'date': 'Date', 'date_unix': 'DateUnix', 'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'home': 'HomeTeam', 'away': 'AwayTeam',
                'fthg': 'FTHG', 'ftag': 'FTAG', 'homegoalcount': 'FTHG', 'awaygoalcount': 'FTAG',
                'team_a_corners': 'HC', 'team_b_corners': 'AC', 'corners_home': 'HC', 'corners_away': 'AC'
            }
            df.rename(columns=rename_map, inplace=True)
            if 'Date' not in df.columns:
                if 'DateUnix' in df.columns: df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
                else: continue
            
            df['League_Custom'] = nome_amigavel
            cols_needed = ['Date', 'League_Custom', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HC', 'AC']
            for c in cols_needed: 
                if c not in df.columns: df[c] = 0
            all_dfs.append(df[cols_needed])
        except Exception: pass
        my_bar.progress((i + 1) / total_files)
    
    my_bar.empty()
    if not all_dfs: return None, None
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy()
    for c in ['FTHG', 'FTAG', 'HC', 'AC']: df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)

    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        mapa_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
        df_today.rename(columns=mapa_today, inplace=True)
        if 'HomeTeam' not in df_today.columns:
             df_today['HomeTeam'] = df_today.iloc[:, 0]
             df_today['AwayTeam'] = df_today.iloc[:, 1]
    except: df_today = pd.DataFrame()
        
    return df_recent, df_today

# --- FUNÇÃO DE TIPS ---
def gerar_tip_visual(stats):
    tips = []
    if stats['Over25'] >= 70: tips.append("⚽ Over 2.5")
    elif stats['Over25'] <= 30: tips.append("🛡️ Under 2.5")
    if stats['BTTS'] >= 65: tips.append("🤝 BTTS")
    if stats['Cantos'] >= 10.5: tips.append("🚩 +10 Cantos")
    elif stats['Cantos'] <= 8.0: tips.append("📉 -9 Cantos")
    if not tips: return "⚠️ Sem Padrão Claro"
    return " | ".join(tips)

# --- APP ---
st.title("🧙‍♂️ Mestre dos Greens PRO")

with st.spinner("Analisando dados globais..."):
    df_recent, df_today = load_data()

if df_recent is not None:
    st.sidebar.markdown("## 🧭 Menu")
    menu = st.sidebar.radio("", ["🎯 Jogos de Hoje (+ Tips)", "⚽ Analisador de Times (Detalhado)", "🏆 Raio-X Ligas (Visual)"])
    
    # ----------------------------------------------------
    # MÓDULO 1: JOGOS DE HOJE + TIPS
    # ----------------------------------------------------
    if menu == "🎯 Jogos de Hoje (+ Tips)":
        st.header("🎯 Grade do Dia & Tips da IA")
        if not df_today.empty:
            lista_final = []
            for idx, row in df_today.iterrows():
                h, a = row.get('HomeTeam', 'Casa'), row.get('AwayTeam', 'Fora')
                stats_h = df_recent[df_recent['HomeTeam'] == h]
                stats_a = df_recent[df_recent['AwayTeam'] == a]
                if len(stats_h) < 3: stats_h = df_recent[df_recent['HomeTeam'].str.contains(h, case=False, na=False)]
                if len(stats_a) < 3: stats_a = df_recent[df_recent['AwayTeam'].str.contains(a, case=False, na=False)]
                
                if len(stats_h) >= 3 and len(stats_a) >= 3:
                    over25 = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2 * 100
                    btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean()) / 2 * 100
                    cantos = ((stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean()) / 2
                    score = (over25*0.4) + (btts*0.3) + (min(cantos,12)/12*30)
                    tip_txt = gerar_tip_visual({'Over25': over25, 'BTTS': btts, 'Cantos': cantos})
                    
                    lista_final.append({
                        "Liga": row.get('League', '-'), "Hora": row.get('Time', '-'),
                        "Jogo": f"{h} x {a}", "Indicação (Tip)": tip_txt,
                        "Over 2.5": over25, "BTTS": btts, "Cantos": cantos, "Score": score
                    })
            
            if lista_final:
                df_front = pd.DataFrame(lista_final).sort_values('Score', ascending=False)
                min_score = st.slider("⚖️ Filtrar Confiança (Score)", 0, 100, 50)
                df_show = df_front[df_front['Score'] >= min_score]
                st.dataframe(
                    df_show,
                    column_config={
                        "Score": st.column_config.ProgressColumn("Confiança", format="%.0f", min_value=0, max_value=100),
                        "Over 2.5": st.column_config.NumberColumn(format="%.1f%%"),
                        "BTTS": st.column_config.NumberColumn(format="%.1f%%"),
                        "Cantos": st.column_config.NumberColumn(format="%.1f"),
                    }, hide_index=True, use_container_width=True
                )
            else: st.info("Jogos encontrados, mas sem histórico suficiente para gerar Tips.")
        else: st.warning("Sem jogos na grade hoje.")

    # ----------------------------------------------------
    # MÓDULO 2: ANALISADOR DE TIMES (HOME/AWAY)
    # ----------------------------------------------------
    elif menu == "⚽ Analisador de Times (Detalhado)":
        st.header("🕵️‍♂️ Scout Profundo de Equipes")
        
        # BUSCA INTELIGENTE DE TIMES
        all_teams = sorted(list(set(df_recent['HomeTeam'].unique()) | set(df_recent['AwayTeam'].unique())))
        
        # O campo agora começa vazio (index=None) e tem placeholder
        team = st.selectbox(
            "🔍 Pesquise o Time (Digite para filtrar):", 
            all_teams, 
            index=None, 
            placeholder="Ex: Flamengo, Real Madrid..."
        )
        
        if team:
            df_home = df_recent[df_recent['HomeTeam'] == team]
            df_away = df_recent[df_recent['AwayTeam'] == team]
            df_all = pd.concat([df_home, df_away]).sort_values('Date', ascending=False)
            if not df_all.empty:
                st.markdown(f"### 📊 Raio-X: {team}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("##### 🌍 Geral")
                    st.metric("Jogos", len(df_all))
                    st.metric("Média Gols (Total)", f"{(df_all['FTHG'] + df_all['FTAG']).mean():.2f}")
                    st.metric("BTTS %", f"{((df_all['FTHG']>0) & (df_all['FTAG']>0)).mean() * 100:.1f}%")
                with c2:
                    st.markdown("##### 🏠 Em Casa")
                    if not df_home.empty:
                        st.write(f"**Gols Pró:** {df_home['FTHG'].mean():.2f}")
                        st.write(f"**Gols Sofridos:** {df_home['FTAG'].mean():.2f}")
                        st.write(f"**Cantos Pró:** {df_home['HC'].mean():.1f}")
                    else: st.info("Sem dados em casa")
                with c3:
                    st.markdown("##### ✈️ Fora de Casa")
                    if not df_away.empty:
                        st.write(f"**Gols Pró:** {df_away['FTAG'].mean():.2f}")
                        st.write(f"**Gols Sofridos:** {df_away['FTHG'].mean():.2f}")
                        st.write(f"**Cantos Pró:** {df_away['AC'].mean():.1f}")
                    else: st.info("Sem dados fora")
                
                st.divider()
                st.subheader("📈 Comparativo: Casa x Fora")
                data_chart = pd.DataFrame({
                    'Situação': ['Casa', 'Casa', 'Fora', 'Fora'],
                    'Tipo': ['Gols Feitos', 'Gols Sofridos', 'Gols Feitos', 'Gols Sofridos'],
                    'Média': [df_home['FTHG'].mean() if not df_home.empty else 0, df_home['FTAG'].mean() if not df_home.empty else 0,
                              df_away['FTAG'].mean() if not df_away.empty else 0, df_away['FTHG'].mean() if not df_away.empty else 0]
                })
                fig = px.bar(data_chart, x='Situação', y='Média', color='Tipo', barmode='group', height=300, color_discrete_sequence=['#00ff00', '#ff0000'])
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("📜 Últimas 10 Partidas")
                st.dataframe(df_all[['Date', 'League_Custom', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam', 'HC', 'AC']].head(10), hide_index=True, use_container_width=True)

    # ----------------------------------------------------
    # MÓDULO 3: RAIO-X LIGAS (VISUAL UPGRADE + FILTRO)
    # ----------------------------------------------------
    elif menu == "🏆 Raio-X Ligas (Visual)":
        st.header("🌎 Inteligência de Campeonatos")
        
        # 1. Processamento Inicial
        stats_liga = df_recent.groupby('League_Custom').apply(lambda x: pd.Series({
            'Jogos': len(x),
            'Média Gols': (x['FTHG']+x['FTAG']).mean(),
            'Over 2.5 (%)': ((x['FTHG']+x['FTAG']) > 2.5).mean() * 100,
            'BTTS (%)': ((x['FTHG']>0) & (x['FTAG']>0)).mean() * 100,
            'Média Cantos': (x['HC']+x['AC']).mean()
        })).sort_values('Média Gols', ascending=False).reset_index()

        # 2. FILTRO DE LIGAS (Novo!)
        ligas_disponiveis = sorted(stats_liga['League_Custom'].unique())
        ligas_selecionadas = st.multiselect(
            "🔍 Filtrar Ligas (Digite para buscar e comparar):", 
            ligas_disponiveis,
            placeholder="Selecione uma ou mais ligas para filtrar..."
        )
        
        # Aplica o filtro se houver seleção
        if ligas_selecionadas:
            stats_liga = stats_liga[stats_liga['League_Custom'].isin(ligas_selecionadas)]

        if not stats_liga.empty:
            # 3. KPIs de Destaque (Baseado no Filtro)
            top_gols = stats_liga.sort_values('Média Gols', ascending=False).iloc[0]
            top_cantos = stats_liga.sort_values('Média Cantos', ascending=False).iloc[0]
            
            k1, k2, k3 = st.columns(3)
            k1.metric("🔥 Mais Goleadora (Filtro)", top_gols['League_Custom'], f"{top_gols['Média Gols']:.2f} Gols/Jogo")
            k2.metric("🚩 Mais Cantos (Filtro)", top_cantos['League_Custom'], f"{top_cantos['Média Cantos']:.1f} Cantos/Jogo")
            k3.metric("📊 Ligas Exibidas", len(stats_liga))
            st.divider()

            # 4. Gráficos
            tab_gols, tab_cantos = st.tabs(["⚽ Análise de Gols", "🚩 Análise de Cantos"])
            
            with tab_gols:
                st.subheader("Comparativo: Gols e Over 2.5")
                fig_gols = px.bar(stats_liga, x='League_Custom', y='Média Gols', 
                                 color='Over 2.5 (%)', title="Média de Gols por Liga (Cor = % Over 2.5)",
                                 color_continuous_scale='RdYlGn', height=400)
                st.plotly_chart(fig_gols, use_container_width=True)
                
            with tab_cantos:
                st.subheader("Comparativo: Escanteios")
                fig_cantos = px.bar(stats_liga.sort_values('Média Cantos', ascending=False), 
                                    x='League_Custom', y='Média Cantos', 
                                    title="Média de Escanteios por Liga",
                                    color_discrete_sequence=['#00ccff'], height=400)
                st.plotly_chart(fig_cantos, use_container_width=True)

            # 5. Tabela
            st.subheader("📋 Tabela Detalhada")
            st.dataframe(
                stats_liga,
                column_config={
                    "League_Custom": st.column_config.TextColumn("Campeonato"),
                    "Média Gols": st.column_config.NumberColumn(format="%.2f ⚽"),
                    "Over 2.5 (%)": st.column_config.ProgressColumn("Over 2.5", format="%.1f%%", min_value=0, max_value=100),
                    "BTTS (%)": st.column_config.ProgressColumn("BTTS (Ambas)", format="%.1f%%", min_value=0, max_value=100),
                    "Média Cantos": st.column_config.NumberColumn(format="%.1f 🚩"),
                },
                hide_index=True,
                use_container_width=True,
                height=500
            )
        else:
            st.warning("Nenhuma liga selecionada.")

else:
    st.error("Erro crítico ao carregar dados.")
