import requests

r = requests.post(
    "https://api.hyperliquid.xyz/info",
    headers={"Content-Type": "application/json"},
    json={"type": "allMids"}
)

print("status:", r.status_code)
print(r.text[:1000])
