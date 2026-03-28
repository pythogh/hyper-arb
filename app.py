import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="HL HIP-3 Scanner", layout="wide")
st.title("🏛️ Hyperliquid HIP-3 (TradFi) Scanner")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- RÉCUPÉRATION DES ASSETS SPOT (HIP-3) ---
@st.cache_data(ttl=60)
def get_hip3_metadata():
    try:
        # C'est ICI que se trouvent les stocks !
        spot_meta = info.spot_meta()
        universe = spot_meta.get('universe', [])
        tokens = spot_meta.get('tokens', [])
        
        # On crée un mapping ID -> Nom (ex: 41 -> @NVDA)
        token_map = {t['index']: t['name'] for t in tokens}
        
        # On cherche les paires de trading (ex: @NVDA/USDC, @NVDA/USDT)
        pairs = []
        for pair in universe:
            # pair['tokens'] contient les IDs des deux tokens de la paire
            t1 = token_map.get(pair['tokens'][0])
            t2 = token_map.get(pair['tokens'][1])
            pairs.append({
                "name": pair['name'], # ex: "@1/USDC"
                "base": t1,           # ex: "@1"
                "quote": t2,          # ex: "USDC"
                "pair_index": pair['index']
            })
        return pairs
    except Exception as e:
        st.error(f"Erreur lors de la lecture du Spot Meta : {e}")
        return []

# --- RÉCUPÉRATION DES PRIX SPOT ---
@st.cache_data(ttl=10)
def get_spot_prices():
    try:
        # Pour le spot, l'endpoint peut différer de all_mids()
        # On utilise souvent l'état complet du registre spot
        return info.all_mids() 
    except:
        return {}

# --- LOGIQUE D'ARBITRAGE ---
all_pairs = get_hip3_metadata()
all_prices = get_spot_prices()

# On regroupe par actif de base (ex: @1) pour trouver les prix en USDC, USDT, USDH
arb_map = {}
for p in all_pairs:
    base = p['base']
    quote = p['quote']
    pair_name = p['name']
    price = float(all_prices.get(pair_name, 0))
    
    if base not in arb_map:
        arb_map[base] = {}
    arb_map[base][quote] = price

# --- INTERFACE ---
st.sidebar.header("Paramètres HIP-3")
stable_to_compare = st.sidebar.selectbox("Comparer USDC contre :", ["USDT", "USDH"])

results = []
for asset, quotes in arb_map.items():
    p_usdc = quotes.get("USDC", 0)
    p_target = quotes.get(stable_to_compare, 0)
    
    if p_usdc > 0 and p_target > 0:
        spread = ((p_target - p_usdc) / p_usdc) * 100
        results.append({
            "Actif": asset,
            "Prix USDC": p_usdc,
            f"Prix {stable_to_compare}": p_target,
            "Spread %": round(spread, 4)
        })

if results:
    df = pd.DataFrame(results)
    st.success(f"Détecté {len(df)} actifs HIP-3 avec double cotation.")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Aucun arbitrage détecté entre USDC et le stable choisi.")
    with st.expander("🔍 Voir toutes les paires SPOT détectées (Debug)"):
        st.write(all_pairs)

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
