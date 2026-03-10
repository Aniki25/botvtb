import json
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "TOKEN"
ADMIN_ID = 123456789
DATA_FILE = "data.json"
CLICK_TIMEOUT = 3

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "counter": 0,
            "last_click": {},
            "daily_count": 0,
            "message_id": None
        }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

def keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Отчет подписан", callback_data="report")]]
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = await update.message.reply_text(
        "Нажимайте кнопку после подписания отчета",
        reply_markup=keyboard()
    )

    try:
        await msg.pin()
    except:
        pass

    data["message_id"] = msg.message_id
    save_data()

async def report_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = str(user.id)
    name = user.first_name

    now = time.time()

    if user_id in data["last_click"]:
        if now - data["last_click"][user_id] < CLICK_TIMEOUT:
            await update.callback_query.answer("Не нажимайте слишком быстро 🙂")
            return

    data["last_click"][user_id] = now

    data["counter"] += 1
    data["daily_count"] += 1

    counter = data["counter"]

    if counter < 9:
        text = f"{name} подписал отчет №{counter}"

    elif counter == 9:
        text = (
            f"{name} подписал отчет №9\n"
            "Внимание! Следующий отчет будет отправлен на экспертную проверку"
        )

    elif counter == 10:
        text = f"{name} подписал отчет №10"
        data["counter"] = 0

    save_data()

    await update.callback_query.message.reply_text(text)
    await update.callback_query.answer()

async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):

    counter = data["counter"]

    if counter == 0:
        text = "Сейчас начало нового цикла. Следующий отчет будет №1."
    else:
        text = f"Сейчас подписывается отчет №{counter}"

    await update.message.reply_text(text)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    counter = data["counter"]

    until_check = 9 - counter
    until_reset = 10 - counter

    if counter == 0:

        text = (
            "Статистика отчетов\n\n"
            "Подписано в текущем цикле: 0\n"
            "Следующий отчет будет №1\n"
            "До экспертной проверки: 9\n"
            "До конца цикла: 10\n\n"
            f"Сегодня подписано: {data['daily_count']}"
        )

    elif counter == 9:

        text = (
            "Статистика отчетов\n\n"
            "Подписано в текущем цикле: 9\n"
            "Следующий отчет будет отправлен на экспертную проверку\n"
            f"До конца цикла: {until_reset}\n\n"
            f"Сегодня подписано: {data['daily_count']}"
        )

    else:

        text = (
            "Статистика отчетов\n\n"
            f"Подписано в текущем цикле: {counter}\n"
            f"До экспертной проверки: {until_check}\n"
            f"До конца цикла: {until_reset}\n\n"
            f"Сегодня подписано: {data['daily_count']}"
        )

    await update.message.reply_text(text)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав.")
        return

    data["counter"] = 0
    save_data()

    await update.message.reply_text("Счетчик сброшен.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("count", count))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CallbackQueryHandler(report_click, pattern="report"))

app.run_polling()