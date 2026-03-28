import streamlit as st
import pandas as pd
from hyperliquid.info import Info
from hyperliquid.utils import constants
import plotly.graph_objects as go

# Config Streamlit
st.set_page_config(page_title="Hyperliquid Arb Finder", layout="wide")
st.title("📊 Hyperliquid Stock Arbitrage Scout")

# Initialisation de l'API (Public Info)
info = Info(constants.MAINNET_API_URL, skip_gemini_low_tier_warning=True)

@st.cache_data(ttl=60)
def get_all_mids():
    # Récupère tous les prix "mid" (milieu du spread) du marché
    return info.all_mids()

def get_market_metadata():
    # Récupère la liste des actifs et leurs noms
    meta = info.meta()
    return meta['universe']

# --- SIDEBAR : Filtres ---
st.sidebar.header("Configuration")
target_stocks = st.sidebar.multiselect(
    "Actions à surveiller", 
    ["NVDA", "HOOD", "GOOGL", "MSFT", "TSLA", "AAPL", "META"],
    default=["NVDA", "HOOD"]
)

# --- LOGIQUE DE CALCUL ---
all_prices = get_all_mids()
universe = get_market_metadata()

data = []

for stock in target_stocks:
    # On cherche les déclinaisons (ex: NVDA, NVDA-USDT, NVDA-USDS)
    # Note : Sur HL, la paire de base (USDC) est souvent juste le nom du ticker
    p_usdc = float(all_prices.get(stock, 0))
    p_usdt = float(all_prices.get(f"{stock}-USDT", 0))
    
    if p_usdc > 0 and p_usdt > 0:
        spread = p_usdt - p_usdc
        spread_pct = (spread / p_usdc) * 100
        
        data.append({
            "Ticker": stock,
            "Price USDC": round(p_usdc, 3),
            "Price USDT": round(p_usdt, 3),
            "Spread ($)": round(spread, 3),
            "Spread (%)": round(spread_pct, 4)
        })

# --- AFFICHAGE ---
if data:
    df = pd.DataFrame(data)
    
    # Dashboard Metrics
    cols = st.columns(len(data))
    for i, row in df.iterrows():
        cols[i].metric(row['Ticker'], f"${row['Price USDC']}", f"{row['Spread (%)']}%")

    st.subheader("Tableau comparatif des spreads")
    st.dataframe(df.style.background_gradient(subset=['Spread (%)'], cmap='RdYlGn_r'), use_container_width=True)

    # Graphique Plotly
    fig = go.Figure(data=[
        go.Bar(name='Spread %', x=df['Ticker'], y=df['Spread (%)'])
    ])
    fig.update_layout(title="Écart de prix relatif (USDT vs USDC)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aucune paire correspondante trouvée. Vérifie que les marchés USDT sont ouverts.")

st.info("💡 Prochaine étape : Ajouter le 'Funding Rate' pour calculer le profit net réel.")
