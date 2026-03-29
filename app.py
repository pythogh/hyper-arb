import requests
import json

url = "https://api.hyperliquid.xyz/info"

payload = {
    "type": "allMids"
}

r = requests.post(url, json=payload)

data = r.json()

for coin in data:
    if "NVDA" in coin:
        print(coin, data[coin])
