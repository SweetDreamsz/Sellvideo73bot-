import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8637242832:AAEdBKu4R1XhyWHCO1VYxBvo67MapnWGk2k"
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

# ===== ТОВАРЫ (БЕЗ ФОТО) =====
PRODUCTS = {
    "1": {"name": "Disable HumaNity Vol 3", "price": 50, "video": "BAACAgIAAxkBAANfaduMEvY26_NwECmM0-jptkIX66kAAu5eAAK8cwhJdoDZmlyZB8M7BA"},
    "2": {"name": "S.A.C necrophiliA", "price": 100, "video": "BAACAgIAAxkBAANiaduMPlKADAoCJyV5LccpZmCy-m4AAms-AAK-lchIyFwgUBEuzx07BA"},
    "3": {"name": "The End Of HelL", "price": 45, "video": "BAACAgUAAxkBAANmaduMbyjGQ4cPphU85n0NOcPNJ60AArcMAAKu-JFVUD19QiuWxTo7BA"},
    "4": {"name": "The End of hell 2", "price": 45, "video": "BAACAgUAAxkBAANladuMb11VN-uGasCiGP6vt38vP4UAAp4MAAKu-JFVx6SiDaJaGqA7BA"},
    "5": {"name": "B0dy Farm", "price": 60, "video": "BAACAgEAAxkBAANraduMsU2NUtoGAhpIkJGw1cL-MPwAAokEAAIaKmBHM0F7wQoKeu87BA"},
    "6": {"name": "Smashed B0dles", "price": 55, "video": "BAACAgUAAxkBAANqaduMsTsl5Pi1Dadmx6QEJzEwk7gAAsgMAAJqushVfatS8S3wZYE7BA"},
    "7": {"name": "Death Day 3", "price": 70, "video": "BAACAgQAAxkBAANvaduM4m5Isr3wNh5m3ammTYlndT8AAk4VAAIM-xlRJWAqfikUixg7BA"},
    "8": {"name": "Death Day 5", "price": 75, "video": "BAACAgIAAxkBAANwaduM4iwlbzWNjsavL6oXmBiC03EAAjhZAAJu_glKmP3N9zjiDjs7BA"},
    "9": {"name": "Red jacket", "price": 100, "video": "BAACAgIAAxkBAAN0aduNExMrapqDLvNnlIK12nCAwKwAAmGWAAJx91lKv5ZmNxMimIY7BA"},
    "10": {"name": "Supremacy Mixtrape", "price": 80, "video": "BAACAgIAAxkBAAN3aduNNfepzoty7tb4FLAW5z3qGCAAApCOAAKgCzBJuVlq2HLhUv07BA"},
    "11": {"name": "PrinFul Vol 3", "price": 20, "video": "BAACAgIAAxkBAAN6aduNXt7hli2oJIUhviWQCH7zsjIAAiONAAKgCzBJoEy_zN75qMg7BA"},
    "12": {"name": "BlackSatanas 3", "price": 10, "video": "BAACAgIAAxkBAAN9aduNyhojJpyhmlSrOoft56nKt70AAv1kAAL177BIWZK9Ur0xY_47BA"},
}

# ===== КАТАЛОГ =====
CATALOG = list(PRODUCTS.items())
PER_PAGE = 5

# ===== СТАРТ =====
@dp.message(CommandStart())
async def start(message: types.Message):
    add_user(message.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог", callback_data="catalog_0")],
        [InlineKeyboardButton(text="📦 Мои покупки", callback_data="my")]
    ])

    await message.answer(
        "💜 Добро пожаловать в магазин\n\n🔥 Выбери товар",
        reply_markup=kb
    )

# ===== КАТАЛОГ =====
@dp.callback_query(F.data.startswith("catalog"))
async def catalog(call: types.CallbackQuery):
    page = int(call.data.split("_")[1])

    start = page * PER_PAGE
    end = start + PER_PAGE

    items = CATALOG[start:end]

    buttons = []

    for pid, p in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"{p['name']} • {p['price']}⭐",
                callback_data=f"product_{pid}"
            )
        ])

    nav = []

    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"catalog_{page-1}"))

    if end < len(CATALOG):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"catalog_{page+1}"))

    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog_0")])

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
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog_0")]
    ])

    await call.message.answer(
        f"🎬 {p['name']}\n\n💰 Цена: {p['price']}⭐",
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

# ===== УСПЕХ =====
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

# ===== FILE_ID =====
@dp.message()
async def get_file_id(message: types.Message):
    if message.video:
        await message.answer(f"FILE_ID:\n{message.video.file_id}")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())