import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Mestre dos Greens PRO",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS VISUAL (MODERNO) ---
st.markdown("""
    <style>
    .metric-card {background-color: #1e2130; border: 1px solid #313547; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);}
    div[data-testid="stMetricValue"] { font-size: 20px; color: #00ff00; }
    div[data-testid="stMetricLabel"] { font-size: 14px; }
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

# --- DADOS (LINKS DA V29.1 PARA GARANTIR COMPATIBILIDADE) ---
URLS_LIGAS = {
    "Argentina": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv",
    "Belgica": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Belgium_Pro_League_2016-2025.csv",
    "Brasileirao": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
    "Inglaterra": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
    "Franca": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/France_Ligue_1_2016-2025.csv",
    "Alemanha": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
    "Italia": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
    "Holanda": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
    "Portugal": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv",
    "Espanha": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
    "Turquia": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Turkey_S%C3%BCper_Lig_2016-2025.csv"
}
URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

# --- CARREGAMENTO INTELIGENTE (LÓGICA V29.1) ---
@st.cache_data(ttl=3600)
def load_data():
    all_dfs = []
    # Barra de progresso visual (estilo V8)
    progress_text = "Baixando dados..."
    my_bar = st.progress(0, text=progress_text)
    total_files = len(URLS_LIGAS)

    for i, (nome, url) in enumerate(URLS_LIGAS.items()):
        try:
            r = requests.get(url)
            if r.status_code != 200: continue
            try: df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), low_memory=False)
            except: df = pd.read_csv(io.StringIO(r.content.decode('latin-1')), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            
            # Mapeamento V29 (Garante leitura correta)
            map_cols = {'homegoalcount': 'fthg', 'awaygoalcount': 'ftag', 'home_score': 'fthg', 'away_score': 'ftag',
                        'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
            df.rename(columns=map_cols, inplace=True)
            df.rename(columns={'date':'Date','home_name':'HomeTeam','away_name':'AwayTeam'}, inplace=True)
            
            for c in ['fthg','ftag','HTHG','HTAG','HC','AC']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            df.rename(columns={'fthg': 'FTHG', 'ftag': 'FTAG'}, inplace=True)
            
            # Feature Engineering
            df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
            df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            df['BTTS'] = ((df['FTHG'] > 0) & (df['FTAG'] > 0)).astype(int)
            df['League_Custom'] = nome # Importante para o Raio-X
            
            if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','Over05HT','Over15FT','Over25FT','BTTS','HC','AC']])
        except: pass
        my_bar.progress((i + 1) / total_files)

    my_bar.empty()
    full_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    full_df['Date'] = pd.to_datetime(full_df['Date'], errors='coerce')
    df_recent = full_df.dropna()
    
    # Grade de Hoje com Odds Reais (V29.1)
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns: df_today['HomeTeam'], df_today['AwayTeam'] = df_today.iloc[:, 0], df_today.iloc[:, 1]
        
        # Mapeamento de Odds (DOCX do Usuário)
        cols_odds = ['odds_ft_1', 'odds_ft_x', 'odds_ft_2', 'odds_ft_over25', 'odds_btts_yes']
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
st.title("🧙‍♂️ Mestre dos Greens PRO - Versão 30.0")

df_recent, df_today = load_data()

if not df_recent.empty:
    model, team_stats = treinar_ia(df_recent)
    
    # Abas com Ícones (Estilo V8)
    tab1, tab2, tab3 = st.tabs(["🎯 Jogos & Alertas", "⚽ Analisador de Times", "🌍 Raio-X Ligas"])
    
    # ------------------------------------------------------------------
    # TAB 1: GRADE INTELIGENTE (Lógica V29 + Visual)
    # ------------------------------------------------------------------
    with tab1:
        st.subheader("🎯 Grade do Dia & Oportunidades")
        if not df_today.empty:
            lista = []
            for idx, row in df_today.iterrows():
                h, a = row['HomeTeam'], row['AwayTeam']
                sh = df_recent[df_recent['HomeTeam'] == h]; sa = df_recent[df_recent['AwayTeam'] == a]
                if len(sh) < 3: sh = df_recent[(df_recent['HomeTeam']==h)|(df_recent['AwayTeam']==h)]
                if len(sa) < 3: sa = df_recent[(df_recent['HomeTeam']==a)|(df_recent['AwayTeam']==a)]

                if len(sh)>=3 and len(sa)>=3:
                    p_ia = model.predict_proba([[team_stats.get(h,0), team_stats.get(a,0)]])[0][1]*100 if model and h in team_stats and a in team_stats else 0
                    p_btts = (sh['BTTS'].mean() + sa['BTTS'].mean())/2*100
                    p_25ft = (sh['Over25FT'].mean() + sa['Over25FT'].mean())/2*100
                    
                    lista.append({
                        "Liga": row.get('League','-'), 
                        "Jogo": f"{h} x {a}",
                        "Odd Casa": f"{row['odds_ft_1']:.2f}" if row['odds_ft_1'] > 1 else "-",
                        "IA (Over 2.5)": p_ia, # Score numérico para ordenar
                        "Stats BTTS": f"{p_btts:.0f}%",
                        "Score_Show": f"{p_ia:.1f}%" # Texto para mostrar
                    })
            
            # Dataframe Interativo
            df_show = pd.DataFrame(lista).sort_values('IA (Over 2.5)', ascending=False)
            st.dataframe(
                df_show, 
                column_config={
                    "IA (Over 2.5)": st.column_config.ProgressColumn("Confiança IA", format="%.1f%%", min_value=0, max_value=100)
                },
                use_container_width=True, hide_index=True
            )
            
            st.divider()
            st.subheader("📡 Disparar Telegram (Manual)")
            col_sel, col_btn = st.columns([3,1])
            with col_sel:
                opcoes = [j['Jogo'] for j in lista]
                sel = st.selectbox("Escolha o jogo para enviar:", opcoes)
            with col_btn:
                st.write("") # Espaço
                st.write("") 
                if st.button("🚀 Enviar Alerta"):
                    enviar_telegram(f"📢 *Alerta Manual do Painel:* O jogo *{sel}* está sendo analisado agora! Fique de olho!")
                    st.success("Enviado com sucesso!")
        else: st.warning("Aguardando grade de jogos...")

    # ------------------------------------------------------------------
    # TAB 2: ANALISADOR DE TIMES (Visual V8 - Scouts Detalhados)
    # ------------------------------------------------------------------
    with tab2:
        st.subheader("🔎 Scout Profundo de Equipes")
        
        # Busca Inteligente
        all_teams = sorted(pd.concat([df_recent['HomeTeam'], df_recent['AwayTeam']]).unique())
        sel_time = st.selectbox("🔍 Pesquise o Time:", all_teams, index=None, placeholder="Digite para filtrar...")
        
        if sel_time:
            df_home = df_recent[df_recent['HomeTeam'] == sel_time]
            df_away = df_recent[df_recent['AwayTeam'] == sel_time]
            df_all = pd.concat([df_home, df_away]).sort_values('Date', ascending=False)
            
            if not df_all.empty:
                st.markdown(f"### 📊 Raio-X: {sel_time}")
                
                # Métricas em Colunas (Estilo V8)
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("##### 🌍 Geral")
                    st.metric("Jogos", len(df_all))
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
                
                # Gráfico Comparativo (Plotly)
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

    # ------------------------------------------------------------------
    # TAB 3: RAIO-X LIGAS (Visual V8 - Filtros e Barras)
    # ------------------------------------------------------------------
    with tab3:
        st.subheader("🌎 Inteligência de Campeonatos")
        
        # 1. Processamento
        stats_liga = df_recent.groupby('League_Custom').apply(lambda x: pd.Series({
            'Jogos': len(x),
            'Média Gols': (x['FTHG']+x['FTAG']).mean(),
            'Over 2.5 (%)': ((x['FTHG']+x['FTAG']) > 2.5).mean() * 100,
            'BTTS (%)': ((x['FTHG']>0) & (x['FTAG']>0)).mean() * 100,
            'Média Cantos': (x['HC']+x['AC']).mean()
        })).reset_index()

        # 2. FILTRO (O Grande Diferencial da V8)
        ligas_disponiveis = sorted(stats_liga['League_Custom'].unique())
        ligas_sel = st.multiselect("🔍 Filtrar Ligas:", ligas_disponiveis, placeholder="Selecione para comparar...")
        
        if ligas_sel:
            stats_liga = stats_liga[stats_liga['League_Custom'].isin(ligas_sel)]

        if not stats_liga.empty:
            # 3. Gráficos
            tab_g, tab_c = st.tabs(["⚽ Gols", "🚩 Cantos"])
            with tab_g:
                fig_gols = px.bar(stats_liga.sort_values('Média Gols', ascending=False), x='League_Custom', y='Média Gols', color='Over 2.5 (%)', title="Média de Gols (Cor = % Over 2.5)", color_continuous_scale='RdYlGn')
                st.plotly_chart(fig_gols, use_container_width=True)
            with tab_c:
                fig_cantos = px.bar(stats_liga.sort_values('Média Cantos', ascending=False), x='League_Custom', y='Média Cantos', title="Média de Escanteios", color_discrete_sequence=['#00ccff'])
                st.plotly_chart(fig_cantos, use_container_width=True)

            # 4. Tabela Visual (Sem matplotlib para não dar erro)
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

else: st.info("Carregando Banco de Dados Inteligente...")
