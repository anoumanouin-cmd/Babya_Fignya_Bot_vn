#!/usr/bin/env python
# coding: utf-8

# In[1]:


import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ChatMemberHandler, ContextTypes
from datetime import datetime
import pytz
import nest_asyncio

nest_asyncio.apply()

TOKEN = "8301083124:AAGhbMXn6LuBpr2mT3tVWvw42dEcC2PYHyk"
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
announcement_posted = {}

# === Функция для определения периода дня ===
def get_time_period():
    now = datetime.now(VN_TZ).time()
    if now >= datetime.strptime("07:00", "%H:%M").time() and now < datetime.strptime("16:00", "%H:%M").time():
        return "morning"
    elif now >= datetime.strptime("16:00", "%H:%M").time() and now < datetime.strptime("23:59", "%H:%M").time():
        return "evening"
    else:
        return "night"

# --- Обработчик сообщений (новые и редактированные) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Берём редактированное сообщение, если есть, иначе новое
    message = getattr(update, "edited_message", None) or update.message
    if not message:
        return

    # Берём текст или подпись
    content = message.text or message.caption
    if not content:
        return

    text = content.lower()
    if "#объявление" not in text:
        return

    author = message.from_user  # автор сообщения
    period = get_time_period()
    today = datetime.now(VN_TZ).date().isoformat()
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

# === Приветствие новых участников ===
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not getattr(message, "new_chat_members", None):
        return
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        await context.bot.send_message(
            chat_id=message.chat.id,
            text=f"Привет, {member.first_name}! Приятного общения!"
        )

# === Инициализация приложения ===
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))

# --- Новые сообщения ---
app.add_handler(MessageHandler(
    (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
    handle_message
))

# --- Редактированные сообщения ---
app.add_handler(MessageHandler(
    filters.UpdateType.EDITED_MESSAGE,
    handle_message
))

# === Запуск бота через asyncio в Jupyter ===
async def start_bot():
    await app.initialize()
    await app.start()
    print("🤖 Бот запущен и следит за группой...")
    await app.updater.start_polling()  # polling работает в фоне

# Создаем задачу, чтобы loop Jupyter не блокировался
asyncio.create_task(start_bot())


# In[ ]:




