import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="Hyperliquid Arb Scout", layout="wide")
st.title("📊 Hyperliquid Stock Arbitrage & Funding Scout")

# --- INITIALISATION API ---
BASE_URL = "https://api.hyperliquid.xyz"
try:
    info = Info(BASE_URL)
except Exception as e:
    st.error(f"Erreur d'initialisation : {e}")
    st.stop()

# --- FONCTIONS DE RÉCUPÉRATION ---

@st.cache_data(ttl=60)
def get_universe_data():
    """Récupère tous les noms d'actifs disponibles"""
    try:
        meta = info.meta()
        # On extrait tous les noms des actifs du "universe"
        names = [coin['name'] for coin in meta['universe']]
        return names
    except:
        return []

@st.cache_data(ttl=30)
def get_live_prices():
    """Récupère les prix mid de tous les actifs"""
    try:
        return info.all_mids()
    except:
        return {}

@st.cache_data(ttl=300)
def get_funding_info(coin):
    """Récupère le taux de funding horaire actuel"""
    end_time = int(time.time() * 1000)
    start_time = end_time - (8 * 60 * 60 * 1000)
    try:
        data = info.funding_history(coin, start_time, end_time)
        if data:
            return float(data[0]['fundingRate'])
    except:
        pass
    return 0.0

# --- LOGIQUE DE DÉTECTION DES PAIRES ---
all_available_names = get_universe_data()
all_prices = get_live_prices()

# On filtre pour trouver les paires qui ont un équivalent -USDT ou -USDS
# Sur HL, la version USDC est souvent juste le nom (ex: "NVDA")
base_stocks = []
for name in all_available_names:
    if f"{name}-USDT" in all_available_names or f"{name}-USDS" in all_available_names:
        if "-" not in name: # On évite de prendre le -USDT comme base
            base_stocks.append(name)

# --- SIDEBAR ---
st.sidebar.header("Configuration")
target_stocks = st.sidebar.multiselect(
    "Actions / Actifs détectés", 
    options=sorted(base_stocks) if base_stocks else ["Vérification en cours..."],
    default=base_stocks[:3] if len(base_stocks) > 3 else base_stocks
)

stable_choice = st.sidebar.selectbox("Comparer USDC contre :", ["USDT", "USDS"])

if st.sidebar.button("🔄 Forcer l'actualisation"):
    st.cache_data.clear()
    st.rerun()

# --- CALCUL DES OPPORTUNITÉS ---
data_rows = []

if not target_stocks:
    st.info("Sélectionnez des actifs dans la barre latérale. Si la liste est vide, l'API ne renvoie pas de paires synthétiques pour le moment.")
else:
    with st.spinner('Analyse en cours...'):
        for stock in target_stocks:
            ticker_a = stock # Version USDC
            ticker_b = f"{stock}-{stable_choice}" # Version choisie
            
            p_a = float(all_prices.get(ticker_a, 0))
            p_b = float(all_prices.get(ticker_b, 0))
            
            if p_a > 0 and p_b > 0:
                spread_pct = ((p_b - p_a) / p_a) * 100
                
                f_a = get_funding_info(ticker_a)
                f_b = get_funding_info(ticker_b)
                
                # Arbitrage : Short B, Long A
                net_apr = (f_b - f_a) * 24 * 365 * 100
                
                data_rows.append({
                    "Actif": stock,
                    f"Prix USDC": p_a,
                    f"Prix {stable_choice}": p_b,
                    "Spread %": round(spread_pct, 4),
                    "Net APR %": round(net_apr, 2),
                    "Funding A (h)": f"{f_a:.5%}",
                    "Funding B (h)": f"{f_b:.5%}"
                })

# --- AFFICHAGE ---
if data_rows:
    df = pd.DataFrame(data_rows)
    
    # Métriques
    cols = st.columns(len(data_rows))
    for i, row in df.iterrows():
        cols[i].metric(row['Actif'], f"{row['Spread %']}%", f"{row['Net APR %']}% APR")

    st.write("---")
    st.subheader("Tableau de bord de l'arbitrage")
    st.dataframe(df, use_container_width=True)
    
    # Graphique
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Actif'], y=df['Spread %'], name="Spread %"))
    fig.add_trace(go.Scatter(x=df['Actif'], y=df['Net APR %'], name="APR %", yaxis="y2"))
    fig.update_layout(
        yaxis2=dict(overlaying='y', side='right'),
        template="plotly_dark",
        legend=dict(orientation="h")
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    if target_stocks:
        st.error("Données de prix introuvables pour les paires sélectionnées. Il est possible que les marchés soient fermés ou que les noms aient changé.")
