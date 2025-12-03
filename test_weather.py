import requests

url = "https://api.yaohud.cn/api/v6/weather"
key = "qbvOGz9XSuLh7MF3rP7"
city = "北京"

params_list = [
    {"key": key, "city": city},
    {"key": key, "location": city},
    {"key": key, "name": city},
    {"key": key, "city": "Beijing"}
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for params in params_list:
    print(f"Testing params: {params}")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content: {response.text}")
        try:
            json_data = response.json()
            print("JSON Parse Success")
        except:
            print("JSON Parse Failed")
    except Exception as e:
        print(f"Request Failed: {e}")
    print("-" * 20)
