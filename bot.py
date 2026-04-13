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
donated INTEGER DEFAULT 0,
verified INTEGER DEFAULT 0,
sub INTEGER DEFAULT 0,
purchased TEXT DEFAULT '',
ref INTEGER DEFAULT 0,
invited_by INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS banned(
id INTEGER PRIMARY KEY
)
""")

conn.commit()

# ===== ФУНКЦИИ =====
def add_user(uid, ref=None):
    if cur.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
        return

    cur.execute("INSERT INTO users(id, invited_by) VALUES(?,?)", (uid, ref))
    conn.commit()

    if ref and ref != uid:
        cur.execute("UPDATE users SET ref=ref+1, balance=balance+3 WHERE id=?", (ref,))
        conn.commit()

def get(uid, field):
    return cur.execute(f"SELECT {field} FROM users WHERE id=?", (uid,)).fetchone()[0]

def add_balance(uid, x):
    cur.execute("UPDATE users SET balance=balance+?, donated=donated+? WHERE id=?", (x, max(x,0), uid))
    conn.commit()

def add_purchase(uid, pid):
    cur.execute("UPDATE users SET purchased = purchased || ? WHERE id=?", (pid+",", uid))
    conn.commit()

def has_product(uid, pid):
    return pid in (get(uid, "purchased") or "")

def is_banned(uid):
    return cur.execute("SELECT 1 FROM banned WHERE id=?", (uid,)).fetchone()

def ban(uid):
    cur.execute("INSERT OR IGNORE INTO banned VALUES(?)", (uid,))
    conn.commit()

def unban(uid):
    cur.execute("DELETE FROM banned WHERE id=?", (uid,))
    conn.commit()

# ===== ПОДПИСКА =====
async def check_sub(uid):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, uid)
        return member.status in ["creator","administrator","member"]
    except:
        return False

# ===== КАПЧА =====
captcha = {}

def gen(uid):
    a,b = random.randint(1,9),random.randint(1,9)
    ans = a+b
    captcha[uid]=ans

    opts=[ans]
    while len(opts)<4:
        x=random.randint(2,20)
        if x not in opts:
            opts.append(x)
    random.shuffle(opts)

    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i),callback_data=f"cap_{i}") for i in opts]
    ])
    return f"{a}+{b}=?",kb

# ===== ТОВАРЫ =====
PRODUCTS = {str(i+1):p for i,p in enumerate([
("Disable HumaNity Vol 3",50,"BAACAgIAAxkBAANfaduMEvY26_NwECmM0-jptkIX66kAAu5eAAK8cwhJdoDZmlyZB8M7BA"),
("S.A.C necrophiliA",100,"BAACAgIAAxkBAANiaduMPlKADAoCJyV5LccpZmCy-m4AAms-AAK-lchIyFwgUBEuzx07BA"),
("The End Of HelL",45,"BAACAgUAAxkBAANmaduMbyjGQ4cPphU85n0NOcPNJ60AArcMAAKu-JFVUD19QiuWxTo7BA"),
("The End of hell 2",45,"BAACAgUAAxkBAANladuMb11VN-uGasCiGP6vt38vP4UAAp4MAAKu-JFVx6SiDaJaGqA7BA"),
("B0dy Farm",60,"BAACAgEAAxkBAANraduMsU2NUtoGAhpIkJGw1cL-MPwAAokEAAIaKmBHM0F7wQoKeu87BA"),
("Smashed B0dles",55,"BAACAgUAAxkBAANqaduMsTsl5Pi1Dadmx6QEJzEwk7gAAsgMAAJqushVfatS8S3wZYE7BA"),
("Death Day 3",70,"BAACAgQAAxkBAANvaduM4m5Isr3wNh5m3ammTYlndT8AAk4VAAIM-xlRJWAqfikUixg7BA"),
("Death Day 5",75,"BAACAgIAAxkBAANwaduM4iwlbzWNjsavL6oXmBiC03EAAjhZAAJu_glKmP3N9zjiDjs7BA"),
("Red jacket",100,"BAACAgIAAxkBAAN0aduNExMrapqDLvNnlIK12nCAwKwAAmGWAAJx91lKv5ZmNxMimIY7BA"),
("Supremacy Mixtrape",80,"BAACAgIAAxkBAAN3aduNNfepzoty7tb4FLAW5z3qGCAAApCOAAKgCzBJuVlq2HLhUv07BA"),
("PrinFul Vol 3",20,"BAACAgIAAxkBAAN6aduNXt7hli2oJIUhviWQCH7zsjIAAiONAAKgCzBJoEy_zN75qMg7BA"),
("BlackSatanas 3",10,"BAACAgIAAxkBAAN9aduNyhojJpyhmlSrOoft56nKt70AAv1kAAL177BIWZK9Ur0xY_47BA")
])}

# ===== МЕНЮ =====
def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог",callback_data="catalog_0")],
        [InlineKeyboardButton(text="💰 Баланс",callback_data="bal")],
        [InlineKeyboardButton(text="👥 Рефералы",callback_data="refs")],
        [InlineKeyboardButton(text="📦 Покупки",callback_data="my")],
        [InlineKeyboardButton(text="👤 Профиль",callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Админ",callback_data="admin")]
    ])

# ===== СТАРТ =====
@dp.message(F.text.startswith("/start"))
async def start(m: types.Message):
    if is_banned(m.from_user.id):
        return await m.answer("🚫 Забанен")

    args=m.text.split()
    ref=int(args[1]) if len(args)>1 and args[1].isdigit() else None

    add_user(m.from_user.id,ref)

    if not await check_sub(m.from_user.id):
        kb=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться",url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="Проверить",callback_data="check")]
        ])
        return await m.answer("Подпишись",reply_markup=kb)

    if not get(m.from_user.id,"verified"):
        t,kb=gen(m.from_user.id)
        return await m.answer(t,reply_markup=kb)

    await m.answer_photo(PHOTO,caption="Меню",reply_markup=menu())

# ===== ПРОВЕРКА =====
@dp.callback_query(F.data=="check")
@cb
async def check(call):
    if not await check_sub(call.from_user.id):
        return await call.answer("Не подписан",show_alert=True)

    cur.execute("UPDATE users SET sub=1 WHERE id=?", (call.from_user.id,))
    conn.commit()

    t,kb=gen(call.from_user.id)
    await call.message.answer(t,reply_markup=kb)

# ===== КАПЧА =====
@dp.callback_query(F.data.startswith("cap_"))
@cb
async def cap(call):
    ans=int(call.data.split("_")[1])
    if ans==captcha.get(call.from_user.id):
        cur.execute("UPDATE users SET verified=1 WHERE id=?", (call.from_user.id,))
        conn.commit()
        await call.message.answer_photo(PHOTO,caption="Меню",reply_markup=menu())
    else:
        await call.answer("Ошибка",show_alert=True)

# ===== КАТАЛОГ =====
@dp.callback_query(F.data.startswith("catalog"))
@cb
async def catalog(call):
    page=int(call.data.split("_")[1])
    items=list(PRODUCTS.items())[page*5:(page+1)*5]

    kb=[[InlineKeyboardButton(text=f"{p[0]} {p[1]}⭐",callback_data=f"buy_{pid}")]
        for pid,(p[0],p[1],_) in PRODUCTS.items()]

    kb=[]
    for pid,p in items:
        kb.append([InlineKeyboardButton(text=f"{p[0]} {p[1]}⭐",callback_data=f"buy_{pid}")])

    nav=[]
    if page>0:
        nav.append(InlineKeyboardButton(text="⬅️",callback_data=f"catalog_{page-1}"))
    if (page+1)*5<len(PRODUCTS):
        nav.append(InlineKeyboardButton(text="➡️",callback_data=f"catalog_{page+1}"))
    if nav:
        kb.append(nav)

    kb.append([InlineKeyboardButton(text="Меню",callback_data="menu")])

    await call.message.answer_photo(PHOTO,caption="Каталог",reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ===== ПОКУПКА =====
@dp.callback_query(F.data.startswith("buy_"))
@cb
async def buy(call):
    pid=call.data.split("_")[1]
    uid=call.from_user.id
    name,price,vid=PRODUCTS[pid]

    if get(uid,"balance")<price:
        return await call.answer("Нет денег",show_alert=True)

    add_balance(uid,-price)
    add_purchase(uid,pid)

    await bot.send_video(uid,vid)

# ===== БАЛАНС =====
@dp.callback_query(F.data=="bal")
@cb
async def bal(call):
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{x}⭐",callback_data=f"add_{x}") for x in [10,30,50]],
        [InlineKeyboardButton(text=f"{x}⭐",callback_data=f"add_{x}") for x in [70,100]]
    ])
    await call.message.answer(f"Баланс: {get(call.from_user.id,'balance')}⭐",reply_markup=kb)

@dp.callback_query(F.data.startswith("add_"))
@cb
async def add(call):
    x=int(call.data.split("_")[1])
    add_balance(call.from_user.id,x)
    await call.message.answer(f"+{x}⭐")

# ===== РЕФЫ =====
@dp.callback_query(F.data=="refs")
@cb
async def refs(call):
    link=f"https://t.me/{(await bot.get_me()).username}?start={call.from_user.id}"
    await call.message.answer(f"Рефералы: {get(call.from_user.id,'ref')}\n{link}")

# ===== ПОКУПКИ =====
@dp.callback_query(F.data=="my")
@cb
async def my(call):
    uid=call.from_user.id
    kb=[]
    for pid,(n,_,_) in PRODUCTS.items():
        if has_product(uid,pid):
            kb.append([InlineKeyboardButton(text=n,callback_data=f"vid_{pid}")])

    await call.message.answer("Покупки",reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("vid_"))
@cb
async def vid(call):
    pid=call.data.split("_")[1]
    await bot.send_video(call.from_user.id,PRODUCTS[pid][2])

# ===== ПРОФИЛЬ =====
@dp.callback_query(F.data=="profile")
@cb
async def profile(call):
    uid=call.from_user.id
    await call.message.answer(
        f"ID: {uid}\n"
        f"Username: @{call.from_user.username}\n"
        f"Рефералы: {get(uid,'ref')}\n"
        f"Донат: {get(uid,'donated')}⭐\n"
        f"Куплено: {len((get(uid,'purchased') or '').split(','))-1}"
    )

# ===== АДМИН =====
@dp.callback_query(F.data=="admin")
@cb
async def admin(call):
    if call.from_user.id!=ADMIN_ID:
        return
    await call.message.answer("Команды:\n/ban id\n/unban id\n/give id amount")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

asyncio.run(main())
