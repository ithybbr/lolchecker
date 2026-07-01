from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from leaguenames import leaguenames
from dotenv import load_dotenv
from Watcher import Watcher
from cache import Cache
from datetime import timedelta, datetime
import os
import json
from flask import Flask
app = Flask(__name__)

load_dotenv()

Token: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
api_key = os.getenv("API_KEY")
watcher = Watcher(api_key)
my_region = 'ru'
#commands
conv_names = json.loads(os.getenv("CONV_NAMES"))
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('So there are 5 commands:\n'
    '/q <name> - to check if someone is playing\n'
    '/pingthem <text> - to ping the group with a custom message\n'
    '/clashwhen - to check when the next clash is\n'
    '/ninjas <text> - to create a poll for the group chat\n'
    '/stats <name> - to check the stats of a player\n'
    f'{json.dumps(conv_names, indent=4, separators=("", " --- "))}\n')
async def query_q(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    text = text.replace('/q','').strip()
    if(text == ''):
        response: str = q_all()
        await update.message.reply_text(response)
        return
    response: str = query(conv_names.get(text,text))
    if response == None:
        response = f'{text} is not playing rn'
    await update.message.reply_text(response)
# JUST PINGS IN THE GROUP CHAT
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    text = text.replace('/pingthem','').strip()
    await update.message.reply_text(f'{os.getenv("PING_TEXT")} {text}', parse_mode='Markdown')
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
        today = datetime.fromtimestamp(start_time).strftime('%H:%M')
        for i in range(0,10):
            if(match['participants'][i]['puuid'] == id):
                championId = match['participants'][i]['championId']
            if(match['participants'][i]['puuid'] in id_cache.values()):
                matches_cache.set(match['participants'][i]['puuid'], match)
        champName = leaguenames(championId)
        return f'{text} is playing {champName}. The game has started at {today} & current in-game time is roughly {minutes}:{seconds :02d}'
    else:
        return None
    
async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name:str = update.message.text
    name = name.replace('/stats','').strip()
    name = conv_names.get(name,name)
    try:
        id = getId(name)
    except:
        await update.message.reply_text(f'bruh {name} got no history')
        return
    stats = watcher.get_stats(my_region, id)
    for x in stats:
        if x['queueType'] == 'RANKED_SOLO_5x5':
            tier = x['tier']
            rank = x['rank']
            wins = x['wins']
            losses = x['losses']
            winrate = round(wins/(wins+losses) * 100,2)
            await update.message.reply_text(f'{name} is in {tier} {rank} with {winrate}% winrate')

#CLASH LOGIC
clash_types = {33: 'Summoner\'s Rift', 34: 'Howling Abyss'}
clash_cache = Cache()
async def next_clash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clash = clash_cache.get('clash')
    if clash == None:
        clash = watcher.get_clash(my_region)
    if clash != None:
            clash_cache.set('clash', clash, ttl=60*60*24*3)  # Cache for 3 days
            start_time = clash[0]['schedule'][0]['startTime'] / 1000
            theme_id = clash[0]['themeId']
            theme = clash_types.get(theme_id, 'Unknown')
            deadline = datetime.fromtimestamp(start_time) - timedelta(hours=1)
            deadline = deadline.strftime('%d.%m %H:%M')
            await update.message.reply_text(f'Next clash is {theme} on {deadline}')
    else:
        await update.message.reply_text('There is no clash scheduled at the moment')
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    if message_type == 'supergroup':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME,'').strip()
            response: str = query(new_text)
        else:
            return
    else:
        response: str = query(text)
    await update.message.reply_text(response)
#creates poll for the group chat
async def ninjas_assemble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text.replace("/ninjas", "").strip()
    message = await update.message.reply_poll(question=f'Are you ready for {text}?',
        options=['Locked In', 'Geeked out'], is_anonymous=False, allows_multiple_answers=False)
    p = await message.pin()
    await p.delete()
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(Token).build()

    #commands
    app.add_handler(CommandHandler('help',help_command))
    app.add_handler(CommandHandler('q',query_q))
    app.add_handler(CommandHandler('ping',ping))
    app.add_handler(CommandHandler('clashwhen',next_clash))
    app.add_handler(CommandHandler('ninjas',ninjas_assemble))
    app.add_handler(CommandHandler('stats',get_stats))
    #messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    #errors
    app.add_error_handler(error)
    print('polling...')
    app.run_polling(poll_interval=5)