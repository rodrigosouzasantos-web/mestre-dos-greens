import pandas as pd
import requests
import io
import time
import os
from scipy.stats import poisson
from datetime import datetime, timedelta

# ==============================================================================
# ⚙️ CONFIGURAÇÕES DO ROBÔ
# ==============================================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "SEU_TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "SEU_ID_AQUI")

HORA_INICIO = 8
HORA_FIM = 22
ARQUIVO_CONTROLE = "controle_envios.txt"

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

# ==============================================================================
# 📂 BANCO DE DADOS (IDÊNTICO AO DASHBOARD V67.2)
# ==============================================================================
def load_data_robot():
    print("📥 Baixando dados e sincronizando com Dashboard...")
    
    # LISTA COMPLETA DE LIGAS (HISTÓRICAS E ATUAIS)
    URLS = {
        # --- HISTÓRICAS ---
        "Argentina Primera": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv",
        "Belgica Pro League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Belgium_Pro_League_2016-2025.csv",
        "Brasileirao Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
        "Inglaterra Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
        "Franca Ligue 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/France_Ligue_1_2016-2025.csv",
        "Alemanha Bundesliga 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
        "Italia Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
        "Holanda Eredivisie": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
        "Portugal Primeira Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv",
        "Espanha La Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
        # --- ATUAIS (2025/26) ---
        "Inglaterra Premier League 25": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/England_Premier_League_2025-2026.csv",
        "Franca Ligue 1 25": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/France_Ligue_1_2025-2026.csv",
        "Alemanha Bundesliga 1 25": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Germany_Bundesliga_2025-2026.csv",
        "Italia Serie A 25": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Italy_Serie_A_2025-2026.csv",
        "Espanha La Liga 25": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Spain_La_Liga_2025-2026.csv",
        "Brasileirao Serie A 25": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/matches/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2025-2026.csv"
    }
    
    URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

    all_dfs = []
    for name, url in URLS.items():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
                df.columns = [c.strip().lower() for c in df.columns]
                map_cols = {'homegoalcount':'fthg', 'awaygoalcount':'ftag', 'home_score':'fthg', 'away_score':'ftag', 
                            'ht_goals_team_a':'HTHG', 'ht_goals_team_b':'HTAG', 
                            'team_a_corners': 'HC', 'team_b_corners': 'AC'}
                df.rename(columns=map_cols, inplace=True)
                if 'date_unix' in df.columns: df['date'] = pd.to_datetime(df['date_unix'], unit='s')
                df.rename(columns={'date':'Date', 'home_name':'HomeTeam', 'away_name':'AwayTeam', 'fthg':'FTHG', 'ftag':'FTAG'}, inplace=True)
                
                for c in ['FTHG','FTAG','HTHG','HTAG','HC','AC']: 
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                
                # Nome da liga limpo (remove o " 25" do final se tiver)
                clean_name = name.replace(" 25", "")
                df['League_Custom'] = clean_name
                
                if 'HomeTeam' in df.columns: 
                    all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG','HC','AC']])
        except: continue

    df_recent = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    if not df_recent.empty:
        df_recent['Date'] = pd.to_datetime(df_recent['Date'], dayfirst=True, errors='coerce')
        df_recent.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last', inplace=True)
        # Filtro de data igual ao Dashboard (>= 2023)
        df_recent = df_recent[df_recent['Date'].dt.year >= 2023].copy()

    # HOJE
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
# 🧮 MOTOR HÍBRIDO (CÓPIA DO DASHBOARD V67.2)
# ==============================================================================

# 1. MÉDIA PONDERADA (30% Geral, 40% Venue, 30% Recent)
def get_weighted_avg(full_df, venue_df, col_name):
    w_geral = full_df[col_name].mean()
    w_venue = venue_df[col_name].mean() if not venue_df.empty else w_geral
    w_5 = full_df.tail(5)[col_name].mean()
    return (w_geral * 0.30) + (w_venue * 0.40) + (w_5 * 0.30)

def get_avg_corners(df_recent, home, away):
    df_h = df_recent[df_recent['HomeTeam'] == home]
    df_a = df_recent[df_recent['AwayTeam'] == away]
    if df_h.empty or df_a.empty: return 10.0
    avg_h = df_h['HC'].mean() + df_h['AC'].mean()
    avg_a = df_a['HC'].mean() + df_a['AC'].mean()
    return (avg_h + avg_a) / 2

