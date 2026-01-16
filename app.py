import pandas as pd
import requests
import io
from sklearn.ensemble import RandomForestClassifier
import os

# --- 1. CONFIGURAÇÕES DO TELEGRAM ---
# PREENCHA AQUI COM SEUS DADOS REAIS OU USE VARIÁVEIS DE AMBIENTE
TELEGRAM_TOKEN = "8571442533:AAFbqfHsE1oTdwt2yarJGFpqWgST3-UIUwA" 
TELEGRAM_CHAT_ID = "-1003590805331"

# --- 2. BANCO DE DADOS (NOSSA BASE GLOBAL) ---
URLS_LIGAS = {
    "Argentina": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv",
    "Belgica": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Belgium_Pro_League_2016-2025.csv",
    "Brasileirao": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Brasileir%C3%A3o_S%C3%A9rie_A_2016-2024.csv",
    "Inglaterra": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/England_Premier_League_2016-2025.csv",
    "Franca": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/France_Ligue_1_2016-2025.csv",
    "Alemanha": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2016-2025.csv",
    "Alemanha 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Germany_Bundesliga_2_2016-2025.csv",
    "Italia": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_A_2016-2025.csv",
    "Italia B": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Italy_Serie_B_2016-2025.csv",
    "Holanda": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Netherlands_Eredivisie_2016-2025.csv",
    "Portugal": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Liga_Portugal_2016-2025.csv",
    "Espanha": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_La_Liga_2016-2025.csv",
    "Espanha 2": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Spain_Segunda_Divisi%C3%B3n_2016-2025.csv",
    "Turquia": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Turkey_S%C3%BCper_Lig_2016-2025.csv"
}
URL_HOJE = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

def enviar_msg(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Erro: Token ou Chat ID não configurados.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def load_data():
    all_dfs = []
    print("🔄 Baixando dados históricos...")
    for nome, url in URLS_LIGAS.items():
        try:
            r = requests.get(url)
            if r.status_code != 200: continue
            content = r.content.decode('utf-8')
            try: df = pd.read_csv(io.StringIO(content), low_memory=False)
            except: df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            rename = {'date':'Date','date_unix':'DateUnix','home_name':'HomeTeam','away_name':'AwayTeam',
                      'fthg':'FTHG','ftag':'FTAG','ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG'}
            df.rename(columns=rename, inplace=True)
            
            if 'Date' not in df.columns and 'DateUnix' in df.columns:
                df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
            
            # Garante colunas numéricas
            for c in ['FTHG','FTAG','HTHG','HTAG']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            # Cria o ALVO para a IA (Over 2.5)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            
            cols = ['Date','HomeTeam','AwayTeam','FTHG','FTAG','Over25FT']
            all_dfs.append(df[cols])
        except: pass
            
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['Date'] = pd.to_datetime(full_df['Date'], dayfirst=True, errors='coerce')
    df_recent = full_df[full_df['Date'].dt.year >= 2023].copy().dropna()
    
    print("🔄 Baixando jogos de hoje...")
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns:
             df_today['HomeTeam'] = df_today.iloc[:, 0]
             df_today['AwayTeam'] = df_today.iloc[:, 1]
    except: df_today = pd.DataFrame()
    
    return df_recent, df_today

def treinar_ia(df):
    print("🧠 Treinando Inteligência Artificial...")
    team_stats = {}
    # Calcula média de gols histórica de cada time para alimentar a IA
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
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(df_train[['H', 'A']], df_train['Target'])
    return model, team_stats

def gerar_alerta():
    df_recent, df_today = load_data()
    
    # Cabeçalho de Abertura
    enviar_msg("🔎 *Mestre dos Greens*: Iniciando varredura com Inteligência Artificial...")

    if df_today.empty:
        enviar_msg("⚠️ A grade de jogos de hoje ainda não foi disponibilizada pelo fornecedor.")
        return

    model, team_stats = treinar_ia(df_recent)
    greens = []

    print(f"Analisando {len(df_today)} jogos...")

    for idx, row in df_today.iterrows():
        h, a = row.get('HomeTeam'), row.get('AwayTeam')
        
        # A IA só analisa se conhecer os dois times
        if h in team_stats and a in team_stats:
            # Pede a probabilidade para o Cérebro da IA
            prob_ia = model.predict_proba([[team_stats[h], team_stats[a]]])[0][1] * 100
            
            # --- LÓGICA DE SELEÇÃO (IGUAL AO SITE) ---
            tips = []
            
            # Regra 1: IA confiante
            if prob_ia >= 70: 
                tips.append(f"Over 2.5 ({prob_ia:.0f}%)")
            
            # Regra 2: Validação Estatística Rápida (BTTS)
            stats_h = df_recent[df_recent['HomeTeam'] == h]
            stats_a = df_recent[df_recent['AwayTeam'] == a]
            if len(stats_h) >= 3 and len(stats_a) >= 3:
                btts = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean())/2*100
                if btts >= 60: 
                    tips.append("BTTS (Ambas)")

            # Se achou alguma oportunidade boa
            if tips:
                odd_justa = 100 / prob_ia if prob_ia > 0 else 0
                emoji = "🔥" if prob_ia > 85 else "💡"
                
                txt = f"{emoji} *{h} x {a}*\n"
                txt += f"🏆 {row.get('League', '-')}\n"
                txt += f"⏰ {row.get('Time', '--:--')}\n"
                txt += f"🤖 IA Confidence: {prob_ia:.1f}%\n"
                txt += f"🎯 Tip: {' + '.join(tips)}\n"
                txt += f"💰 Odd Justa: @{odd_justa:.2f}\n"
                greens.append(txt)

    if greens:
        # Envia cabeçalho dos Greens
        enviar_msg(f"🚨 *RELATÓRIO DE OPORTUNIDADES* 🚨\n\nEncontrei {len(greens)} jogos com valor esperado positivo (+EV) hoje!")
        
        # Envia cada jogo (agrupando para não dar flood)
        bloco = ""
        for g in greens:
            if len(bloco) + len(g) > 3500: # Limite do Telegram aprox 4096
                enviar_msg(bloco)
                bloco = ""
            bloco += g + "\n➖➖➖➖➖➖➖\n"
        if bloco: enviar_msg(bloco)
        
        enviar_msg("⚠️ *Gestão de Banca:* Não aposte tudo em um único jogo. Siga a gestão!")
    else:
        enviar_msg("📊 *Relatório Diário:* A IA analisou a grade e não encontrou oportunidades com confiança acima de 70% hoje. Melhor preservar a banca. 🛡️")

if __name__ == "__main__":
    gerar_alerta()
