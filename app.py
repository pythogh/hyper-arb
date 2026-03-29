import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Hyperliquid HIP-3 Arb", layout="wide")
st.title("🏛️ Arbitrage TradFi (HIP-3 Specialists)")

# Initialisation de l'API
BASE_URL = "https://api.hyperliquid.xyz"
@st.cache_resource
def init_info():
    return Info(BASE_URL)

info = init_info()

# --- MAPPING MANUEL (Basé sur tes logs) ---
# On utilise tes IDs vérifiés pour garantir l'affichage
ID_MAP = {
    "@401": "QONE", "@402": "US", "@403": "UMEGA", "@404": "XMR1",
    "@405": "HMT", "@406": "PEUR", "@407": "TSLA", "@408": "NVDA",
    "@409": "CRCL", "@410": "SOON", "@411": "SLV", "@412": "GOOGL"
}

# --- RÉCUPÉRATION DES DONNÉES ---
@st.cache_data(ttl=5)
def get_arb_data():
    all_prices = info.all_mids()
    
    # Structure pour regrouper les prix : { "NVDA": {"USDC": 120, "USDT": 121}, ... }
    organized_data = {}
    
    for ticker, price in all_prices.items():
        # On cherche les IDs qui sont dans notre map (ex: @408)
        # Le format peut être "@408", "@408/USDC", "@408/USDT", "@408/USDH"
        base_id = ticker.split('/')[0]
        
        if base_id in ID_MAP:
            name = ID_MAP[base_id]
            quote = ticker.split('/')[1] if '/' in ticker else "USDC"
            
            if name not in organized_data:
                organized_data[name] = {"ID": base_id}
            
            organized_data[name][quote] = float(price)
            
    return organized_data

# --- LOGIQUE D'AFFICHAGE ---
organized_prices = get_arb_data()

st.sidebar.header("Paramètres")
selected_stable = st.sidebar.selectbox("Comparer USDC contre :", ["USDT", "USDH", "USDS"])
auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)

if auto_refresh:
    time.sleep(5)
    st.rerun()

# Calcul des spreads
rows = []
for name, quotes in organized_prices.items():
    p_usdc = quotes.get("USDC")
    p_target = quotes.get(selected_stable)
    
    if p_usdc and p_target:
        spread_abs = p_target - p_usdc
        spread_pct = (spread_abs / p_usdc) * 100
        
        rows.append({
            "Action": name,
            "ID": quotes["ID"],
            "Prix USDC": round(p_usdc, 3),
            f"Prix {selected_stable}": round(p_target, 3),
            "Spread ($)": round(spread_abs, 3),
            "Spread (%)": round(spread_pct, 4)
        })

# --- RENDU ---
if rows:
    df = pd.DataFrame(rows)
    
    # Métriques en haut
    top_cols = st.columns(min(len(df), 4))
    for i, row in df.head(4).iterrows():
        top_cols[i].metric(
            row['Action'], 
            f"${row['Prix USDC']}", 
            f"{row['Spread (%)']}%",
            delta_color="normal" if row['Spread (%)'] > 0 else "inverse"
        )

    st.write("---")
    st.subheader(f"Tableau de bord : USDC vs {selected_stable}")
    
    # Style conditionnel pour les spreads importants
    st.dataframe(
        df.style.background_gradient(subset=['Spread (%)'], cmap='RdYlGn_r'),
        use_container_width=True
    )

    # Graphique de comparaison
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Action'], y=df['Spread (%)'], name='Spread %', marker_color='royalblue'))
    fig.update_layout(
        title=f"Écart de prix relatif (USDC vs {selected_stable})",
        yaxis_title="Spread %",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning(f"Aucune paire double (USDC + {selected_stable}) détectée pour le moment.")
    st.info("💡 Conseil : Si l'interface reste vide, vérifie que les paires USDT/USDH sont actives sur l'exchange pour les IDs listés.")

with st.expander("🔍 Debug : Données brutes reçues"):
    st.json(organized_prices)
