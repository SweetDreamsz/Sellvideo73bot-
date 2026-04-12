import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "ВСТАВЬ_СЮДА_ТОКЕН"
ADMIN_ID = 8314718448

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== БАЗА =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    purchased TEXT DEFAULT ''
)
""")
conn.commit()

def add_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def add_purchase(uid, pid):
    cursor.execute("SELECT purchased FROM users WHERE user_id=?", (uid,))
    res = cursor.fetchone()
    current = res[0] if res else ""
    cursor.execute("UPDATE users SET purchased=? WHERE user_id=?", (current + pid + ",", uid))
    conn.commit()

def has_product(uid, pid):
    cursor.execute("SELECT purchased FROM users WHERE user_id=?", (uid,))
    res = cursor.fetchone()
    return res and pid in (res[0] or "")

# ===== ТОВАРЫ (ВСТАВЬ СВОИ FILE_ID) =====
PRODUCTS = {
    "1": {
        "name": "🔥 Видео 1",
        "price": 50,
        "photo": "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg",
        "video": "PASTE_FILE_ID_1"
    },
    "2": {
        "name": "💜 Видео 2",
        "price": 75,
        "photo": "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg",
        "video": "PASTE_FILE_ID_2"
    }
}

PHOTO_MENU = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo.jpg"

# ===== СТАРТ =====
@dp.message(CommandStart())
async def start(message: types.Message):
    add_user(message.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="📦 Мои покупки", callback_data="my")]
    ])

    await message.answer_photo(
        photo=PHOTO_MENU,
        caption="💜 Добро пожаловать в магазин\n\n🔥 Выбери товар",
        reply_markup=kb
    )

# ===== КАТАЛОГ =====
@dp.callback_query(F.data == "catalog")
async def catalog(call: types.CallbackQuery):

    buttons = []
    for pid, p in PRODUCTS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{p['name']} • {p['price']}⭐",
                callback_data=f"product_{pid}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    await call.message.answer(
        "📦 Каталог товаров:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ===== ТОВАР =====
@dp.callback_query(F.data.startswith("product_"))
async def product(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💰 Купить за {p['price']}⭐", callback_data=f"buy_{pid}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")]
    ])

    await call.message.answer_photo(
        photo=p["photo"],
        caption=f"{p['name']}\n💰 Цена: {p['price']}⭐",
        reply_markup=kb
    )

# ===== ПОКУПКА =====
@dp.callback_query(F.data.startswith("buy_"))
async def buy(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    prices = [types.LabeledPrice(label=p["name"], amount=p["price"])]

    await bot.send_invoice(
        chat_id=call.message.chat.id,
        title=p["name"],
        description="Покупка доступа",
        payload=pid,
        provider_token="",
        currency="XTR",
        prices=prices
    )

# ===== ПРОВЕРКА =====
@dp.pre_checkout_query()
async def checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

# ===== УСПЕШНАЯ ОПЛАТА =====
@dp.message(F.successful_payment)
async def success(message: types.Message):
    pid = message.successful_payment.invoice_payload

    add_purchase(message.from_user.id, pid)

    await message.answer("✅ Оплата прошла!")

    await message.answer_video(
        video=PRODUCTS[pid]["video"],
        protect_content=True
    )

# ===== МОИ ПОКУПКИ =====
@dp.callback_query(F.data == "my")
async def my(call: types.CallbackQuery):
    uid = call.from_user.id

    found = False

    for pid, p in PRODUCTS.items():
        if has_product(uid, pid):
            await call.message.answer_video(
                video=p["video"],
                protect_content=True
            )
            found = True

    if not found:
        await call.message.answer("❌ У тебя нет покупок")

# ===== ПОЛУЧЕНИЕ FILE_ID (временно включи) =====
@dp.message()
async def get_file_id(message: types.Message):
    if message.video:
        await message.answer(f"FILE_ID:\n{message.video.file_id}")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
