import requests
from cache import Cache

rate_cache = Cache()
def get_exchange_rate(first_currency = "USD", second_currency = "KZT") -> float:
    if rate_cache.get(first_currency) != None:
        response = rate_cache.get(first_currency)
    else:
        url = f"https://api.exchangerate-api.com/v4/latest/{first_currency}"
        response = requests.get(url)
        rate_cache.set(first_currency, response, ttl=60*60*4)
    if response.status_code == 200:
        data = response.json()
        return data['rates'][second_currency]
    else:
        return None