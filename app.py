import streamlit as st
import pandas as pd
from hyperliquid.info import Info

# --- CONFIG ---
st.set_page_config(page_title="HL HIP-3 Scanner", layout="wide")
st.title("🏛️ Scanner Final : Actifs TradFi HIP-3")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- RÉCUPÉRATION ---
try:
    # 1. On récupère les METADONNÉES du SPOT (C'est là que sont les stocks)
    spot_meta = info.spot_meta()
    tokens = spot_meta.get('tokens', [])
    universe = spot_meta.get('universe', [])
    
    # 2. On crée un dictionnaire : Index du Token -> Nom (ex: 41 -> NVDA)
    # On cherche aussi le nom complet (fullName) pour être sûr
    token_map = {t['index']: t['name'] for t in tokens}
    full_name_map = {t['index']: t.get('fullName', t['name']) for t in tokens}

    # 3. On reconstruit les paires de trading réelles
    active_pairs = []
    for pair in universe:
        base_id = pair['tokens'][0]
        quote_id = pair['tokens'][1]
        
        base_name = token_map.get(base_id, "Unknown")
        quote_name = token_map.get(quote_id, "Unknown")
        
        active_pairs.append({
            "Pair Name": pair['name'],
            "Base Asset": base_name,
            "Quote (Stable)": quote_name,
            "Full Name": full_name_map.get(base_id, ""),
            "Pair Index": pair['index']
        })

    df_pairs = pd.DataFrame(active_pairs)

    # --- FILTRAGE TRADFI ---
    # On cherche tout ce qui ressemble à une action (NVDA, HOOD, etc.)
    search = st.text_input("Rechercher un stock (ex: NVDA, HOOD) :", "").upper()
    
    if search:
        filtered = df_pairs[df_pairs['Full Name'].str.contains(search) | df_pairs['Base Asset'].str.contains(search)]
    else:
        filtered = df_pairs

    st.subheader("Paires de trading détectées sur le Spot")
    st.dataframe(filtered, use_container_width=True)

    # --- ÉTAPE FINALE : RÉCUPÉRATION DES PRIX ---
    if not filtered.empty:
        st.write("---")
        st.subheader("Prix en temps réel pour ces paires")
        all_prices = info.all_mids()
        
        price_data = []
        for _, row in filtered.iterrows():
            p_name = row['Pair Name']
            price = all_prices.get(p_name, "N/A")
            price_data.append({"Paire": p_name, "Prix": price})
        
        st.table(pd.DataFrame(price_data))

except Exception as e:
    st.error(f"Erreur lors de l'accès au Spot Meta : {e}")

if st.button("🔄 Rafraîchir"):
    st.cache_data.clear()
    st.rerun()
