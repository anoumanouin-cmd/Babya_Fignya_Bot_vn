from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ChatMemberHandler,
    ContextTypes
)
from datetime import datetime
import pytz
import os
import asyncio
from threading import Thread

# -----------------------------
# 🔹 Настройки
# -----------------------------
TOKEN = os.environ.get("BOT_TOKEN", "8301083124:AAGhbMXn6LuBpr2mT3tVWvw42dEcC2PYHyk")
TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")
announcement_posted = {}

# -----------------------------
# 🔹 Определение времени суток
# -----------------------------
def get_time_period():
    now = datetime.now(TIMEZONE).time()
    if datetime.strptime("07:00", "%H:%M").time() <= now < datetime.strptime("16:00", "%H:%M").time():
        return "morning"
    elif datetime.strptime("16:00", "%H:%M").time() <= now <= datetime.strptime("23:59", "%H:%M").time():
        return "evening"
    return "night"

# -----------------------------
# 🔹 Обработчик объявлений
# -----------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = getattr(update, "edited_message", None) or update.message
    if not message:
        return

    content = message.text or message.caption
    if not content or "#объявление" not in content.lower():
        return

    author = message.from_user
    period = get_time_period()
    today = datetime.now(TIMEZONE).date().isoformat()

    if today not in announcement_posted:
        announcement_posted[today] = {"morning": False, "evening": False}

    if period == "night":
        await context.bot.send_message(
            chat_id=message.chat.id,
            text=f"{author.mention_html()}, Объявление удалено. Перезалейте с 07:00 до 16:00",
            parse_mode="HTML"
        )
        await message.delete()
        return

    if period == "morning":
        if not announcement_posted[today]["morning"]:
            announcement_posted[today]["morning"] = True
            await context.bot.send_message(chat_id=message.chat.id, text="Утреннее объявление ✅")
        else:
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f"{author.mention_html()}, Утреннее объявление уже было сегодня.",
                parse_mode="HTML"
            )
            await message.delete()
        return

    if period == "evening":
        if not announcement_posted[today]["evening"]:
            announcement_posted[today]["evening"] = True
            await context.bot.send_message(chat_id=message.chat.id, text="Вечернее объявление ✅")
        else:
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f"{author.mention_html()}, Вечернее объявление уже было сегодня.",
                parse_mode="HTML"
            )
            await message.delete()
        return

# -----------------------------
# 🔹 Приветствие новых участников
# -----------------------------
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.new_chat_members:
        return

    for member in msg.new_chat_members:
        if not member.is_bot:
            await context.bot.send_message(
                chat_id=msg.chat.id,
                text=f"Привет, {member.first_name}! Ознакомьтесь с правилами в закрепе! Приятного общения ❤️"
            )

# -----------------------------
# 🔹 Инициализация бота
# -----------------------------
app_bot = ApplicationBuilder().token(TOKEN).build()

app_bot.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))
app_bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))
app_bot.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, handle_message))
app_bot.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_message))

# -----------------------------
# 🔹 Flask — Webhook
# -----------------------------
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print(">>> Update received")

    update = Update.de_json(data, app_bot.bot)
    asyncio.run_coroutine_threadsafe(app_bot.process_update(update), app_bot._loop)

    return "ok", 200

# -----------------------------
# 🔹 Запуск: бот в отдельном потоке, Flask — в главном
# -----------------------------
def start_bot():
    asyncio.set_event_loop(app_bot.loop)
    app_bot.run_polling(stop_signals=None)

if __name__ == "__main__":
    print("🚀 Стартуем...")

    bot_thread = Thread(target=start_bot, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)