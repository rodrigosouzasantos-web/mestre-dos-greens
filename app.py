import pandas as pd
import requests
import io
import time
import os
from scipy.stats import poisson
from datetime import datetime, timedelta

# ==============================================================================
# ⚙️ CONFIGURAÇÕES E SEGREDOS
# ==============================================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "SEU_TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "SEU_ID_AQUI")

HORA_INICIO = 8
HORA_FIM = 22
ARQUIVO_CONTROLE = "controle_envios.txt"

# ==============================================================================
# 📂 BANCO DE DADOS (CÓPIA EXATA DO DASHBOARD V66.9)
# ==============================================================================
def load_data_robot():
    print("📥 Baixando e Sincronizando dados com o Dashboard...")
    
    # 1. LISTA COMPLETA (HISTÓRICAS)
    URLS_HISTORICAS = {
        "Argentina Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv",
        "Belgica Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Belgium_Pro_League_2016-2025.csv",
        "Brasileirao Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
        "Colombia Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Colombia_Primera_Liga_2016-2024.csv",
        "Inglaterra Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
        "Franca Ligue 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/France_Ligue_1_2016-2025.csv",
        "Alemanha Bundesliga 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
        "Alemanha Bundesliga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2_2016-2025.csv",
        "Italia Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
        "Italia Serie B": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_B_2016-2025.csv",
        "Japao J1 League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Japan_J1_League_2016-2024.csv",
        "Portugal 2 Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/LigaPro_Portugal_2a_divisi%C3%B3n_2016-2025.csv",
        "Portugal Primeira Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv",
        "Holanda Eredivisie": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
        "Noruega Eliteserien": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Norway_Eliteserien_2016-2024.csv",
        "Arabia Saudita Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Saudi_Pro_League_2016-2025.csv",
        "Coreia do Sul K-League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/South_Korea_K_League_1_2016-2024.csv",
        "Espanha La Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
        "Espanha La Liga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_Segunda_Divisi%C3%B3n_2016-2025.csv",
        "Turquia Super Lig": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Turkey_S%C3%BCper_Lig_2025-2026.csv",
        "USA MLS": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/USA_Major_League_Soccer_2025.csv"
    }

    # 2. LISTA COMPLETA (ATUAIS - PARA DADOS RECENTES)
    URLS_ATUAIS = {
        "Argentina Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Argentina_Primera_Divisi%C3%B3n_2025.csv",
        "Belgica Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Belgium_Pro_League_2025-2026.csv",
        "Brasileirao Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2025-2026.csv",
        "Colombia Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Colombia_Primera_Liga_2025.csv",
        "Inglaterra Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/England_Premier_League_2025-2026.csv",
        "Franca Ligue 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/France_Ligue_1_2025-2026.csv",
        "Alemanha Bundesliga 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Germany_Bundesliga_2025-2026.csv",
        "Alemanha Bundesliga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Germany_Bundesliga_2_2025-2026.csv",
        "Italia Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Italy_Serie_A_2025-2026.csv",
        "Italia Serie B": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Italy_Serie_B_2025-2026.csv",
        "Japao J1 League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Japan_J1_League_2025.csv",
        "Liga Portugal": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Liga_Portugal_2025-2026.csv",
        "Holanda Eredivisie": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Netherlands_Eredivisie_2025-2026.csv",
        "Noruega Eliteserien": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Norway_Eliteserien_2025.csv",
        "Arabia Saudita Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Saudi_Pro_League_2025-2026.csv",
        "Coreia do Sul K-League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/South_Korea_K_League_1_2025.csv",
        "Espanha La Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Spain_La_Liga_2025-2026.csv",
        "Espanha La Liga 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Spain_Segunda_Divisi%C3%B3n_2025-2026.csv",
        "Turquia Super Lig": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Turkey_S%C3%BCper_Lig_2025-2026.csv",
        "USA MLS": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/USA_Major_League_Soccer_2025.csv"
    }
    
    URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

    all_dfs = []

    # 1. Carrega Histórico
    for name, url in URLS_HISTORICAS.items():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
                df.columns = [c.strip().lower() for c in df.columns]
                map_cols = {'homegoalcount':'fthg', 'awaygoalcount':'ftag', 'home_score':'fthg', 'away_score':'ftag', 'ht_goals_team_a':'HTHG', 'ht_goals_team_b':'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
                df.rename(columns=map_cols, inplace=True)
                if 'date_unix' in df.columns: df['date'] = pd.to_datetime(df['date_unix'], unit='s')
                df.rename(columns={'date':'Date', 'home_name':'HomeTeam', 'away_name':'AwayTeam', 'fthg':'FTHG', 'ftag':'FTAG'}, inplace=True)
                for c in ['FTHG','FTAG','HTHG','HTAG','HC','AC']: 
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                df['League_Custom'] = name
                if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','HC','AC']])
        except: continue

    # 2. Carrega Atual (Para garantir dados recentes de ligas ativas)
    for name, url in URLS_ATUAIS.items():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
                df.columns = [c.strip().lower() for c in df.columns]
                map_cols = {'homegoalcount':'fthg', 'awaygoalcount':'ftag', 'home_score':'fthg', 'away_score':'ftag', 'ht_goals_team_a':'HTHG', 'ht_goals_team_b':'HTAG', 'team_a_corners': 'HC', 'team_b_corners': 'AC'}
                df.rename(columns=map_cols, inplace=True)
                if 'date_unix' in df.columns: df['date'] = pd.to_datetime(df['date_unix'], unit='s')
                df.rename(columns={'date':'Date', 'home_name':'HomeTeam', 'away_name':'AwayTeam', 'fthg':'FTHG', 'ftag':'FTAG'}, inplace=True)
                for c in ['FTHG','FTAG','HTHG','HTAG','HC','AC']: 
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                df['League_Custom'] = name
                if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','HC','AC']])
        except: continue

    df_recent = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    if not df_recent.empty:
        df_recent['Date'] = pd.to_datetime(df_recent['Date'], dayfirst=True, errors='coerce')
        df_recent.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last', inplace=True)
        # Filtro de data igual ao Dashboard (>= 2023)
        df_recent = df_recent[df_recent['Date'].dt.year >= 2023].copy()

    # 3. Jogos de Hoje
    try:
        r_today = requests.get(URL_HOJE, timeout=10)
        df_today = pd.read_csv(io.StringIO(r_today.content.decode('utf-8')))
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        
        if 'date_unix' in df_today.columns:
            df_today['match_time'] = pd.to_datetime(df_today['date_unix'], unit='s') - timedelta(hours=3)
        elif 'date' in df_today.columns:
            df_today['match_time'] = pd.to_datetime(df_today['date']) - timedelta(hours=3)
        else:
            df_today['match_time'] = datetime.now() - timedelta(hours=3)
    except: df_today = pd.DataFrame()

    return df_recent, df_today

# ==============================================================================
# 🧮 MOTOR MATEMÁTICO (CLONE DO DASHBOARD)
# ==============================================================================

def get_weighted_avg(full_df, venue_df, col_name):
    # Mesma função de média ponderada do Dashboard
    w_geral = full_df[col_name].mean()
    w_venue = venue_df[col_name].mean() if not venue_df.empty else w_geral
    w_10 = full_df.tail(10)[col_name].mean()
    w_5 = full_df.tail(5)[col_name].mean()
    return (w_geral * 0.10) + (w_venue * 0.40) + (w_10 * 0.20) + (w_5 * 0.30)

def get_avg_corners(df_recent, home, away):
    df_h = df_recent[df_recent['HomeTeam'] == home]
    df_a = df_recent[df_recent['AwayTeam'] == away]
    if df_h.empty or df_a.empty: return 10.0
    avg_h = df_h['HC'].mean() + df_h['AC'].mean()
    avg_a = df_a['HC'].mean() + df_a['AC'].mean()
    return (avg_h + avg_a) / 2

def calcular_xg_robot(df_historico, home, away):
    # Tenta achar a liga exatamente como o Dashboard faz
    try: 
        league = df_historico[df_historico['HomeTeam'] == home]['League_Custom'].mode()[0]
    except: 
        if home in df_historico['HomeTeam'].unique(): 
            league = df_historico[df_historico['HomeTeam'] == home].iloc[-1]['League_Custom']
        else: return None, None, None # Time novo ou sem dados

    df_league = df_historico[df_historico['League_Custom'] == league]
    if df_league.empty: return None, None, None
    
    avg_h = df_league['FTHG'].mean()
    avg_a = df_league['FTAG'].mean()
    
    # Filtros de Home/Away iguais ao Dashboard
    df_h_all = df_historico[(df_historico['HomeTeam'] == home) | (df_historico['AwayTeam'] == home)].sort_values('Date')
    df_a_all = df_historico[(df_historico['HomeTeam'] == away) | (df_historico['AwayTeam'] == away)].sort_values('Date')
    df_h_home = df_historico[df_historico['HomeTeam'] == home]
    df_a_away = df_historico[df_historico['AwayTeam'] == away]
    
    if len(df_h_all) < 5 or len(df_a_all) < 5: return None, None, None # Mínimo 5 jogos (Dashboard usa 5)
    
    # Cálculo de Força (Ataque e Defesa)
    att_h = get_weighted_avg(df_h_all, df_h_home, 'FTHG')
    def_a = get_weighted_avg(df_a_all, df_a_away, 'FTHG') # Defesa Visitante = Gols que Home costuma fazer neles
    att_a = get_weighted_avg(df_a_all, df_a_away, 'FTAG')
    def_h = get_weighted_avg(df_h_all, df_h_home, 'FTAG') # Defesa Mandante = Gols que Away costuma fazer neles
    
    # Cálculo Poisson
    strength_att_h = att_h / avg_h if avg_h > 0 else 1.0
    strength_def_a = def_a / avg_h if avg_h > 0 else 1.0
    xg_h = strength_att_h * strength_def_a * avg_h

    strength_att_a = att_a / avg_a if avg_a > 0 else 1.0
    strength_def_h = def_h / avg_a if avg_a > 0 else 1.0
    xg_a = strength_att_a * strength_def_h * avg_a
    
    return xg_h, xg_a, league

def calcular_probs(xg_h, xg_a):
    probs = {"Home":0, "Draw":0, "Away":0, "Over15":0, "Over25":0, "BTTS":0, "Under35":0}
    
    # Estimativa HT (Simples para Card)
    xg_h_ht = xg_h * 0.45 
    xg_a_ht = xg_a * 0.45
    prob_00_ht = poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht)
    probs['Over05HT'] = 1 - prob_00_ht

    for h in range(6):
        for a in range(6):
            p = poisson.pmf(h, xg_h) * poisson.pmf(a, xg_a)
            if h > a: probs["Home"] += p
            elif a > h: probs["Away"] += p
            else: probs["Draw"] += p
            
            total = h + a
            if total > 1.5: probs["Over15"] += p
            if total > 2.5: probs["Over25"] += p
            if total < 3.5: probs["Under35"] += p
            if h > 0 and a > 0: probs["BTTS"] += p
    return probs

