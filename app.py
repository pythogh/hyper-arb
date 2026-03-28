import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="HL TradFi Arb", layout="wide")
st.title("🏛️ Hyperliquid TradFi Arbitrage Scout (USDH Edition)")

# --- INIT API ---
BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- RÉCUPÉRATION DES PRIX ---
@st.cache_data(ttl=10)
def fetch_all_prices():
    try:
        return info.all_mids()
    except Exception as e:
        st.error(f"Erreur API Prices: {e}")
        return {}

all_prices = fetch_all_prices()

# --- LOGIQUE DE DÉTECTION MANUELLE ---
# Liste des stocks connus sur HL TradFi (HIP-3)
known_stocks = ["NVDA", "HOOD", "TSLA", "AAPL", "GOOGL", "MSFT", "META", "AMZN", "NFLX", "COIN", "MSTR"]
stable_suffixes = ["-USDT", "-USDH"]

st.sidebar.header("Configuration")
selected_stable = st.sidebar.selectbox("Comparer USDC contre :", stable_suffixes)

# --- ANALYSE ---
data_rows = []

if all_prices:
    for stock in known_stocks:
        # On teste différentes variantes de noms que HL pourrait utiliser
        # 1. Direct (ex: NVDA)
        # 2. Préfixé (ex: @NVDA)
        # 3. Suffixé (ex: NVDA/USD)
        
        variants = [stock, f"@{stock}", f"{stock}/USD"]
        
        for v in variants:
            ticker_a = v
            ticker_b = f"{v}{selected_stable}"
            
            p_a = float(all_prices.get(ticker_a, 0))
            p_b = float(all_prices.get(ticker_b, 0))
            
            if p_a > 0 and p_b > 0:
                spread = ((p_b - p_a) / p_a) * 100
                
                # Récupération Funding rapide
                try:
                    # On prend le dernier taux (index 0)
                    end = int(time.time() * 1000)
                    f_a = float(info.funding_history(ticker_a, end-3600000, end)[0]['fundingRate'])
                    f_b = float(info.funding_history(ticker_b, end-3600000, end)[0]['fundingRate'])
                    net_apr = (f_b - f_a) * 24 * 365 * 100
                except:
                    f_a, f_b, net_apr = 0, 0, 0

                data_rows.append({
                    "Stock": stock,
                    "Ticker A": ticker_a,
                    "Ticker B": ticker_b,
                    "Prix A": p_a,
                    "Prix B": p_b,
                    "Spread %": round(spread, 4),
                    "Net APR %": round(net_apr, 2)
                })
                break # Si on a trouvé une variante qui marche, on passe au stock suivant

# --- AFFICHAGE ---
if data_rows:
    df = pd.DataFrame(data_rows)
    st.success(f"Détecté {len(df)} opportunités d'arbitrage !")
    
    st.dataframe(df.style.background_gradient(subset=['Net APR %'], cmap='RdYlGn'), use_container_width=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Stock'], y=df['Spread %'], name="Spread Prix %"))
    fig.add_trace(go.Scatter(x=df['Stock'], y=df['Net APR %'], name="APR Funding %", yaxis="y2"))
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aucun actif TradFi détecté avec les noms standards.")
    
    with st.expander("🛠️ DEBUG : Cliquer ici pour voir les noms de TOUS les actifs HIP-3"):
        # On va chercher spécifiquement les actifs qui ont un '-' dans le nom mais qui ne sont pas des perps classiques
        all_keys = sorted(list(all_prices.keys()))
        hip3_candidates = [k for k in all_keys if "-" in k and any(s in k for s in stable_suffixes)]
        st.write("Candidats potentiels (contenant USDT ou USDH) :", hip3_candidates)
        st.write("Aperçu de 50 tickers au hasard :", all_keys[:50])

if st.button("🔄 Rafraîchir"):
    st.cache_data.clear()
    st.rerun()
