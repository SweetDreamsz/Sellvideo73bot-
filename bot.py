import asyncio
import sqlite3
import logging
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8637242832:AAEdBKu4R1XhyWHCO1VYxBvo67MapnWGk2k"
ADMIN_ID = 8314718448

CHANNEL_ID = -1003491649657
CHANNEL_LINK = "https://t.me/+9DI7onJBz0I1ZWQy"

PHOTO_CATALOG = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== БД =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, purchased TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)")
conn.commit()

# ===== ФУНКЦИИ =====
def add_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, purchased) VALUES (?, '')", (uid,))
    conn.commit()

def add_purchase(uid, pid):
    cursor.execute("UPDATE users SET purchased = purchased || ? WHERE user_id=?", (pid+",", uid))
    conn.commit()

def has_product(uid, pid):
    cursor.execute("SELECT purchased FROM users WHERE user_id=?", (uid,))
    res = cursor.fetchone()
    return res and pid in (res[0] or "")

def is_banned(uid):
    cursor.execute("SELECT user_id FROM banned WHERE user_id=?", (uid,))
    return cursor.fetchone() is not None

def ban(uid):
    cursor.execute("INSERT OR IGNORE INTO banned VALUES (?)", (uid,))
    conn.commit()

# ===== ТОВАРЫ =====
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

# ===== ПРОВЕРКА ПОДПИСКИ =====
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return True  # если ошибка (приват канал) — пропускаем

# ===== МЕНЮ =====
def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💜 Купить", callback_data="buy")],
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="catalog_0")],
        [InlineKeyboardButton(text="📦 Мои покупки", callback_data="my")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="admin")]
    ])

# ===== СТАРТ =====
@dp.message(F.text == "/start")
async def start(message: types.Message):
    if is_banned(message.from_user.id):
        return await message.answer("🚫 Ты забанен")

    add_user(message.from_user.id)

    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await message.answer("Подпишись на канал", reply_markup=kb)

    await message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())

# ===== ПРОВЕРКА =====
@dp.callback_query(F.data == "check_sub")
async def check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.answer("✅ Доступ открыт", reply_markup=menu())
    else:
        await call.answer("❌ Подпишись", show_alert=True)

# ===== КАТАЛОГ =====
@dp.callback_query(F.data.startswith("catalog"))
async def catalog(call: types.CallbackQuery):
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
async def buy(call: types.CallbackQuery):
    pid = call.data.split("_")[1]

    if has_product(call.from_user.id, pid):
        return await call.answer("Уже куплено")

    p = PRODUCTS[pid]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💰 Купить за {p['price']}⭐", callback_data=f"pay_{pid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog_0")]
    ])

    await call.message.answer(f"{p['name']}\nЦена: {p['price']}⭐", reply_markup=kb)

# ===== ОПЛАТА =====
@dp.callback_query(F.data.startswith("pay_"))
async def pay(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    add_purchase(call.from_user.id, pid)

    await bot.send_video(call.from_user.id, p["video"])
    await call.message.answer("✅ Куплено", reply_markup=menu())

# ===== МОИ ПОКУПКИ =====
@dp.callback_query(F.data == "my")
async def my(call):
    text = "📦 Покупки:\n"
    for pid, p in PRODUCTS.items():
        if has_product(call.from_user.id, pid):
            text += f"✔ {p['name']}\n"

    await call.message.answer(text, reply_markup=menu())

# ===== ПРОФИЛЬ =====
@dp.callback_query(F.data == "profile")
async def profile(call):
    await call.message.answer(f"👤 ID: {call.from_user.id}", reply_markup=menu())

# ===== АДМИН =====
@dp.callback_query(F.data == "admin")
async def admin(call):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Бан", callback_data="ban")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="send")]
    ])

    await call.message.answer("⚙️ Админка", reply_markup=kb)

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())