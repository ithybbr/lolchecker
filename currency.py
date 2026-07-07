import requests

def get_exchange_rate(first_currency = "USD", second_currency = "KZT") -> float:
    url = f"https://api.exchangerate-api.com/v4/latest/{first_currency}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['rates'].get(second_currency)
    else:
        return None