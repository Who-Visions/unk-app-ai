
import requests
import json

def test_cryptocompare():
    print("Testing CryptoCompare News...")
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        print(f"GET {url}")
        res = requests.get(url, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"Message: {data.get('Message')}")
            news = data.get('Data', [])
            print(f"News Count: {len(news)}")
            if news:
                print("Sample Article:")
                print(json.dumps(news[0], indent=2))
        else:
            print("Failed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cryptocompare()
