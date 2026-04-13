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

def add_purchase(uid, pid):
    current = get_field(uid, "purchased") or ""
    purchased_list = current.split(",")
    if pid not in purchased_list:
        new_val = current + pid + ","
        cur.execute("UPDATE users SET purchased = ? WHERE id=?", (new_val, uid))
        conn.commit()

def is_banned(uid):
    return cur.execute("SELECT 1 FROM banned WHERE id=?", (uid,)).fetchone() is not None

async def check_sub(uid):
    if uid == ADMIN_ID: return True
    try:
        m = await bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ["creator", "administrator", "member"]
    except:
        return False

# ===== ДЕКОРАТОР ПРОВЕРКИ (ИСПРАВЛЕН) =====
def check_access(func):
    async def wrapper(event, *args, **kwargs):
        uid = event.from_user.id
        
        # 1. Проверка бана
        if is_banned(uid):
            if isinstance(event, types.CallbackQuery):
                await event.answer("🚫 Доступ заблокирован", show_alert=True)
            return

        # 2. Проверка подписки
        if not await check_sub(uid):
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
            ])
            msg_text = "❌ Чтобы пользоваться ботом, подпишись на наш канал!"
            
            if isinstance(event, types.CallbackQuery):
                await event.answer("❌ Подпишитесь!")
                # Если сообщение уже содержит этот текст, не шлем дубль
                if event.message.caption != msg_text:
                    await event.message.answer(msg_text, reply_markup=kb)
            else:
                await event.answer(msg_text, reply_markup=kb)
            return

        # 3. Ответ на CallbackQuery, чтобы кнопка не "висела"
        if isinstance(event, types.CallbackQuery):
            try:
                await event.answer()
            except:
                pass

        return await func(event, *args, **kwargs)
    return wrapper

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
        [InlineKeyboardButton(text="🎬 Каталог", callback_data="catalog_0")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="refs")],
        [InlineKeyboardButton(text="📦 Покупки", callback_data="my_purchases")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="admin_panel")]
    ])

# ===== ОБРАБОТЧИКИ =====

@dp.message(F.text.startswith("/start"))
async def start_cmd(m: types.Message):
    args = m.text.split()
    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    add_user(m.from_user.id, ref)
    
    if not await check_sub(m.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await m.answer("Добро пожаловать! Сначала подпишись на канал.", reply_markup=kb)

    await m.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "check_sub")
async def check_sub_btn(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.answer("✅ Подписка подтверждена!", show_alert=True)
        await call.message.delete()
        await call.message.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_menu_kb())
    else:
        await call.answer("❌ Вы всё еще не подписаны", show_alert=True)

@dp.callback_query(F.data.startswith("catalog_"))
@check_access
async def catalog_handler(call: types.CallbackQuery):
    page = int(call.data.split("_")[1])
    items = list(PRODUCTS.items())[page*5:(page+1)*5]
    kb = []
    for pid, (name, price, _) in items:
        kb.append([InlineKeyboardButton(text=f"{name} — {price}⭐", callback_data=f"buy_direct_{pid}")])
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"catalog_{page-1}"))
    if (page+1)*5 < len(PRODUCTS): nav.append(InlineKeyboardButton(text="➡️", callback_data=f"catalog_{page+1}"))
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="back_to_menu")])
    
    await call.message.edit_caption(caption="🎬 Выберите видео для покупки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("buy_direct_"))
@check_access
async def process_buy(call: types.CallbackQuery):
    pid = call.data.split("_")[2]
    name, price, video = PRODUCTS[pid]
    
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"Видео: {name}",
        description=f"Прямая оплата доступа. После оплаты видео придет сюда.",
        payload=f"stars_pay_{pid}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=price)],
        provider_token=""
    )

@dp.pre_checkout_query()
async def pre_checkout_handler(q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def success_pay(msg: types.Message):
    pid = msg.successful_payment.invoice_payload.split("_")[2]
    if pid in PRODUCTS:
        name, price, video = PRODUCTS[pid]
        add_purchase(msg.from_user.id, pid)
        cur.execute("UPDATE users SET donated=donated+? WHERE id=?", (price, msg.from_user.id))
        conn.commit()
        await msg.answer(f"✅ Оплачено! Лови видео: {name}")
        await bot.send_video(msg.from_user.id, video, caption=f"🎬 {name}")

@dp.callback_query(F.data == "my_purchases")
@check_access
async def my_purchases_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    purchased = (get_field(uid, "purchased") or "").split(",")
    kb = []
    for pid, (name, _, _) in PRODUCTS.items():
        if pid in purchased and pid != "":
            kb.append([InlineKeyboardButton(text=f"📺 {name}", callback_data=f"get_vid_{pid}")])
    
    if not kb:
        return await call.answer("📦 У вас пока нет покупок", show_alert=True)
    
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="back_to_menu")])
    await call.message.edit_caption(caption="📦 Ваши купленные видео:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("get_vid_"))
@check_access
async def show_purchased_vid(call: types.CallbackQuery):
    pid = call.data.split("_")[2]
    await bot.send_video(call.from_user.id, PRODUCTS[pid][2], caption=f"🎬 {PRODUCTS[pid][0]}")

@dp.callback_query(F.data == "refs")
@check_access
async def refs_handler(call: types.CallbackQuery):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={call.from_user.id}"
    text = f"👥 Рефералы: {get_field(call.from_user.id,'ref')}\n\nТвоя ссылка:\n{link}"
    await call.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="back_to_menu")]]))

@dp.callback_query(F.data == "profile")
@check_access
async def profile_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    username = call.from_user.username or "none"
    p_count = len([p for p in (get_field(uid, "purchased") or "").split(",") if p])
    text = (f"👤 Профиль\n\n🆔 ID: {uid}\n👤 Юзер: @{username}\n💰 Донат: {get_field(uid,'donated')}⭐\n🎬 Куплено: {p_count}")
    await call.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="back_to_menu")]]))

@dp.callback_query(F.data == "back_to_menu")
@check_access
async def back_menu(call: types.CallbackQuery):
    await call.message.edit_caption(caption="💜 Главное меню", reply_markup=main_menu_kb())

# ===== АДМИН ПАНЕЛЬ (БЕЗ ДЕКОРАТОРА ЧТОБЫ ВСЕГДА МОГЛИ ЗАЙТИ) =====
@dp.callback_query(F.data == "admin_panel")
async def admin_handler(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ У вас нет прав", show_alert=True)
    await call.answer()
    await call.message.edit_caption(caption="⚙️ Админка\n\nКоманды:\n/ban id\n/unban id", 
                                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="back_to_menu")]]))

@dp.message(F.text.startswith("/ban"))
async def cmd_ban(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        uid = int(m.text.split()[1])
        cur.execute("INSERT OR IGNORE INTO banned VALUES(?)", (uid,))
        conn.commit()
        await m.answer(f"✅ Пользователь {uid} забанен.")
    except: await m.answer("Ошибка. Пример: /ban 123456")

@dp.message(F.text.startswith("/unban"))
async def cmd_unban(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        uid = int(m.text.split()[1])
        cur.execute("DELETE FROM banned WHERE id=?", (uid,))
        conn.commit()
        await m.answer(f"✅ Пользователь {uid} разбанен.")
    except: await m.answer("Ошибка. Пример: /unban 123456")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

