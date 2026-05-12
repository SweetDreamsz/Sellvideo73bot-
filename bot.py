import asyncio
import sqlite3
import logging
import json

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, WebAppInfo

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8637242832:AAEdBKu4R1XhyWHCO1VYxBvo67MapnWGk2k"
ADMIN_ID = 8314718448
CHANNEL_ID = -1003491649657
CHANNEL_LINK = "https://t.me/+9DI7onJBz0I1ZWQy"
PHOTO = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg"

# Твоя ссылка из GitHub Pages (обязательно с /admin.html)
WEB_APP_URL = "https://htmeetdreamsz99.github.io/Jjakwsieql/"

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
        [InlineKeyboardButton(text="⚙️ Админ-панель", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

# ===== ОБРАБОТКА ДАННЫХ ИЗ WEB APP =====
@dp.message(F.web_app_data)
async def web_app_handler(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    
    try:
        # Парсим данные, которые отправила твоя HTML-панель
        data = json.loads(m.web_app_data.data)
        action = data.get("action")
        user_id = int(data.get("user_id"))
        
        if action == "give_stars":
            amount = int(data.get("amount", 0))
            cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
            conn.commit()
            await m.answer(f"✅ Успешно! Пользователю {user_id} начислено {amount}⭐")
            try: await bot.send_message(user_id, f"🎁 Администратор начислил вам {amount}⭐")
            except: pass

        elif action == "ban_user":
            cur.execute("INSERT OR IGNORE INTO banned(id) VALUES(?)", (user_id,))
            conn.commit()
            await m.answer(f"🚫 Пользователь {user_id} заблокирован.")

    except Exception as e:
        await m.answer(f"⚠️ Ошибка обработки: {e}")

# ===== ХЕНДЛЕРЫ ПРИЛОЖЕНИЯ =====
@dp.message(F.text.startswith("/start"))
async def start(m: types.Message):
    uid = m.from_user.id
    if cur.execute("SELECT 1 FROM banned WHERE id=?", (uid,)).fetchone(): return
    args = m.text.split()
    ref = args[1] if len(args) > 1 and args[1].isdigit() else None
    register_user(uid, ref)
    if not await check_sub(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await m.answer("Подпишитесь на канал для доступа!", reply_markup=kb)
    await m.answer_photo(PHOTO, caption="💜 Добро пожаловать в Sweet Shop!", reply_markup=main_kb())

@dp.callback_query(F.data == "check_sub")
async def sub_check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.answer("✅ Доступ открыт")
        await call.message.delete()
        await call.message.answer_photo(PHOTO, caption="💜 Главное меню", reply_markup=main_kb())
    else: await call.answer("❌ Вы не подписались!", show_alert=True)

@dp.callback_query(F.data == "wallet")
async def wallet_menu(call: types.CallbackQuery):
    bal = get_balance(call.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="+50⭐", callback_data="topup_50"), InlineKeyboardButton(text="+100⭐", callback_data="topup_100")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]
    ])
    await call.message.edit_caption(caption=f"💰 Ваш баланс: {bal}⭐\nВыберите сумму пополнения:", reply_markup=kb)

@dp.callback_query(F.data == "to_menu")
async def to_menu(call: types.CallbackQuery):
    await call.message.edit_caption(caption="💜 Главное меню", reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    uid = call.from_user.id
    res = cur.execute("SELECT balance, donated, ref FROM users WHERE id=?", (uid,)).fetchone()
    text = f"👤 Профиль\n🆔 ID: `{uid}`\n💰 Баланс: {res[0]}⭐\n💎 Донат: {res[1]}⭐\n👥 Рефералы: {res[2]}"
    await call.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="to_menu")]]), parse_mode="Markdown")

# (Каталог и оплата остаются без изменений)
@dp.callback_query(F.data.startswith("cat_"))
async def catalog(call: types.CallbackQuery):
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
    await call.message.edit_caption(caption="🎬 Выберите видео:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

async def main():
    # Перед запуском на хостинге убедись, что другие копии бота выключены!
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

