import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

st.set_page_config(page_title="HL Arb Finder", layout="wide")

# --- INIT ---
BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- DATA ---
@st.cache_data(ttl=10)
def fetch_data():
    prices = info.all_mids()
    return prices

prices = fetch_data()

# --- LOGIQUE DE DÉTECTION ---
# On identifie les paires de type 'ACTIF' et 'ACTIF-USDT'
detected_pairs = []
if prices:
    for ticker in prices.keys():
        if "-USDT" in ticker:
            base = ticker.replace("-USDT", "")
            if base in prices:
                detected_pairs.append(base)

# --- INTERFACE ---
st.title("🚀 Arbitrage Opportunité")

st.sidebar.header("Configuration")
if not detected_pairs:
    st.sidebar.error("Aucune paire -USDT détectée. Regardez les noms bruts.")
    # On affiche les 50 premiers tickers pour t'aider à trouver le bon format
    st.sidebar.write("Exemples de noms réels :", list(prices.keys())[:20])
else:
    st.sidebar.success(f"{len(detected_pairs)} paires d'arbitrage trouvées !")

# Sélection de l'actif
selected_stock = st.sidebar.selectbox("Choisir l'actif à analyser", options=sorted(detected_pairs) if detected_pairs else ["Aucun"])

# --- CALCUL ---
if selected_stock != "Aucun":
    p_usdc = float(prices.get(selected_stock))
    p_usdt = float(prices.get(f"{selected_stock}-USDT"))
    
    spread = ((p_usdt - p_usdc) / p_usdc) * 100
    
    # Affichage
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Prix {selected_stock} (USDC)", f"${p_usdc:,.3f}")
    col2.metric(f"Prix {selected_stock} (USDT)", f"${p_usdt:,.3f}")
    col3.metric("Spread", f"{spread:.4f}%", delta=f"{p_usdt-p_usdc:.4f}$")

    # Historique de Funding rapide
    st.write("---")
    st.subheader(f"Comparatif Funding : {selected_stock}")
    
    with st.spinner("Récupération du funding..."):
        def get_f(coin):
            end = int(time.time() * 1000)
            data = info.funding_history(coin, end - (3600000 * 5), end)
            return float(data[0]['fundingRate']) if data else 0.0

        f_usdc = get_f(selected_stock)
        f_usdt = get_f(f"{selected_stock}-USDT")
        
        apr = (f_usdt - f_usdc) * 24 * 365 * 100
        
        c1, c2, c3 = st.columns(3)
        c1.write(f"Funding USDC: **{f_usdc:.6%}**")
        c2.write(f"Funding USDT: **{f_usdt:.6%}**")
        c3.info(f"APR Arbitrage: **{apr:.2f}%**")

else:
    st.warning("Veuillez sélectionner un actif dans la liste à gauche.")
    st.write("Si la liste est vide, c'est que les stocks n'utilisent pas le suffixe -USDT sur cet exchange.")
