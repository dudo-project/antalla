import os


MARKETS = [
    "BTC_USD",
    "ETH_USD",
    "BTC_ETH",
    "BTC_EOS",
    "ETH_USDT",
    "BTC_BCH",
    "BTC_BSV",
    "BTC_BTG",
    "BTC_BNB",
    "ETH_FTM",
]


IDEX_EVENTS = {
    "trade": ["market_trades"],
    "depth": ["market_orders", "market_cancels"],
}
IDEX_API_KEY = "17paIsICur8sA0OBqG6dH5G1rmrHNMwt4oNk4iX9"
IDEX_WS_URL = "wss://datastream.idex.market"
IDEX_API = "https://api.idex.market"
IDEX_API_MARKETS = "return24Volume"
IDEX_MARKETS = MARKETS

BINANCE_MARKETS = MARKETS
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

ENV = os.environ.get("ENV", "development")

if ENV == "test":
    DB_URL = os.environ.get("DB_URL", "postgresql+psycopg2://antalla:antalla@localhost/antalla-test?client_encoding=utf8")
else:
    DB_URL = os.environ.get("DB_URL", "postgresql+psycopg2://antalla:antalla@localhost/antalla?client_encoding=utf8")

#DB_URL = os.environ.get("DB_URL", "postgresql+psycopg2://antalla:antalla@satoshi.doc.ic.ac.uk/antalla?client_encoding=utf8")
PACKAGE = "antalla"

COINBASE_WS_URL = "wss://ws-feed.pro.coinbase.com"

COINBASE_MARKETS = MARKETS
#COINBASE_CHANNELS = ["full"]
COINBASE_CHANNELS = {
    "depth": ["level2"],
    "trade": ["full"],
}

COINBASE_API_KEY = os.environ.get("COINBASE_API_KEY")
COINBASE_API_SECRET = os.environ.get("COINBASE_API_SECRET")
COINBASE_API = "https://api.pro.coinbase.com"
COINBASE_API_PRODUCTS = "products"
COINBASE_API_TICKER =  "ticker"

COINMARKETCAP_URL = "https://coinmarketcap.com/all/views/all/"

HITBTC_MARKETS = MARKETS
HITBTC_WS_URL = "wss://api.hitbtc.com/api/2/ws"
HITBTC_API = "https://api.hitbtc.com/api/2"
HITBTC_API_MARKETS = "public/ticker"
HITBTC_API_SYMBOLS = "public/symbol"
HITBTC_API_KEY = "hBjmU7CawOCRg248JLloOerbOKg8I8k3"
