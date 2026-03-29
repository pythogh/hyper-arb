import streamlit as st
import pandas as pd
from hyperliquid.info import Info

# --- CONFIG ---
st.set_page_config(page_title="HL TradFi Discovery", layout="wide")
st.title("🏛️ Arbitrage TradFi (HIP-3 Indexé)")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- STEP 1 : MAPPING ID -> NOM ---
@st.cache_data(ttl=3600)
def get_token_mapping():
    try:
        spot_meta = info.spot_meta()
        tokens = spot_meta.get('tokens', [])
        # On crée un dictionnaire { "@1": "NOM_REEL", ... }
        mapping = { f"@{t['index']}": t['name'] for t in tokens }
        # On garde aussi le nom complet si dispo
        full_names = { f"@{t['index']}": t.get('fullName', t['name']) for t in tokens }
        return mapping, full_names
    except:
        return {}, {}

# --- STEP 2 : CALCUL ARBITRAGE ---
mapping, full_names = get_token_mapping()
all_prices = info.all_mids()

# On organise les données par Actif de Base
# Structure : { "@1": {"USDC": 150.2, "USDT": 150.5}, ... }
arb_table = {}

for ticker, price in all_prices.items():
    if ticker.startswith("@"):
        parts = ticker.split("/")
        base_id = parts[0]
        quote = parts[1] if len(parts) > 1 else "USDC" # Par défaut USDC
        
        if base_id not in arb_table:
            arb_table[base_id] = {}
        
        arb_table[base_id][quote] = float(price)

# --- AFFICHAGE ---
data_rows = []
for base_id, quotes in arb_table.items():
    if len(quotes) > 1: # On ne garde que s'il y a au moins 2 prix à comparer
        real_name = mapping.get(base_id, base_id)
        full_name = full_names.get(base_id, "")
        
        row = {
            "ID": base_id,
            "Nom": real_name,
            "Description": full_name
        }
        # On ajoute les colonnes dynamiquement pour chaque quote trouvée
        for q, p in quotes.items():
            row[q] = p
            
        # Calcul du spread max si on a USDC et une autre
        if "USDC" in quotes:
            other_quotes = [q for q in quotes.keys() if q != "USDC"]
            if other_quotes:
                target_q = other_quotes[0]
                spread = ((quotes[target_q] - quotes["USDC"]) / quotes["USDC"]) * 100
                row["Spread % (vs USDC)"] = round(spread, 4)
        
        data_rows.append(row)

if data_rows:
    df = pd.DataFrame(data_rows)
    st.subheader("Opportunités d'Arbitrage Détectées")
    st.dataframe(df.style.background_gradient(subset=["Spread % (vs USDC)"], cmap="RdYlGn_r"), use_container_width=True)
else:
    st.warning("Aucun arbitrage multi-quote trouvé pour le moment.")
    with st.expander("Voir tous les IDs HIP-3 détectés"):
        st.write(mapping)
