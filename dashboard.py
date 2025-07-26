import streamlit as st
import pandas as pd
import aiohttp
import asyncio

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="Arbitrage Stablecoins", layout="wide")
st.title("📊 Arbitrage Stablecoins - Solana (Jupiter Multi-Platform)")

STABLECOINS = ["USDC", "USDT", "DAI", "UXD", "USDL"]

TOKEN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERk8F3nWjrmA7z4S2k7GFHPiDTbvu9K5bD",
    "DAI":  "DAwBSgGZDTFzyxAqzJp9SLwz1gdEDhnno2nZyzVSV7Ez",
    "UXD":  "7kbnvuGBxxj8AG9qp8Scn56muWGaRaFqxg1FsRp3PaFT",
    "USDL": "5vfjkX5jGsdYVYcWy6HRgUxhN6hzXZGTmA8qcRfXhCz7"
}

# On nomme bien la constante URL, et on l'utilise ensuite
JUPITER_API_URL = "https://quote-api.jup.ag/v6/quote"

# --------------------------
# Récupérer un prix sur Jupiter
# --------------------------
async def get_price(session, token_in: str, token_out: str) -> float | None:
    # Vérifie que les tokens existent
    if token_in not in TOKEN_MINTS or token_out not in TOKEN_MINTS:
        return None

    # Params minimaux, multi-hop par défaut
    params = {
        "inputMint":   TOKEN_MINTS[token_in],
        "outputMint":  TOKEN_MINTS[token_out],
        "amount":      1_000_000,  # en micro-unités = 1 token
        "slippageBps": 10,
    }

    # Debug HTTP brut
    st.write("🔗 Requête brute Jupiter :", params)

    try:
        # Attention on utilise bien JUPITER_API_URL
        async with session.get(JUPITER_API_URL, params=params) as resp:
            st.write("📶 Statut HTTP :", resp.status)
            body = await resp.text()
            st.write("📦 Corps (trunc) :", body[:200])

            if resp.status == 200:
                data = await resp.json()
                arr = data.get("data", [])
                if arr:
                    out_amount = int(arr[0]["outAmount"])
                    return round(out_amount / 1_000_000, 6)
    except Exception as e:
        st.write("❌ Erreur get_price():", e)

    return None

# --------------------------
# Comparer toutes les paires
# --------------------------
async def fetch_all(min_spread: float):
    results = []
    async with aiohttp.ClientSession() as session:
        for i, base in enumerate(STABLECOINS):
            for quote in STABLECOINS[i+1:]:
                row = {"Paire": f"{base}/{quote}"}

                price = await get_price(session, base, quote)
                row["Jupiter"] = price

                if isinstance(price, float):
                    # on met à 0 le spread pour simplement vérifier l'affichage
                    row["Spread Max (%)"] = 0.0
                    row["💸 Arbitrage"]   = "✅" if 0.0 >= min_spread else ""
                results.append(row)
    return results

# --------------------------
# UI
# --------------------------
min_spread = st.slider(
    "📊 Spread minimum affiché (%)",
    min_value=0.01, max_value=2.0, value=0.01, step=0.01
)

if st.button("🔄 Actualiser les prix"):
    with st.spinner("Chargement des données…"):
        data = asyncio.run(fetch_all(min_spread))
        st.write("📦 Données brutes :", data)
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
else:
    st.info("Clique sur Actualiser pour tester.")
