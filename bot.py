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

# ===== ФУНКЦИИ БД =====
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
    # Увеличиваем баланс и статистику доната (если пополнение положительное)
    donated_inc = amount if amount > 0 else 0
    cur.execute("UPDATE users SET balance = balance + ?, donated = donated + ? WHERE id = ?", (amount, donated_inc, uid))
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

# ===== МЕНЮ =====
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="cat_0")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="wallet")],
        [InlineKeyboardButton(text="📦 Покупки", callback_data="my_vids")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="prof")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="adm")]
    ])

# ===== ОБРАБОТЧИКИ =====

@dp.message(F.text.startswith("/start"))
async def start(m: types.Message):
    if cur.execute("SELECT 1 FROM banned WHERE id=?", (m.from_user.id,)).fetchone():
        return await m.answer("🚫 Вы забанены.")
    
    args = m.text.split()
    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    add_user(m.from_user.id, ref)
    
    if not await check_sub(m.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await m.answer("Добро пожаловать! Подпишитесь на канал для доступа.", reply_markup=kb)
    
    await m.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "check_sub")
async def check_btn(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.answer("✅ Доступ разрешен")
        try: await call.message.delete()
        except: pass
        await call.message.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_menu_kb())
    else:
        await call.answer("❌ Вы не подписаны", show_alert=True)

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

# ВЫБОР СПОСОБА ОПЛАТЫ
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

# ОПЛАТА С БАЛАНСА
@dp.callback_query(F.data.startswith("pay_bal_"))
async def pay_bal(call: types.CallbackQuery):
    pid = call.data.split("_")[2]
    uid = call.from_user.id
    name, price, video = PRODUCTS[pid]
    
    if get_field(uid, "balance") < price:
        return await call.answer("❌ Недостаточно звезд на балансе!", show_alert=True)
    
    add_balance(uid, -price) # Снимаем деньги
    add_purchase(uid, pid)   # Добавляем в покупки
    await call.answer("✅ Успешно куплено!")
    await call.message.answer(f"✅ Вы приобрели '{name}' с баланса!")
    await bot.send_video(uid, video, caption=f"🎬 {name}")

# ПРЯМАЯ ОПЛАТА (ЗВЕЗДЫ)
@dp.callback_query(F.data.startswith("pay_now_"))
async def pay_now(call: types.CallbackQuery):
    pid = call.data.split("_")[2]
    name, price, _ = PRODUCTS[pid]
    await bot.send_invoice(
        call.from_user.id,
        title=name,
        description=f"Покупка видео '{name}'",
        payload=f"item_{pid}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=price)],
        provider_token=""
    )

# БАЛАНС
@dp.callback_query(F.data == "wallet")
async def wallet(call: types.CallbackQuery):
    bal = get_field(call.from_user.id, "balance")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить +50⭐", callback_data="topup_50")],
        [InlineKeyboardButton(text="Пополнить +100⭐", callback_data="topup_100")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]
    ])
    await call.message.edit_caption(caption=f"💰 Ваш баланс: {bal}⭐\n\nЗдесь вы можете пополнить счет звезд.", reply_markup=kb)

@dp.callback_query(F.data.startswith("topup_"))
async def topup(call: types.CallbackQuery):
    amount = int(call.data.split("_")[1])
    await bot.send_invoice(
        call.from_user.id,
        title="Пополнение баланса",
        description=f"Начисление {amount} звезд на ваш баланс в боте",
        payload=f"topup_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=amount)],
        provider_token=""
    )

# ПРОВЕРКА ПЛАТЕЖЕЙ
@dp.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(msg: types.Message):
    payload = msg.successful_payment.invoice_payload
    uid = msg.from_user.id
    
    if payload.startswith("item_"):
        pid = payload.split("_")[1]
        add_purchase(uid, pid)
        # Добавляем в статистику доната (но не на баланс, так как товар уже куплен)
        cur.execute("UPDATE users SET donated = donated + ? WHERE id = ?", (msg.successful_payment.total_amount, uid))
        conn.commit()
        await msg.answer("✅ Оплата прошла! Ваше видео:")
        await bot.send_video(uid, PRODUCTS[pid][2], caption=f"🎬 {PRODUCTS[pid][0]}")
        
    elif payload.startswith("topup_"):
        amount = int(payload.split("_")[1])
        add_balance(uid, amount)
        await msg.answer(f"✅ Баланс успешно пополнен на {amount}⭐!")

