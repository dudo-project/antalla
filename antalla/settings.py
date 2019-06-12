import os

if os.environ.get("MARKETS"):
    MARKETS = os.environ["MARKETS"].split(",")
else:
    MARKETS = ["ETH_AURA", "ETH_IDXM", "ETH_FTM", "ETH_LTO"]

IDEX_EVENTS = ["market_orders", "market_cancels", "market_trades"]
IDEX_API_KEY = "17paIsICur8sA0OBqG6dH5G1rmrHNMwt4oNk4iX9"
IDEX_WS_URL = "wss://datastream.idex.market"
DB_NAME = "antalla.db"
DB_URL = os.environ.get("DB_URL", "sqlite:///"+DB_NAME)
PACKAGE = "antalla"
