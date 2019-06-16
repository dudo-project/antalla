import os

if os.environ.get("MARKETS"):
    MARKETS = os.environ["MARKETS"].split(",")
else:
    MARKETS = ["ETH_AURA", "ETH_IDXM", "ETH_FTM", "ETH_LTO"]

IDEX_EVENTS = ["market_orders", "market_cancels", "market_trades"]
IDEX_API_KEY = "17paIsICur8sA0OBqG6dH5G1rmrHNMwt4oNk4iX9"
IDEX_WS_URL = "wss://datastream.idex.market"

BINANCE_MARKETS = ["BNB_BTC", "ETH_BTC"]
BINANCE_STREAMS = ["depth", "trade"]
BINANCE_SINGLE_STREAM = "wss://stream.binance.com:9443/ws/"
BINANCE_COMBINED_STREAM = "wss://stream.binance.com:9443/stream?streams="
BINANCE_API_KEY = "IddI1NMcPNMMm7vNeavClaP86k3zpGbOuEGLoUoL1euLohzRxFjK5y0nI7jQ1swZ"
BINANCE_SECRET_KEY = "G4XdKRYm9A7Wtq2zoNTV6WJbRf3NN3s4156zRQKvCVGyyQFsPkZMlIbXljkCS2h6"
BINANCE_API = "https://api.binance.com"
BINANCE_PUBLIC_API = "api/v1"
BINANCE_PRIVATE_API = "api/v3"

DB_URL = os.environ.get("DB_URL", "sqlite:///antalla.db")
PACKAGE = "antalla"

COINBASE_WS_URL = "wss://ws-feed.pro.coinbase.com"
