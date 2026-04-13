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

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect("db.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    donated INTEGER DEFAULT 0,
    purchased TEXT DEFAULT '',
    ref INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")
cur.execute("CREATE TABLE IF NOT EXISTS banned(id INTEGER PRIMARY KEY)")
conn.commit()

# ===== ФУНКЦИИ БД =====
def register_user(uid, ref=None):
    uid = int(uid)
    if not cur.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
        cur.execute("INSERT INTO users(id, invited_by) VALUES(?,?)", (uid, ref))
        conn.commit()
        if ref and int(ref) != uid:
            cur.execute("UPDATE users SET ref = ref + 1 WHERE id = ?", (int(ref),))
            conn.commit()

def get_user_data(uid):
    res = cur.execute("SELECT balance, donated, purchased, ref FROM users WHERE id=?", (int(uid),)).fetchone()
    if res:
        return {"balance": res[0], "donated": res[1], "purchased": res[2], "ref": res[3]}
    return None

async def is_subscribed(uid):
    if uid == ADMIN_ID: return True
    try:
        m = await bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ["creator", "administrator", "member"]
    except: return False

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

# ===== МЕНЮ =====
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="catalog_0")],
        [InlineKeyboardButton(text="💰 Баланс / Пополнить", callback_data="wallet")],
        [InlineKeyboardButton(text="📦 Мои Покупки", callback_data="purchases")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="admin")]
    ])

# ===== ОСНОВНАЯ ЛОГИКА =====

@dp.message(F.text.startswith("/start"))
async def cmd_start(m: types.Message):
    uid = m.from_user.id
    if cur.execute("SELECT 1 FROM banned WHERE id=?", (uid,)).fetchone():
        return await m.answer("🚫 Вы заблокированы.")
    
    args = m.text.split()
    ref = args[1] if len(args) > 1 and args[1].isdigit() else None
    register_user(uid, ref) # Автоматическая регистрация
    
    if not await is_subscribed(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
        ])
        return await m.answer("Добро пожаловать! Чтобы пользоваться ботом, подпишись на канал.", reply_markup=kb)
    
    await m.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_kb())

@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(call: types.CallbackQuery):
    register_user(call.from_user.id) # Доп. регистрация на всякий случай
    if await is_subscribed(call.from_user.id):
        await call.answer("✅ Доступ разрешен")
        try: await call.message.delete()
        except: pass
        await call.message.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_kb())
    else:
        await call.answer("❌ Подписка не найдена", show_alert=True)

