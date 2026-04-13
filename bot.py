import asyncio
import sqlite3
import logging
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

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

# ===== ДЕКОРАТОР =====
def cb_handler(func):
    async def wrapper(call: types.CallbackQuery, *args, **kwargs):
        try:
            await call.answer()
        except:
            pass
        return await func(call, *args, **kwargs)
    return wrapper

# ===== БД =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    sub_passed INTEGER DEFAULT 0
)
""")

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

    return f"🤖 {a} + {b} = ?", kb

# ===== ФУНКЦИИ =====
def add_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0]

def add_balance(uid, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def is_verified(uid):
    cursor.execute("SELECT verified FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0] == 1

def set_verified(uid):
    cursor.execute("UPDATE users SET verified=1 WHERE user_id=?", (uid,))
    conn.commit()

def is_sub_passed(uid):
    cursor.execute("SELECT sub_passed FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0] == 1

def set_sub_passed(uid):
    cursor.execute("UPDATE users SET sub_passed=1 WHERE user_id=?", (uid,))
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

# ===== МЕНЮ =====
def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="catalog_0")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")]
    ])

# ===== СТАРТ =====
@dp.message(F.text == "/start")
async def start(message: types.Message):
    add_user(message.from_user.id)

    if not is_sub_passed(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await message.answer("Подпишись на канал", reply_markup=kb)

    if not is_verified(message.from_user.id):
        text, kb = generate_captcha(message.from_user.id)
        return await message.answer(text, reply_markup=kb)

    await message.answer_photo(PHOTO_CATALOG, caption="💜 Меню", reply_markup=menu())

# ===== ПОДПИСКА =====
@dp.callback_query(F.data == "check_sub")
@cb_handler
async def check(call):
    set_sub_passed(call.from_user.id)
    text, kb = generate_captcha(call.from_user.id)
    await call.message.edit_text(text, reply_markup=kb)

# ===== КАПЧА =====
@dp.callback_query(F.data.startswith("captcha_"))
@cb_handler
async def captcha(call):
    if int(call.data.split("_")[1]) == captcha_data.get(call.from_user.id):
        set_verified(call.from_user.id)
        await call.message.answer_photo(PHOTO_CATALOG, caption="💜 Меню", reply_markup=menu())

# ===== БАЛАНС =====
@dp.callback_query(F.data == "balance")
@cb_handler
async def balance(call):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 10⭐", callback_data="topup_10")],
        [InlineKeyboardButton(text="💰 50⭐", callback_data="topup_50")],
        [InlineKeyboardButton(text="💰 100⭐", callback_data="topup_100")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="menu")]
    ])

    await call.message.edit_caption(
        caption=f"💰 Баланс: {get_balance(call.from_user.id)}⭐",
        reply_markup=kb
    )

# ===== ПОПОЛНЕНИЕ =====
@dp.callback_query(F.data.startswith("topup_"))
@cb_handler
async def topup(call):
    amount = int(call.data.split("_")[1])

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="Пополнение",
        description=f"{amount}⭐",
        payload=f"topup_{amount}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=amount)]
    )

# ===== ОПЛАТА =====
@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_q: types.PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload

    if payload.startswith("topup_"):
        amount = int(payload.split("_")[1])
        add_balance(message.from_user.id, amount)
        await message.answer(f"✅ Баланс пополнен на {amount}⭐")

# ===== ПОКУПКА =====
@dp.callback_query(F.data.startswith("buy_"))
@cb_handler
async def buy(call):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    if get_balance(call.from_user.id) < p["price"]:
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    add_balance(call.from_user.id, -p["price"])
    await bot.send_video(call.from_user.id, p["video"])
    await call.message.answer("✅ Куплено", reply_markup=menu())

# ===== КАТАЛОГ =====
@dp.callback_query(F.data.startswith("catalog"))
@cb_handler
async def catalog(call):
    kb = [[InlineKeyboardButton(text=f"{p['name']} - {p['price']}⭐", callback_data=f"buy_{pid}")]
          for pid, p in PRODUCTS.items()]

    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])

    await call.message.edit_caption(caption="🎬 Каталог", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ===== МЕНЮ =====
@dp.callback_query(F.data == "menu")
@cb_handler
async def menu_back(call):
    await call.message.edit_caption(caption="💜 Меню", reply_markup=menu())

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
