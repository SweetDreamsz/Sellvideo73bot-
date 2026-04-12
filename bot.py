import asyncio
import sqlite3
import logging
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8637242832:AAEdBKu4R1XhyWHCO1VYxBvo67MapnWGk2k"
ADMIN_ID = 8314718448
BOT_USERNAME = "Sellvideo73bot"

PHOTO_CATALOG = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== БД =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    referrer INTEGER,
    verified INTEGER DEFAULT 0
)
""")

cursor.execute("CREATE TABLE IF NOT EXISTS purchases (user_id INTEGER, product TEXT)")
conn.commit()

# ===== КАПЧА =====
captcha_data = {}

def generate_captcha(uid):
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    correct = a + b

    options = [correct]
    while len(options) < 4:
        fake = random.randint(2, 20)
        if fake not in options:
            options.append(fake)

    random.shuffle(options)

    captcha_data[uid] = correct

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(opt), callback_data=f"captcha_{opt}") for opt in options]
    ])

    return f"🤖 Докажи что ты человек:\n{a} + {b} = ?", kb

# ===== ФУНКЦИИ =====
def add_user(uid, ref=None):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, referrer) VALUES (?, ?)", (uid, ref))
        conn.commit()

def is_verified(uid):
    cursor.execute("SELECT verified FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0] == 1

def set_verified(uid):
    cursor.execute("UPDATE users SET verified=1 WHERE user_id=?", (uid,))
    conn.commit()

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0]

def add_balance(uid, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def buy_product(uid, pid):
    cursor.execute("INSERT INTO purchases VALUES (?,?)", (uid, pid))
    conn.commit()

def has_product(uid, pid):
    cursor.execute("SELECT * FROM purchases WHERE user_id=? AND product=?", (uid, pid))
    return cursor.fetchone()

# ===== ТОВАРЫ =====
PRODUCTS = {
    "1": {"name": "Disable HumaNity Vol 3", "price": 50, "video": "BAACAgIAAxkBAANfaduMEvY26_NwECmM0-jptkIX66kAAu5eAAK8cwhJdoDZmlyZB8M7BA"},
    "2": {"name": "S.A.C necrophiliA", "price": 100, "video": "BAACAgIAAxkBAANiaduMPlKADAoCJyV5LccpZmCy-m4AAms-AAK-lchIyFwgUBEuzx07BA"},
}

# ===== МЕНЮ =====
def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="📦 Покупки", callback_data="my")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="refs")],
    ])

# ===== СТАРТ =====
@dp.message(F.text.startswith("/start"))
async def start(message: types.Message):
    args = message.text.split()

    ref = None
    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = None

    add_user(message.from_user.id, ref)

    # 💸 3⭐ за реферала
    if ref and ref != message.from_user.id:
        add_balance(ref, 3)

    # 🤖 КАПЧА
    if not is_verified(message.from_user.id):
        text, kb = generate_captcha(message.from_user.id)
        return await message.answer(text, reply_markup=kb)

    await message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())

# ===== КАПЧА ПРОВЕРКА =====
@dp.callback_query(F.data.startswith("captcha_"))
async def captcha_check(call: types.CallbackQuery):
    uid = call.from_user.id
    answer = int(call.data.split("_")[1])

    if uid not in captcha_data:
        return

    if answer == captcha_data[uid]:
        set_verified(uid)
        del captcha_data[uid]

        await call.message.edit_text("✅ Проверка пройдена!")
        await call.message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())
    else:
        await call.answer("❌ Неверно", show_alert=True)

# ===== КАТАЛОГ =====
@dp.callback_query(F.data == "catalog")
async def catalog(call):
    kb = []
    for pid, p in PRODUCTS.items():
        kb.append([InlineKeyboardButton(
            text=f"{p['name']} - {p['price']}⭐",
            callback_data=f"buy_{pid}"
        )])

    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])

    await call.message.answer("🎬 Каталог", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ===== ПОКУПКА =====
@dp.callback_query(F.data.startswith("buy_"))
async def buy(call):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    if has_product(call.from_user.id, pid):
        return await call.answer("Уже куплено")

    balance = get_balance(call.from_user.id)

    if balance < p["price"]:
        return await call.answer("❌ Недостаточно средств")

    add_balance(call.from_user.id, -p["price"])
    buy_product(call.from_user.id, pid)

    await bot.send_video(call.from_user.id, p["video"], protect_content=True)
    await call.message.answer("✅ Покупка успешна", reply_markup=menu())

# ===== БАЛАНС =====
@dp.callback_query(F.data == "balance")
async def balance(call):
    bal = get_balance(call.from_user.id)
    await call.message.answer(f"💰 Баланс: {bal}⭐", reply_markup=menu())

# ===== РЕФЕРАЛЫ =====
@dp.callback_query(F.data == "refs")
async def refs(call):
    uid = call.from_user.id

    cursor.execute("SELECT COUNT(*) FROM users WHERE referrer=?", (uid,))
    count = cursor.fetchone()[0]

    ref_link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    await call.message.answer(
        f"👥 Рефералы: {count}\n\n🔗 {ref_link}",
        reply_markup=menu()
    )

# ===== ПОКУПКИ =====
@dp.callback_query(F.data == "my")
async def my(call):
    cursor.execute("SELECT product FROM purchases WHERE user_id=?", (call.from_user.id,))
    items = cursor.fetchall()

    text = "📦 Покупки:\n"
    for i in items:
        text += f"✔ {PRODUCTS[i[0]]['name']}\n"

    await call.message.answer(text, reply_markup=menu())

# ===== НАЗАД В МЕНЮ =====
@dp.callback_query(F.data == "menu")
async def back(call):
    await call.message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
