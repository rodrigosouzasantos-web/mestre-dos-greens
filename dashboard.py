import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

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

# --- CONFIGURAÇÃO TELEGRAM ---
if "TELEGRAM_TOKEN" in st.secrets and "TELEGRAM_CHAT_ID" in st.secrets:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
    telegram_status = "✅ Conectado (Secrets)"
else:
    with st.sidebar.expander("📲 Configuração Telegram"):
        TELEGRAM_TOKEN = st.text_input("Bot Token", type="password")
        TELEGRAM_CHAT_ID = st.text_input("Chat ID")
    telegram_status = "⚠️ Manual"

def enviar_telegram(mensagem):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=data)
            return True
        except: return False
    return False

# --- BANCO DE DADOS ---
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
    with st.spinner("🔄 Conectando satélites e baixando dados..."):
        for nome, url in URLS_LIGAS.items():
            try:
                r = requests.get(url)
                if r.status_code != 200: continue
                content = r.content.decode('utf-8')
                try: df = pd.read_csv(io.StringIO(content), low_memory=False)
                except: df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
                
                df.columns = [c.strip().lower() for c in df.columns]
                rename = {'date':'Date','date_unix':'DateUnix','home_name':'HomeTeam','away_name':'AwayTeam',
                          'fthg':'FTHG','ftag':'FTAG','homegoalcount':'FTHG','awaygoalcount':'FTAG',
                          'team_a_corners':'HC','team_b_corners':'AC','corners_home':'HC','corners_away':'AC',
                          'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG'}
                df.rename(columns=rename, inplace=True)
                
                if 'Date' not in df.columns and 'DateUnix' in df.columns:
                    df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
                
                df['League_Custom'] = nome
                
                cols_num = ['FTHG','FTAG','HTHG','HTAG','HC','AC']
                for c in cols_num:
                    if c not in df.columns: df[c] = 0
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                
                df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
                df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
                df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
                
                cols = ['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','HC','AC','Over05HT','Over15FT','Over25FT']
                for c in cols: 
                    if c not in df.columns: df[c] = 0
                all_dfs.append(df[cols])
            except: pass
            
    if not all_dfs: return None, None
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy().dropna()
    
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns:
             df_today['HomeTeam'] = df_today.iloc[:, 0]
             df_today['AwayTeam'] = df_today.iloc[:, 1]
    except: df_today = pd.DataFrame()
    
    return df_recent, df_today

# --- FUNÇÃO DE TIPS ---
def gerar_tip_visual(stats, prob_ia):
    tips = []
    if prob_ia >= 70: tips.append(f"🤖 IA Over 2.5 ({prob_ia:.0f}%)")
    if stats['Over15FT'] >= 80: tips.append("🛡️ Over 1.5")
    if stats['BTTS'] >= 60: tips.append("🤝 BTTS")
    if stats['Cantos'] >= 10.5: tips.append("🚩 +10 Cantos")
    if not tips: return "⚠️ Sem Padrão"
    return " | ".join(tips)

# --- IA ENGINE 🧠 ---
@st.cache_resource
def treinar_ia(df):
    team_stats = {}
    for team in pd.concat([df['HomeTeam'], df['AwayTeam']]).unique():
        games = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)]
        if len(games) < 5: continue
        avg_goals = (games['FTHG'].sum() + games['FTAG'].sum()) / len(games)
        team_stats[team] = avg_goals
        
    model_data = []
    for idx, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        if h in team_stats and a in team_stats:
            model_data.append({'H': team_stats[h], 'A': team_stats[a], 'Target': row['Over25FT']})
            
    df_train = pd.DataFrame(model_data)
    if df_train.empty: return None, None
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(df_train[['H', 'A']], df_train['Target'])
    return model, team_stats

# --- APP ---
st.title("🧙‍♂️ Mestre dos Greens PRO")

with st.spinner("Analisando dados globais..."):
    df_recent, df_today = load_data()

