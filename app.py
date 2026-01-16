import pandas as pd
import requests
import io
from sklearn.ensemble import RandomForestClassifier
import warnings

warnings.filterwarnings('ignore')

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = "8571442533:AAFbqfHsE1oTdwt2yarJGFpqWgST3-UIUwA"
TELEGRAM_CHAT_ID = "-1003590805331"

# --- BANCO DE DADOS ---
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
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def load_data():
    all_dfs = []
    for nome, url in URLS_LIGAS.items():
        try:
            r = requests.get(url)
            if r.status_code != 200: continue
            try: content = r.content.decode('utf-8')
            except: content = r.content.decode('latin-1')
            try: df = pd.read_csv(io.StringIO(content), low_memory=False)
            except: df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)
            
            df.columns = [c.strip().lower() for c in df.columns]
            rename = {'date':'Date','home_name':'HomeTeam','away_name':'AwayTeam','fthg':'FTHG','ftag':'FTAG','ht_goals_team_a':'HTHG','ht_goals_team_b':'HTAG'}
            df.rename(columns=rename, inplace=True)
            for c in ['FTHG','FTAG','HTHG','HTAG']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
            df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            df['BTTS'] = ((df['FTHG'] > 0) & (df['FTAG'] > 0)).astype(int)
            df['HomeWin'] = (df['FTHG'] > df['FTAG']).astype(int)
            df['AwayWin'] = (df['FTAG'] > df['FTHG']).astype(int)

            if 'HomeTeam' in df.columns: all_dfs.append(df[['HomeTeam','AwayTeam','Over05HT','Over15FT','Over25FT','BTTS','HomeWin','AwayWin','FTHG','FTAG']])
        except: pass
            
    if not all_dfs: return pd.DataFrame(), pd.DataFrame()
    full_df = pd.concat(all_dfs, ignore_index=True)
    df_recent = full_df.tail(15000).copy()
    df_recent.dropna(subset=['HomeTeam', 'AwayTeam'], inplace=True)
    
    try:
        df_today = pd.read_csv(URL_HOJE)
        df_today.columns = [c.strip().lower() for c in df_today.columns]
        df_today.rename(columns={'home_name':'HomeTeam','away_name':'AwayTeam','league':'League','time':'Time'}, inplace=True)
        if 'HomeTeam' not in df_today.columns: df_today['HomeTeam'], df_today['AwayTeam'] = df_today.iloc[:, 0], df_today.iloc[:, 1]
    except: df_today = pd.DataFrame()
    return df_recent, df_today

def treinar_ia(df):
    if df.empty: return None, {}
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
    if df_train.empty or len(df_train) < 10: return None, team_stats
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(df_train[['H', 'A']], df_train['Target'])
    return model, team_stats

def gerar_alerta():
    enviar_msg("🔎 *Mestre dos Greens*: Iniciando varredura (V22.0 - Odd Fix)...")
    try: df_recent, df_today = load_data()
    except: return
    if df_today.empty or df_recent.empty: 
        enviar_msg("⚠️ Sem dados hoje.")
        return
    model, team_stats = treinar_ia(df_recent)
    if not model: 
        enviar_msg("⚠️ IA Calibrando...")
        return

    greens = []
    for idx, row in df_today.iterrows():
        h, a = row.get('HomeTeam'), row.get('AwayTeam')
        if h in team_stats and a in team_stats:
            try:
                preds = model.predict_proba([[team_stats[h], team_stats[a]]])
                prob_ia = preds[0][1] * 100 if preds.shape[1] == 2 else (100.0 if model.classes_[0] == 1 else 0.0)
                
                stats_h = df_recent[df_recent['HomeTeam'] == h]
                stats_a = df_recent[df_recent['AwayTeam'] == a]
                if len(stats_h) < 3: stats_h = df_recent[(df_recent['HomeTeam']==h)|(df_recent['AwayTeam']==h)]
                if len(stats_a) < 3: stats_a = df_recent[(df_recent['HomeTeam']==a)|(df_recent['AwayTeam']==a)]

                if len(stats_h) >= 3 and len(stats_a) >= 3:
                    tips = []
                    # Calcula probabilidades
                    p_05ht = (stats_h['Over05HT'].mean() + stats_a['Over05HT'].mean())/2*100
                    p_15ft = (stats_h['Over15FT'].mean() + stats_a['Over15FT'].mean())/2*100
                    p_btts = (stats_h['BTTS'].mean() + stats_a['BTTS'].mean())/2*100
                    wh = stats_h['HomeWin'].mean() * 100
                    wa = stats_a['AwayWin'].mean() * 100
                    
                    # Variável para guardar a melhor porcentagem encontrada
                    best_prob = 0 

                    # --- GATILHOS ---
                    if prob_ia >= 60: 
                        tips.append(f"🤖 Over 2.5 ({prob_ia:.0f}%)")
                        best_prob = max(best_prob, prob_ia)
                    
                    if p_15ft >= 80: 
                        tips.append(f"🛡️ Over 1.5 ({p_15ft:.0f}%)")
                        best_prob = max(best_prob, p_15ft)

                    if p_05ht >= 75: 
                        tips.append(f"⚡ Over 0.5 HT ({p_05ht:.0f}%)")
                        best_prob = max(best_prob, p_05ht)

                    if p_btts >= 60: 
                        tips.append(f"🤝 BTTS ({p_btts:.0f}%)")
                        best_prob = max(best_prob, p_btts)
                    
                    if wh >= 80: 
                        tips.append(f"🔥 CASA SUPER ({wh:.0f}%)")
                        best_prob = max(best_prob, wh)
                    elif 60 <= wh < 80: 
                        tips.append(f"🏠 Casa ({wh:.0f}%)")
                        best_prob = max(best_prob, wh)

                    if wa >= 80: 
                        tips.append(f"🔥 VISITANTE SUPER ({wa:.0f}%)")
                        best_prob = max(best_prob, wa)
                    elif 60 <= wa < 80: 
                        tips.append(f"✈️ Visitante ({wa:.0f}%)")
                        best_prob = max(best_prob, wa)

                    if tips:
                        # Cálculo Dinâmico: Usa a melhor probabilidade encontrada no jogo
                        odd_justa = 100 / best_prob if best_prob > 0 else 0
                        
                        tips_str = " | ".join(tips)
                        txt = f"💎 *{h} x {a}*\n🏆 {row.get('League','-')} | ⏰ {row.get('Time','--:--')}\n💡 {tips_str}\n💰 Odd Justa: @{odd_justa:.2f}"
                        greens.append(txt)
            except: continue

    if greens:
        enviar_msg(f"🚨 *Mestre dos Greens (V22)* 🚨\n\nEncontrei {len(greens)} oportunidades!")
        bloco = ""
        for g in greens:
            if len(bloco)+len(g) > 3000: enviar_msg(bloco); bloco=""
            bloco += g + "\n➖➖➖➖➖➖➖\n"
        if bloco: enviar_msg(bloco)
    else: enviar_msg("📊 Analisei tudo. Nada bateu seus critérios hoje.")

if __name__ == "__main__":
    gerar_alerta()
if __name__ == "__main__":
    gerar_alerta()
