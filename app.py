import streamlit as st
import pandas as pd
from hyperliquid.info import Info

# --- CONFIG ---
st.set_page_config(page_title="HL Ultimate Finder", layout="wide")
st.title("🕵️ Le Détective Hyperliquid (HIP-3)")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def get_api():
    return Info(BASE_URL)

info = get_api()

# Tes IDs cibles
TARGET_IDS = ["407", "408", "412", "411"] 
# (On enlève le @ pour faire une recherche textuelle large)

def fetch_data():
    try:
        return info.all_mids()
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return {}

prices = fetch_data()

if prices:
    st.success(f"API Connectée - {len(prices)} actifs trouvés.")
    
    all_keys = list(prices.keys())
    found_data = []

    for tid in TARGET_IDS:
        # On cherche toutes les clés qui contiennent ce numéro (ex: "408")
        matches = [k for k in all_keys if tid in k]
        
        for m in matches:
            found_data.append({
                "ID Recherché": tid,
                "Clé Réelle (Ticker)": m,
                "Prix": float(prices[m])
            })

    if found_data:
        df = pd.DataFrame(found_data)
        st.subheader("🎯 Correspondances trouvées dans l'API")
        st.table(df)
        
        # Petit outil d'analyse de spread automatique
        if len(df) > 1:
            st.info("💡 Pour arbitrer : comparez les prix des clés ayant le même ID mais des suffixes différents (ex: /USDC vs /USDT).")
    else:
        st.warning("Aucune clé contenant ces IDs n'a été trouvée dans 'all_mids'.")
        with st.expander("🧐 Inspecter les 100 premières clés brutes pour trouver le format"):
            st.write(all_keys[:100])
            
else:
    st.error("Aucune donnée reçue de l'API.")

st.button("🔄 Scanner à nouveau")
