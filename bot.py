import asyncio
import sqlite3
import logging
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8637242832:AAEdBKu4R1XhyWHCO1VYxBvo67MapnWGk2k"
ADMIN_ID = 8314718448

CHANNEL_ID = -1003491649657
CHANNEL_LINK = "https://t.me/+9DI7onJBz0I1ZWQy"

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

def is_verified(uid):
    cursor.execute("SELECT verified FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0] == 1

def set_verified(uid):
    cursor.execute("UPDATE users SET verified=1 WHERE user_id=?", (uid,))
    conn.commit()

# ===== ПОДПИСКА =====
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return True

# ===== ТОВАРЫ (ВСЕ 12) =====
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

# ===== МЕНЮ =====
def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="catalog_0")],
        [InlineKeyboardButton(text="📦 Покупки", callback_data="my")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="refs")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="admin")]
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

    if ref and ref != message.from_user.id:
        add_balance(ref, 3)

    # проверка подписки
    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await message.answer("Подпишись на канал", reply_markup=kb)

    # капча
    if not is_verified(message.from_user.id):
        text, kb = generate_captcha(message.from_user.id)
        return await message.answer(text, reply_markup=kb)

    await message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())

# ===== ПРОВЕРКА ПОДПИСКИ =====
@dp.callback_query(F.data == "check_sub")
async def check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        text, kb = generate_captcha(call.from_user.id)
        await call.message.answer("✅ Подписка подтверждена")
        await call.message.answer(text, reply_markup=kb)
    else:
        await call.answer("❌ Подпишись", show_alert=True)

# ===== КАПЧА =====
@dp.callback_query(F.data.startswith("captcha_"))
async def captcha_check(call: types.CallbackQuery):
    uid = call.from_user.id
    answer = int(call.data.split("_")[1])

    if uid not in captcha_data:
        return

    if answer == captcha_data[uid]:
        set_verified(uid)
        del captcha_data[uid]

        await call.message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())
    else:
        await call.answer("❌ Неверно", show_alert=True)

# ===== КАТАЛОГ (С ПАГИНАЦИЕЙ) =====
@dp.callback_query(F.data.startswith("catalog"))
async def catalog(call):
    page = int(call.data.split("_")[1])
    items = list(PRODUCTS.items())

    start = page * 5
    end = start + 5

    kb = []
    for pid, p in items[start:end]:
        kb.append([InlineKeyboardButton(
            text=f"{p['name']} - {p['price']}⭐",
            callback_data=f"buy_{pid}"
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"catalog_{page-1}"))
    if end < len(items):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"catalog_{page+1}"))

    kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])

    await call.message.answer_photo(PHOTO_CATALOG, caption="🎬 Каталог", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ===== ПОКУПКА =====
@dp.callback_query(F.data.startswith("buy_"))
async def buy(call):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    if has_product(call.from_user.id, pid):
        return await call.answer("Уже куплено")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💰 Купить за {p['price']}⭐", callback_data=f"pay_{pid}")]
    ])

    await call.message.answer(f"{p['name']}\nЦена: {p['price']}⭐", reply_markup=kb)

# ===== ОПЛАТА =====
@dp.callback_query(F.data.startswith("pay_"))
async def pay(call):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    if get_balance(call.from_user.id) < p["price"]:
        return await call.answer("❌ Недостаточно средств")

    add_balance(call.from_user.id, -p["price"])
    buy_product(call.from_user.id, pid)

    await bot.send_video(call.from_user.id, p["video"])
    await call.message.answer("✅ Куплено", reply_markup=menu())

# ===== ОСТАЛЬНОЕ =====
@dp.callback_query(F.data == "balance")
async def balance(call):
    await call.message.answer(f"Баланс: {get_balance(call.from_user.id)}⭐", reply_markup=menu())

@dp.callback_query(F.data == "refs")
async def refs(call):
    uid = call.from_user.id
    cursor.execute("SELECT COUNT(*) FROM users WHERE referrer=?", (uid,))
    count = cursor.fetchone()[0]

    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    await call.message.answer(f"Рефералы: {count}\n{link}", reply_markup=menu())

@dp.callback_query(F.data == "my")
async def my(call):
    cursor.execute("SELECT product FROM purchases WHERE user_id=?", (call.from_user.id,))
    items = cursor.fetchall()

    text = "📦 Покупки:\n"
    for i in items:
        text += f"✔ {PRODUCTS[i[0]]['name']}\n"

    await call.message.answer(text, reply_markup=menu())

@dp.callback_query(F.data == "menu")
async def back(call):
    await call.message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())

# ===== АДМИН =====
@dp.callback_query(F.data == "admin")
async def admin(call):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌")

    await call.message.answer("⚙️ Админ панель")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
