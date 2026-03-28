import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="HL TradFi Arb", layout="wide")
st.title("🏛️ Hyperliquid TradFi (HIP-3) Arbitrage Scout")

# --- INIT API ---
BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- RÉCUPÉRATION DES MÉTADONNÉES HIP-3 ---
@st.cache_data(ttl=60)
def fetch_tradfi_universe():
    try:
        meta = info.meta()
        universe = meta.get('universe', [])
        
        # Sur HL, les stocks HIP-3 ont souvent un nom qui commence par '@' 
        # ou des propriétés spécifiques dans le dictionnaire meta.
        # On va lister tout ce qui ressemble à un stock ou un index.
        tradfi_assets = []
        for asset in universe:
            name = asset['name']
            # On cherche les paires de base (souvent @1, @2... ou direct NVDA)
            # Et on vérifie si une version -USDT existe dans le même univers
            tradfi_assets.append(name)
            
        return tradfi_assets, meta
    except Exception as e:
        st.error(f"Erreur meta : {e}")
        return [], {}

# --- LOGIQUE DE DÉTECTION DES PAIRES ARB ---
universe_names, full_meta = fetch_tradfi_universe()
prices = info.all_mids()

hip3_pairs = []
for name in universe_names:
    # On cherche le pattern : 'Asset' vs 'Asset-USDT' ou 'Asset-USDS'
    # Dans HIP-3, l'actif de base est souvent @NUMERO
    if f"{name}-USDT" in universe_names:
        hip3_pairs.append(name)

# --- INTERFACE SIDEBAR ---
st.sidebar.header("Configuration TradFi")
selected_assets = st.sidebar.multiselect(
    "Actifs HIP-3 détectés",
    options=sorted(hip3_pairs) if hip3_pairs else ["NVDA", "HOOD", "AAPL", "TSLA"],
    default=hip3_pairs[:5] if len(hip3_pairs) > 5 else hip3_pairs
)

stable_choice = st.sidebar.selectbox("Stablecoin de comparaison", ["USDT", "USDS"])

# --- DASHBOARD ---
if not selected_assets:
    st.info("Sélectionnez des actifs. Si la liste est vide, c'est que le filtre HIP-3 doit être ajusté selon les noms réels.")
    with st.expander("Consulter tous les noms de l'Universe (HIP-3 Debug)"):
        st.write(universe_names)
else:
    results = []
    for asset in selected_assets:
        ticker_usdc = asset
        ticker_stable = f"{asset}-{stable_choice}"
        
        p_usdc = float(prices.get(ticker_usdc, 0))
        p_stable = float(prices.get(ticker_stable, 0))
        
        if p_usdc > 0 and p_stable > 0:
            spread = ((p_stable - p_usdc) / p_usdc) * 100
            
            # Récupération Funding rapide
            try:
                # On récupère le dernier taux pour les deux
                f_usdc = float(info.funding_history(ticker_usdc, int(time.time()*1000)-3600000, int(time.time()*1000))[0]['fundingRate'])
                f_stable = float(info.funding_history(ticker_stable, int(time.time()*1000)-3600000, int(time.time()*1000))[0]['fundingRate'])
                apr = (f_stable - f_usdc) * 24 * 365 * 100
            except:
                f_usdc, f_stable, apr = 0, 0, 0

            results.append({
                "Asset": asset,
                "Price USDC": p_usdc,
                f"Price {stable_choice}": p_stable,
                "Spread %": round(spread, 4),
                "Net APR %": round(apr, 2)
            })

    if results:
        df = pd.DataFrame(results)
        st.dataframe(df.style.background_gradient(subset=['Net APR %'], cmap='RdYlGn'), use_container_width=True)
        
        # Graphique
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Asset'], y=df['Spread %'], name="Spread %", marker_color='gold'))
        fig.add_trace(go.Scatter(x=df['Asset'], y=df['Net APR %'], name="APR %", yaxis="y2", line=dict(color='cyan')))
        fig.update_layout(yaxis2=dict(overlaying='y', side='right'), template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
