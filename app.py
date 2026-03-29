import streamlit as st
import pandas as pd
from hyperliquid.info import Info

# --- CONFIGURATION ---
st.set_page_config(page_title="HL NVDA Debugger", layout="wide")
st.title("🔍 Recherche de 'NVDA' sur Hyperliquid")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- BOUTON DE RECHARGE ---
if st.sidebar.button("Forcer rafraîchissement"):
    st.cache_data.clear()
    st.rerun()

# --- ÉTAPE 1 : RECHERCHE DANS LES PERPS (META) ---
st.header("1. Recherche dans l'Univers des Perps (Meta)")
try:
    meta = info.meta()
    perp_names = [asset['name'] for asset in meta.get('universe', [])]
    nvda_perps = [n for n in perp_names if "NVDA" in n.upper()]
    
    if nvda_perps:
        st.success(f"Trouvé dans Perps : {nvda_perps}")
    else:
        st.info("Aucune trace de NVDA dans les Perps classiques.")
except Exception as e:
    st.error(f"Erreur Meta Perps : {e}")

# --- ÉTAPE 2 : RECHERCHE DANS LE SPOT (SPOT_META) ---
st.header("2. Recherche dans l'Univers Spot (Spot Meta)")
try:
    spot_meta = info.spot_meta()
    
    # On regarde les Tokens (les actifs eux-mêmes)
    tokens = spot_meta.get('tokens', [])
    nvda_tokens = [t for t in tokens if "NVDA" in t['name'].upper()]
    
    # On regarde les Paires (les marchés de trading)
    universe = spot_meta.get('universe', [])
    nvda_pairs = [p['name'] for p in universe if "NVDA" in p['name'].upper()]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tokens détectés")
        if nvda_tokens:
            st.json(nvda_tokens)
        else:
            st.write("Aucun token NVDA.")
            
    with col2:
        st.subheader("Marchés (Pairs) détectés")
        if nvda_pairs:
            st.success(f"Marchés trouvés : {nvda_pairs}")
        else:
            st.write("Aucune paire NVDA.")
except Exception as e:
    st.error(f"Erreur Spot Meta : {e}")

# --- ÉTAPE 3 : PRIX EN TEMPS RÉEL ---
st.header("3. Vérification des prix (All Mids)")
try:
    all_prices = info.all_mids()
    # On cherche toutes les clés qui contiennent NVDA
    nvda_prices = {k: v for k, v in all_prices.items() if "NVDA" in k.upper()}
    
    if nvda_prices:
        st.write("Prix détectés pour :")
        st.json(nvda_prices)
    else:
        st.warning("L'API 'all_mids' ne renvoie aucun prix contenant le texte 'NVDA'.")
except Exception as e:
    st.error(f"Erreur All Mids : {e}")

# --- ÉTAPE 4 : LISTE BRUTE DES 50 PREMIERS (POUR VOIR LE FORMAT) ---
with st.expander("Voir le format des 50 premiers actifs de l'échange"):
    if 'all_prices' in locals() and all_prices:
        st.write(list(all_prices.keys())[:50])
