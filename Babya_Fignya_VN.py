#!/usr/bin/env python
# coding: utf-8

from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, filters
from datetime import datetime
import pytz

# -----------------------------
# 🔹 Настройки
# -----------------------------
TOKEN = "8301083124:AAGhbMXn6LuBpr2mT3tVWvw42dEcC2PYHyk"  # токен твоего бота
TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")  # часовой пояс
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
# 🔹 Обработчик сообщений
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
            await context.bot.send_message(
                chat_id=message.chat.id,
                text="Утреннее объявление ✅"
            )
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
            await context.bot.send_message(
                chat_id=message.chat.id,
                text="Вечернее объявление ✅"
            )
        else:
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f"{author.mention_html()}, Объявление удалено: вечернее объявление уже было сегодня.",
                parse_mode="HTML"
            )
            await message.delete()
        return

# -----------------------------
# 🔹 Настройка Flask + Telegram
# -----------------------------
bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# -----------------------------
# 🔹 Endpoint для webhook
# -----------------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Telegram будет присылать сюда обновления"""
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# -----------------------------
# 🔹 Старт сервиса
# -----------------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render назначает порт
    app.run(host="0.0.0.0", port=port)