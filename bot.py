from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import json
from flask import Flask
import lolchecker
app = Flask(__name__)

load_dotenv()

Token: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
conv_names = json.loads(os.getenv("CONV_NAMES"))

#Leaving this just in case
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('So there are 5 commands:\n'
    '/q <name> - to check if someone is playing\n'
    '/pingthem <text> - to ping the group with a custom message\n'
    '/clashwhen - to check when the next clash is\n'
    '/ninjas <text> - to create a poll for the group chat\n'
    '/stats <name> - to check the stats of a player\n'
    f'{json.dumps(conv_names, indent=4, separators=("", " --- "))}\n')

# JUST PINGS IN THE GROUP CHAT
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    text = text.replace('/pingthem','').strip()
    await update.message.reply_text(f'{os.getenv("PING_TEXT")} {text}', parse_mode='Markdown')

#creates poll for the group chat
async def ninjas_assemble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text.replace("/ninjas", "").strip()
    message = await update.message.reply_poll(question=f'Are you ready for {text}?',
        options=['Locked In', 'Geeked out'], is_anonymous=False, allows_multiple_answers=False)
    p = await message.pin()
    await p.delete()

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

async def query_q(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    text = text.replace('/q','').strip()
    if(text == ''):
        response: str = lolchecker.q_all()
        await update.message.reply_text(response)
        return
    response: str = lolchecker.query(conv_names.get(text,text))
    if response == None:
        response = f'{text} is not playing rn'
    await update.message.reply_text(response)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name:str = update.message.text
    name = name.replace('/stats','').strip()
    if(name == ''):
        response: str = lolchecker.all_stats()
        await update.message.reply_text(response)
        return
    name = conv_names.get(name,name)
    response: str = lolchecker.get_stats(name)
    await update.message.reply_text(response)

#CLASH
async def clash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response: str = lolchecker.next_clash()
    await update.message.reply_text(response)

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(Token).build()

    #commands
    app.add_handler(CommandHandler('help',help_command))
    app.add_handler(CommandHandler('q',query_q))
    app.add_handler(CommandHandler('ping',ping))
    app.add_handler(CommandHandler('clashwhen',clash))
    app.add_handler(CommandHandler('ninjas',ninjas_assemble))
    app.add_handler(CommandHandler('stats',stats))
    #messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    #errors
    app.add_error_handler(error)
    print('polling...')
    app.run_polling(poll_interval=5)