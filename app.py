import requests
import time

API_URL = "https://api.hyperliquid.xyz/info"

# Assets HIP-3 identifiés
ASSETS = {
    "NVDA": "@408",
    "TSLA": "@407",
    "GOOGL": "@412"
}

# Deployers / DEX
DEXES = {
    "TradeXYZ": "XYZ",
    "Dreamcash": "DRM",
    "Kinetiq": "KIN"
}

def get_l2_book(asset_id, dex):
    payload = {
        "type": "l2Book",
        "coin": asset_id,
        "dex": dex
    }

    try:
        r = requests.post(API_URL, json=payload)
        data = r.json()

        bid = float(data["levels"][0][0]["px"])
        ask = float(data["levels"][1][0]["px"])

        mid = (bid + ask) / 2

        return {
            "bid": bid,
            "ask": ask,
            "mid": mid
        }

    except Exception:
        return None


def scan_markets():

    results = {}

    for asset, asset_id in ASSETS.items():

        results[asset] = {}

        for dex_name, dex_code in DEXES.items():

            book = get_l2_book(asset_id, dex_code)

            if book:
                results[asset][dex_name] = book["mid"]
            else:
                results[asset][dex_name] = None

    return results


def find_arbitrage(prices):

    for asset, dex_prices in prices.items():

        dex_list = list(dex_prices.keys())

        for i in range(len(dex_list)):
            for j in range(i+1, len(dex_list)):

                d1 = dex_list[i]
                d2 = dex_list[j]

                p1 = dex_prices[d1]
                p2 = dex_prices[d2]

                if p1 is None or p2 is None:
                    continue

                spread = p1 - p2

                if abs(spread) > 0.2:   # seuil arbitrage

                    print(
                        f"ARBITRAGE {asset}: "
                        f"{d1}={p1:.2f} vs {d2}={p2:.2f} "
                        f"spread={spread:.2f}"
                    )


def main():

    while True:

        prices = scan_markets()

        print("\nPrices:")
        for asset in prices:
            print(asset, prices[asset])

        find_arbitrage(prices)

        time.sleep(3)


if __name__ == "__main__":
    main()
