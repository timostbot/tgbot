import asyncio
import nest_asyncio
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackContext, filters
from telegram.ext.webhook import WebhookServer
import gspread
from aiohttp import web

# Підключення до Google Sheets
gc = gspread.service_account(filename='telegrambotproject-443815-170f4d0283c5.json')
spreadsheet = gc.open("Telegram Messages")  # Відкриваємо таблицю
bought_sheet = spreadsheet.get_worksheet(0)  # Лист "Купили"
not_bought_sheet = spreadsheet.get_worksheet(1)  # Лист "Не купили"

# Головне меню з постійними кнопками
MAIN_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Купили"), KeyboardButton("Не купили")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Додаткові меню
BOUGHT_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Підписка"), KeyboardButton("Гарантія")],
        [KeyboardButton("Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

NOT_BOUGHT_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Чохол"), KeyboardButton("Підписка")],
        [KeyboardButton("Гарантія"), KeyboardButton("Телефон")],
        [KeyboardButton("Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

CANCEL_BUTTON = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Відміна")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

user_states = {}

# Telegram Handlers
async def start(update: Update, context: CallbackContext) -> None:
    user_states[update.effective_user.id] = None
    await update.message.reply_text("Виберіть дію:", reply_markup=MAIN_MENU)

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if text == "купили":
        user_states[user_id] = "bought"
        await update.message.reply_text("Що саме купили?", reply_markup=BOUGHT_MENU)
    elif text == "не купили":
        user_states[user_id] = "notB"
        await update.message.reply_text("Що саме не купили?", reply_markup=NOT_BOUGHT_MENU)
    elif text in ["підписка", "гарантія", "чохол", "телефон"]:
        action = user_states.get(user_id)
        if action == "bought" or action == "notB":
            user_states[user_id] = f"{action}_item_{text}"
            await update.message.reply_text(f"Що стало вирішальним фактором для покупки/не покупки {text.capitalize()}? Напишіть фактор.",
                                            reply_markup=CANCEL_BUTTON)
        else:
            await update.message.reply_text("Оберіть дію перед тим, як вказувати товар.", reply_markup=MAIN_MENU)
    elif text == "назад":
        user_states[user_id] = None
        await update.message.reply_text("Повертаємось до головного меню:", reply_markup=MAIN_MENU)
    elif text == "відміна":
        user_states[user_id] = None
        await update.message.reply_text("Ви скасували введення фактора. Повертаємось до головного меню.", reply_markup=MAIN_MENU)
    else:
        if user_states[user_id] and "item" in user_states[user_id]:
            item = user_states[user_id].split("_")[0]
            product = user_states[user_id].split("_")[2]
            factor = text

            if item == "bought":
                bought_sheet.append_row([update.effective_user.username, product.capitalize(), factor])
            elif item == "notB":
                not_bought_sheet.append_row([update.effective_user.username, product.capitalize(), factor])

            user_states[user_id] = None
            await update.message.reply_text(f"Ваша відповідь '{text}' збережена. Повертаємось до головного меню.", reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text("Я не розумію цю команду. Скористайтесь кнопками.")

# Запуск aiohttp-сервера
async def webhook(request):
    data = await request.json()
    await application.update_queue.put(data)
    return web.Response(text="OK")

async def flask_app():
    app = web.Application()
    app.router.add_post('/', webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0')
    await site.start()

# Головна функція
async def main():
    global application
    application = Application.builder().token("7187419303:AAGbvkC47sDqHv2POD8705OiUGKxYsyFu1w").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await asyncio.gather(application.start(), flask_app())

# Додано nest_asyncio
if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
