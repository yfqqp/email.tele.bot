import asyncio
import requests
from flask import Flask, request

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, WEBHOOK_PATH
from mail import create_email, get_messages, extract_code
from db import get_user, set_user

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = Flask(__name__)

# ================= USERS CACHE =================
users = {}

# ================= UI =================
def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📧 New Email", callback_data="new")],
        [InlineKeyboardButton(text="📥 Inbox", callback_data="inbox")]
    ])

# ================= START =================
@dp.message()
async def start(msg: types.Message):

    uid = msg.from_user.id

    user = get_user(uid)

    if not user:
        email = create_email()
        set_user(uid, email)
    else:
        email = user[0]

    users[uid] = email

    await msg.answer(
        f"📧 Temp Mail Bot\n\n{email}",
        reply_markup=menu()
    )

# ================= CALLBACKS =================
@dp.callback_query()
async def cb(call: types.CallbackQuery):

    uid = call.from_user.id

    user = get_user(uid)

    if not user:
        email = create_email()
        set_user(uid, email)
    else:
        email = user[0]

    users[uid] = email

    # ➕ New Email
    if call.data == "new":

        email = create_email()
        set_user(uid, email)
        users[uid] = email

        await call.message.edit_text(
            f"📧 New Email:\n\n{email}",
            reply_markup=menu()
        )

    # 📥 Inbox
    elif call.data == "inbox":

        messages = get_messages(email)

        text = f"📥 Inbox\n\n{email}\n\n"

        for m in messages[:6]:

            subject = m.get("subject", "No Subject")
            body = m.get("body_text") or m.get("body_html")

            code = extract_code(body)

            text += f"📩 {subject}\n"

            if code:
                text += f"🔑 OTP: {code}\n"

            text += "\n"

        await call.message.edit_text(text, reply_markup=menu())

# ================= WEBHOOK =================
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():

    update = types.Update(**request.json)

    asyncio.run(dp.feed_update(bot, update))

    return "ok"

# ================= HOME =================
@app.route("/")
def home():
    return "Bot is running"

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)