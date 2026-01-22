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
# Deixe assim no código público. O GitHub vai preencher com os Secrets.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") 
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# Horários que o robô pode trabalhar (ex: das 09h às 20h)
HORA_INICIO = 9
HORA_FIM = 20

# Nome do arquivo para evitar duplicidade (memória do robô)
ARQUIVO_CONTROLE = "controle_envios.txt"

def verificar_se_ja_enviou_hoje():
    """Verifica no arquivo se já houve envio na data de hoje"""
    hoje = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(ARQUIVO_CONTROLE):
        return False
    
    with open(ARQUIVO_CONTROLE, "r") as f:
        ultima_data = f.read().strip()
        
    return ultima_data == hoje

def registrar_envio():
    """Salva a data de hoje para não enviar mais"""
    hoje = datetime.now().strftime("%Y-%m-%d")
    with open(ARQUIVO_CONTROLE, "w") as f:
        f.write(hoje)

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Configuração de Telegram ausente.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            print("✅ Mensagem enviada para o Telegram!")
            return True
        else:
            print(f"❌ Erro Telegram: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Erro conexão: {e}")
        return False

# ==============================================================================
# 📂 NÚCLEO DE DADOS (Mesma lógica V66.8)
# ==============================================================================
def load_data_robot():
    print("📥 Baixando dados atualizados...")
    
    URLS_HISTORICAS = {
        "Brasileirao Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
        "Inglaterra Premier League": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
        "Espanha La Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
        "Italia Serie A": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
        "Alemanha Bundesliga 1": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
        "Holanda Eredivisie": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
        "Portugal Primeira Liga": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv"
    }
    URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

    all_dfs = []
    # Histórico
    for name, url in URLS_HISTORICAS.items():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
                df.columns = [c.strip().lower() for c in df.columns]
                map_cols = {'homegoalcount':'fthg', 'awaygoalcount':'ftag', 'home_score':'fthg', 'away_score':'ftag', 'ht_goals_team_a':'HTHG', 'ht_goals_team_b':'HTAG'}
                df.rename(columns=map_cols, inplace=True)
                if 'date_unix' in df.columns: df['date'] = pd.to_datetime(df['date_unix'], unit='s')
                df.rename(columns={'date':'Date', 'home_name':'HomeTeam', 'away_name':'AwayTeam', 'fthg':'FTHG', 'ftag':'FTAG'}, inplace=True)
                for c in ['FTHG','FTAG','HTHG','HTAG']: 
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                df['League_Custom'] = name
                if 'HomeTeam' in df.columns: all_dfs.append(df[['Date','League_Custom','HomeTeam','AwayTeam','FTHG','FTAG','HTHG','HTAG']])
        except: continue

    df_recent = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    if not df_recent.empty:
        df_recent['Date'] = pd.to_datetime(df_recent['Date'], dayfirst=True, errors='coerce')
        df_recent = df_recent[df_recent['Date'].dt.year >= 2024].copy()

    # Hoje
    try:
        r_today = requests.get(URL_HOJE, timeout=10)
        df_today = pd.read_csv(io.StringIO(r_today.content.decode('utf-8')))
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        # Fuso Brasil -3
        if 'date_unix' in df_today.columns:
            df_today['match_time'] = pd.to_datetime(df_today['date_unix'], unit='s') - timedelta(hours=3)
        else:
            df_today['match_time'] = datetime.now()
    except: df_today = pd.DataFrame()

    return df_recent, df_today

# --- CÁLCULOS ---
def get_weighted_avg(full_df, venue_df, col_name):
    w_geral = full_df[col_name].mean()
    w_venue = venue_df[col_name].mean() if not venue_df.empty else w_geral
    w_10 = full_df.tail(10)[col_name].mean()
    w_5 = full_df.tail(5)[col_name].mean()
    return (w_geral * 0.10) + (w_venue * 0.40) + (w_10 * 0.20) + (w_5 * 0.30)

def calcular_xg_robot(df_historico, home, away):
    try: league = df_historico[df_historico['HomeTeam'] == home]['League_Custom'].mode()[0]
    except: 
        if home in df_historico['HomeTeam'].unique(): league = df_historico[df_historico['HomeTeam'] == home].iloc[-1]['League_Custom']
        else: return None, None
            
    df_league = df_historico[df_historico['League_Custom'] == league]
    if df_league.empty: return None, None
    
    avg_h = df_league['FTHG'].mean(); avg_a = df_league['FTAG'].mean()
    df_h_all = df_historico[(df_historico['HomeTeam'] == home) | (df_historico['AwayTeam'] == home)].sort_values('Date')
    df_a_all = df_historico[(df_historico['HomeTeam'] == away) | (df_historico['AwayTeam'] == away)].sort_values('Date')
    df_h_home = df_historico[df_historico['HomeTeam'] == home]
    df_a_away = df_historico[df_historico['AwayTeam'] == away]
    
    if len(df_h_all) < 3 or len(df_a_all) < 3: return None, None
    
    att_h = get_weighted_avg(df_h_all, df_h_home, 'FTHG'); def_a = get_weighted_avg(df_a_all, df_a_away, 'FTHG')
    att_a = get_weighted_avg(df_a_all, df_a_away, 'FTAG'); def_h = get_weighted_avg(df_h_all, df_h_home, 'FTAG')
    
    xg_h = (att_h / avg_h) * (def_a / avg_h) * avg_h
    xg_a = (att_a / avg_a) * (def_h / avg_a) * avg_a
    return xg_h, xg_a

def calcular_probs(xg_h, xg_a):
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

# ==============================================================================
# 🚀 MOTOR DE CICLO 
# ==============================================================================
def job():
    print(f"⏰ Verificando rotina: {datetime.now().strftime('%H:%M:%S')}")
    
    # 1. Verifica Horário de Trabalho
    hora_atual = datetime.now().hour
    if hora_atual < HORA_INICIO or hora_atual > HORA_FIM:
        print("💤 Fora do horário de operação.")
        return

    # 2. Verifica se já enviou hoje
    if verificar_se_ja_enviou_hoje():
        print("✅ Ciclo de hoje já foi enviado. Aguardando amanhã.")
        return

    # 3. Executa Análise
    df_recent, df_today = load_data_robot()
    if df_today.empty: return
    
    step1_candidates = []
    step2_candidates = []
    
    for i, row in df_today.iterrows():
        home, away = row['HomeTeam'], row['AwayTeam']
        hora = row['match_time'].strftime('%H:%M')
        
        xg_h, xg_a = calcular_xg_robot(df_recent, home, away)
        if xg_h is None: continue
        probs = calcular_probs(xg_h, xg_a)
        
        # --- CRITÉRIOS DE ODDS ---
        # Step 1: 1.40 - 1.60
        if 0.60 <= probs['Over15'] <= 0.75:
            step1_candidates.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'Over 1.5', 'Odd': 1/probs['Over15'], 'Prob': probs['Over15']})
        if 0.58 <= probs['BTTS'] <= 0.72:
            step1_candidates.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'BTTS', 'Odd': 1/probs['BTTS'], 'Prob': probs['BTTS']})

        # Step 2: 1.25 - 1.42
        if probs['Over15'] > 0.70:
             step2_candidates.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'Over 1.5', 'Odd': 1/probs['Over15'], 'Prob': probs['Over15']})
        if probs['Under35'] > 0.70:
             step2_candidates.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': 'Under 3.5', 'Odd': 1/probs['Under35'], 'Prob': probs['Under35']})
        prob_1x = probs['Home'] + probs['Draw']
        if prob_1x > 0.70:
             step2_candidates.append({'Jogo': f"{home}x{away}", 'Hora': hora, 'Tipo': '1X', 'Odd': 1/prob_1x, 'Prob': prob_1x})

    # --- DISPARO ---
    if step1_candidates and step2_candidates:
        step1_candidates.sort(key=lambda x: x['Prob'], reverse=True)
        step2_candidates.sort(key=lambda x: x['Prob'], reverse=True)
        
        s1 = step1_candidates[0]
        s2 = step2_candidates[0]
        
        # Tenta não repetir o jogo
        if s1['Jogo'] == s2['Jogo'] and len(step2_candidates) > 1:
            s2 = step2_candidates[1]
        
        msg = (
            f"🦅 *ALERTA OFICIAL: CICLO DO DIA* 🦅\n\n"
            f"🗓️ *{datetime.now().strftime('%d/%m/%Y')}*\n\n"
            f"1️⃣ *PASSO 1* (Odd ~{s1['Odd']:.2f})\n"
            f"⚽ {s1['Jogo']} ({s1['Hora']})\n"
            f"🎯 *{s1['Tipo']}*\n"
            f"📊 Confiança: {s1['Prob']*100:.1f}%\n\n"
            f"2️⃣ *PASSO 2* (Odd ~{s2['Odd']:.2f})\n"
            f"⚽ {s2['Jogo']} ({s2['Hora']})\n"
            f"🎯 *{s2['Tipo']}*\n"
            f"📊 Confiança: {s2['Prob']*100:.1f}%\n\n"
            f"💎 *Gestão:* Aplique o lucro do Passo 1 no Passo 2.\n"
            f"🍀 *Boa sorte!*"
        )
        
        sucesso = enviar_telegram(msg)
        if sucesso:
            registrar_envio() # <--- AQUI ELE TRAVA PARA NÃO MANDAR MAIS HOJE
            print("🚀 Ciclo enviado e registrado!")
    else:
        print("❌ Nenhum ciclo ideal encontrado nesta rodada.")

# ==============================================================================
# 🚀 EXECUÇÃO (MODO GITHUB ACTIONS)
# ==============================================================================
if __name__ == "__main__":
    print("🤖 Iniciando Verificação Única do Robô...")
    
    # Executa apenas uma vez e encerra. 
    # O agendamento quem faz é o GitHub Actions (main.yml)
    analisar_e_enviar() 
    
    print("🏁 Verificação concluída. Encerrando.")
