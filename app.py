import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
from hyperliquid.utils import constants
import plotly.graph_objects as go

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="Hyperliquid Arb Scout", layout="wide")
st.title("📊 Hyperliquid Stock Arbitrage & Funding Scout")

# Initialisation de l'API (Public Info uniquement)
# Utilisation de l'URL directe pour éviter les conflits de version SDK
BASE_URL = "https://api.hyperliquid.xyz"
info = Info(BASE_URL, skip_canvas_logging=True)

# --- FONCTIONS DE RÉCUPÉRATION ---

@st.cache_data(ttl=30)
def get_live_data():
    """Récupère les prix mid de tous les actifs"""
    return info.all_mids()

@st.cache_data(ttl=3600)
def get_funding_info(coin):
    """Récupère le taux de funding actuel et historique récent"""
    # Note: On récupère l'historique sur 24h pour avoir une idée de la tendance
    end_time = int(time.time() * 1000)
    start_time = end_time - (24 * 60 * 60 * 1000)
    try:
        data = info.funding_history(coin, start_time, end_time)
        if data:
            # On prend le dernier taux enregistré
            last_rate = float(data[0]['fundingRate'])
            return last_rate
    except:
        return 0.0
    return 0.0

# --- SIDEBAR : FILTRES ---
st.sidebar.header("Configuration")
target_stocks = st.sidebar.multiselect(
    "Actions à surveiller", 
    ["NVDA", "HOOD", "GOOGL", "MSFT", "TSLA", "AAPL", "META", "AMZN", "NFLX", "COIN"],
    default=["NVDA", "HOOD", "TSLA"]
)

refresh = st.sidebar.button("🔄 Actualiser les données")

# --- LOGIQUE PRINCIPALE ---

all_prices = get_live_data()
data_rows = []

with st.spinner('Analyse des spreads et des taux de funding...'):
    for stock in target_stocks:
        # Paire A: USDC (Nom du ticker seul sur HL)
        # Paire B: USDT (Ticker-USDT)
        ticker_usdc = stock
        ticker_usdt = f"{stock}-USDT"
        
        p_usdc = float(all_prices.get(ticker_usdc, 0))
        p_usdt = float(all_prices.get(ticker_usdt, 0))
        
        if p_usdc > 0 and p_usdt > 0:
            # Calcul du Spread de prix
            spread_abs = p_usdt - p_usdc
            spread_pct = (spread_abs / p_usdc) * 100
            
            # Récupération du Funding (Taux horaire)
            f_usdc = get_funding_info(ticker_usdc)
            f_usdt = get_funding_info(ticker_usdt)
            
            # Différentiel de Funding (ce que tu gagnes si tu es Short USDT et Long USDC)
            # Profit = (Funding reçu du Short USDT) - (Funding payé/reçu du Long USDC)
            net_funding_hourly = f_usdt - f_usdc
            net_funding_apr = net_funding_hourly * 24 * 365 * 100
            
            data_rows.append({
                "Ticker": stock,
                "Price USDC": round(p_usdc, 3),
                "Price USDT": round(p_usdt, 3),
                "Spread %": round(spread_pct, 4),
                "Funding USDC (h)": f"{f_usdc:.5%}",
                "Funding USDT (h)": f"{f_usdt:.5%}",
                "Net APR (%)": round(net_funding_apr, 2)
            })

# --- AFFICHAGE ---

if data_rows:
    df = pd.DataFrame(data_rows)
    
    # 1. Metrics clés
    st.subheader("Opportunités Détectées")
    cols = st.columns(len(data_rows))
    for i, row in df.iterrows():
        # Couleur verte si l'APR est positif (favorable à l'arbitrage Short USDT / Long USDC)
        delta_color = "normal" if row['Net APR (%)'] > 0 else "inverse"
        cols[i].metric(
            label=row['Ticker'], 
            value=f"{row['Spread %']}% Spread", 
            delta=f"{row['Net APR (%)']}% APR",
            delta_color=delta_color
        )

    # 2. Tableau détaillé
    st.write("---")
    st.subheader("Analyse détaillée")
    
    # Styliser le tableau pour mettre en évidence les opportunités
    def highlight_profit(val):
        color = 'lightgreen' if val > 10 else 'white'
        return f'background-color: {color}'

    st.dataframe(
        df.style.applymap(highlight_profit, subset=['Net APR (%)']),
        use_container_width=True
    )

    # 3. Visualisation du Spread vs Funding
    st.write("---")
    st.subheader("Visualisation Spread vs Rendement")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Ticker'], y=df['Spread %'], name='Spread Prix (%)', marker_color='indianred'))
    fig.add_trace(go.Scatter(x=df['Ticker'], y=df['Net APR (%)'], name='APR Funding (%)', yaxis='y2', line=dict(color='royalblue', width=4)))

    fig.update_layout(
        title="Relation entre l'écart de prix et le taux de financement",
        yaxis=dict(title="Spread Prix (%)"),
        yaxis2=dict(title="APR Funding (%)", overlaying='y', side='right'),
        legend=dict(x=0, y=1.1, orientation="h")
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Aucune donnée trouvée. Assurez-vous que les marchés sélectionnés sont actifs.")

st.sidebar.markdown("""
---
**Note d'arbitrage :**
Si le **Net APR** est élevé et positif, la stratégie consiste à :
1. **Short** la paire USDT
2. **Long** la paire USDC
*Le profit vient du taux de financement payé par les Longs sur USDT.*
""")
