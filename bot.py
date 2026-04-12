import asyncio
import logging
import sqlite3
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789  # ВСТАВЬ СВОЙ ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== БАЗА =====
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

# ===== ФОТО =====
PHOTO_MENU = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo.jpg"
PHOTO_PRODUCT = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg"
VIDEO_FILE = "video.mp4"

# ===== СТАРТ =====
@dp.message(CommandStart())
async def start(message: types.Message):
    add_user(message.from_user.id)

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🛒 Купить")]
        ],
        resize_keyboard=True
    )

    await message.answer_photo(
        photo=PHOTO_MENU,
        caption="💜 Sweet Shop\n\n🎬 Доступ за 50⭐",
        reply_markup=kb
    )

# ===== ВЫБОР ТОВАРА =====
@dp.message(F.text == "🛒 Купить")
async def choose_product(message: types.Message):

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💰 Купить за 50⭐")],
            [types.KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

    await message.answer_photo(
        photo=PHOTO_PRODUCT,
        caption="🎬 Выбери товар",
        reply_markup=kb
    )

# ===== НАЗАД =====
@dp.message(F.text == "⬅️ Назад")
async def back(message: types.Message):
    await start(message)

# ===== ОПЛАТА =====
@dp.message(F.text == "💰 Купить за 50⭐")
async def buy(message: types.Message):

    prices = [types.LabeledPrice(label="Доступ", amount=50)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Доступ",
        description="Покупка контента",
        payload="buy",
        provider_token="",
        currency="XTR",
        prices=prices
    )

# ===== УСПЕШНАЯ ОПЛАТА =====
@dp.message(F.successful_payment)
async def success(message: types.Message):

    mark_purchased(message.from_user.id)

    await message.answer("✅ Оплата прошла!")

    await message.answer_video(
        video=types.FSInputFile(VIDEO_FILE),
        protect_content=True
    )

# ===== МОИ ПОКУПКИ =====
@dp.message(Command("my"))
async def my(message: types.Message):
    if not is_purchased(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await message.answer_video(
        video=types.FSInputFile(VIDEO_FILE),
        protect_content=True
    )

# ===== АДМИН =====
@dp.message(Command("stats"))
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users WHERE purchased=1")
    count = cursor.fetchone()[0]

    await message.answer(f"💰 Купили: {count}")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
