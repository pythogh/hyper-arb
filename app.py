import streamlit as st
import pandas as pd
from hyperliquid.info import Info

# --- CONFIG ---
st.set_page_config(page_title="HL HIP-3 Spot Scanner", layout="wide")
st.title("🏛️ Scanner de Prix Spot HIP-3 (TradFi)")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def get_api():
    return Info(BASE_URL)

info = get_api()

def fetch_hip3_spot_data():
    try:
        # Cet endpoint renvoie Metadata + Prix (Asset Contexts)
        data = info.spot_meta_and_asset_ctxs()
        universe = data[0]['universe'] # Liste des paires
        tokens = data[0]['tokens']     # Liste des actifs
        ctxs = data[1]                 # Liste des prix et stats
        
        # 1. Mapping ID -> Nom (ex: 408 -> NVDA)
        token_map = {t['index']: t['name'] for t in tokens}
        
        # 2. Construction du tableau des prix
        rows = []
        for i, pair in enumerate(universe):
            pair_name = pair['name'] # ex: "@408/USDT"
            base_token_id = pair['tokens'][0]
            quote_token_id = pair['tokens'][1]
            
            base_symbol = token_map.get(base_token_id, f"@{base_token_id}")
            quote_symbol = token_map.get(quote_token_id, f"@{quote_token_id}")
            
            # Le prix est dans le context à l'index correspondant
            price = "N/A"
            if i < len(ctxs):
                price = float(ctxs[i]['mid_sz']) if ctxs[i]['mid_sz'] else "N/A"
            
            rows.append({
                "Paire": pair_name,
                "Actif": base_symbol,
                "Stable": quote_symbol,
                "Prix": price
            })
        return rows
    except Exception as e:
        st.error(f"Erreur API Spot : {e}")
        return []

data = fetch_hip3_spot_data()

if data:
    df = pd.DataFrame(data)
    
    # Filtrage sur tes IDs cibles (407, 408, etc.)
    target_ids = ["407", "408", "412"]
    filtered_df = df[df['Paire'].str.contains('|'.join(target_ids))]

    st.subheader("📊 Prix Spot Détectés (Moteur HIP-3)")
    if not filtered_df.empty:
        st.table(filtered_df)
        
        # --- ANALYSE D'ARBITRAGE ---
        st.write("---")
        st.subheader("💡 Analyse d'Arbitrage Rapide")
        # On regroupe par actif pour voir les écarts entre USDC/USDT/USDH
        for asset in filtered_df['Actif'].unique():
            asset_rows = filtered_df[filtered_df['Actif'] == asset]
            if len(asset_rows) > 1:
                st.write(f"Comparaison pour **{asset}** :")
                st.dataframe(asset_rows[['Stable', 'Prix']], use_container_width=True)
    else:
        st.warning("Aucune des paires cibles n'a été trouvée dans le Spot Universe.")
        st.write("Voici TOUTES les paires Spot détectées :", df)
else:
    st.info("Aucune donnée Spot reçue.")

st.button("🔄 Rafraîchir")
