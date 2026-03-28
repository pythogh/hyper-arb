import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="HL Arb Debugger", layout="wide")
st.title("🔍 Hyperliquid API Debugger & Arb Scout")

# --- INITIALISATION API ---
BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- RÉCUPÉRATION BRUTE DES PRIX ---
@st.cache_data(ttl=10)
def fetch_all_prices():
    try:
        prices = info.all_mids()
        return prices
    except Exception as e:
        st.error(f"Erreur lors de l'appel API all_mids : {e}")
        return {}

prices = fetch_all_prices()

# --- SECTION DIAGNOSTIC (TRÈS IMPORTANT) ---
with st.expander("🛠️ DEBUG : Liste de tous les Tickers détectés par l'API"):
    if prices:
        all_tickers = sorted(list(prices.keys()))
        st.write(f"Nombre total d'actifs trouvés : {len(all_tickers)}")
        # On affiche les 20 premiers et ceux qui contiennent NVDA ou HOOD
        search_term = st.text_input("Rechercher un ticker spécifique (ex: NVDA, HOOD, @) :", "NVDA")
        filtered_list = [t for t in all_tickers if search_term.upper() in t.upper()]
        st.write("Résultats de recherche :", filtered_list)
        st.write("Tous les tickers :", all_tickers)
    else:
        st.warning("L'API n'a renvoyé aucun prix.")

# --- LOGIQUE D'ARBITRAGE ---
st.sidebar.header("Configuration")

# Tentative de détection des paires
st.sidebar.subheader("Paires détectées")
pairs_to_check = []
if prices:
    for t in prices.keys():
        # Si on trouve 'NVDA' et 'NVDA-USDT', ou '@NVDA' et '@NVDA-USDT'
        if "-USDT" in t:
            base_name = t.replace("-USDT", "")
            if base_name in prices:
                pairs_to_check.append(base_name)

target_stocks = st.sidebar.multiselect(
    "Actifs à arbitrer", 
    options=sorted(list(set(pairs_to_check))) if pairs_to_check else ["NVDA", "HOOD", "TSLA"],
    default=pairs_to_check[:5] if pairs_to_check else []
)

stable_choice = st.sidebar.selectbox("Comparer USDC vs :", ["USDT", "USDS"])

# --- CALCUL ---
data_rows = []
if target_stocks:
    for stock in target_stocks:
        p_usdc = float(prices.get(stock, 0))
        p_stable = float(prices.get(f"{stock}-{stable_choice}", 0))
        
        if p_usdc > 0 and p_stable > 0:
            spread = ((p_stable - p_usdc) / p_usdc) * 100
            
            # Pour le debug, on affiche simplifié sans le funding pour l'instant
            data_rows.append({
                "Ticker": stock,
                "Prix USDC": p_usdc,
                f"Prix {stable_choice}": p_stable,
                "Spread %": round(spread, 4)
            })

if data_rows:
    st.success(f"Données récupérées pour {len(data_rows)} actifs.")
    df = pd.DataFrame(data_rows)
    st.dataframe(df, use_container_width=True)
    
    fig = go.Figure(go.Bar(x=df['Ticker'], y=df['Spread %'], marker_color='gold'))
    fig.update_layout(title="Spread en temps réel (%)", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sélectionnez des actifs valides. Utilisez le menu 'DEBUG' au-dessus pour voir comment l'API nomme vos stocks.")
