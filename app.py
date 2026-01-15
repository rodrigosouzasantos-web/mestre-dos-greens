import pandas as pd
import requests
import io
import time
from datetime import datetime

# --- 1. CONFIGURAÇÃO (PREENCHA AQUI!) ---
TELEGRAM_TOKEN = "8571442533:AAFbqfHsE1oTdwt2yarJGFpqWgST3-UIUwA" 
CHAT_ID = "-1003590805331"       

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except:
        pass

# --- 2. LINKS ---
URL_HISTORY = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/past-seasons/matches/leagues-total/all_matches_combined.csv"
URL_TODAY = "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv"

# Pega a data de hoje para o Cabeçalho
data_hoje = datetime.now().strftime("%d/%m/%Y")

print(f"🔄 Mestre dos Greens iniciando trabalhos para {data_hoje}...")

# --- 3. LIMPEZA VISUAL (CABEÇALHO) ---
msg_abertura = (
    f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
    f"📅 *RELATÓRIO DO DIA: {data_hoje}* 🚀\n"
    f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
    f"🔎 _Iniciando varredura no mercado..._"
)
send_telegram(msg_abertura)

print("1. Baixando Histórico...")
try:
    s = requests.get(URL_HISTORY).content
    try:
        df_history = pd.read_csv(io.StringIO(s.decode('utf-8')), low_memory=False)
    except:
        df_history = pd.read_csv(io.StringIO(s.decode('utf-8')), sep=';', low_memory=False)

    # Mapeamento
    df_history.columns = [c.strip() for c in df_history.columns]
    rename_map = {
        'date': 'Date', 'date_unix': 'DateUnix',
        'home_name': 'HomeTeam', 'away_name': 'AwayTeam',
        'homeGoalCount': 'FTHG', 'awayGoalCount': 'FTAG',
        'ht_goals_team_a': 'HTHG', 'ht_goals_team_b': 'HTAG',
        'team_a_corners': 'HC', 'team_b_corners': 'AC',
        'team_a_cards_num': 'HY', 'team_b_cards_num': 'AY'
    }
    for old, new in rename_map.items():
        if old in df_history.columns:
            df_history.rename(columns={old: new}, inplace=True)
            
    if 'Date' not in df_history.columns and 'DateUnix' in df_history.columns:
        df_history['Date'] = pd.to_datetime(df_history['DateUnix'], unit='s')
    else:
        df_history['Date'] = pd.to_datetime(df_history['Date'], errors='coerce')

    df_recent = df_history[df_history['Date'].dt.year >= 2024].copy()
    
    cols_stats = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HC', 'AC', 'HY', 'AY']
    for c in cols_stats:
        if c not in df_recent.columns:
            df_recent[c] = 0
        df_recent[c] = pd.to_numeric(df_recent[c], errors='coerce').fillna(0)
    
    df_recent['WinH'] = (df_recent['FTHG'] > df_recent['FTAG']).astype(int)
    df_recent['WinA'] = (df_recent['FTAG'] > df_recent['FTHG']).astype(int)

    print("2. Baixando Agenda...")
    df_today = pd.read_csv(URL_TODAY)
    rename_today = {'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'league': 'League', 'time': 'Time'}
    df_today.rename(columns=rename_today, inplace=True)
    if 'HomeTeam' not in df_today.columns:
         df_today['HomeTeam'] = df_today.iloc[:, 0]
         df_today['AwayTeam'] = df_today.iloc[:, 1]

    print(f"✅ Calibrado! Analisando {len(df_today)} jogos...")
    
    count_alertas = 0

    # --- 4. SCANNER ---
    for index, row in df_today.iterrows():
        home = row.get('HomeTeam', 'Casa')
        away = row.get('AwayTeam', 'Fora')
        league = row.get('League', 'Liga')
        horario = row.get('Time', '--:--')
        
        stats_h = df_recent[df_recent['HomeTeam'] == home]
        stats_a = df_recent[df_recent['AwayTeam'] == away]
        
        if len(stats_h) >= 3 and len(stats_a) >= 3:
            
            # Médias e Probabilidades
            avg_gols_total = (stats_h['FTHG'].mean() + stats_h['FTAG'].mean() + stats_a['FTHG'].mean() + stats_a['FTAG'].mean()) / 2
            avg_cantos = (stats_h['HC'].mean() + stats_h['AC'].mean() + stats_a['HC'].mean() + stats_a['AC'].mean()) / 2
            avg_cartoes = (stats_h['HY'].mean() + stats_h['AY'].mean() + stats_a['HY'].mean() + stats_a['AY'].mean()) / 2
            
            prob_ht = (((stats_h['HTHG']+stats_h['HTAG']) > 0).mean() + ((stats_a['HTHG']+stats_a['HTAG']) > 0).mean()) / 2
            prob_05_ft = (((stats_h['FTHG']+stats_h['FTAG']) > 0).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 0).mean()) / 2
            prob_15_ft = (((stats_h['FTHG']+stats_h['FTAG']) > 1.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 1.5).mean()) / 2
            prob_25_ft = (((stats_h['FTHG']+stats_h['FTAG']) > 2.5).mean() + ((stats_a['FTHG']+stats_a['FTAG']) > 2.5).mean()) / 2
            
            btts_h = ((stats_h['FTHG'] > 0) & (stats_h['FTAG'] > 0)).mean()
            btts_a = ((stats_a['FTHG'] > 0) & (stats_a['FTAG'] > 0)).mean()
            prob_btts = (btts_h + btts_a) / 2
            
            prob_win_h = stats_h['WinH'].mean()
            prob_win_a = stats_a['WinA'].mean()

            # --- GATILHOS ---
            tips = []

            # BTTS
            if prob_btts > 0.65: tips.append(f"🤝 **Ambas Marcam (BTTS)**: Alta probabilidade ({prob_btts*100:.0f}%)")
            # Zebra
            if stats_a['FTAG'].mean() > 1.5 and stats_h['FTAG'].mean() > 1.5:
                tips.append(f"🦁 **ALERTA ZEBRA**: Visitante marca {stats_a['FTAG'].mean():.1f} p/j")
            # Vitórias
            if prob_win_h > 0.60: tips.append(f"🏠 **Casa Vence**: {home} ({prob_win_h*100:.0f}%)")
            if prob_win_a > 0.60: tips.append(f"✈️ **Visitante Vence**: {away} ({prob_win_a*100:.0f}%)")
            # Gols
            if prob_ht > 0.75: tips.append(f"⚡ **Over 0.5 HT**: {prob_ht*100:.0f}% (Intervalo)")
            if prob_05_ft > 0.95: tips.append(f"⚽ **Over 0.5 FT**: {prob_05_ft*100:.0f}%")
            if prob_15_ft > 0.80: tips.append(f"🥅 **Over 1.5 FT**: {prob_15_ft*100:.0f}%")
            if prob_25_ft > 0.65: tips.append(f"🔥 **Over 2.5 FT**: {prob_25_ft*100:.0f}%")
            if avg_gols_total < 2.2: tips.append(f"🛡️ **Under 3.5**: Jogo Truncado")
            # Outros
            if avg_cantos > 11.0: tips.append(f"🚩 **Cantos**: +{avg_cantos:.1f}")
            if avg_cartoes > 4.5: tips.append(f"🟨 **Cartões**: +{avg_cartoes:.1f}")

            # Envio
            if tips:
                lista_tips = "\n".join(tips)
                msg = (
                    f"🔮 *ANÁLISE MESTRE DOS GREENS*\n"
                    f"🏆 {league}\n"
                    f"⚔️ *{home}* x *{away}*\n"
                    f"⏰ {horario}\n\n"
                    f"{lista_tips}\n"
                    f"➖➖➖➖➖➖➖➖"
                )
                send_telegram(msg)
                print(f"-> Enviado: {home} x {away}")
                count_alertas += 1

    # Fechamento
    if count_alertas == 0:
        msg_neg = (
            f"🚫 *Sem Oportunidades Claras Hoje ({data_hoje})*\n"
            "O mercado está difícil e não arriscaremos a banca.\n"
            "Voltamos amanhã! 🛡️"
        )
        send_telegram(msg_neg)
        print("Relatório negativo enviado.")
    else:
        msg_fim = (
            f"✅ *Fim das Análises de Hoje*\n"
            f"Foram enviadas {count_alertas} dicas de valor.\n"
            f"Lembre-se: Gestão de Banca é tudo! 💰"
        )
        send_telegram(msg_fim)
        print(f"🚀 Sucesso! {count_alertas} oportunidades.")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
