import streamlit as st
import pandas as pd
import aiohttp
import asyncio

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="Arbitrage Multi-Platform", layout="wide")
st.title("📊 Arbitrage Stablecoins - Solana (Jupiter Multi-Platform)")

STABLECOINS = ["USDC", "USDT", "DAI", "UXD", "USDL"]

TOKEN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERk8F3nWjrmA7z4S2k7GFHPiDTbvu9K5bD",
    "DAI":  "DAwBSgGZDTFzyxAqzJp9SLwz1gdEDhnno2nZyzVSV7Ez",
    "UXD":  "7kbnvuGBxxj8AG9qp8Scn56muWGaRaFqxg1FsRp3PaFT",
    "USDL": "5vfjkX5jGsdYVYcWy6HRgUxhN6hzXZGTmA8qcRfXhCz7"
}

JUPITER_API_URL = "https://quote-api.jup.ag/v6/quote"

# --------------------------
# FONCTION DE PRIX
# --------------------------
async def get_price(session, token_in, token_out) -> float | None:
    if token_in not in TOKEN_MINTS or token_out not in TOKEN_MINTS:
        return None

    # 1) Paramètres de base, on force multi-hop
    params = {
        "inputMint":        TOKEN_MINTS[token_in],
        "outputMint":       TOKEN_MINTS[token_out],
        "amount":           1_000_000,
        "slippageBps":      10,
        "onlyDirectRoutes": "false",      # << clé !!!
    }

    # 2) (Optionnel) Filtrer par AMM direct
    # if want_direct_pool:
    #     params["onlyDirectRoutes"] = "true"
    #     params["platforms"]        = ["raydium"]  # example

    # 3) Requête
    async with session.get(JUPITER_API_URL, params=params) as resp:
        # debug logs…
        if resp.status == 200:
            data = await resp.json()
            arr = data.get("data", [])
            if arr:
                return round(int(arr[0]["outAmount"]) / 1_000_000, 6)
    return None

    return None

# --------------------------
# FONCTION COLLECTE DES PRIX
# --------------------------
async def fetch_all(min_spread: float):
    results = []
    async with aiohttp.ClientSession() as session:
        for i, base in enumerate(STABLECOINS):
            for quote in STABLECOINS[i+1:]:
                row = {"Paire": f"{base}/{quote}"}
                prices = []

                # collecte sur Jupiter global multi-hop
                price = await get_price(session, base, quote)
                row["Jupiter"] = price
                if isinstance(price, float):
                    prices.append(price)

                # calcul du spread max et flag arbitrage
                if prices:
                    spread = (max(prices) - min(prices)) / min(prices) * 100
                    row["Spread Max (%)"] = round(spread, 4)
                    row["💸 Arbitrage"] = "✅" if spread >= min_spread else ""
                results.append(row)
    return results

# --------------------------
# UI
# --------------------------
min_spread = st.slider("📊 Spread minimum affiché (%)", 0.01, 2.0, 0.01, 0.01)

if st.button("🔄 Actualiser les prix"):
    with st.spinner("Chargement des données..."):
        data = asyncio.run(fetch_all(min_spread))
        st.write("📦 Données brutes (fetch_all) :", data)

        df = pd.DataFrame(data)
        if not df.empty and "Spread Max (%)" in df.columns:
            df = df.sort_values("Spread Max (%)", ascending=False)
        st.dataframe(df, use_container_width=True)
else:
    st.info("Clique sur le bouton pour scanner les paires.")
