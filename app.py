import pandas as pd
import requests
import io
from sklearn.ensemble import RandomForestClassifier
import warnings

# Ignora avisos para limpar o log
warnings.filterwarnings('ignore')

# --- 1. CONFIGURAÇÕES ---
TELEGRAM_TOKEN = "8571442533:AAFbqfHsE1oTdwt2yarJGFpqWgST3-UIUwA"
TELEGRAM_CHAT_ID = "-1003590805331"

# --- 2. BANCO DE DADOS ---
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

def enviar_msg(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def load_data():
    all_dfs = []
    print("🔄 Baixando dados...")
    for nome, url in URLS_LIGAS.items():
        try:
            r = requests.get(url)
            if r.status_code != 200: continue
            # Tratamento de erro de decodificação
            try: content = r.content.decode('utf-8')
            except: content = r.content.decode('latin-1')
            
            try: df = pd.read_csv(io.StringIO(content), low_memory=False)
            except: df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            rename = {'date':'Date','home_name':'HomeTeam','away_name':'AwayTeam',
                      'fthg':'FTHG','ftag':'FTAG'}
            df.rename(columns=rename, inplace=True)
            
            # Garante números onde precisa (preenche vazios com 0 em vez de deletar a linha)
            for c in ['FTHG','FTAG']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            # Cria alvo
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            
            # Só guarda colunas essenciais para economizar memória
            if 'HomeTeam' in df.columns and 'AwayTeam' in df.columns:
                all_dfs.append(df[['HomeTeam','AwayTeam','FTHG','FTAG','Over25FT']])
        except: pass
            
    if not all_dfs: return pd.DataFrame(), pd.DataFrame()

    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # EM VEZ DE FILTRAR POR ANO (QUE DAVA ERRO), PEGAMOS OS ÚLTIMOS 10.000 JOGOS
    # Isso garante que temos dados, mesmo se a data estiver bagunçada
    df_recent = full_df.tail(15000).copy()
    
    # Remove apenas se não tiver nome de time
    df_recent.dropna(subset=['HomeTeam', 'AwayTeam'], inplace=True)
    
    print("🔄 Baixando grade de hoje...")
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        # Ajuste se colunas não tiverem nome
        if 'HomeTeam' not in df_today.columns:
             df_today['HomeTeam'] = df_today.iloc[:, 0]
             df_today['AwayTeam'] = df_today.iloc[:, 1]
    except: df_today = pd.DataFrame()
    
    return df_recent, df_today

def treinar_ia(df):
    print("🧠 Treinando IA...")
    if df.empty: return None, {}

    team_stats = {}
    # Calcula força ofensiva média
    for team in pd.concat([df['HomeTeam'], df['AwayTeam']]).unique():
        games = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)]
        if len(games) < 3: continue # Reduzi exigência para 3 jogos
        avg_goals = (games['FTHG'].sum() + games['FTAG'].sum()) / len(games)
        team_stats[team] = avg_goals
        
    model_data = []
    for idx, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        if h in team_stats and a in team_stats:
            model_data.append({'H': team_stats[h], 'A': team_stats[a], 'Target': row['Over25FT']})
            
    df_train = pd.DataFrame(model_data)
    
    # Se não tiver dados suficientes, aborta sem quebrar
    if df_train.empty or len(df_train) < 10:
        return None, team_stats

    model = RandomForestClassifier(n_estimators=50, random_state=42) # 50 arvores é mais leve e rápido
    model.fit(df_train[['H', 'A']], df_train['Target'])
    return model, team_stats

def gerar_alerta():
    enviar_msg("🔎 *Mestre dos Greens*: Iniciando varredura (V19.0 - Turbo)...")
    
    try:
        df_recent, df_today = load_data()
    except Exception as e:
        enviar_msg(f"⚠️ Erro ao baixar dados: {str(e)}")
        return

    if df_today.empty:
        enviar_msg("⚠️ Grade vazia.")
        return
    
    if df_recent.empty:
        enviar_msg("⚠️ Falha crítica no histórico.")
        return

    model, team_stats = treinar_ia(df_recent)
    
    if not model:
        enviar_msg("⚠️ IA precisa de mais dados para calibrar hoje.")
        return

    greens = []
    print(f"Analisando {len(df_today)} jogos...")

    for idx, row in df_today.iterrows():
        h, a = row.get('HomeTeam'), row.get('AwayTeam')
        
        if h in team_stats and a in team_stats:
            try:
                # Proteção contra erro de índice (IndexError)
                preds = model.predict_proba([[team_stats[h], team_stats[a]]])
                if preds.shape[1] == 2:
                    prob_ia = preds[0][1] * 100
                else:
                    prob_ia = 100.0 if model.classes_[0] == 1 else 0.0
                
                tips = []
                if prob_ia >= 70: tips.append(f"Over 2.5 ({prob_ia:.0f}%)")
                
                # BTTS simplificado (Verifica apenas média simples)
                stats_h = df_recent[df_recent['HomeTeam'] == h]
                stats_a = df_recent[df_recent['AwayTeam'] == a]
                if not stats_h.empty and not stats_a.empty:
                    btts_rate = (((stats_h['FTHG']>0)&(stats_h['FTAG']>0)).mean() + ((stats_a['FTHG']>0)&(stats_a['FTAG']>0)).mean())/2
                    if btts_rate >= 0.60: tips.append("BTTS")

                if tips:
                    odd_justa = 100 / prob_ia if prob_ia > 0 else 0
                    emoji = "🔥" if prob_ia > 85 else "💡"
                    
                    txt = f"{emoji} *{h} x {a}*\n"
                    txt += f"🏆 {row.get('League', '-')}\n"
                    txt += f"🤖 IA: {prob_ia:.1f}%\n"
                    txt += f"🎯 Tip: {' + '.join(tips)}\n"
                    txt += f"💰 Odd Justa: @{odd_justa:.2f}\n"
                    greens.append(txt)
            except:
                continue # Se der erro em um jogo específico, pula para o próximo

    if greens:
        enviar_msg(f"🚨 *RELATÓRIO TURBO* 🚨\n\nEncontrei {len(greens)} oportunidades!")
        bloco = ""
        for g in greens:
            if len(bloco) + len(g) > 3000:
                enviar_msg(bloco)
                bloco = ""
            bloco += g + "\n➖➖➖➖➖➖➖\n"
        if bloco: enviar_msg(bloco)
    else:
        enviar_msg("📊 IA analisou a grade e não encontrou entradas com +70% de confiança.")

if __name__ == "__main__":
    gerar_alerta()
