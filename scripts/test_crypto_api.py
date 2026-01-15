
import requests
import json

def test_crypto_api():
    print("Testing CryptoAPI.news...")
    
    # Test News
    try:
        url = "https://cryptoapi.news/api/v1/free/lastnews/all/5"
        print(f"GET {url}")
        res = requests.get(url, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("News Response:")
            try:
                print(json.dumps(res.json(), indent=2))
            except:
                print(res.text[:500])
        else:
            print("Failed.")
    except Exception as e:
        print(f"Error: {e}")

    # Test Sentiment
    try:
        url = "https://cryptoapi.news/api/v1/free/sentiment/all"
        print(f"\nGET {url}")
        res = requests.get(url, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("Sentiment Response:")
            try:
                print(json.dumps(res.json(), indent=2))
            except:
                print(res.text[:500])
        else:
            print("Failed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_crypto_api()
