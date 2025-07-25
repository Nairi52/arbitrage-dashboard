
import asyncio
import aiohttp
import pandas as pd
import streamlit as st

# ---------- CONFIG ----------
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

# ---------- CORE ----------
async def get_price(session, token_in, token_out, amount=1_000_000):
    params = {
        "inputMint": TOKEN_MINTS[token_in],
        "outputMint": TOKEN_MINTS[token_out],
        "amount": amount,
        "slippageBps": 10,
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

async def fetch_arbitrage_data(min_spread=0.05):
    results = []
    async with aiohttp.ClientSession() as session:
        for base, quote in STABLE_PAIRS:
            try:
                fwd = await get_price(session, base, quote)
                bwd = await get_price(session, quote, base)
                if fwd and bwd:
                    spread = round((fwd * bwd - 1) * 100, 4)
                    if spread >= min_spread:
                        results.append({
                            "Paire": f"{base} ⇄ {quote}",
                            "Prix Aller": fwd,
                            "Prix Retour": bwd,
                            "Spread (%)": spread,
                            "💸 Arbitrage": "✅" if spread >= 0.2 else ""
                        })
            except:
                pass
    return results

# ---------- UI ----------
def main():
    st.set_page_config(page_title="Arbitrage Stablecoins Solana", layout="wide")
    st.title("✅ Dashboard d'Arbitrage Stablecoins - Solana (via Jupiter)")

    refresh_rate = st.slider("⏱ Rafraîchissement (secondes)", 5, 60, 10)
    min_spread = st.slider("📊 Spread minimum affiché (%)", 0.01, 1.0, 0.05)

    placeholder = st.empty()

    while True:
        data = asyncio.run(fetch_arbitrage_data(min_spread))
        st.write("📦 Données brutes :", data)
        df = pd.DataFrame(data)

        if not df.empty and "Spread (%)" in df.columns:
            df = df.sort_values("Spread (%)", ascending=False)
            placeholder.dataframe(df, use_container_width=True)
        else:
            placeholder.warning("❌ Aucune opportunité détectée pour le moment.")

        asyncio.run(asyncio.sleep(refresh_rate))

# ---------- PASSWORD ----------
mot_de_passe = st.text_input("🔐 Entrez le mot de passe :", type="password")
if mot_de_passe != "NolaRaya":
    st.warning("⛔ Accès refusé.")
    st.stop()
else:
    main()
