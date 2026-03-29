import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info

# --- CONFIGURATION ---
st.set_page_config(page_title="HL HIP-3 Decoder", layout="wide")
st.title("🏛️ Hyperliquid HIP-3 (TradFi) Specialist")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- RÉCUPÉRATION DES PRIX ET NOMS ---
@st.cache_data(ttl=10)
def fetch_hip3_data():
    # On récupère tous les prix (le dictionnaire all_mids contient TOUT, même HIP-3)
    all_prices = info.all_mids()
    
    # On filtre les actifs HIP-3 (format ISSUER:ASSET)
    hip3_tickers = [t for t in all_prices.keys() if ":" in t]
    
    return all_prices, hip3_tickers

prices, hip3_list = fetch_hip3_data()

# --- INTERFACE ---
st.sidebar.header("Scan HIP-3")
if not hip3_list:
    st.sidebar.warning("Aucun actif avec ':' détecté. Tentative de scan par mots clés...")
    # Fallback : scanne tout ce qui contient NVDA ou HOOD
    hip3_list = [t for t in prices.keys() if any(x in t for x in ["NVDA", "HOOD", "TSLA", "AAPL"])]

search = st.sidebar.text_input("Filtrer un stock (ex: NVDA)", "NVDA").upper()
filtered_hip3 = [t for t in hip3_list if search in t]

# --- LOGIQUE DE COMPARAISON ---
st.subheader(f"Résultats pour : {search}")

if filtered_hip3:
    # On essaie de grouper les paires par actif (ex: trouver toutes les déclinaisons de NVDA)
    # Les noms ressemblent à : 'XYZ:NVDA-USDH', 'XYZ:NVDA-USDT', etc.
    data = []
    for ticker in filtered_hip3:
        data.append({
            "Ticker Complet": ticker,
            "Prix Actuel": float(prices.get(ticker, 0)),
        })
    
    df = pd.DataFrame(data)
    st.table(df)
    
    # Tentative d'arbitrage automatique
    if len(df) >= 2:
        st.info("💡 Plusieurs paires détectées pour cet actif. Calcul du spread...")
        # On compare la paire la moins chère et la plus chère
        df['Prix Actuel'] = df['Prix Actuel'].astype(float)
        p_min = df['Prix Actuel'].min()
        p_max = df['Prix Actuel'].max()
        t_min = df.loc[df['Prix Actuel'].idxmin(), 'Ticker Complet']
        t_max = df.loc[df['Prix Actuel'].idxmax(), 'Ticker Complet']
        
        spread_pct = ((p_max - p_min) / p_min) * 100
        
        c1, c2 = st.columns(2)
        c1.metric("Spread Détecté", f"{spread_pct:.4f}%")
        c1.write(f"Acheter: `{t_min}` / Vendre: `{t_max}`")
        
        # Funding (Optionnel - si disponible)
        if st.button("Récupérer Funding Rates"):
            for t in [t_min, t_max]:
                try:
                    f = info.funding_history(t, int(time.time()*1000)-3600000, int(time.time()*1000))
                    st.write(f"Funding {t} : **{float(f[0]['fundingRate']):.6%}**")
                except:
                    st.write(f"Funding non disponible pour {t}")
else:
    st.error("Aucun actif trouvé. Essaie de chercher '@' ou de regarder la liste brute ci-dessous.")
    with st.expander("Voir TOUS les tickers de l'échange"):
        st.write(list(prices.keys()))