if df_recent is not None:
    model, team_stats = treinar_ia(df_recent)
    all_teams = sorted(list(set(df_recent['HomeTeam'].unique()) | set(df_recent['AwayTeam'].unique())))

    st.sidebar.markdown(f"## 🧭 Menu\n{telegram_status}")
    menu = st.sidebar.radio("", ["🎯 Jogos de Hoje (+ Tips)", "⚽ Analisador de Times", "🏆 Raio-X Ligas", "📡 Disparar Telegram"])
    
    # ----------------------------------------------------
    # LÓGICA DE PROCESSAMENTO (PARA USAR EM VÁRIAS ABAS)
    # ----------------------------------------------------
    lista_jogos_calculados = []
    if not df_today.empty:
        for idx, row in df_today.iterrows():
            h, a = row.get('HomeTeam', 'Casa'), row.get('AwayTeam', 'Fora')
            stats_h = df_recent[df_recent['HomeTeam'] == h]
            stats_a = df_recent[df_recent['AwayTeam'] == a]
            if len(stats_h)<3: stats_h = df_recent[df_recent['HomeTeam'].str.contains(h, case=False, na=False)]
            if len(stats_a)<3: stats_a = df_recent[df_recent['AwayTeam'].str.contains(a, case=False, na=False)]
            
            if len(stats_h)>=3 and len(stats_a)>=3:
                over25 = (((stats_h['FTHG']+stats_h['FTAG'])>2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG'])>2.5).mean())/2*100
                btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean())/2*100
                cantos = ((stats_h['HC']+stats_h['AC']).mean() + (stats_a['HC']+stats_a['AC']).mean())/2
                p_05ht = ((stats_h['Over05HT'].mean() + stats_a['Over05HT'].mean())/2)*100
                p_15ft = ((stats_h['Over15FT'].mean() + stats_a['Over15FT'].mean())/2)*100
                
                prob_ia = 0
                if model and h in team_stats and a in team_stats:
                    prob_ia = model.predict_proba([[team_stats[h], team_stats[a]]])[0][1]*100
                
                fair_odd = 100 / prob_ia if prob_ia > 0 else 0
                tip_txt = gerar_tip_visual({'Over25': over25, 'BTTS': btts, 'Cantos': cantos, 'Over15FT': p_15ft}, prob_ia)
                score = (over25*0.4)+(btts*0.3)+(min(cantos,12)/12*30)
                
                lista_jogos_calculados.append({
                    "Liga": row.get('League','-'), 
                    "Jogo": f"{h} x {a}", 
                    "Indicação (Tip)": tip_txt,
                    "Over 2.5 (IA)": prob_ia, 
                    "Odd Justa": fair_odd,
                    "Over 1.5 FT": p_15ft, 
                    "BTTS": btts, 
                    "Cantos": cantos, 
                    "Score": score
                })

    # === JOGOS DE HOJE + SIMULADOR ===
    if menu == "🎯 Jogos de Hoje (+ Tips)":
        
        # SIMULADOR
        with st.expander("🎮 Simulador Manual (IA)", expanded=False):
            c1, c2, c3 = st.columns([2,2,1])
            t1 = c1.selectbox("Casa", all_teams, index=None)
            t2 = c2.selectbox("Fora", all_teams, index=None)
            if c3.button("Calcular") and t1 and t2:
                if model:
                    p = model.predict_proba([[team_stats.get(t1,0), team_stats.get(t2,0)]])[0][1]*100
                    st.success(f"🤖 IA Over 2.5: {p:.1f}%")
                else: st.error("Erro IA")

        st.header("🎯 Grade do Dia")
        if lista_jogos_calculados:
            df_show = pd.DataFrame(lista_jogos_calculados).sort_values('Score', ascending=False)
            min_score = st.slider("⚖️ Filtrar Score", 0, 100, 50)
            st.dataframe(df_show[df_show['Score']>=min_score], column_config={
                "Over 2.5 (IA)": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "Odd Justa": st.column_config.NumberColumn(format="%.2f"),
                "Score": st.column_config.ProgressColumn(format="%.0f", min_value=0, max_value=100)
            }, hide_index=True, use_container_width=True)
        else: st.warning("Grade vazia.")

    # === ANALISADOR ===
    elif menu == "⚽ Analisador de Times":
        st.header("🕵️‍♂️ Scout")
        team = st.selectbox("Time:", all_teams, index=None, placeholder="Buscar...")
        if team:
            df_h = df_recent[df_recent['HomeTeam']==team]
            df_a = df_recent[df_recent['AwayTeam']==team]
            df_all = pd.concat([df_h, df_a]).sort_values('Date', ascending=False)
            if not df_all.empty:
                c1,c2,c3 = st.columns(3)
                c1.metric("Geral", f"{(df_all['FTHG']+df_all['FTAG']).mean():.2f} Gols")
                c2.metric("Casa", f"{df_h['FTHG'].mean() if not df_h.empty else 0:.2f}")
                c3.metric("Fora", f"{df_a['FTAG'].mean() if not df_a.empty else 0:.2f}")
                
                d_chart = pd.DataFrame({'Sit':['Casa','Casa','Fora','Fora'], 'Tipo':['Feitos','Sofridos','Feitos','Sofridos'],
                                        'Média':[df_h['FTHG'].mean() if not df_h.empty else 0, df_h['FTAG'].mean() if not df_h.empty else 0,
                                                 df_a['FTAG'].mean() if not df_a.empty else 0, df_a['FTHG'].mean() if not df_a.empty else 0]})
                st.plotly_chart(px.bar(d_chart, x='Sit', y='Média', color='Tipo', barmode='group'), use_container_width=True)
                st.dataframe(df_all.head(10), hide_index=True, use_container_width=True)

    # === RAIO-X ===
    elif menu == "🏆 Raio-X Ligas":
        st.header("🌎 Ligas")
        stats = df_recent.groupby('League_Custom').apply(lambda x: pd.Series({
            'Jogos': len(x), 'Média Gols': (x['FTHG']+x['FTAG']).mean(),
            'Over 2.5 (%)': ((x['FTHG']+x['FTAG'])>2.5).mean()*100,
            'BTTS (%)': ((x['FTHG']>0)&(x['FTAG']>0)).mean()*100,
            'Cantos': (x['HC']+x['AC']).mean()
        })).sort_values('Média Gols', ascending=False).reset_index()
        
        sel = st.multiselect("Filtrar:", sorted(stats['League_Custom'].unique()))
        if sel: stats = stats[stats['League_Custom'].isin(sel)]
        
        if not stats.empty:
            c1,c2 = st.tabs(["Gols","Cantos"])
            with c1: st.plotly_chart(px.bar(stats, x='League_Custom', y='Média Gols', color='Over 2.5 (%)', color_continuous_scale='RdYlGn'), use_container_width=True)
            with c2: st.plotly_chart(px.bar(stats.sort_values('Cantos', ascending=False), x='League_Custom', y='Cantos'), use_container_width=True)
            st.dataframe(stats, hide_index=True, use_container_width=True)

    # === TELEGRAM INTELIGENTE (NOVO) ===
    elif menu == "📡 Disparar Telegram":
        st.header("📲 Enviar Sinal")
        
        # PREENCHIMENTO AUTOMÁTICO
        opcoes_greens = []
        if lista_jogos_calculados:
            df_top = pd.DataFrame(lista_jogos_calculados).sort_values('Score', ascending=False)
            # Filtra apenas os bons (Score > 60 ou IA > 70)
            df_vip = df_top[(df_top['Score'] > 60) | (df_top['Over 2.5 (IA)'] > 70)]
            opcoes_greens = df_vip['Jogo'].tolist()
        
        jogo_selecionado = st.selectbox("💎 Escolha uma Oportunidade do Dia:", ["(Digitar Manualmente)"] + opcoes_greens)
        
        texto_padrao = ""
        if jogo_selecionado != "(Digitar Manualmente)":
            # Busca os dados do jogo selecionado
            dados_jogo = df_top[df_top['Jogo'] == jogo_selecionado].iloc[0]
            texto_padrao = f"""🔥 *ALERTA GREEN MESTRE* 🔥

⚽ **Jogo:** {dados_jogo['Jogo']}
🏆 **Liga:** {dados_jogo['Liga']}

🤖 **Inteligência Artificial:**
📈 Chance Over 2.5: {dados_jogo['Over 2.5 (IA)']:.1f}%
💡 Tip: {dados_jogo['Indicação (Tip)']}

💰 **Odd Justa (Mínima):** @{dados_jogo['Odd Justa']:.2f}
(Se a Casa pagar mais que isso, é Valor!)

🌪️ Média Cantos: {dados_jogo['Cantos']:.1f}
"""
        
        with st.form("telegram"):
            msg = st.text_area("Mensagem:", height=250, value=texto_padrao if texto_padrao else "🔥 *ALERTA GREEN*\n\n⚽ Jogo:\n📈 Entrada:\n💰 Odd:")
            if st.form_submit_button("🚀 ENVIAR AGORA"):
                if enviar_telegram(msg): st.success("Green Enviado com Sucesso!")
                else: st.error("Erro no envio.")
else: st.error("Erro dados")
