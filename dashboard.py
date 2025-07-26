# README.md
# Crypto Arbitrage Bot - Stablecoins on Solana

This project contains a Python-based arbitrage bot for stablecoins on the Solana blockchain, using the Jupiter aggregator for multi-hop routing, and a Streamlit dashboard for real-time monitoring.

## Project Structure

- `config.py`: Configuration variables (token mints, API URLs).
- `arbitrage_bot.py`: Core logic to fetch prices across DEXes.
- `dashboard.py`: Streamlit dashboard to display real-time price spreads.
- `requirements.txt`: Python dependencies.

## Installation

```bash
# Create & activate a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run the arbitrage bot (console)
```bash
python arbitrage_bot.py
```

### Launch the dashboard (web UI)
```bash
streamlit run dashboard.py
```

---

# config.py
```python
# config.py

# Stablecoins to track
STABLECOINS = ["USDC", "USDT", "DAI", "UXD", "USDL"]

# Solana mint addresses
TOKEN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERk8F3nWjrmA7z4S2k7GFHPiDTbvu9K5bD",
    "DAI":  "DAwBSgGZDTFzyxAqzJp9SLwz1gdEDhnno2nZyzVSV7Ez",
    "UXD":  "7kbnvuGBxxj8AG9qp8Scn56muWGaRaFqxg1FsRp3PaFT",
    "USDL": "5vfjkX5jGsdYVYcWy6HRgUxhN6hzXZGTmA8qcRfXhCz7"
}

# Jupiter API endpoint
JUPITER_API_URL = "https://quote-api.jup.ag/v6/quote"
```

# arbitrage_bot.py
```python
import asyncio
import aiohttp
from config import STABLECOINS, TOKEN_MINTS, JUPITER_API_URL

async def fetch_price(session, token_in: str, token_out: str) -> float | None:
    """
    Fetch a single price quote from Jupiter (multi-hop enabled).
    Returns the outAmount converted to units, or None.
    """
    if token_in not in TOKEN_MINTS or token_out not in TOKEN_MINTS:
        return None

    params = {
        "inputMint": TOKEN_MINTS[token_in],
        "outputMint": TOKEN_MINTS[token_out],
        "amount": 1_000_000,
        "slippageBps": 10,
        "onlyDirectRoutes": "false"
    }

    async with session.get(JUPITER_API_URL, params=params) as resp:
        if resp.status != 200:
            return None
        data = await resp.json()
        arr = data.get("data") or []
        if arr:
            out_amount = int(arr[0]["outAmount"])
            return out_amount / 1_000_000
    return None

async def scan_arbitrage():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, base in enumerate(STABLECOINS):
            for quote in STABLECOINS[i+1:]:
                tasks.append((base, quote, fetch_price(session, base, quote)))

        results = []
        for base, quote, coro in tasks:
            price = await coro
            results.append((f"{base}/{quote}", price))

        # Print results
        for pair, price in results:
            print(f"{pair}: {price}")

if __name__ == "__main__":
    asyncio.run(scan_arbitrage())
```

# dashboard.py
```python
import streamlit as st
import pandas as pd
import aiohttp
import asyncio
from config import STABLECOINS, TOKEN_MINTS, JUPITER_API_URL

st.set_page_config(page_title="Kali Crypto Arbitrage", layout="wide")
st.title("🔍 Kali Crypto Arbitrage — Stablecoins Solana 📈")

async def fetch_price(session, token_in: str, token_out: str) -> float | None:
    params = {
        "inputMint": TOKEN_MINTS[token_in],
        "outputMint": TOKEN_MINTS[token_out],
        "amount": 1_000_000,
        "slippageBps": 10,
        "onlyDirectRoutes": "false"
    }
    async with session.get(JUPITER_API_URL, params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            arr = data.get("data") or []
            if arr:
                return round(int(arr[0]["outAmount"]) / 1_000_000, 6)
    return None

async def scan_prices():
    rows = []
    async with aiohttp.ClientSession() as session:
        for i, base in enumerate(STABLECOINS):
            for quote in STABLECOINS[i+1:]:
                price = await fetch_price(session, base, quote)
                rows.append({"Pair": f"{base}/{quote}", "Jupiter Price": price})
    return rows

# UI
st.sidebar.header("Settings")
refresh = st.sidebar.slider("Refresh Interval (s)", 5, 60, 10)

placeholder = st.empty()

while True:
    data = asyncio.run(scan_prices())
    df = pd.DataFrame(data)
    placeholder.table(df)
    st.experimental_rerun()
```

# requirements.txt
```
streamlit
pandas
aiohttp