# ==============================================================================
# 🚀 ROTINA DE ANÁLISE E ENVIO
# ==============================================================================
def verificar_se_ja_enviou_hoje():
    hoje = (datetime.utcnow() - timedelta(hours=3)).strftime("%Y-%m-%d")
    if not os.path.exists(ARQUIVO_CONTROLE): return False
    with open(ARQUIVO_CONTROLE, "r") as f: return f.read().strip() == hoje

def registrar_envio():
    hoje = (datetime.utcnow() - timedelta(hours=3)).strftime("%Y-%m-%d")
    with open(ARQUIVO_CONTROLE, "w") as f: f.write(hoje)

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except: return False

def analisar_e_enviar():
    agora_brasil = datetime.utcnow() - timedelta(hours=3)
    data_hoje_brasil = agora_brasil.date()
    
    print(f"⏰ {agora_brasil.strftime('%H:%M:%S')} - Iniciando Análise Sincronizada com Dashboard...")
    
    if agora_brasil.hour < HORA_INICIO or agora_brasil.hour > HORA_FIM:
        print("💤 Fora de horário.")
        return

    if verificar_se_ja_enviou_hoje():
        print("✅ Já operou hoje.")
        return

    df_recent, df_today = load_data_robot()
    
    if df_today.empty:
        enviar_telegram(f"🦅 *ALERTA*: Sem jogos na grade para {data_hoje_brasil.strftime('%d/%m')}.")
        registrar_envio()
        return

    # Listas
    step1_candidatos = []
    step2_candidatos = []
    cards_para_enviar = []
    jogos_validos = 0
    
    for i, row in df_today.iterrows():
        if row['match_time'].date() != data_hoje_brasil: continue
        jogos_validos += 1
        
        home, away = row['HomeTeam'], row['AwayTeam']
        hora = row['match_time'].strftime('%H:%M')
        
        xg_h, xg_a, liga = calcular_xg_robot(df_recent, home, away)
        if xg_h is None: continue # Sem histórico suficiente (Dashboard também ignora)
        
        probs = calcular_probs(xg_h, xg_a)
        
        # --- 1. LÓGICA DE ALAVANCAGEM (CICLOS) ---
        if 0.60 <= probs['Over15'] <= 0.75:
            step1_candidatos.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'Over 1.5', 'Odd': 1/probs['Over15'], 'Prob': probs['Over15']})
        if probs['Over15'] > 0.70:
            step2_candidatos.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'Over 1.5', 'Odd': 1/probs['Over15'], 'Prob': probs['Over15']})

        # --- 2. CARD INDIVIDUAL (MÉTRICAS DO DASHBOARD) ---
        # Só envia se estiver "VERDE" no Dashboard (Alta Probabilidade)
        mostrar_card = False
        destaque_str = ""
        
        # Critérios de "Luz Verde" do Dashboard
        if probs['Over25'] >= 0.60: 
            mostrar_card = True; destaque_str += "Over 2.5 | "
        if probs['BTTS'] >= 0.60: 
            mostrar_card = True; destaque_str += "BTTS | "
        if probs['Over15'] >= 0.80: 
            mostrar_card = True; destaque_str += "Over 1.5 | "
        if probs['Home'] >= 0.60: 
            mostrar_card = True
        if probs['Over05HT'] >= 0.80: # Critério forte de HT
            mostrar_card = True; destaque_str += "0.5 HT | "

        if mostrar_card:
            titulo = "JOGO EQUILIBRADO"
            if probs['Home'] > 0.60: titulo = "FAVORITO (CASA)"
            elif probs['Away'] > 0.60: titulo = "FAVORITO (VISITANTE)"
            elif probs['Over25'] > 0.60: titulo = "JOGO PARA GOLS"
            
            avg_cantos = get_avg_corners(df_recent, home, away)
            if destaque_str.endswith(" | "): destaque_str = destaque_str[:-3]
            if destaque_str == "": destaque_str = "Alta Probabilidade"

            def odd(p): return f"@{1/p:.2f}" if p > 0 else "@--"
            def pct(p): return f"{p*100:.0f}%"

            msg_card = (
                f"🏆 *{titulo}*\n"
                f"🏆 {liga}\n\n"
                f"⚽ *{home}* vs *{away}*\n"
                f"⏰ {hora}\n\n"
                f"🔥 *Destaque:* {destaque_str}\n\n"
                f"📊 *PROBABILIDADES (1x2):*\n"
                f"🏠 Casa: {odd(probs['Home'])} ({pct(probs['Home'])})\n"
                f"⚖️ Empate: {odd(probs['Draw'])} ({pct(probs['Draw'])})\n"
                f"✈️ Visitante: {odd(probs['Away'])} ({pct(probs['Away'])})\n\n"
                f"🎯 *MERCADOS DE GOLS:*\n"
                f"⚽ 0.5 HT: {odd(probs['Over05HT'])} ({pct(probs['Over05HT'])})\n"
                f"⚽ 1.5 FT: {odd(probs['Over15'])} ({pct(probs['Over15'])})\n"
                f"⚽ 2.5 FT: {odd(probs['Over25'])} ({pct(probs['Over25'])})\n"
                f"🤝 Ambas: {odd(probs['BTTS'])} ({pct(probs['BTTS'])})\n\n"
                f"🚩 *CANTOS:* Avg {avg_cantos:.1f}\n"
                f"--------------------------------\n"
                f"🍀 Aposte com Responsabilidade\n\n"
                f"🦅 *Mestre dos Greens*"
            )
            cards_para_enviar.append({'texto': msg_card, 'hora': hora})

    enviou_algo = False

    # ENVIO CARDS
    if cards_para_enviar:
        cards_para_enviar.sort(key=lambda x: x['hora'])
        enviar_telegram(f"🦅 *GRADE DE OPORTUNIDADES - {data_hoje_brasil.strftime('%d/%m')}* 🦅")
        time.sleep(2)
        
        print(f"🚀 Enviando {len(cards_para_enviar)} cards...")
        for card in cards_para_enviar:
            enviar_telegram(card['texto'])
            time.sleep(3)
        enviou_algo = True

    # ENVIO ALAVANCAGEM
    if step1_candidatos and step2_candidatos:
        step1_candidatos.sort(key=lambda x: x['Prob'], reverse=True)
        step2_candidatos.sort(key=lambda x: x['Prob'], reverse=True)
        s1 = step1_candidatos[0]
        s2 = step2_candidatos[0]
        if s1['Jogo'] == s2['Jogo'] and len(step2_candidatos) > 1: s2 = step2_candidatos[1]
        
        msg_ciclo = (
            f"💎 *CICLO DE ALAVANCAGEM DO DIA*\n\n"
            f"1️⃣ *PASSO 1* (@{s1['Odd']:.2f})\n⚽ {s1['Jogo']} - {s1['Tipo']}\n\n"
            f"2️⃣ *PASSO 2* (@{s2['Odd']:.2f})\n⚽ {s2['Jogo']} - {s2['Tipo']}"
        )
        enviar_telegram(msg_ciclo)
        enviou_algo = True

    if enviou_algo:
        registrar_envio()
        print("✅ Operação finalizada!")
    elif jogos_validos > 0:
        enviar_telegram(f"🦅 *Grade de Hoje*: {jogos_validos} jogos analisados, mas nenhum dentro do padrão.")
        registrar_envio()
    else:
        print("⚠️ Sem jogos HOJE.")

if __name__ == "__main__":
    analisar_e_enviar()