# 2. FREQUÊNCIA REAL (PDF)
def get_frequencia_real(df_recent, home, away):
    df_h = df_recent[df_recent['HomeTeam'] == home]
    df_a = df_recent[df_recent['AwayTeam'] == away]
    if df_h.empty or df_a.empty: return None

    freq_ht = (((df_h['HTHG'] + df_h['HTAG']) > 0).mean() + ((df_a['HTHG'] + df_a['HTAG']) > 0).mean()) / 2
    freq_15 = (((df_h['FTHG'] + df_h['FTAG']) > 1.5).mean() + ((df_a['FTHG'] + df_a['FTAG']) > 1.5).mean()) / 2
    freq_25 = (((df_h['FTHG'] + df_h['FTAG']) > 2.5).mean() + ((df_a['FTHG'] + df_a['FTAG']) > 2.5).mean()) / 2
    freq_btts = (((df_h['FTHG'] > 0) & (df_h['FTAG'] > 0)).mean() + ((df_a['FTHG'] > 0) & (df_a['FTAG'] > 0)).mean()) / 2
    freq_u35 = (((df_h['FTHG'] + df_h['FTAG']) < 3.5).mean() + ((df_a['FTHG'] + df_a['FTAG']) < 3.5).mean()) / 2

    return {"Over05HT": freq_ht, "Over15": freq_15, "Over25": freq_25, "BTTS": freq_btts, "Under35": freq_u35}

# 3. MATEMÁTICA (POISSON)
def calcular_xg_robot(df_historico, league, home, away, col_home='FTHG', col_away='FTAG'):
    if league: df_league = df_historico[df_historico['League_Custom'] == league]
    else: df_league = df_historico
    
    if df_league.empty: return None, None
    
    avg_h = df_league[col_home].mean(); avg_a = df_league[col_away].mean()
    df_h_all = df_historico[(df_historico['HomeTeam'] == home) | (df_historico['AwayTeam'] == home)].sort_values('Date')
    df_a_all = df_historico[(df_historico['HomeTeam'] == away) | (df_historico['AwayTeam'] == away)].sort_values('Date')
    df_h_venue = df_historico[df_historico['HomeTeam'] == home]
    df_a_venue = df_historico[df_historico['AwayTeam'] == away]
    
    if len(df_h_all) < 5 or len(df_a_all) < 5: return None, None
    
    att_h = get_weighted_avg(df_h_all, df_h_venue, col_home)
    def_a = get_weighted_avg(df_a_all, df_a_venue, col_home)
    xg_h = (att_h / avg_h) * (def_a / avg_h) * avg_h if avg_h > 0 else 0

    att_a = get_weighted_avg(df_a_all, df_a_venue, col_away)
    def_h = get_weighted_avg(df_h_all, df_h_venue, col_away)
    xg_a = (att_a / avg_a) * (def_h / avg_a) * avg_a if avg_a > 0 else 0
    
    return xg_h, xg_a

def gerar_probs_poisson(xg_h, xg_a):
    probs = {"Home":0, "Draw":0, "Away":0, "Over15":0, "Over25":0, "BTTS":0, "Under35":0}
    for h in range(6):
        for a in range(6):
            p = poisson.pmf(h, xg_h) * poisson.pmf(a, xg_a)
            if h > a: probs["Home"] += p
            elif a > h: probs["Away"] += p
            else: probs["Draw"] += p
            if h+a > 1.5: probs["Over15"] += p
            if h+a > 2.5: probs["Over25"] += p
            if h+a < 3.5: probs["Under35"] += p
            if h > 0 and a > 0: probs["BTTS"] += p
    return probs

# 4. CÁLCULO FINAL (HÍBRIDO)
def calcular_hibrido_robot(df_recent, league, home, away):
    # Math
    xg_h, xg_a = calcular_xg_robot(df_recent, league, home, away, 'FTHG', 'FTAG')
    if xg_h is None: return None
    math_probs = gerar_probs_poisson(xg_h, xg_a)
    
    # Math HT
    xg_h_ht, xg_a_ht = calcular_xg_robot(df_recent, league, home, away, 'HTHG', 'HTAG')
    if xg_h_ht: math_prob_ht = 1 - (poisson.pmf(0, xg_h_ht) * poisson.pmf(0, xg_a_ht))
    else: math_prob_ht = 0
    
    # Real
    freq = get_frequencia_real(df_recent, home, away)
    if freq is None: return None
    
    # Hibridismo (50/50)
    final = {
        "Over05HT": (math_prob_ht + freq['Over05HT']) / 2,
        "Over15": (math_probs['Over15'] + freq['Over15']) / 2,
        "Over25": (math_probs['Over25'] + freq['Over25']) / 2,
        "BTTS": (math_probs['BTTS'] + freq['BTTS']) / 2,
        "Under35": (math_probs['Under35'] + freq['Under35']) / 2,
        "Home": math_probs['Home'], "Draw": math_probs['Draw'], "Away": math_probs['Away']
    }
    return final

