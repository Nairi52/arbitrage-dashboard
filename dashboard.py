
import streamlit as st
import asyncio
import aiohttp
import pandas as pd
# --- Protection par mot de passe ---
mot_de_passe = st.text_input("🔐 Entrez le mot de passe :", type="password")

if mot_de_passe != "NolaRaya":  # <-- Mets ici le mot de passe que tu veux
    st.warning("Accès refusé.")
    st.stop()
STABLE_PAIRS = [
    ("USDC", "USDT"),
    ("USDC", "DAI"),
    ("USDC", "UXD"),
    ("USDT", "DAI"),
    ("USDT", "UXD"),
    ("DAI", "UXD"),
]

TOKEN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERk8F3nWjrmA7z4S2k7GFHPiDTbvu9K5bD",
    "UXD":  "7kbnvuGBxxj8AG9qp8Scn56muWGaRaFqxg1FsRp3PaFT",
    "DAI":  "DAwBSgGZDTFzyxAqzJp9SLwz1gdEDhnno2nZyzVSV7Ez",
}

JUPITER_API_URL = "https://quote-api.jup.ag/v6/quote"

async def get_price(session, token_in, token_out, amount=1_000_000):
    params = {
        "inputMint": TOKEN_MINTS[token_in],
        "outputMint": TOKEN_MINTS[token_out],
        "amount": amount,
        "slippageBps": 10
    }
    async with session.get(JUPITER_API_URL, params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            if "data" in data and len(data["data"]) > 0:
                route = data["data"][0]
                out_amount = int(route["outAmount"]) / 10**6
                in_amount = amount / 10**6
                return round(out_amount / in_amount, 6)
    return None

async def fetch_arbitrage_data():
    results = []
    async with aiohttp.ClientSession() as session:
        for base, quote in STABLE_PAIRS:
            fwd = await get_price(session, base, quote)
            bwd = await get_price(session, quote, base)
            if fwd and bwd:
                spread = round((fwd * bwd - 1) * 100, 4)
                results.append({
                    "Paire": f"{base} ⇄ {quote}",
                    "Prix Aller": fwd,
                    "Prix Retour": bwd,
                    "Spread (%)": spread,
                    "Arbitrage": "✅" if spread > 0.2 else ""
                })
    return results

def main():
    st.set_page_config(page_title="Bot Arbitrage Solana", layout="wide")
    st.title("💹 Dashboard d'Arbitrage Stablecoins - Solana (via Jupiter)")

    refresh_rate = st.slider("⏱️ Rafraîchissement (secondes)", 5, 60, 10)

    placeholder = st.empty()

    while True:
        data = asyncio.run(fetch_arbitrage_data())
        df = pd.DataFrame(data)
        df = df.sort_values("Spread Max (%)", ascending=False)
        placeholder.dataframe(df, use_container_width=True)
        asyncio.run(asyncio.sleep(refresh_rate))

if __name__ == "__main__":
    main()
