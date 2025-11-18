from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    MessageHandler,
    filters,
    ChatMemberHandler,
    ContextTypes
)
from datetime import datetime
import pytz
import os
import threading
import asyncio

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
# 🔹 Инициализация Telegram Application
# -----------------------------
application = (
    ApplicationBuilder()
    .token(TOKEN)
    .concurrent_updates(True)
    .build()
)

# Handlers
application.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))
application.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_message))

# -----------------------------
# 🔹 Flask — Webhook
# -----------------------------
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    # Кладём обновление в очередь обработки
    application.update_queue.put_nowait(update)

    return "ok", 200


@flask_app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200


# -----------------------------
# 🔹 Запуск Telegram в фоне
# -----------------------------
def run_telegram():
    asyncio.run(application.initialize())
    asyncio.run(application.start())
    asyncio.get_event_loop().run_forever()


# -----------------------------
# 🔹 Главный блок запуска
# -----------------------------
if __name__ == "__main__":
    print("🚀 Стартуем...")

    # Запускаем Telegram Application в отдельном потоке
    threading.Thread(target=run_telegram, daemon=True).start()

    # Запускаем Flask на Render
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)