import streamlit as st
import pandas as pd
import aiohttp
import asyncio

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="Arbitrage Multi-Plateforme", layout="wide")
st.title("📊 Arbitrage Stablecoins - Solana (Jupiter Multi-Platform)")

# Tokens and platforms
STABLECOINS = ["USDC", "USDT", "DAI", "UXD", "USDL"]
PLATFORMS   = ["Jupiter", "Raydium", "Orca", "Lifinity", "Meteora"]

# Mint addresses
TOKEN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERk8F3nWjrmA7z4S2k7GFHPiDTbvu9K5bD",
    "DAI":  "DAwBSgGZDTFzyxAqzJp9SLwz1gdEDhnno2nZyzVSV7Ez",
    "UXD":  "7kbnvuGBxxj8AG9qp8Scn56muWGaRaFqxg1FsRp3PaFT",
    "USDL": "5vfjkX5jGsdYVYcWy6HRgUxhN6hzXZGTmA8qcRfXhCz7"
}

JUPITER_API_URL = "https://quote-api.jup.ag/v6/quote"

# --------------------------
# FUNCTIONS
# --------------------------
async def get_price(session, input_token, output_token, platform=None):
    # Vérifie que les tokens existent
    if input_token not in TOKEN_MINTS or output_token not in TOKEN_MINTS:
        return None

    # Prépare les paramètres de la requête Jupiter
    params = {
        "inputMint":  TOKEN_MINTS[input_token],
        "outputMint": TOKEN_MINTS[output_token],
        "amount":     1_000_000,
        "slippageBps": 10,
    }

    # Si on cible une plateforme spécifique (pas "Jupiter"), indique-la dans une liste
    if platform and platform != "Jupiter":
        params["onlyDirectRoutes"] = False
        params["platforms"]       = [platform.lower()]

    # Appel à l'API avec logs pour debug
    try:
        async with session.get(JUPITER_API_URL, params=params) as resp:
            # ——— LOGS HTTP ———
            st.write(f"🔗 Requête vers Jupiter ({platform}):", params)
            st.write("📶 Statut HTTP:", resp.status)
            body = await resp.text()
            st.write("📦 Corps de la réponse (trunc):", body[:300])
            # —————————————

            if resp.status == 200:
                data = await resp.json()
                if "data" in data and len(data["data"]) > 0:
                    out_amount = int(data["data"][0]["outAmount"])
                    return round(out_amount / 1_000_000, 6)
    except Exception:
        # En cas d'erreur réseau ou JSON invalide
        return None

    return None

async def fetch_all(min_spread):
    results = []
    async with aiohttp.ClientSession() as session:
        for i, base in enumerate(STABLECOINS):
            for quote in STABLECOINS[i+1:]:
                row = {"Paire": f"{base}/{quote}"}
                prices = []
                for plat in PLATFORMS:
                    # ← ici, ligne ~65–70 selon ton fichier
                    actual_platform = None if plat == "Jupiter" else plat
                    price = await get_price(session, base, quote, actual_platform)
                    row[plat] = price
                    if isinstance(price, float):
                        prices.append(price)
                # … le reste de ta logique …
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
    st.info("Clique sur le bouton pour scanner les plateformes.")
