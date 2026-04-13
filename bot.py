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
)""")
cur.execute("CREATE TABLE IF NOT EXISTS banned(id INTEGER PRIMARY KEY)")
conn.commit()

# ===== ФУНКЦИИ =====
def register_user(uid, ref=None):
    uid = int(uid)
    if not cur.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
        cur.execute("INSERT INTO users(id, invited_by) VALUES(?,?)", (uid, ref))
        conn.commit()
        if ref and int(ref) != uid:
            cur.execute("UPDATE users SET ref = ref + 1 WHERE id = ?", (int(ref),))
            conn.commit()

def get_balance(uid):
    res = cur.execute("SELECT balance FROM users WHERE id=?", (int(uid),)).fetchone()
    return res[0] if res else 0

async def check_sub(uid):
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

# ===== КЛАВИАТУРЫ =====
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="cat_0")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="wallet")],
        [InlineKeyboardButton(text="📦 Покупки", callback_data="purchases")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="admin")]
    ])

# ===== ХЕНДЛЕРЫ =====
@dp.message(F.text.startswith("/start"))
async def start(m: types.Message):
    uid = m.from_user.id
    if cur.execute("SELECT 1 FROM banned WHERE id=?", (uid,)).fetchone():
        return
    args = m.text.split()
    ref = args[1] if len(args) > 1 and args[1].isdigit() else None
    register_user(uid, ref)
    if not await check_sub(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await m.answer("Подпишитесь на канал!", reply_markup=kb)
    await m.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_kb())

@dp.callback_query(F.data == "check_sub")
async def sub_check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.answer("✅ Доступ открыт")
        await call.message.delete()
        await call.message.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_kb())
    else: await call.answer("❌ Нет подписки", show_alert=True)

# КНОПКА БАЛАНС (ИСПРАВЛЕНО)
@dp.callback_query(F.data == "wallet")
async def wallet_menu(call: types.CallbackQuery):
    register_user(call.from_user.id) # Гарантируем наличие в базе
    bal = get_balance(call.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="+50⭐", callback_data="topup_50"), InlineKeyboardButton(text="+100⭐", callback_data="topup_100")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]
    ])
    await call.message.edit_caption(caption=f"💰 Ваш текущий баланс: {bal}⭐\n\nВы можете пополнить его, купив звезды ниже:", reply_markup=kb)

@dp.callback_query(F.data.startswith("topup_"))
async def topup(call: types.CallbackQuery):
    amt = int(call.data.split("_")[1])
    await bot.send_invoice(call.from_user.id, title="Пополнение", description=f"Покупка {amt} звезд", payload=f"top_{amt}", currency="XTR", prices=[LabeledPrice(label="Stars", amount=amt)], provider_token="")

# КАТАЛОГ И ОПЛАТА
@dp.callback_query(F.data.startswith("cat_"))
async def catalog(call: types.CallbackQuery):
    await call.answer()
    page = int(call.data.split("_")[1])
    items = list(PRODUCTS.items())[page*5:(page+1)*5]
    kb = []
    for pid, (name, price, _) in items:
        kb.append([InlineKeyboardButton(text=f"{name} — {price}⭐", callback_data=f"pre_{pid}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"cat_{page-1}"))
    if (page+1)*5 < len(PRODUCTS): nav.append(InlineKeyboardButton(text="➡️", callback_data=f"cat_{page+1}"))
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")])
    await call.message.edit_caption(caption="🎬 Каталог видео:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("pre_"))
async def pre_buy(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    name, price, _ = PRODUCTS[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Купить сразу ({price}⭐)", callback_data=f"paynow_{pid}")],
        [InlineKeyboardButton(text=f"💎 С баланса ({price}⭐)", callback_data=f"paybal_{pid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cat_0")]
    ])
    await call.message.edit_caption(caption=f"🛒 {name}\n💰 Цена: {price}⭐", reply_markup=kb)

@dp.callback_query(F.data.startswith("paybal_"))
async def buy_bal(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    uid = call.from_user.id
    name, price, video = PRODUCTS[pid]
    if get_balance(uid) < price:
        return await call.answer("❌ Недостаточно средств!", show_alert=True)
    
    cur.execute("UPDATE users SET balance = balance - ?, purchased = purchased || ? WHERE id = ?", (price, f"{pid},", uid))
    conn.commit()
    await call.answer("✅ Успешно!")
    await bot.send_video(uid, video, caption=f"🎬 {name}")

@dp.callback_query(F.data.startswith("paynow_"))
async def buy_now(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    name, price, _ = PRODUCTS[pid]
    await bot.send_invoice(call.from_user.id, title=name, description="Покупка", payload=f"buy_{pid}", currency="XTR", prices=[LabeledPrice(label="Stars", amount=price)], provider_token="")

# ОБРАБОТКА ОПЛАТ
@dp.pre_checkout_query()
async def pre_check(q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def success(m: types.Message):
    pay = m.successful_payment.invoice_payload
    amt = m.successful_payment.total_amount
    if pay.startswith("buy_"):
        pid = pay.split("_")[1]
        cur.execute("UPDATE users SET purchased = purchased || ?, donated = donated + ? WHERE id = ?", (f"{pid},", amt, m.from_user.id))
        conn.commit()
        await bot.send_video(m.from_user.id, PRODUCTS[pid][2], caption="🎬 Спасибо за покупку!")
    elif pay.startswith("top_"):
        cur.execute("UPDATE users SET balance = balance + ?, donated = donated + ? WHERE id = ?", (amt, amt, m.from_user.id))
        conn.commit()
        await m.answer(f"✅ Баланс пополнен на {amt}⭐")

# ПРОФИЛЬ
@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    uid = call.from_user.id
    res = cur.execute("SELECT balance, donated, ref FROM users WHERE id=?", (uid,)).fetchone()
    text = f"👤 Профиль\n🆔 ID: `{uid}`\n💰 Баланс: {res[0]}⭐\n💎 Донат: {res[1]}⭐\n👥 Рефы: {res[2]}"
    await call.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "to_menu")
async def to_menu(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_caption(caption="💜 Главное меню", reply_markup=main_kb())

# АДМИНКА
@dp.callback_query(F.data == "admin")
async def admin(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Всем +100⭐", callback_data="giveall_100")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]
    ])
    await call.message.edit_caption(caption="⚙️ Админ\n`/give ID AMOUNT`", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("giveall_"))
async def give_all(call: types.CallbackQuery):
    amt = int(call.data.split("_")[1])
    cur.execute("UPDATE users SET balance = balance + ?", (amt,))
    conn.commit()
    await call.answer(f"✅ Всем выдано {amt}⭐", show_alert=True)

@dp.message(F.text.startswith("/give"))
async def give_cmd(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, uid, amt = m.text.split()
        register_user(uid) # Регистрируем, если его не было
        cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (int(amt), int(uid)))
        conn.commit()
        await m.answer("✅ Выдано")
        try: await bot.send_message(int(uid), f"🎁 Вам начислено {amt}⭐")
        except: pass
    except: await m.answer("Ошибка формата")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

