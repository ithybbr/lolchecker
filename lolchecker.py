from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from riotwatcher import LolWatcher, ApiError
from leaguenames import leaguenames
import pandas as pd
import datetime
import os
from flask import Flask
app = Flask(__name__)

Token: Final = os.getenv("TOKEN ")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
api_key = os.getenv("API_KEY")
watcher = LolWatcher(api_key)
my_region = 'ru'
    #commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hi! I check em playing')
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I ping when they play')
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    names = ['Naginata06', 'Adik20000', 'MindZedOnly', 'Lord Divan', 'Amrano', 'Belovist', 'ithyb']
    main_text = ''
    for x in names:
        temp_text = handle_response(x)
        print(f'this is temp {temp_text}')
        if temp_text != 'nah':
            main_text += temp_text + '\n'
    if main_text == '':
        main_text = 'nobody is playing rn'
    print (main_text)
    await update.message.reply_text(main_text)
async def custom_command2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nagi_id = os.getenv("NAGI_ID")
    nagi = '[Nurda](tg://user?id='+str(nagi_id)+')'
    nuri_id = os.getenv("NURI_ID")
    nuri = '[Nurial](tg://user?id='+str(nuri_id)+')'
    divan_id = os.getenv("DIVAN_ID")
    divan = '[@Divan_Amir](tg://user?id='+str(divan_id)+')'
    await update.message.reply_text(f'@Adik20000 @mrinooo {nuri} {nagi} {divan}', parse_mode='Markdown')
    #responses
def handle_response(text: str) -> str:
    if 'stats' in text:
        check: str = text.replace('stats','').strip()
        ida = watcher.summoner.by_name(my_region, check)
        showem = watcher.league.by_summoner(my_region, ida['id'])
        for x in showem:
            print(x)
            if x['queueType'] == 'RANKED_SOLO_5x5':
                tier = x['tier']
                rank = x['rank']
                wins = x['wins']
                losses = x['losses']
                winrate = round(wins/(wins+losses) * 100,2)
                return f'{check} is in {tier} {rank} with {winrate}% winrate'
        return f'bruh {check} got no history'
    try:
        k = 0
        lol = watcher.summoner.by_name(my_region, text)
        match = watcher.spectator.by_summoner(my_region, lol['id'])
        print(match)
        k = 1
    except:
        pass
    if k == 1:
        length = match['gameLength'] + 160
        minutes = round(length / 60)
        seconds = length % 60
        #current_time = datetime.now.strftime("%H:%M:%S")
        start_time = match['gameStartTime'] / 1000
        #converted = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S.%f')
        today = datetime.datetime.fromtimestamp(start_time).strftime('%H:%M')
        for i in range(0,10):
            if(match['participants'][i]['summonerId'] == lol['id']):
                championId = match['participants'][i]['championId']
        champName = leaguenames(championId)
        return f'{text} is playing {champName}. The game has started at {today} & current in-game time is roughly {minutes}:{seconds :02d}'
    else:
        return 'nah'   
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'supergroup':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME,'').strip()
            print(new_text)
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    
    print('Bot:', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(Token).build()

    #commands
    app.add_handler(CommandHandler('start',start_command))
    app.add_handler(CommandHandler('help',help_command))
    app.add_handler(CommandHandler('pingme',custom_command))
    app.add_handler(CommandHandler('pingthem',custom_command2))

    #messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    #errors
    app.add_error_handler(error)
    print('polling...')
    app.run_polling(poll_interval=5)