import streamlit as st
import pandas as pd
import aiohttp
import asyncio

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="Arbitrage Stablecoins", layout="wide")
st.title("📊 Arbitrage Stablecoins — Solana (via Jupiter)")

# Les stablecoins à comparer
STABLECOINS = ["USDC", "USDT", "DAI", "UXD", "USDL"]

# Mint-addresses sur Solana
TOKEN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERk8F3nWjrmA7z4S2k7GFHPiDTbvu9K5bD",
    "DAI":  "DAwBSgGZDTFzyxAqzJp9SLwz1gdEDhnno2nZyzVSV7Ez",
    "UXD":  "7kbnvuGBxxj8AG9qp8Scn56muWGaRaFqxg1FsRp3PaFT",
    "USDL": "5vfjkX5jGsdYVYcWy6HRgUxhN6hzXZGTmA8qcRfXhCz7"
}

JUPITER_API_URL = "https://quote-api.jup.ag/v6/quote"

# --------------------------
# get_price : interroge Jupiter
# --------------------------
async def get_price(session, token_in: str, token_out: str) -> float | None:
    if token_in not in TOKEN_MINTS or token_out not in TOKEN_MINTS:
        return None

    params = {
        "inputMint":   TOKEN_MINTS[token_in],
        "outputMint":  TOKEN_MINTS[token_out],
        "amount":      1_000_000,  # 1 token = 1e6 micro-unités
        "slippageBps": 10,
        # ne pas passer de filtre, pour laisser Jupiter router multi-hop
    }

    try:
        async with session.get(JUPITER_API_URL, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                arr  = data.get("data", [])
                if arr:
                    out_amount = int(arr[0]["outAmount"])
                    return round(out_amount / 1_000_000, 6)
    except:
        return None

    return None

# --------------------------
# fetch_all : boucle sur toutes les paires
# --------------------------
async def fetch_all():
    rows = []
    async with aiohttp.ClientSession() as session:
        for i, base in enumerate(STABLECOINS):
            for quote in STABLECOINS[i+1:]:
                price = await get_price(session, base, quote)
                rows.append({
                    "Paire":        f"{base}/{quote}",
                    "Jupiter":      price
                })
    return rows

# --------------------------
# UI
# --------------------------
if st.button("🔄 Actualiser les prix"):
    with st.spinner("Chargement…"):
        data = asyncio.run(fetch_all())
        df   = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
else:
    st.info("Clique sur « Actualiser les prix » pour démarrer.")
