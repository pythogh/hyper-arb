import streamlit as st
import pandas as pd
from hyperliquid.info import Info

# --- CONFIG ---
st.set_page_config(page_title="HL Fast Arb", layout="wide")
st.title("⚡ Hyperliquid Fast TradFi Scout")

# Initialisation simple
BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def get_api():
    return Info(BASE_URL)

info = get_api()

# Mapping des IDs que TU as trouvé dans les logs
ID_MAP = {
    "@407": "TSLA",
    "@408": "NVDA",
    "@412": "GOOGL",
    "@411": "SLV"
}

# --- RÉCUPÉRATION CIBLÉE ---
def fetch_data():
    try:
        # On récupère TOUS les prix une seule fois
        with st.spinner("Récupération des prix en cours..."):
            all_mids = info.all_mids()
        return all_mids
    except Exception as e:
        st.error(f"Erreur de connexion API : {e}")
        return None

prices = fetch_data()

if prices:
    st.success("Connexion API établie.")
    
    results = []
    # On boucle uniquement sur nos stocks cibles
    for asset_id, name in ID_MAP.items():
        # On cherche manuellement les paires dans le dictionnaire
        # Hyperliquid utilise souvent / ou rien
        p_usdc = float(prices.get(asset_id, 0))
        p_usdt = float(prices.get(f"{asset_id}/USDT", 0))
        p_usdh = float(prices.get(f"{asset_id}/USDH", 0))
        
        # On n'ajoute que si on a au moins l'USDC et un autre
        if p_usdc > 0:
            results.append({
                "Action": name,
                "ID": asset_id,
                "USDC": p_usdc,
                "USDT": p_usdt if p_usdt > 0 else "N/A",
                "USDH": p_usdh if p_usdh > 0 else "N/A"
            })

    if results:
        df = pd.DataFrame(results)
        
        # Calcul du spread USDT vs USDC pour l'exemple
        def calc_spread(row):
            try:
                if row['USDT'] != "N/A":
                    return round(((row['USDT'] - row['USDC']) / row['USDC']) * 100, 4)
            except:
                pass
            return 0.0

        df['Spread USDT %'] = df.apply(calc_spread, axis=1)
        
        st.subheader("Tableau des Spreads")
        st.table(df)
        
    else:
        st.warning("Prix USDC introuvables pour ces IDs. Vérifie le format dans le debug ci-dessous.")

    # --- DEBUG SIMPLE ---
    with st.expander("🛠️ DEBUG : Voir les 20 premières clés de l'API"):
        st.write(list(prices.keys())[:20])
else:
    st.error("Impossible de joindre l'API. Vérifie ta connexion internet ou si Hyperliquid est en maintenance.")

if st.button("🔄 Rafraîchir Manuellement"):
    st.cache_data.clear()
    st.rerun()