# КАТАЛОГ И ПОКУПКА
@dp.callback_query(F.data.startswith("catalog_"))
async def open_catalog(call: types.CallbackQuery):
    register_user(call.from_user.id)
    if not await is_subscribed(call.from_user.id): return await call.answer("❌ Нет подписки", show_alert=True)
    await call.answer()
    page = int(call.data.split("_")[1])
    items = list(PRODUCTS.items())[page*5:(page+1)*5]
    kb = []
    for pid, (name, price, _) in items:
        kb.append([InlineKeyboardButton(text=f"{name} — {price}⭐", callback_data=f"buychoice_{pid}")])
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"catalog_{page-1}"))
    if (page+1)*5 < len(PRODUCTS): nav.append(InlineKeyboardButton(text="➡️", callback_data=f"catalog_{page+1}"))
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="back")])
    await call.message.edit_caption(caption="🎬 Выберите видео:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("buychoice_"))
async def buy_choice(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    name, price, _ = PRODUCTS[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Купить сразу ({price}⭐)", callback_data=f"paynow_{pid}")],
        [InlineKeyboardButton(text=f"💎 С баланса ({price}⭐)", callback_data=f"paybal_{pid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog_0")]
    ])
    await call.message.edit_caption(caption=f"🛒 {name}\n💰 Цена: {price}⭐\n\nКак будем оплачивать?", reply_markup=kb)

@dp.callback_query(F.data.startswith("paybal_"))
async def pay_from_balance(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    uid = call.from_user.id
    name, price, video = PRODUCTS[pid]
    
    data = get_user_data(uid)
    if data["balance"] < price:
        return await call.answer(f"❌ Недостаточно ⭐ (Баланс: {data['balance']})", show_alert=True)
    
    # Списание и запись покупки
    new_purchased = (data["purchased"] or "") + pid + ","
    cur.execute("UPDATE users SET balance = balance - ?, purchased = ? WHERE id = ?", (price, new_purchased, uid))
    conn.commit()
    
    await call.answer("✅ Успешно куплено!")
    await call.message.answer(f"✅ Видео '{name}' теперь доступно!")
    await bot.send_video(uid, video, caption=f"🎬 {name}")

@dp.callback_query(F.data.startswith("paynow_"))
async def pay_direct(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    name, price, _ = PRODUCTS[pid]
    await bot.send_invoice(call.from_user.id, title=name, description=f"Покупка {name}", payload=f"buy_{pid}", currency="XTR", prices=[LabeledPrice(label="Stars", amount=price)], provider_token="")

# КОШЕЛЕК
@dp.callback_query(F.data == "wallet")
async def wallet_handler(call: types.CallbackQuery):
    bal = get_field(call.from_user.id, "balance") if get_user_data(call.from_user.id) else 0
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить 50⭐", callback_data="topup_50"), InlineKeyboardButton(text="Пополнить 100⭐", callback_data="topup_100")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="back")]
    ])
    await call.message.edit_caption(caption=f"💰 Ваш баланс: {bal}⭐\n\nВы можете купить звезды для оплаты внутри бота.", reply_markup=kb)

@dp.callback_query(F.data.startswith("topup_"))
async def topup_stars(call: types.CallbackQuery):
    amt = int(call.data.split("_")[1])
    await bot.send_invoice(call.from_user.id, title="Пополнение", description=f"Покупка {amt} звезд", payload=f"topup_{amt}", currency="XTR", prices=[LabeledPrice(label="Stars", amount=amt)], provider_token="")

# ОБРАБОТКА ОПЛАТ
@dp.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def on_success(msg: types.Message):
    payload = msg.successful_payment.invoice_payload
    uid = msg.from_user.id
    amt = msg.successful_payment.total_amount
    
    if payload.startswith("buy_"):
        pid = payload.split("_")[1]
        cur.execute("UPDATE users SET donated = donated + ?, purchased = purchased || ? WHERE id = ?", (amt, f"{pid},", uid))
        conn.commit()
        await msg.answer("✅ Оплачено! Ваше видео:")
        await bot.send_video(uid, PRODUCTS[pid][2], caption=f"🎬 {PRODUCTS[pid][0]}")
        
    elif payload.startswith("topup_"):
        cur.execute("UPDATE users SET balance = balance + ?, donated = donated + ? WHERE id = ?", (amt, amt, uid))
        conn.commit()
        await msg.answer(f"✅ Баланс пополнен на {amt}⭐!")

# ПРОФИЛЬ И ПОКУПКИ
@dp.callback_query(F.data == "profile")
async def profile_handler(call: types.CallbackQuery):
    d = get_user_data(call.from_user.id)
    if not d: return await call.answer("Перезапустите бота /start")
    text = f"👤 Профиль\n🆔 ID: `{call.from_user.id}`\n💰 Баланс: {d['balance']}⭐\n💎 Донат: {d['donated']}⭐\n👥 Рефералы: {d['ref']}"
    await call.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="back")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "purchases")
async def my_purchases(call: types.CallbackQuery):
    d = get_user_data(call.from_user.id)
    purchased = d["purchased"].split(",") if d and d["purchased"] else []
    kb = []
    for pid, (name, _, _) in PRODUCTS.items():
        if pid in purchased:
            kb.append([InlineKeyboardButton(text=f"📺 {name}", callback_data=f"getv_{pid}")])
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="back")])
    await call.message.edit_caption(caption="📦 Ваши покупки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("getv_"))
async def send_v(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    await bot.send_video(call.from_user.id, PRODUCTS[pid][2], caption=f"🎬 {PRODUCTS[pid][0]}")

@dp.callback_query(F.data == "back")
async def to_menu(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_caption(caption="💜 Главное меню", reply_markup=main_kb())

# ===== АДМИНКА =====
@dp.callback_query(F.data == "admin")
async def admin_menu(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return await call.answer("❌ Нет доступа")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Всем +100⭐", callback_data="give_all_100")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="back")]
    ])
    await call.message.edit_caption(caption="⚙️ Админка\n`/give ID Сумма` - выдать\n`/ban ID` - бан", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("give_all_"))
async def give_all(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    amt = int(call.data.split("_")[2])
    cur.execute("UPDATE users SET balance = balance + ?", (amt,))
    conn.commit()
    await call.answer(f"✅ Начислено по {amt}⭐ всем!", show_alert=True)

@dp.message(F.text.startswith("/give"))
async def adm_give_cmd(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, target, amt = m.text.split()
        target = int(target)
        amt = int(amt)
        
        # Принудительная регистрация, если ты вводишь ID вручную
        if not cur.execute("SELECT 1 FROM users WHERE id=?", (target,)).fetchone():
             cur.execute("INSERT INTO users(id) VALUES(?)", (target,))
        
        cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amt, target))
        conn.commit()
        await m.answer(f"✅ Выдано {amt}⭐ юзеру {target}")
        try: await bot.send_message(target, f"🎁 Админ выдал вам {amt}⭐!")
        except: pass
    except: await m.answer("Формат: `/give 12345 500`")

@dp.message(F.text.startswith("/ban"))
async def adm_ban(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        uid = int(m.text.split()[1])
        cur.execute("INSERT OR IGNORE INTO banned VALUES(?)", (uid,))
        conn.commit()
        await m.answer(f"🚫 {uid} забанен")
    except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