# ==============================================================================
# 🚀 MOTOR DE ENVIO (LÓGICA HÍBRIDA)
# ==============================================================================
def analisar_e_enviar():
    agora_brasil = datetime.utcnow() - timedelta(hours=3)
    data_hoje_brasil = agora_brasil.date()
    
    print(f"⏰ Verificando: {agora_brasil.strftime('%H:%M:%S')} (Data: {data_hoje_brasil})")
    
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

    step1_candidatos = []
    step2_candidatos = []
    cards_para_enviar = []
    jogos_validos = 0
    
    print("🔎 Analisando jogos com Motor Híbrido...")

    for i, row in df_today.iterrows():
        if row['match_time'].date() != data_hoje_brasil: continue
        jogos_validos += 1
        
        home, away = row['HomeTeam'], row['AwayTeam']
        hora = row['match_time'].strftime('%H:%M')
        
        # Tenta achar liga
        try: liga = df_recent[df_recent['HomeTeam'] == home]['League_Custom'].mode()[0]
        except: 
            if home in df_recent['HomeTeam'].unique(): liga = df_recent[df_recent['HomeTeam'] == home].iloc[-1]['League_Custom']
            else: continue
            
        probs = calcular_hibrido_robot(df_recent, liga, home, away)
        if probs is None: continue
        
        # --- 1. ALAVANCAGEM ---
        if 0.60 <= probs['Over15'] <= 0.75:
            step1_candidatos.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'Over 1.5', 'Odd': 1/probs['Over15'], 'Prob': probs['Over15']})
        if probs['Over15'] > 0.70:
            step2_candidatos.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'Over 1.5', 'Odd': 1/probs['Over15'], 'Prob': probs['Over15']})

        # --- 2. CARD INDIVIDUAL (MÉTRICAS DO DASHBOARD) ---
        mostrar_card = False
        destaque_str = ""
        
        # Critérios de "Luz Verde" Híbrida
        if probs['Over25'] >= 0.60: 
            mostrar_card = True; destaque_str += "Over 2.5 | "
        if probs['BTTS'] >= 0.60: 
            mostrar_card = True; destaque_str += "BTTS | "
        if probs['Over15'] >= 0.80: 
            mostrar_card = True; destaque_str += "Over 1.5 | "
        if probs['Home'] >= 0.60: 
            mostrar_card = True
        if probs['Over05HT'] >= 0.80: 
            mostrar_card = True; destaque_str += "0.5 HT | "

        if mostrar_card:
            titulo = "JOGO EQUILIBRADO"
            if probs['Home'] > 0.60: titulo = "FAVORITO (CASA)"
            elif probs['Away'] > 0.60: titulo = "FAVORITO (VISITANTE)"
            elif probs['Over25'] > 0.60: titulo = "JOGO PARA GOLS"
            
            avg_cantos = get_avg_corners(df_recent, home, away)
            if destaque_str.endswith(" | "): destaque_str = destaque_str[:-3]
            if destaque_str == "": destaque_str = "Probabilidades Reais"

            def odd(p): return f"@{1/p:.2f}" if p > 0 else "@--"
            def pct(p): return f"{p*100:.0f}%"

            msg_card = (
                f"🏆 *{titulo}*\n"
                f"🏆 {liga}\n\n"
                f"⚽ *{home}* vs *{away}*\n"
                f"⏰ {hora}\n\n"
                f"🔥 *Destaque:* {destaque_str}\n\n"
                f"📊 *PROBABILIDADES HÍBRIDAS:*\n"
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

    if cards_para_enviar:
        cards_para_enviar.sort(key=lambda x: x['hora'])
        enviar_telegram(f"🦅 *GRADE DE OPORTUNIDADES - {data_hoje_brasil.strftime('%d/%m')}* 🦅")
        time.sleep(2)
        print(f"🚀 Enviando {len(cards_para_enviar)} cards...")
        for card in cards_para_enviar:
            enviar_telegram(card['texto'])
            time.sleep(3)
        enviou_algo = True

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
