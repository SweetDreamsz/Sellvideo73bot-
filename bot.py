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

PHOTO = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== ДЕКОРАТОР =====
def cb(func):
    async def wrapper(call: types.CallbackQuery):
        try:
            await call.answer()
        except:
            pass
        return await func(call)
    return wrapper

# ===== БД =====
conn = sqlite3.connect("db.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
balance INTEGER DEFAULT 0,
verified INTEGER DEFAULT 0,
sub INTEGER DEFAULT 0,
purchased TEXT DEFAULT '',
ref INTEGER DEFAULT 0,
invited_by INTEGER
)
""")
conn.commit()

# ===== ФУНКЦИИ =====
def add_user(uid, ref=None):
    cur.execute("SELECT id FROM users WHERE id=?", (uid,))
    if cur.fetchone():
        return

    cur.execute("INSERT INTO users(id, invited_by) VALUES(?,?)", (uid, ref))
    conn.commit()

    if ref and ref != uid:
        cur.execute("UPDATE users SET ref=ref+1, balance=balance+3 WHERE id=?", (ref,))
        conn.commit()

def get_refs(uid):
    return cur.execute("SELECT ref FROM users WHERE id=?", (uid,)).fetchone()[0]

def get_balance(uid):
    return cur.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()[0]

def add_balance(uid, x):
    cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (x, uid))
    conn.commit()

def set_sub(uid):
    cur.execute("UPDATE users SET sub=1 WHERE id=?", (uid,))
    conn.commit()

def is_sub(uid):
    return cur.execute("SELECT sub FROM users WHERE id=?", (uid,)).fetchone()[0]

def set_ver(uid):
    cur.execute("UPDATE users SET verified=1 WHERE id=?", (uid,))
    conn.commit()

def is_ver(uid):
    return cur.execute("SELECT verified FROM users WHERE id=?", (uid,)).fetchone()[0]

def add_purchase(uid, pid):
    cur.execute("UPDATE users SET purchased = purchased || ? WHERE id=?", (pid+",", uid))
    conn.commit()

def has_product(uid, pid):
    res = cur.execute("SELECT purchased FROM users WHERE id=?", (uid,)).fetchone()
    return res and pid in (res[0] or "")

# ===== ПРОВЕРКА ПОДПИСКИ =====
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

# ===== КАПЧА =====
captcha = {}

def gen(uid):
    a, b = random.randint(1,9), random.randint(1,9)
    ans = a+b
    captcha[uid] = ans

    opts = [ans]
    while len(opts) < 4:
        x = random.randint(2,20)
        if x not in opts:
            opts.append(x)

    random.shuffle(opts)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"cap_{i}") for i in opts]
    ])

    return f"🤖 {a}+{b}=?", kb

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
        [InlineKeyboardButton(text="💰 Баланс", callback_data="bal")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="refs")],
        [InlineKeyboardButton(text="📦 Мои покупки", callback_data="my")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="admin")]
    ])

# ===== СТАРТ =====
@dp.message(F.text.startswith("/start"))
async def start(m: types.Message):
    args = m.text.split()
    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    add_user(m.from_user.id, ref)

    if not is_sub(m.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check")]
        ])
        return await m.answer("Подпишись на канал", reply_markup=kb)

    if not is_ver(m.from_user.id):
        t, kb = gen(m.from_user.id)
        return await m.answer(t, reply_markup=kb)

    await m.answer_photo(PHOTO, caption="💜 Меню", reply_markup=menu())

# ===== ПРОВЕРКА =====
@dp.callback_query(F.data == "check")
@cb
async def check(call):
    uid = call.from_user.id

    if not await check_sub(uid):
        return await call.answer("❌ Ты не подписан", show_alert=True)

    set_sub(uid)

    t, kb = gen(uid)

    await call.message.delete()
    await call.message.answer("✅ Подписка подтверждена")
    await call.message.answer(t, reply_markup=kb)

# ===== КАПЧА =====
@dp.callback_query(F.data.startswith("cap_"))
@cb
async def cap(call):
    uid = call.from_user.id
    ans = int(call.data.split("_")[1])

    if ans == captcha.get(uid):
        set_ver(uid)
        await call.message.answer_photo(PHOTO, caption="💜 Меню", reply_markup=menu())
    else:
        await call.answer("❌ Неверно", show_alert=True)

# ===== КАТАЛОГ =====
@dp.callback_query(F.data.startswith("catalog"))
@cb
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

    if nav:
        kb.append(nav)

    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])

    await call.message.answer_photo(PHOTO, caption="🎬 Каталог", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ===== ПОКУПКА =====
@dp.callback_query(F.data.startswith("buy_"))
@cb
async def buy(call):
    uid = call.from_user.id
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]

    if has_product(uid, pid):
        return await call.answer("Уже куплено", show_alert=True)

    if get_balance(uid) < p["price"]:
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    add_balance(uid, -p["price"])
    add_purchase(uid, pid)

    await bot.send_video(uid, p["video"])
    await call.message.answer("✅ Куплено", reply_markup=menu())

# ===== РЕФЕРАЛЫ =====
@dp.callback_query(F.data == "refs")
@cb
async def refs(call):
    link = f"https://t.me/{(await bot.get_me()).username}?start={call.from_user.id}"
    await call.message.answer(
        f"👥 Рефералы: {get_refs(call.from_user.id)}\n⭐ +3⭐ за каждого\n\n🔗 {link}",
        reply_markup=menu()
    )

# ===== МОИ ПОКУПКИ =====
@dp.callback_query(F.data == "my")
@cb
async def my(call):
    uid = call.from_user.id
    text = "📦 Покупки:\n"

    for pid, p in PRODUCTS.items():
        if has_product(uid, pid):
            text += f"✔ {p['name']}\n"

    await call.message.answer(text, reply_markup=menu())

# ===== ПРОФИЛЬ =====
@dp.callback_query(F.data == "profile")
@cb
async def profile(call):
    await call.message.answer(f"👤 ID: {call.from_user.id}", reply_markup=menu())

# ===== АДМИН =====
@dp.callback_query(F.data == "admin")
@cb
async def admin(call):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Нет доступа", show_alert=True)

    await call.message.answer("⚙️ Админ панель")

# ===== БАЛАНС =====
@dp.callback_query(F.data == "bal")
@cb
async def bal(call):
    await call.message.answer_photo(
        PHOTO,
        caption=f"Баланс: {get_balance(call.from_user.id)}⭐",
        reply_markup=menu()
    )

# ===== МЕНЮ =====
@dp.callback_query(F.data == "menu")
@cb
async def back(call):
    await call.message.answer_photo(PHOTO, caption="💜 Меню", reply_markup=menu())

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

asyncio.run(main())
