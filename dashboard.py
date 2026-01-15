import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Mestre dos Greens PRO", page_icon="⚽", layout="wide")

# --- ⚠️ ÁREA DE LINKS (VOCÊ PRECISA ATUALIZAR AQUI!) ---
# Siga o tutorial abaixo do código para pegar os links RAW corretos.
URLS_LIGAS = {
    "Jogos de Hoje": "https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/main/csv/todays_matches/todays_matches.csv",
    # Cole seus links RAW aqui embaixo:
    "Argentina_Primera_División_2016-2024": https://raw.githubusercontent.com/bet2all-scorpion/football-data-bet2all/refs/heads/main/csv/past-seasons/leagues/Argentina_Primera_Divisi%C3%B3n_2016-2024.csv" 
}

# --- FUNÇÃO DE CARREGAMENTO SEGURA ---
@st.cache_data(ttl=3600)
def load_data():
    all_dfs = []
    
    st.sidebar.markdown("### 📡 Status da Conexão")
    
    for nome, url in URLS_LIGAS.items():
        if "Exemplo" in nome: continue # Pula o exemplo
        
        try:
            # 1. Tenta baixar
            response = requests.get(url)
            
            # Se der erro 404 (Não encontrado)
            if response.status_code == 404:
                st.sidebar.warning(f"⚠️ {nome}: Link não encontrado (404)")
                continue
                
            # 2. Verifica se é CSV mesmo (e não página de erro)
            content = response.content.decode('utf-8')
            if "<!DOCTYPE html>" in content:
                st.sidebar.warning(f"⚠️ {nome}: Link incorreto (é uma página Web, não Raw)")
                continue

            # 3. Tenta Ler
            try:
                df = pd.read_csv(io.StringIO(content), low_memory=False)
            except:
                df = pd.read_csv(io.StringIO(content), sep=';', low_memory=False)

            # 4. Padroniza Colunas
            df.columns = [c.strip().lower() for c in df.columns]
            rename_map = {
                'date': 'Date', 'date_unix': 'DateUnix',
                'home_name': 'HomeTeam', 'away_name': 'AwayTeam', 'home': 'HomeTeam', 'away': 'AwayTeam',
                'fthg': 'FTHG', 'ftag': 'FTAG', 'homegoalcount': 'FTHG', 'awaygoalcount': 'FTAG',
                'team_a_corners': 'HC', 'team_b_corners': 'AC'
            }
            df.rename(columns=rename_map, inplace=True)
            
            # Cria data se não tiver
            if 'Date' not in df.columns:
                if 'DateUnix' in df.columns:
                    df['Date'] = pd.to_datetime(df['DateUnix'], unit='s')
                else:
                    st.sidebar.error(f"❌ {nome}: Arquivo sem coluna de Data")
                    continue
            
            # Filtro e Limpeza Final
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df['League'] = nome # Cria coluna com nome da liga
            
            # Garante colunas numéricas
            for c in ['FTHG', 'FTAG', 'HC', 'AC']:
                if c not in df.columns: df[c] = 0
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                
            all_dfs.append(df)
            st.sidebar.success(f"✅ {nome}: Carregado!")
            
        except Exception as e:
            st.sidebar.error(f"❌ {nome}: Erro desconhecido ({e})")

    if not all_dfs: return pd.DataFrame() # Retorna vazio se tudo falhar
    
    return pd.concat(all_dfs, ignore_index=True)

# --- APP ---
st.title("⚽ Mestre dos Greens")
df = load_data()

if not df.empty:
    # Separa Jogos de Hoje (Futuro) e Passado
    # Assumindo que o link 'Jogos de Hoje' traz datas futuras ou de hoje
    
    menu = st.radio("Menu", ["Jogos de Hoje", "Histórico e Estatísticas"], horizontal=True)
    
    if menu == "Jogos de Hoje":
        # Filtra jogos de hoje baseado na data do sistema ou da flag 'Jogos de Hoje'
        df_hoje = df[df['League'] == "Jogos de Hoje"]
        
        if not df_hoje.empty:
            st.dataframe(df_hoje[['Date', 'HomeTeam', 'AwayTeam', 'League']])
        else:
            st.info("O link 'Jogos de Hoje' não retornou partidas ou não foi configurado.")
            
    elif menu == "Histórico e Estatísticas":
        # Mostra o resto
        df_hist = df[df['League'] != "Jogos de Hoje"]
        if not df_hist.empty:
            st.metric("Total de Jogos na Base", len(df_hist))
            st.dataframe(df_hist.head())
        else:
            st.warning("Adicione os links das ligas no código para ver o histórico!")
else:
    st.warning("Nenhum dado carregado. Verifique os Links na barra lateral.")
