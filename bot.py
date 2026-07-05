from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, JobQueue, MessageHandler, PollAnswerHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import json
from flask import Flask
import lolchecker
import gemini
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
    '/ping <text> - to ping the group with a custom message\n'
    '/clashwhen - to check when the next clash is\n'
    '/poll <text> - to create a poll for the group chat\n'
    '/stats <name> - to check the stats of a player\n'
    '/chat <text> - to prompt gemini\n'
    f'{json.dumps(conv_names, indent=4, separators=("", " --- "))}\n')
async def delete_pin_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.delete()
# JUST PINGS IN THE GROUP CHAT
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    text = text.replace('/ping','').strip()
    await update.message.reply_text(f'{os.getenv("PING_TEXT")} {text}', parse_mode='Markdown')

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    text = text.replace('/chat','').strip()
    response: str = gemini.ask_gemini(text)
    await update.message.reply_text(response)
#creates poll for the group chat
async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text.replace("/poll", "").strip()
    message = await update.message.reply_poll(question=f'{text}?',
        options=['Locked In', 'Geeked out'], is_anonymous=False, allows_multiple_answers=False)

    base_ping = os.getenv("PING_TEXT")

    context.bot_data.setdefault('active_polls', {})[message.poll.id] = {
        'chat_id': message.chat_id,
        'message_id': message.message_id,
        'question': text,
        'ping_text': base_ping,   # per-poll copy
    }

    await message.pin(disable_notification=False)

    context.job_queue.run_repeating(reminder, interval=60 * 60, first=60 * 60, last=60 * 60 * 4, data=message.poll.id, chat_id=message.chat_id, name=str(message.poll.id))

    context.job_queue.run_once(delete_poll_message, when=60 * 60 * 5, data={'chat_id': message.chat_id, 'message_id': message.message_id, 'poll_id': message.poll.id})

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user = answer.user
    poll_info = context.bot_data.get('active_polls', {}).get(answer.poll_id)
    if poll_info and poll_info.get('ping_text'):
        poll_info['ping_text'] = poll_info['ping_text'].replace(f'@{user.username}', '')

async def reminder(context: ContextTypes.DEFAULT_TYPE):
    poll_id = context.job.data
    poll_info = context.bot_data.get('active_polls', {}).get(poll_id)
    if poll_info and poll_info.get('ping_text', '').strip():
        message = await context.bot.send_message(chat_id=poll_info['chat_id'],text=poll_info['ping_text'],parse_mode='Markdown', reply_to_message_id=poll_info['message_id'])
        context.bot_data.setdefault('active_pings', []).append(message.message_id)

async def delete_poll_message(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    context.bot_data.get('active_polls', {}).pop(data['poll_id'], None)
    await context.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])
    await context.bot.delete_messages(chat_id=data['chat_id'], message_ids=list(context.bot_data.get('active_pings', [])))
    
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

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(Token).build()

    #commands
    app.add_handler(CommandHandler('help',help_command))
    app.add_handler(CommandHandler('q',query_q))
    app.add_handler(CommandHandler('ping',ping))
    app.add_handler(CommandHandler('clashwhen',clash))
    app.add_handler(CommandHandler('poll',poll))
    app.add_handler(CommandHandler('stats',stats))
    app.add_handler(CommandHandler('chat',chat))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, delete_pin_notification))
    app.add_handler(PollAnswerHandler(receive_poll_answer))
    #errors
    app.add_error_handler(error)
    print('polling...')
    app.run_polling(poll_interval=5)