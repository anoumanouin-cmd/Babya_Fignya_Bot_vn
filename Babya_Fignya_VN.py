#!/usr/bin/env python
# coding: utf-8

from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ChatMemberHandler, ContextTypes
from datetime import datetime
import pytz
import asyncio

# -----------------------------
# 🔹 Настройки
# -----------------------------
TOKEN = "8301083124:AAGhbMXn6LuBpr2mT3tVWvw42dEcC2PYHyk"
TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")
announcement_posted = {}

# -----------------------------
# 🔹 Функция для определения периода дня
# -----------------------------
def get_time_period():
    now = datetime.now(TIMEZONE).time()
    if now >= datetime.strptime("07:00", "%H:%M").time() and now < datetime.strptime("16:00", "%H:%M").time():
        return "morning"
    elif now >= datetime.strptime("16:00", "%H:%M").time() and now < datetime.strptime("23:59", "%H:%M").time():
        return "evening"
    else:
        return "night"

# -----------------------------
# 🔹 Обработчики сообщений
# -----------------------------
async def handle_message(update, context):
    message = getattr(update, "edited_message", None) or update.message
    if not message:
        return

    content = message.text or message.caption
    if not content:
        return

    text = content.lower()
    if "#объявление" not in text:
        return

    author = message.from_user
    period = get_time_period()
    today = datetime.now(TIMEZONE).date().isoformat()
    if today not in announcement_posted:
        announcement_posted[today] = {'morning': False, 'evening': False}

    # --- Ночь ---
    if period == "night":
        await context.bot.send_message(
            chat_id=message.chat.id,
            text=f"{author.mention_html()}, Объявление удалено. Перезалейте с 07:00 до 16:00",
            parse_mode="HTML"
        )
        await message.delete()
        return

    # --- Утро ---
    if period == "morning":
        if not announcement_posted[today]["morning"]:
            announcement_posted[today]["morning"] = True
            await context.bot.send_message(chat_id=message.chat.id, text="Утреннее объявление ✅")
        else:
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f"{author.mention_html()}, Объявление удалено: утреннее объявление уже было сегодня.",
                parse_mode="HTML"
            )
            await message.delete()
        return

    # --- Вечер ---
    if period == "evening":
        if not announcement_posted[today]["evening"]:
            announcement_posted[today]["evening"] = True
            await context.bot.send_message(chat_id=message.chat.id, text="Вечернее объявление ✅")
        else:
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f"{author.mention_html()}, Объявление удалено: вечернее объявление уже было сегодня.",
                parse_mode="HTML"
            )
            await message.delete()
        return

# === Приветствие новых участников ===
async def greet_new_member(update, context):
    message = update.message
    if not message or not getattr(message, "new_chat_members", None):
        return
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        await context.bot.send_message(chat_id=message.chat.id,
                                       text=f"Привет, {member.first_name}! Приятного общения!")

# -----------------------------
# 🔹 Инициализация бота
# -----------------------------
app_bot = ApplicationBuilder().token(TOKEN).build()
app_bot.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))
app_bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))
app_bot.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, handle_message))
app_bot.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_message))

# -----------------------------
# 🔹 Flask + webhook
# -----------------------------
bot = Bot(token=TOKEN)
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Telegram присылает сюда обновления"""
    update = Update.de_json(request.get_json(force=True), bot)
    # Создаем асинхронную задачу, чтобы не блокировать Flask
    asyncio.create_task(app_bot.process_update(update))
    return "ok"

# -----------------------------
# 🔹 Старт сервиса
# -----------------------------
if __name__ == "__main__":
    import os

    async def main():
        await app_bot.initialize()
        await app_bot.start()
        print("🤖 Бот готов к работе!")

        # Flask запускается синхронно
        port = int(os.environ.get("PORT", 5000))
        flask_app.run(host="0.0.0.0", port=port)

    asyncio.run(main())