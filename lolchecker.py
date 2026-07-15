from leaguenames import leaguenames
from dotenv import load_dotenv
from Watcher import Watcher
from cache import Cache
from datetime import timedelta, datetime, timezone
import os

load_dotenv()

api_key = os.getenv("API_KEY")
watcher = Watcher(api_key)
my_region = 'ru'
tz_utc5 = timezone(timedelta(hours=5))
id_cache = Cache()
def getId(name: str) -> str:
    try:
        if id_cache.get(name) != None:
            return id_cache.get(name)
        gameName = name.split('#')[0]
        tagLine = name.split('#')[1]
        puuid = watcher.get_puuid(gameName, tagLine)
        id_cache.set(name, puuid, ttl=60*60*24)  # Cache for 24 hours
        return puuid
    except:
        return None
    
# GET LIVE STATS
def q_all() -> str:
    names = os.getenv("NAMES").split(",")
    main_text = ''
    for x in names:
        curr_text = query(x)
        if curr_text != None:
            main_text += curr_text + '\n'
    if main_text == '':
        main_text = 'nobody is playing rn'
    return main_text

matches_cache = Cache()
def query(text: str) -> str:
    try:
        try:
            id = getId(text)
        except Exception as e:
            print(f'Error occurred while getting ID for {text}: {e}')
            return f'didnt find id for {text}'
        match = matches_cache.get(id)
        if match == None:
            match = watcher.get_spectator(my_region, id)
    except:
        pass
    if match != None:
        length = match['gameLength']
        minutes = round(length / 60)
        seconds = length % 60
        start_time = match['gameStartTime'] / 1000
        today = datetime.fromtimestamp(start_time, tz_utc5).strftime('%H:%M')
        for i in range(0,10):
            if(match['participants'][i]['puuid'] == id):
                championId = match['participants'][i]['championId']
            if(match['participants'][i]['puuid'] in id_cache.values()):
                matches_cache.set(match['participants'][i]['puuid'], match)
        champName = leaguenames(championId)
        return f'{text} is playing {champName}. The game has started at {today} & current in-game time is roughly {minutes}:{seconds :02d}'
    else:
        return None
    
def all_stats() -> str:
    names = os.getenv("NAMES").split(",")
    main_text = ''
    for x in names:
        curr_text = get_stats(x)
        if curr_text != None:
            main_text += curr_text + '\n'
    if main_text == '':
        main_text = 'stats are so dogshit there are no records'
    return main_text
def get_stats(name:str) -> str:
    try:
        id = getId(name)
    except:
        return f'twin, this guy {name} is chopped'
    stats = watcher.get_stats(my_region, id)
    for x in stats:
        if x['queueType'] == 'RANKED_SOLO_5x5':
            tier = x['tier']
            rank = x['rank']
            wins = x['wins']
            losses = x['losses']
            winrate = round(wins/(wins+losses) * 100,2)
            return f'{name} is in {tier} {rank} with {winrate}% winrate'

#CLASH LOGIC
clash_types = {33: 'Summoner\'s Rift', 34: 'Howling Abyss'}
clash_cache = Cache()
def next_clash() -> str:
    clash = clash_cache.get('clash')
    if clash == None:
        clash = watcher.get_clash(my_region)
    if clash != None:
            clash_cache.set('clash', clash, ttl=60*60*24*3)  # Cache for 3 days
            start_time = clash[0]['schedule'][0]['startTime'] / 1000
            theme_id = clash[0]['themeId']
            theme = clash_types.get(theme_id, 'Unknown')
            deadline = datetime.fromtimestamp(start_time, tz_utc5) - timedelta(hours=1)
            deadline = deadline.strftime('%d.%m %H:%M')
            return f'Next clash is {theme} on {deadline}'
    else:
        return 'There is no clash scheduled at the moment'