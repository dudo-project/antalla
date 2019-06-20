import os

if os.environ.get("MARKETS"):
    MARKETS = os.environ["MARKETS"].split(",")
else:
    MARKETS = ["ETH_AURA", "ETH_IDXM", "ETH_FTM", "ETH_LTO"]

IDEX_EVENTS = ["market_orders", "market_cancels", "market_trades"]
IDEX_API_KEY = "17paIsICur8sA0OBqG6dH5G1rmrHNMwt4oNk4iX9"
IDEX_WS_URL = "wss://datastream.idex.market"
IDEX_API = "https://api.idex.market"
IDEX_API_MARKETS = "return24Volume"

BINANCE_MARKETS = ["BNB_BTC", "ETH_BTC", "LTC_BTC"]
BINANCE_STREAMS = ["depth", "trade"]
BINANCE_SINGLE_STREAM = "wss://stream.binance.com:9443/ws/"
BINANCE_COMBINED_STREAM = "wss://stream.binance.com:9443/stream?streams="
BINANCE_API_KEY = "IddI1NMcPNMMm7vNeavClaP86k3zpGbOuEGLoUoL1euLohzRxFjK5y0nI7jQ1swZ"
BINANCE_SECRET_KEY = "G4XdKRYm9A7Wtq2zoNTV6WJbRf3NN3s4156zRQKvCVGyyQFsPkZMlIbXljkCS2h6"
BINANCE_API = "https://api.binance.com"
BINANCE_PUBLIC_API = "api/v1"
BINANCE_PRIVATE_API = "api/v3"
BINANCE_API_MARKETS = "ticker/24hr?"
BINANCE_API_INFO = "exchangeInfo"

DB_URL = os.environ.get("DB_URL", "postgresql+psycopg2://antalla@localhost/antalla?client_encoding=utf8")
PACKAGE = "antalla"

COINBASE_WS_URL = "wss://ws-feed.pro.coinbase.com"
COINBASE_MARKETS = ["ETH_USD", "ETH_EUR"]
COINBASE_CHANNELS = ["full"]
COINBASE_API_KEY = os.environ.get("COINBASE_API_KEY")
COINBASE_API_SECRET = os.environ.get("COINBASE_API_SECRET")
COINBASE_API = "https://api.pro.coinbase.com"
COINBASE_API_PRODUCTS = "products"
COINBASE_API_TICKER =  "ticker"

PACKAGE = "antalla"