# ПРОФИЛЬ И ПОКУПКИ
@dp.callback_query(F.data == "prof")
async def profile(call: types.CallbackQuery):
    uid = call.from_user.id
    bal = get_field(uid, "balance")
    don = get_field(uid, "donated")
    ref = get_field(uid, "ref")
    text = f"👤 Профиль\n\n🆔 ID: `{uid}`\n💰 Баланс: {bal}⭐\n💎 Всего доната: {don}⭐\n👥 Рефералов: {ref}"
    await call.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "my_vids")
async def my_vids(call: types.CallbackQuery):
    purchased = (get_field(call.from_user.id, "purchased") or "").split(",")
    kb = []
    for pid, (name, _, _) in PRODUCTS.items():
        if pid in purchased and pid:
            kb.append([InlineKeyboardButton(text=f"📺 {name}", callback_data=f"getv_{pid}")])
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")])
    await call.message.edit_caption(caption="📦 Список ваших покупок:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("getv_"))
async def send_purchased(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    await bot.send_video(call.from_user.id, PRODUCTS[pid][2], caption=f"🎬 {PRODUCTS[pid][0]}")

@dp.callback_query(F.data == "to_menu")
async def to_menu_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_caption(caption="💜 Главное меню", reply_markup=main_menu_kb())

# ===== АДМИН ПАНЕЛЬ =====
@dp.callback_query(F.data == "adm")
async def admin_panel(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Всем +100⭐", callback_data="give_all_100")],
        [InlineKeyboardButton(text="🎁 Всем +500⭐", callback_data="give_all_500")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]
    ])
    text = (
        "⚙️ **Админ-панель**\n\n"
        "Команды (отправлять просто в чат):\n"
        "`/give ID СУММА` — выдать звезды\n"
        "`/ban ID` — забанить\n"
        "`/unban ID` — разбанить"
    )
    await call.message.edit_caption(caption=text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("give_all_"))
async def give_all_btn(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    amount = int(call.data.split("_")[2])
    cur.execute("UPDATE users SET balance = balance + ?", (amount,))
    conn.commit()
    await call.answer(f"✅ Начислено по {amount}⭐ всем пользователям!", show_alert=True)

@dp.message(F.text.startswith("/give"))
async def admin_give_stars(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        parts = m.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        
        # Проверка юзера
        res = cur.execute("SELECT 1 FROM users WHERE id=?", (target_id,)).fetchone()
        if not res:
            return await m.answer(f"❌ Юзер `{target_id}` не найден в БД.")

        cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, target_id))
        conn.commit()
        
        await m.answer(f"✅ Успешно! Выдано {amount}⭐ пользователю `{target_id}`.")
        try:
            await bot.send_message(target_id, f"🎁 Админ начислил вам **{amount}⭐**!")
        except: pass
    except:
        await m.answer("❌ Ошибка. Формат: `/give 1234567 500`")

@dp.message(F.text.startswith("/ban"))
async def admin_ban_user(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        uid = int(m.text.split()[1])
        cur.execute("INSERT OR IGNORE INTO banned VALUES(?)", (uid,))
        conn.commit()
        await m.answer(f"🚫 Юзер {uid} забанен.")
    except: pass

@dp.message(F.text.startswith("/unban"))
async def admin_unban_user(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        uid = int(m.text.split()[1])
        cur.execute("DELETE FROM banned WHERE id=?", (uid,))
        conn.commit()
        await m.answer(f"✅ Юзер {uid} разбанен.")
    except: pass

# ЗАПУСК
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

