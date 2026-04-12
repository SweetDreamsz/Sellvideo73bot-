import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice
from aiogram.filters import CommandStart

BOT_TOKEN = "8637242832:AAFTvqB1A2a7R0re_FGTSDMzrW3MkVAR53M"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 📀 БАЗА
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    purchased INTEGER DEFAULT 0
)
""")
conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def mark_purchased(user_id):
    cursor.execute("UPDATE users SET purchased=1 WHERE user_id=?", (user_id,))
    conn.commit()

def is_purchased(user_id):
    cursor.execute("SELECT purchased FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

# 🚀 СТАРТ
@dp.message(CommandStart())
async def start(message: types.Message):
    add_user(message.from_user.id)

    kb = [
        [types.KeyboardButton(text="Купить видео ⭐")],
        [types.KeyboardButton(text="Мои покупки 🎬")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer("Выбери действие 👇", reply_markup=keyboard)

# ⭐ КУПИТЬ
@dp.message(F.text == "Купить видео ⭐")
async def buy(message: types.Message):

    if is_purchased(message.from_user.id):
        await message.answer("Ты уже купил 👍")
        return

    prices = [LabeledPrice(label="Видео", amount=100)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Видео",
        description="Доступ",
        payload="video",
        provider_token="",
        currency="XTR",
        prices=prices
    )

# ✅ ПОДТВЕРЖДЕНИЕ
@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

# 💰 УСПЕШНАЯ ОПЛАТА
@dp.message(F.successful_payment)
async def success(message: types.Message):
    mark_purchased(message.from_user.id)

    await message.answer("Оплата прошла ✅")

    with open("video.mp4", "rb") as v:
        await message.answer_video(v)

# 🎬 МОИ ПОКУПКИ
@dp.message(F.text == "Мои покупки 🎬")
async def my_videos(message: types.Message):
    if is_purchased(message.from_user.id):
        with open("video.mp4", "rb") as v:
            await message.answer_video(v)
    else:
        await message.answer("Ты ничего не купил ❌")

# ▶️ ЗАПУСК
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())