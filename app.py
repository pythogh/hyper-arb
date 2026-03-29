import requests
import time

URL = "https://api.hyperliquid.xyz/info"

# coins HIP3
COINS = [
    "xyz:NVDA",
    "drm:NVDA",
    "kin:NVDA",

    "xyz:TSLA",
    "drm:TSLA",
    "kin:TSLA",

    "xyz:GOOGL",
    "drm:GOOGL",
    "kin:GOOGL",
]


def get_mid(coin):

    payload = {
        "type": "l2Book",
        "coin": coin
    }

    try:
        r = requests.post(URL, json=payload, timeout=5)
        data = r.json()

        bids = data["levels"][0]
        asks = data["levels"][1]

        bid = float(bids[0]["px"])
        ask = float(asks[0]["px"])

        mid = (bid + ask) / 2

        return mid

    except Exception as e:
        print("error", coin, e)
        return None


while True:

    prices = {}

    for coin in COINS:

        mid = get_mid(coin)

        if mid:
            prices[coin] = mid

    print("\nPrices:")
    for k, v in prices.items():
        print(k, v)

    time.sleep(2)
