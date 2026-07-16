import os
from dotenv import load_dotenv
import requests

class Watcher:
    def __init__(self, api_key):
        self.api_key = api_key
    def get_puuid(self, summoner_name, tag_line):
        url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tag_line}?api_key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['puuid']
        else:
            return None
    def get_stats(self, region, puuid):
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}?api_key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    def get_spectator(self, region, puuid):
        url = f"https://{region}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}?api_key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    def get_clash(self, region):
        url = f"https://{region}.api.riotgames.com/lol/clash/v1/tournaments?api_key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
if(__name__ == '__main__'):
    load_dotenv()
    test_names = os.getenv("NAMES").split(",")
    print(test_names)
    w = Watcher(os.getenv("API_KEY"))
    print(os.getenv("API_KEY"))
    p = w.get_puuid(test_names[0].split("#")[0], test_names[0].split("#")[1])
    print(p)
    print(w.get_stats('ru', p))
    print(w.get_spectator('ru', p))
    print(w.get_clash('ru'))

