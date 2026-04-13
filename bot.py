import asyncio
import sqlite3
import logging

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

# ===== БД =====
conn = sqlite3.connect("db.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    donated INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    purchased TEXT DEFAULT '',
    ref INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")
cur.execute("CREATE TABLE IF NOT EXISTS banned(id INTEGER PRIMARY KEY)")
conn.commit()

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def add_user(uid, ref=None):
    if cur.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
        return
    cur.execute("INSERT INTO users(id, invited_by) VALUES(?,?)", (uid, ref))
    conn.commit()
    if ref and ref != uid:
        cur.execute("UPDATE users SET ref=ref+1 WHERE id=?", (ref,))
        conn.commit()

def get_field(uid, field):
    res = cur.execute(f"SELECT {field} FROM users WHERE id=?", (uid,)).fetchone()
    return res[0] if res else 0

def add_balance(uid, amount):
    cur.execute("UPDATE users SET balance = balance + ?, donated = donated + ? WHERE id = ?", (amount, amount if amount > 0 else 0, uid))
    conn.commit()

def add_purchase(uid, pid):
    current = get_field(uid, "purchased") or ""
    purchased_list = current.split(",")
    if pid not in purchased_list:
        new_val = current + pid + ","
        cur.execute("UPDATE users SET purchased = ? WHERE id=?", (new_val, uid))
        conn.commit()

async def check_sub(uid):
    if uid == ADMIN_ID: return True
    try:
        m = await bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ["creator", "administrator", "member"]
    except: return False

async def access_denied(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
    ])
    await call.answer("❌ Подпишитесь!")
    await call.message.answer("❌ Чтобы пользоваться ботом, подпишись на наш канал!", reply_markup=kb)

# ===== ТОВАРЫ =====
PRODUCTS = {
    "1": ("Disable HumaNity Vol 3", 50, "BAACAgIAAxkBAANfaduMEvY26_NwECmM0-jptkIX66kAAu5eAAK8cwhJdoDZmlyZB8M7BA"),
    "2": ("S.A.C necrophiliA", 100, "BAACAgIAAxkBAANiaduMPlKADAoCJyV5LccpZmCy-m4AAms-AAK-lchIyFwgUBEuzx07BA"),
    "3": ("The End Of HelL", 45, "BAACAgUAAxkBAANmaduMbyjGQ4cPphU85n0NOcPNJ60AArcMAAKu-JFVUD19QiuWxTo7BA"),
    "4": ("The End of hell 2", 45, "BAACAgUAAxkBAANladuMb11VN-uGasCiGP6vt38vP4UAAp4MAAKu-JFVx6SiDaJaGqA7BA"),
    "5": ("B0dy Farm", 60, "BAACAgEAAxkBAANraduMsU2NUtoGAhpIkJGw1cL-MPwAAokEAAIaKmBHM0F7wQoKeu87BA"),
    "6": ("Smashed B0dles", 55, "BAACAgUAAxkBAANqaduMsTsl5Pi1Dadmx6QEJzEwk7gAAsgMAAJqushVfatS8S3wZYE7BA"),
    "7": ("Death Day 3", 70, "BAACAgQAAxkBAANvaduM4m5Isr3wNh5m3ammTYlndT8AAk4VAAIM-xlRJWAqfikUixg7BA"),
    "8": ("Death Day 5", 75, "BAACAgIAAxkBAANwaduM4iwlbzWNjsavL6oXmBiC03EAAjhZAAJu_glKmP3N9zjiDjs7BA"),
    "9": ("Red jacket", 100, "BAACAgIAAxkBAAN0aduNExMrapqDLvNnlIK12nCAwKwAAmGWAAJx91lKv5ZmNxMimIY7BA"),
    "10": ("Supremacy Mixtrape", 80, "BAACAgIAAxkBAAN3aduNNfepzoty7tb4FLAW5z3qGCAAApCOAAKgCzBJuVlq2HLhUv07BA"),
    "11": ("PrinFul Vol 3", 20, "BAACAgIAAxkBAAN6aduNXt7hli2oJIUhviWQCH7zsjIAAiONAAKgCzBJoEy_zN75qMg7BA"),
    "12": ("BlackSatanas 3", 10, "BAACAgIAAxkBAAN9aduNyhojJpyhmlSrOoft56nKt70AAv1kAAL177BIWZK9Ur0xY_47BA")
}

