import streamlit as st
import pandas as pd
from hyperliquid.info import Info

# --- CONFIG ---
st.set_page_config(page_title="HL HIP-3 Specialist", layout="wide")
st.title("🏛️ Hyperliquid HIP-3 (TradFi) Specialist")

BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- RÉCUPÉRATION ---
try:
    # 1. On récupère TOUS les prix du registre
    all_prices = info.all_mids()
    
    # 2. On filtre uniquement les actifs qui ont un ":" (Signature HIP-3 / TradeXYZ)
    # Et on sépare le Builder du Ticker
    hip3_data = []
    for ticker, price in all_prices.items():
        if ":" in ticker:
            # Format attendu : "BUILDER:SYMBOL/QUOTE"
            try:
                parts = ticker.split(":")
                builder = parts[0]
                rest = parts[1]
                
                # On sépare le symbole de la quote (USDC, USDT, USDH)
                if "/" in rest:
                    symbol, quote = rest.split("/")
                else:
                    symbol, quote = rest, "Unknown"
                
                hip3_data.append({
                    "Full Ticker": ticker,
                    "Builder": builder,
                    "Asset": symbol,
                    "Quote": quote,
                    "Price": float(price)
                })
            except:
                continue

    if hip3_data:
        df = pd.DataFrame(hip3_data)
        
        # --- INTERFACE ---
        st.subheader("Marchés TradFi (HIP-3) Détectés")
        
        # Filtre par Builder
        builders = df['Builder'].unique()
        selected_builder = st.sidebar.multiselect("Filtrer par Builder", builders, default=builders)
        
        # Filtre par Actif
        assets = df['Asset'].unique()
        selected_assets = st.sidebar.multiselect("Filtrer par Action (NVDA, HOOD...)", assets, default=assets[:5] if len(assets) > 5 else assets)
        
        mask = df['Builder'].isin(selected_builder) & df['Asset'].isin(selected_assets)
        filtered_df = df[mask]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # --- LOGIQUE D'ARBITRAGE ---
        st.write("---")
        st.subheader("Opportunités d'Arbitrage")
        
        # On groupe par Asset pour trouver les différences de prix entre Quotes
        for asset in selected_assets:
            asset_group = filtered_df[filtered_df['Asset'] == asset]
            if len(asset_group) > 1:
                st.write(f"📊 Analyse pour **{asset}** :")
                st.table(asset_group[['Quote', 'Price']])
                
                p_min = asset_group['Price'].min()
                p_max = asset_group['Price'].max()
                spread = ((p_max - p_min) / p_min) * 100
                st.info(f"Spread max détecté sur {asset} : **{spread:.4f}%**")
    else:
        st.warning("Aucun actif HIP-3 (avec ':') n'a été trouvé.")
        with st.expander("Voir les 50 premiers tickers bruts pour analyse"):
            st.write(list(all_prices.keys())[:50])

except Exception as e:
    st.error(f"Erreur lors de la lecture des données : {e}")
