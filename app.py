import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
from hyperliquid.utils import constants
import plotly.graph_objects as go

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="Hyperliquid Arb Scout", layout="wide")
st.title("📊 Hyperliquid Stock Arbitrage & Funding Scout")

# --- INITIALISATION API ---
# On simplifie l'init pour éviter les TypeError sur les arguments optionnels
BASE_URL = "https://api.hyperliquid.xyz"
try:
    # Initialisation standard sans arguments superflus
    info = Info(BASE_URL)
except Exception as e:
    st.error(f"Erreur d'initialisation du SDK Hyperliquid : {e}")
    st.stop()

# --- FONCTIONS DE RÉCUPÉRATION ---

@st.cache_data(ttl=30)
def get_live_data():
    """Récupère les prix mid de tous les actifs"""
    try:
        return info.all_mids()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des prix : {e}")
        return {}

@st.cache_data(ttl=300) # Cache de 5 minutes pour le funding
def get_funding_info(coin):
    """Récupère le taux de funding actuel via l'historique récent"""
    end_time = int(time.time() * 1000)
    # On regarde les 8 dernières heures pour être sûr d'avoir le dernier point
    start_time = end_time - (8 * 60 * 60 * 1000)
    try:
        # La méthode funding_history est la plus fiable pour extraire le taux exact
        data = info.funding_history(coin, start_time, end_time)
        if data and len(data) > 0:
            # Le premier élément est généralement le plus récent
            last_rate = float(data[0]['fundingRate'])
            return last_rate
    except:
        return 0.0
    return 0.0

# --- SIDEBAR : FILTRES ---
st.sidebar.header("Configuration")
# Liste étendue des tickers stocks dispos sur HL
available_tickers = ["NVDA", "HOOD", "GOOGL", "MSFT", "TSLA", "AAPL", "META", "AMZN", "NFLX", "COIN", "MSTR"]
target_stocks = st.sidebar.multiselect(
    "Actions à surveiller", 
    available_tickers,
    default=["NVDA", "HOOD", "TSLA"]
)

if st.sidebar.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

# --- LOGIQUE PRINCIPALE ---

all_prices = get_live_data()
data_rows = []

if not all_prices:
    st.warning("Impossible de charger les prix. Vérifiez votre connexion à l'API Hyperliquid.")
else:
    with st.spinner('Analyse des spreads et des taux de funding...'):
        for stock in target_stocks:
            # Paire A: USDC (Ticker seul)
            # Paire B: USDT (Ticker-USDT)
            ticker_usdc = stock
            ticker_usdt = f"{stock}-USDT"
            
            p_usdc = float(all_prices.get(ticker_usdc, 0))
            p_usdt = float(all_prices.get(ticker_usdt, 0))
            
            if p_usdc > 0 and p_usdt > 0:
                # Calcul du Spread
                spread_abs = p_usdt - p_usdc
                spread_pct = (spread_abs / p_usdc) * 100
                
                # Récupération du Funding
                f_usdc = get_funding_info(ticker_usdc)
                f_usdt = get_funding_info(ticker_usdt)
                
                # Différentiel de Funding (Arbitrage Short USDT / Long USDC)
                net_funding_hourly = f_usdt - f_usdc
                # APR = Taux horaire * 24h * 365j
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
    
    # Dashboard Metrics
    st.subheader("Points chauds d'arbitrage")
    cols = st.columns(len(data_rows))
    for i, row in df.iterrows():
        # L'APR est vert s'il est > 5% (seuil arbitraire de rentabilité)
        color = "normal" if row['Net APR (%)'] > 5 else "off"
        cols[i].metric(
            label=row['Ticker'], 
            value=f"{row['Spread %']}% Sprd", 
            delta=f"{row['Net APR (%)']}% APR",
            delta_color=color
        )

    st.write("---")
    
    # Tableau
    st.subheader("Analyse comparative USDC vs USDT")
    st.dataframe(
        df.style.background_gradient(subset=['Net APR (%)'], cmap='RdYlGn'),
        use_container_width=True
    )

    # Graphique
    st.write("---")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Ticker'], y=df['Spread %'], name='Spread Prix (%)', marker_color='#FFA07A'))
    fig.add_trace(go.Scatter(x=df['Ticker'], y=df['Net APR (%)'], name='Net APR Funding (%)', yaxis='y2', line=dict(color='#00CC96', width=3)))

    fig.update_layout(
        title="Relation Spread vs APR (Potentiel d'arbitrage)",
        yaxis=dict(title="Spread Prix (%)"),
        yaxis2=dict(title="Net APR (%)", overlaying='y', side='right'),
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Sélectionnez des tickers dans la barre latérale pour commencer l'analyse.")

st.sidebar.info("💡 **Stratégie :** Si l'APR est positif et élevé, vous gagnez de l'argent en vendant la paire USDT et en achetant la paire USDC tout en restant neutre sur le prix de l'action.")
