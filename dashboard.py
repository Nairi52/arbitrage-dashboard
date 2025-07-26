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
DEXES       = ["Jupiter", "Raydium", "Orca", "Lifinity", "Meteora"]

TOKEN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERk8F3nWjrmA7z4S2k7GFHPiDTbvu9K5bD",
    "DAI":  "DAwBSgGZDTFzyxAqzJp9SLwz1gdEDhnno2nZyzVSV7Ez",
    "UXD":  "7kbnvuGBxxj8AG9qp8Scn56muWGaRaFqxg1FsRp3PaFT",
    "USDL": "5vfjkX5jGsdYVYcWy6HRgUxhN6hzXZGTmA8qcRfXhCz7"
}

JUPITER_API = "https://quote-api.jup.ag/v6/quote"

# --------------------------
# FETCH ONE PRICE
# --------------------------
async def get_price(session, token_in: str, token_out: str, dex: str|None=None) -> float|None:
    # verify tokens
    if token_in not in TOKEN_MINTS or token_out not in TOKEN_MINTS:
        return None

    # build params
    params = {
        "inputMint":        TOKEN_MINTS[token_in],
        "outputMint":       TOKEN_MINTS[token_out],
        "amount":           1_000_000,
        "slippageBps":      10,
        "onlyDirectRoutes": "false",      # string, to allow multi-hop
    }
    if dex and dex != "Jupiter":
        params["onlyDirectRoutes"] = "true"   # direct only for this DEX
        params["dexes"]            = [dex.lower()]

    # DEBUG logs
    st.write("🔗 REQUEST:", params)
    try:
        async with session.get(JUPITER_API, params=params) as resp:
            st.write("📶 STATUS:", resp.status)
            text = await resp.text()
            st.write("📦 BODY (trunc):", text[:300])

            if resp.status == 200:
                data = await resp.json()
                arr  = data.get("data", [])
                if arr:
                    out = int(arr[0]["outAmount"])
                    return round(out/1_000_000, 6)
    except Exception as e:
        st.write("❌ fetch error:", e)
    return None

# --------------------------
# COLLECT ALL QUOTES
# --------------------------
async def fetch_all(min_spread: float):
    results = []
    async with aiohttp.ClientSession() as session:
        for i, base in enumerate(STABLECOINS):
            for quote in STABLECOINS[i+1:]:
                row    = {"Paire": f"{base}/{quote}"}
                prices = []

                for dex in DEXES:
                    # "Jupiter" = global multi-hop
                    actual = None if dex=="Jupiter" else dex
                    price  = await get_price(session, base, quote, actual)
                    row[dex] = price
                    if isinstance(price, float):
                        prices.append(price)

                if prices:
                    spread = (max(prices)-min(prices))/min(prices)*100
                    row["Spread Max (%)"] = round(spread, 4)
                    row["💸 Arbitrage"]   = "✅" if spread>=min_spread else ""
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
    with st.spinner("Scanning…"):
        data = asyncio.run(fetch_all(min_spread))
        st.write("📦 Données brutes:", data)
        df = pd.DataFrame(data)
        if not df.empty and "Spread Max (%)" in df.columns:
            df = df.sort_values("Spread Max (%)", ascending=False)
        st.dataframe(df, use_container_width=True)
else:
    st.info("Clique sur 🔄 pour lancer le scan.")
