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

def get_odd(prob):
    if prob <= 0: return 0.00
    return 100 / prob

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
            rename = {
                'date':'Date','home_name':'HomeTeam','away_name':'AwayTeam',
                'fthg':'FTHG','ftag':'FTAG','ht_goals_team_a':'HTHG','ht_goals_team_b':'HTAG',
                'team_a_corners': 'HC', 'team_b_corners': 'AC'
            }
            df.rename(columns=rename, inplace=True)
            for c in ['FTHG','FTAG','HTHG','HTAG','HC','AC']: 
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            df['Over05HT'] = ((df['HTHG'] + df['HTAG']) > 0.5).astype(int)
            df['Over15FT'] = ((df['FTHG'] + df['FTAG']) > 1.5).astype(int)
            df['Over25FT'] = ((df['FTHG'] + df['FTAG']) > 2.5).astype(int)
            df['BTTS'] = ((df['FTHG'] > 0) & (df['FTAG'] > 0)).astype(int)
            df['HomeWin'] = (df['FTHG'] > df['FTAG']).astype(int)
            df['AwayWin'] = (df['FTAG'] > df['FTHG']).astype(int)

            if 'HomeTeam' in df.columns: 
                all_dfs.append(df[['HomeTeam','AwayTeam','Over05HT','Over15FT','Over25FT','BTTS','HomeWin','AwayWin','FTHG','FTAG','HC','AC']])
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
    enviar_msg("🔎 *Mestre dos Greens*: Iniciando varredura (V24.0 - Layout Pro)...")
    try: df_recent, df_today = load_data()
    except: return
    if df_today.empty or df_recent.empty: return
    model, team_stats = treinar_ia(df_recent)
    if not model: return

    for idx, row in df_today.iterrows():
        h, a = row.get('HomeTeam'), row.get('AwayTeam')
        if h in team_stats and a in team_stats:
            try:
                # --- CÁLCULOS ---
                preds = model.predict_proba([[team_stats[h], team_stats[a]]])
                prob_ia = preds[0][1] * 100 if preds.shape[1] == 2 else (100.0 if model.classes_[0] == 1 else 0.0)
                
                stats_h = df_recent[df_recent['HomeTeam'] == h]
                stats_a = df_recent[df_recent['AwayTeam'] == a]
                if len(stats_h) < 3: stats_h = df_recent[(df_recent['HomeTeam']==h)|(df_recent['AwayTeam']==h)]
                if len(stats_a) < 3: stats_a = df_recent[(df_recent['HomeTeam']==a)|(df_recent['AwayTeam']==a)]

                if len(stats_h) >= 3 and len(stats_a) >= 3:
                    # Probabilidades
                    p_05ht = (stats_h['Over05HT'].mean() + stats_a['Over05HT'].mean())/2*100
                    p_15ft = (stats_h['Over15FT'].mean() + stats_a['Over15FT'].mean())/2*100
                    p_25ft = (stats_h['Over25FT'].mean() + stats_a['Over25FT'].mean())/2*100 # Usado no card, mas IA define o trigger
                    p_btts = (stats_h['BTTS'].mean() + stats_a['BTTS'].mean())/2*100
                    wh = stats_h['HomeWin'].mean() * 100
                    wa = stats_a['AwayWin'].mean() * 100
                    wd = 100 - (wh + wa) # Prob Empate Estimada
                    if wd < 0: wd = 0
                    
                    avg_corners = (stats_h['HC'].mean() + stats_a['AC'].mean())

                    # --- GATILHOS (Critérios para ENVIAR) ---
                    destaques = []
                    
                    if prob_ia >= 60: destaques.append(f"🤖 Over 2.5 (IA)")
                    if p_15ft >= 80: destaques.append("🛡️ Over 1.5 FT")
                    if p_05ht >= 75: destaques.append("⚡ Over 0.5 HT")
                    if p_btts >= 60: destaques.append("🤝 BTTS")
                    if avg_corners >= 9.5: destaques.append("🚩 Over Cantos")
                    
                    header = ""
                    if wa >= 50 and wh <= 40: destaques.append("🦓 ZEBRA/VALOR"); header = "🦓 ALERTA DE ZEBRA"
                    elif wh >= 80: header = "🔥 SUPER FAVORITO (CASA)"
                    elif wa >= 80: header = "🔥 SUPER FAVORITO (VISITANTE)"
                    
                    # SE TIVER PELO MENOS UM DESTAQUE, MONTA O CARD
                    if destaques:
                        destaque_str = " | ".join(destaques)
                        if not header: header = "⚽ ANÁLISE PRÉ-JOGO"
                        
                        txt = f"{header}\n"
                        txt += f"🏆 *{row.get('League','-').upper()}*\n\n"
                        txt += f"⚔️ *{h}* vs *{a}*\n"
                        txt += f"⏰ {row.get('Time','--:--')}\n\n"
                        
                        txt += f"🎯 *Destaque:* {destaque_str}\n\n"
                        
                        txt += f"📊 *PROBABILIDADES (1x2):*\n"
                        txt += f"🏠 Casa: @{get_odd(wh):.2f} ({wh:.0f}%)\n"
                        txt += f"⚖️ Empate: @{get_odd(wd):.2f} ({wd:.0f}%)\n"
                        txt += f"✈️ Visitante: @{get_odd(wa):.2f} ({wa:.0f}%)\n\n"
                        
                        txt += f"⚽ *MERCADOS DE GOLS:*\n"
                        txt += f"⚡ 0.5 HT: @{get_odd(p_05ht):.2f} ({p_05ht:.0f}%)\n"
                        txt += f"🛡️ 1.5 FT: @{get_odd(p_15ft):.2f} ({p_15ft:.0f}%)\n"
                        txt += f"🔥 2.5 FT: @{get_odd(p_25ft):.2f} ({p_25ft:.0f}%)\n"
                        txt += f"🤝 Ambas: @{get_odd(p_btts):.2f} ({p_btts:.0f}%)\n"
                        
                        if avg_corners >= 8.0: # Mostra cantos se tiver média razoável
                            txt += f"\n🚩 *CANTOS:* Avg {avg_corners:.1f}\n"

                        txt += "--------------------------------\n"
                        txt += "🤖 *GreenScore Bot*"
                        
                        enviar_msg(txt)
            except: continue

if __name__ == "__main__":
    gerar_alerta()
if __name__ == "__main__":
    gerar_alerta()
