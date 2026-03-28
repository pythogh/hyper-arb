import streamlit as st
import pandas as pd
import time
from hyperliquid.info import Info
import plotly.graph_objects as go

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="Hyperliquid Arb Scout", layout="wide")
st.title("📊 Hyperliquid Stock Arbitrage & Funding Scout")

# --- INITIALISATION API ---
BASE_URL = "https://api.hyperliquid.xyz"
try:
    # On initialise l'API une seule fois
    if 'info' not in st.session_state:
        st.session_state.info = Info(BASE_URL)
    info = st.session_state.info
except Exception as e:
    st.error(f"Erreur d'initialisation : {e}")
    st.stop()

# --- FONCTIONS DE RÉCUPÉRATION ---

@st.cache_data(ttl=10)
def get_live_prices():
    """Récupère tous les prix mid actuels"""
    try:
        return info.all_mids()
    except Exception as e:
        st.error(f"Erreur API (Prices): {e}")
        return {}

@st.cache_data(ttl=300)
def get_funding_info(coin):
    """Récupère le taux de funding horaire actuel"""
    end_time = int(time.time() * 1000)
    start_time = end_time - (4 * 60 * 60 * 1000)
    try:
        data = info.funding_history(coin, start_time, end_time)
        if data and len(data) > 0:
            return float(data[0]['fundingRate'])
    except:
        pass
    return 0.0

# --- LOGIQUE DE DÉTECTION ---
all_prices = get_live_prices()

# Construction de la liste des stocks disponibles (ceux qui ont un équivalent stable)
detected_stocks = []
if all_prices:
    all_tickers = list(all_prices.keys())
    # On cherche les tickers de base qui ont un suffixe -USDT ou -USDS
    for t in all_tickers:
        if "-" not in t: # Ticker de base (ex: NVDA)
            if f"{t}-USDT" in all_tickers or f"{t}-USDS" in all_tickers:
                detected_stocks.append(t)

# --- SIDEBAR ---
st.sidebar.header("Configuration")

if not detected_stocks:
    st.sidebar.warning("⚠️ Aucun stock détecté. Tentative de lecture brute...")
    # Liste de secours au cas où le filtrage automatique échoue
    detected_stocks = ["NVDA", "HOOD", "TSLA", "AAPL", "GOOGL", "MSFT", "META"]

target_stocks = st.sidebar.multiselect(
    "Choisir les actifs", 
    options=sorted(detected_stocks),
    default=detected_stocks[:5] if len(detected_stocks) > 0 else None
)

stable_choice = st.sidebar.selectbox("Comparer USDC vs :", ["USDT", "USDS"])

if st.sidebar.button("🔄 Actualiser"):
    st.cache_data.clear()
    st.rerun()

# --- CALCUL DES OPPORTUNITÉS ---
data_rows = []

if not target_stocks:
    st.info("👈 Sélectionnez des actifs dans la barre latérale pour lancer l'analyse.")
else:
    progress_bar = st.progress(0)
    for idx, stock in enumerate(target_stocks):
        ticker_a = stock             # Paire USDC (Base)
        ticker_b = f"{stock}-{stable_choice}" # Paire Stable choisie
        
        p_a = float(all_prices.get(ticker_a, 0))
        p_b = float(all_prices.get(ticker_b, 0))
        
        if p_a > 0 and p_b > 0:
            spread_pct = ((p_b - p_a) / p_a) * 100
            
            # Récupération funding
            f_a = get_funding_info(ticker_a)
            f_b = get_funding_info(ticker_b)
            
            net_apr = (f_b - f_a) * 24 * 365 * 100
            
            data_rows.append({
                "Actif": stock,
                "Prix USDC": f"{p_a:,.2f}",
                f"Prix {stable_choice}": f"{p_b:,.2f}",
                "Spread %": round(spread_pct, 4),
                "Net APR %": round(net_apr, 2),
                "Funding A (h)": f"{f_a:.6%}",
                "Funding B (h)": f"{f_b:.6%}"
            })
        progress_bar.progress((idx + 1) / len(target_stocks))

# --- AFFICHAGE ---
if data_rows:
    df = pd.DataFrame(data_rows)
    
    # Dashboard
    st.subheader("État des lieux de l'arbitrage")
    
    # Affichage en colonnes pour les 3 plus gros APR
    top_3 = df.sort_values(by="Net APR %", ascending=False).head(3)
    cols = st.columns(len(top_3))
    for i, (_, row) in enumerate(top_3.iterrows()):
        cols[i].metric(row['Actif'], f"{row['Spread %']}% Sprd", f"{row['Net APR %']}% APR")

    st.write("---")
    
    # Tableau principal
    st.dataframe(
        df.style.background_gradient(subset=['Net APR %'], cmap='RdYlGn'),
        use_container_width=True
    )

    # Graphique Plotly
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Actif'], y=df['Spread %'], name="Spread Prix (%)", marker_color='orange'))
    fig.add_trace(go.Scatter(x=df['Actif'], y=df['Net APR %'], name="Net APR Funding (%)", yaxis="y2", line=dict(color='cyan')))
    
    fig.update_layout(
        title="Analyse Comparative Spread vs Funding",
        yaxis=dict(title="Spread %"),
        yaxis2=dict(title="APR %", overlaying='y', side='right'),
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

elif all_prices:
    st.error(f"Les paires {stable_choice} ne semblent pas encore listées ou actives pour ces stocks.")