# ===== КЛАВИАТУРЫ =====
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="cat_0")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="wallet")],
        [InlineKeyboardButton(text="📦 Покупки", callback_data="my_vids")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="prof")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="adm")]
    ])

# ===== ХЭНДЛЕРЫ =====
@dp.message(F.text.startswith("/start"))
async def start(m: types.Message):
    if cur.execute("SELECT 1 FROM banned WHERE id=?", (m.from_user.id,)).fetchone(): return
    ref = int(m.text.split()[1]) if len(m.text.split()) > 1 and m.text.split()[1].isdigit() else None
    add_user(m.from_user.id, ref)
    if not await check_sub(m.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)], [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]])
        return await m.answer("Добро пожаловать! Подпишитесь на канал.", reply_markup=kb)
    await m.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "check_sub")
async def check_btn(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.answer("✅ Доступ разрешен")
        await call.message.delete()
        await call.message.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_menu_kb())
    else: await call.answer("❌ Вы не подписаны", show_alert=True)

# КАТАЛОГ
@dp.callback_query(F.data.startswith("cat_"))
async def catalog(call: types.CallbackQuery):
    if not await check_sub(call.from_user.id): return await access_denied(call)
    await call.answer()
    page = int(call.data.split("_")[1])
    items = list(PRODUCTS.items())[page*5:(page+1)*5]
    kb = []
    for pid, (name, price, _) in items:
        kb.append([InlineKeyboardButton(text=f"{name} — {price}⭐", callback_data=f"prebuy_{pid}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"cat_{page-1}"))
    if (page+1)*5 < len(PRODUCTS): nav.append(InlineKeyboardButton(text="➡️", callback_data=f"cat_{page+1}"))
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")])
    await call.message.edit_caption(caption="🎬 Выберите товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ВЫБОР ОПЛАТЫ
@dp.callback_query(F.data.startswith("prebuy_"))
async def prebuy(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    name, price, _ = PRODUCTS[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Купить сразу ({price}⭐)", callback_data=f"pay_now_{pid}")],
        [InlineKeyboardButton(text=f"💎 С баланса ({price}⭐)", callback_data=f"pay_bal_{pid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cat_0")]
    ])
    await call.message.edit_caption(caption=f"🛒 Видео: {name}\n💰 Цена: {price}⭐\n\nВыберите способ оплаты:", reply_markup=kb)

# ОПЛАТА СРАЗУ (ИНВОЙС)
@dp.callback_query(F.data.startswith("pay_now_"))
async def pay_now(call: types.CallbackQuery):
    pid = call.data.split("_")[2]
    name, price, _ = PRODUCTS[pid]
    await bot.send_invoice(call.from_user.id, title=name, description="Прямая покупка видео", payload=f"item_{pid}", currency="XTR", prices=[LabeledPrice(label="Stars", amount=price)], provider_token="")

# ОПЛАТА С БАЛАНСА
@dp.callback_query(F.data.startswith("pay_bal_"))
async def pay_bal(call: types.CallbackQuery):
    pid = call.data.split("_")[2]
    uid = call.from_user.id
    name, price, video = PRODUCTS[pid]
    if get_field(uid, "balance") < price:
        return await call.answer("❌ Недостаточно звезд на балансе!", show_alert=True)
    
    add_balance(uid, -price)
    add_purchase(uid, pid)
    await call.answer("✅ Успешная покупка!")
    await call.message.answer(f"✅ Вы купили '{name}' с баланса!")
    await bot.send_video(uid, video, caption=f"🎬 {name}")

# БАЛАНС (ПОПОЛНЕНИЕ)
@dp.callback_query(F.data == "wallet")
async def wallet(call: types.CallbackQuery):
    bal = get_field(call.from_user.id, "balance")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="+50⭐", callback_data="topup_50"), InlineKeyboardButton(text="+100⭐", callback_data="topup_100")],
        [InlineKeyboardButton(text="+500⭐", callback_data="topup_500")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]
    ])
    await call.message.edit_caption(caption=f"💰 Ваш баланс: {bal}⭐\n\nВы можете пополнить баланс для будущих покупок:", reply_markup=kb)

