import asyncio
import sqlite3
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, SuccessfullPayment

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8637242832:AAEdBKu4R1XhyWHCO1VYxBvo67MapnWGk2k"
ADMIN_ID = 8314718448
CHANNEL_ID = -1003491649657
CHANNEL_LINK = "https://t.me/+9DI7onJBz0I1ZWQy"
PHOTO_CATALOG = "https://raw.githubusercontent.com/SweetDreamsz/Sellvideo73bot-/main/photo2.jpg"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== БД (Без изменений) =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, purchased TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)")
conn.commit()

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

# ===== ТОВАРЫ (Без изменений) =====
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
        [InlineKeyboardButton(text="📦 Мои покупки", callback_data="my")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Админ", callback_data="admin")]
    ])

# ===== СТАРТ И ПРОВЕРКА ПОДПИСКИ (Без изменений) =====
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except: return True

@dp.message(F.text == "/start")
async def start(message: types.Message):
    if is_banned(message.from_user.id): return
    add_user(message.from_user.id)
    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        return await message.answer("Подпишись на канал", reply_markup=kb)
    await message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())

# ===== КАТАЛОГ =====
@dp.callback_query(F.data.startswith("catalog"))
async def catalog(call: types.CallbackQuery):
    page = int(call.data.split("_")[1])
    items = list(PRODUCTS.items())
    start, end = page * 5, (page + 1) * 5
    kb = [[InlineKeyboardButton(text=f"{p['name']} - {p['price']}⭐", callback_data=f"buy_{pid}")] for pid, p in items[start:end]]
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f_catalog_{page-1}"))
    if end < len(items): nav.append(InlineKeyboardButton(text="➡️", callback_data=f"catalog_{page+1}"))
    kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Меню", callback_data="menu")])
    await call.message.edit_caption(caption="🎬 Каталог", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ===== ВЫБОР ТОВАРА =====
@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    if has_product(call.from_user.id, pid):
        return await call.answer("У вас уже есть этот доступ!", show_alert=True)
    
    p = PRODUCTS[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {p['price']} ⭐", callback_data=f"pay_{pid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog_0")]
    ])
    await call.message.answer(f"Товар: {p['name']}\nСтоимость: {p['price']} Telegram Stars", reply_markup=kb)

# ===== ВЫСТАВЛЕНИЕ СЧЕТА (XTR - STARS) =====
@dp.callback_query(F.data.startswith("pay_"))
async def send_stars_invoice(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = PRODUCTS[pid]
    
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"Покупка: {p['name']}",
        description=f"Доступ к видеоматериалу {p['name']}",
        payload=pid, # Передаем ID товара в payload
        provider_token="", # Для Telegram Stars оставляем пустым
        currency="XTR",
        prices=[LabeledPrice(label="Оплата звездами", amount=p['price'])]
    )
    await call.answer()

# ===== ПОДТВЕРЖДЕНИЕ ПЛАТЕЖА (PreCheckout) =====
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# ===== УСПЕШНАЯ ОПЛАТА (Выдача товара) =====
@dp.message(F.successful_payment)
async def success_pay(message: types.Message):
    pid = message.successful_payment.invoice_payload
    p = PRODUCTS.get(pid)
    
    if p:
        add_purchase(message.from_user.id, pid)
        await message.answer(f"✅ Оплата прошла успешно! Ваш товар: {p['name']}")
        await bot.send_video(message.from_user.id, p["video"])
    else:
        await message.answer("⚠ Произошла ошибка при выдаче товара. Обратитесь к админу.")

# ===== ОСТАЛЬНЫЕ ФУНКЦИИ (Профиль, Админ и т.д.) =====
@dp.callback_query(F.data == "menu")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.answer_photo(PHOTO_CATALOG, caption="💜 Главное меню", reply_markup=menu())

# ... (Остальной код из вашего файла без изменений) ...

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
