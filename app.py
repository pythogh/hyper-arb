import requests
import json

url = "https://api.hyperliquid.xyz/info"

payload = {
    "type": "l2Book",
    "coin": "xyz:NVDA"
}

r = requests.post(url, json=payload)

print(r.json())