@dp.callback_query(F.data.startswith("topup_"))
async def topup(call: types.CallbackQuery):
    amount = int(call.data.split("_")[1])
    await bot.send_invoice(call.from_user.id, title="Пополнение баланса", description=f"Покупка {amount} звезд для бота", payload=f"topup_{amount}", currency="XTR", prices=[LabeledPrice(label="Stars", amount=amount)], provider_token="")

# ОБРАБОТКА ВСЕХ ПЛАТЕЖЕЙ
@dp.pre_checkout_query()
async def pre_check(q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def success_pay(msg: types.Message):
    payload = msg.successful_payment.invoice_payload
    uid = msg.from_user.id
    
    if payload.startswith("item_"):
        pid = payload.split("_")[1]
        add_purchase(uid, pid)
        add_balance(uid, 0) # Просто обновим donated в статистике если нужно
        await msg.answer("✅ Оплата принята! Ваше видео:")
        await bot.send_video(uid, PRODUCTS[pid][2], caption=f"🎬 {PRODUCTS[pid][0]}")
        
    elif payload.startswith("topup_"):
        amount = int(payload.split("_")[1])
        add_balance(uid, amount)
        await msg.answer(f"✅ Баланс пополнен на {amount}⭐!")

# ПРОФИЛЬ И ПОКУПКИ
@dp.callback_query(F.data == "my_vids")
async def my_vids(call: types.CallbackQuery):
    purchased = (get_field(call.from_user.id, "purchased") or "").split(",")
    kb = []
    for pid, (name, _, _) in PRODUCTS.items():
        if pid in purchased and pid:
            kb.append([InlineKeyboardButton(text=f"📺 {name}", callback_data=f"getv_{pid}")])
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")])
    await call.message.edit_caption(caption="📦 Купленные товары:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("getv_"))
async def getv(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    await bot.send_video(call.from_user.id, PRODUCTS[pid][2], caption=f"🎬 {PRODUCTS[pid][0]}")

@dp.callback_query(F.data == "prof")
async def prof(call: types.CallbackQuery):
    uid = call.from_user.id
    text = f"👤 Профиль\n🆔 ID: {uid}\n💰 Баланс: {get_field(uid,'balance')}⭐\n💎 Всего задоначено: {get_field(uid,'donated')}⭐"
    await call.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]]))

@dp.callback_query(F.data == "to_menu")
async def to_menu(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_caption(caption="💜 Главное меню", reply_markup=main_menu_kb())

# ===== АДМИН ПАНЕЛЬ =====
@dp.callback_query(F.data == "adm")
async def adm_panel(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Всем +100⭐", callback_data="give_all_100")],
        [InlineKeyboardButton(text="🎁 Всем +500⭐", callback_data="give_all_500")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]
    ])
    await call.message.edit_caption(caption="⚙️ Админка\n\nКоманды в чат:\n/give [id] [кол-во] — выдать звезды\n/ban [id] — бан\n/unban [id] — разбан", reply_markup=kb)

@dp.callback_query(F.data.startswith("give_all_"))
async def give_all(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    amount = int(call.data.split("_")[2])
    cur.execute("UPDATE users SET balance = balance + ?", (amount,))
    conn.commit()
    await call.answer(f"✅ Выдано по {amount}⭐ всем пользователям!", show_alert=True)

@dp.message(F.text.startswith("/give"))
async def adm_give(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, uid, amount = m.text.split()
        add_balance(int(uid), int(amount))
        await m.answer(f"✅ Выдано {amount}⭐ пользователю {uid}")
    except: await m.answer("Ошибка. Формат: /give 12345 500")

@dp.message(F.text.startswith("/ban"))
async def adm_ban(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    uid = m.text.split()[1]
    cur.execute("INSERT OR IGNORE INTO banned VALUES(?)", (uid,))
    conn.commit()
    await m.answer("Забанен")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

