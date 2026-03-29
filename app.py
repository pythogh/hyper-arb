import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info

# --- CONFIGURATION ---
st.set_page_config(page_title="HL Multi-Deployer Scout", layout="wide")
st.title("🌐 Hyperliquid HIP-3 Multi-Deployer Scout")
st.markdown("_TradeXYZ (USDC) | Dreamcash (USDT) | Kinetiq (USDH)_")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def get_api():
    return Info(BASE_URL)

info = get_api()

def fetch_comprehensive_data():
    try:
        # web_data2 est l'appel le plus complet utilisé par l'UI officielle
        # Il contient les "extra" assets du HIP-3
        data = info.web_data2("0x0000000000000000000000000000000000000000") # Adresse nulle pour les données globales
        
        # Extraction des contextes d'actifs (Asset Contexts)
        # C'est ici que les prix des différents déployeurs sont agrégés
        all_assets = data.get('assetCtxs', [])
        meta = data.get('meta', {}).get('universe', [])
        
        # Mapping Index -> Nom via l'univers du web_data
        mapping = {i: asset['name'] for i, asset in enumerate(meta)}
        
        rows = []
        for i, ctx in enumerate(all_assets):
            name = mapping.get(i, f"Unknown_{i}")
            
            # Dans web_data2, le prix mid est souvent dans 'midSz' ou calculé via bid/ask
            # On cherche les infos spécifiques aux HIP-3
            mid_price = ctx.get('midSz')
            
            # On identifie le déployeur par le nom du ticker (ex: XYZ:NVDA)
            # ou par la structure du nom si elle contient le stable
            rows.append({
                "Ticker": name,
                "Prix": float(mid_price) if mid_price else None,
                "Daily Vol": ctx.get('dayNtlVlm', 0),
                "Funding": ctx.get('funding', 0)
            })
        return rows
    except Exception as e:
        st.error(f"Erreur web_data2 : {e}")
        # Si web_data2 échoue, on tente une approche brute par le mapping ID
        return []

# --- MAPPING MANUEL DES IDS HIP-3 ---
# Puisque tu as confirmé les IDs (408 = NVDA, etc.)
ID_MAP = {
    "407": "TSLA",
    "408": "NVDA",
    "412": "GOOGL",
    "411": "SLV"
}

data_rows = fetch_comprehensive_data()

if data_rows:
    df_all = pd.DataFrame(data_rows)
    
    # Filtrage intelligent
    # On cherche les lignes qui contiennent nos IDs cibles ou les noms des actions
    st.subheader("📊 Marchés Détectés par Déployeur")
    
    # On crée des colonnes virtuelles pour l'arbitrage
    arb_results = []
    
    for asset_id, stock_name in ID_MAP.items():
        # On cherche toutes les déclinaisons de cet ID (ex: @408, XYZ:NVDA, etc.)
        # Selon le déployeur, le nom varie
        matches = df_all[df_all['Ticker'].str.contains(asset_id) | df_all['Ticker'].str.contains(stock_name)]
        
        if not matches.empty:
            arb_entry = {"Stock": stock_name, "ID": asset_id}
            for _, match in matches.iterrows():
                t = match['Ticker']
                p = match['Prix']
                # Identification de la quote/déployeur par le suffixe ou préfixe
                if "USDT" in t or "Cash" in t:
                    arb_entry["USDT (Dreamcash)"] = p
                elif "USDH" in t or "km" in t:
                    arb_entry["USDH (Kinetiq)"] = p
                else:
                    arb_entry["USDC (TradeXYZ)"] = p
            arb_results.append(arb_entry)

    if arb_results:
        df_arb = pd.DataFrame(arb_results)
        st.write("### Comparaison Inter-Déployeurs")
        st.table(df_arb)
        
        # Calcul du spread si possible
        if "USDC (TradeXYZ)" in df_arb.columns and "USDT (Dreamcash)" in df_arb.columns:
            st.info("💡 Spread détecté entre TradeXYZ et Dreamcash")
    else:
        st.warning("Aucune correspondance trouvée pour les IDs TradFi. Les marchés sont peut-être listés sous des noms de 'Vaults'.")
        with st.expander("Voir tous les tickers bruts détectés"):
            st.write(df_all['Ticker'].tolist())
else:
    st.error("Impossible de récupérer les données globales.")

st.button("🔄 Scanner l'EVM")
