import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timedelta

# --- Конфигурация ---
TELEGRAM_TOKEN = '8155418035:AAFJRv6HBTaxqkHeujTcPHDlk3SrxrzLGBY'
SPREADSHEET_NAME = 'BotResponse'

# --- Подключение к Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google-credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).sheet1

bot = telebot.TeleBot(TELEGRAM_TOKEN)

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

russia_flag = "🇷🇺"
world_emoji = "🌍"
money_emoji = "💰"

def make_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton(f"РФ {russia_flag} 1"),
        KeyboardButton(f"РФ {russia_flag} 2"),
        KeyboardButton(f"РФ {russia_flag} 3"),
        KeyboardButton(f"РФ {russia_flag} 4"),
        KeyboardButton(f"РФ {russia_flag} 5"),
    )
    keyboard.row(
        KeyboardButton(f"МИР {world_emoji} 1"),
        KeyboardButton(f"МИР {world_emoji} 2"),
        KeyboardButton(f"МИР {world_emoji} 3"),
        KeyboardButton(f"МИР {world_emoji} 4"),
        KeyboardButton(f"МИР {world_emoji} 5"),
    )
    keyboard.row(
        KeyboardButton(f"КО {money_emoji} 1"),
        KeyboardButton(f"КО {money_emoji} 2"),
        KeyboardButton(f"КО {money_emoji} 4"),
        KeyboardButton(f"КО {money_emoji} 6"),
        KeyboardButton(f"КО {money_emoji} 8"),
        KeyboardButton(f"КО {money_emoji} 10"),
    )
    return keyboard

def parse_message(text):
    try:
        parts = text.split()
        if len(parts) >= 2:
            key = parts[0].upper()
            amount = int(parts[-1])
            return key, amount
    except:
        return None, None
    return None, None

def add_row(key, amount):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if key == "РФ":
        row = [amount, 0, 0, now_str]
    elif key == "МИР":
        row = [0, amount, 0, now_str]
    elif key == "КО":
        row = [0, 0, amount, now_str]
    else:
        return False
    sheet.append_row(row)
    return True

def get_sums_by_date_range(start_date, end_date):
    try:
        records = sheet.get_all_records()
    except Exception:
        return 0,0,0
    sum_rf = 0
    sum_mir = 0
    sum_ko = 0
    for rec in records:
        dt_str = rec.get('Дата и время', '')
        if dt_str:
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").date()
                if start_date <= dt <= end_date:
                    sum_rf += int(rec.get('РФ', 0) or 0)
                    sum_mir += int(rec.get('МИР', 0) or 0)
                    sum_ko += int(rec.get('КО', 0) or 0)
            except:
                continue
    return sum_rf, sum_mir, sum_ko

def get_today_sums():
    today = date.today()
    return get_sums_by_date_range(today, today)

def get_week_sums():
    today = date.today()
    start = today - timedelta(days=today.weekday())  # Понедельник этой недели
    end = start + timedelta(days=6)  # Воскресенье
    return get_sums_by_date_range(start, end)

def get_month_sums():
    today = date.today()
    start = today.replace(day=1)
    # конец месяца: следующий месяц первый день -1
    if today.month == 12:
        next_month = today.replace(year=today.year+1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month+1, day=1)
    end = next_month - timedelta(days=1)
    return get_sums_by_date_range(start, end)

@bot.message_handler(commands=['start'])
def start_handler(message):
    welcome_text = (
        "Привет! Я бот для записи данных в Google Sheets.\n\n"
        "Доступные команды:\n"
        "/today — итоги за сегодня\n"
        "/week — итоги за неделю\n"
        "/month — итоги за месяц\n"
        "/last — последняя запись\n"
        "/delete — удалить последнюю запись\n\n"
        "Или просто отправляй сообщения в формате:\n"
        "РФ 5, МИР 3, КО 4 и т.д."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=make_keyboard())

@bot.message_handler(commands=['today'])
def today_handler(message):
    sum_rf, sum_mir, sum_ko = get_today_sums()
    bot.send_message(message.chat.id, f"Итоги за сегодня:\nРФ: {sum_rf}\nМИР: {sum_mir}\nКО: {sum_ko}")

@bot.message_handler(commands=['week'])
def week_handler(message):
    sum_rf, sum_mir, sum_ko = get_week_sums()
    bot.send_message(message.chat.id, f"Итоги за эту неделю:\nРФ: {sum_rf}\nМИР: {sum_mir}\nКО: {sum_ko}")

@bot.message_handler(commands=['month'])
def month_handler(message):
    sum_rf, sum_mir, sum_ko = get_month_sums()
    bot.send_message(message.chat.id, f"Итоги за этот месяц:\nРФ: {sum_rf}\nМИР: {sum_mir}\nКО: {sum_ko}")

@bot.message_handler(commands=['last'])
def last_handler(message):
    try:
        all_values = sheet.get_all_values()
        if len(all_values) <= 1:
            bot.send_message(message.chat.id, "Нет записей в таблице.")
            return
        last_row = all_values[-1]
        text = (
            f"Последняя запись:\n"
            f"РФ: {last_row[0]}\n"
            f"МИР: {last_row[1]}\n"
            f"КО: {last_row[2]}\n"
            f"Дата и время: {last_row[3]}"
        )
        bot.send_message(message.chat.id, text)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при получении последней записи: {e}")

@bot.message_handler(commands=['delete'])
def delete_handler(message):
    try:
        rows = len(sheet.get_all_values())
        if rows > 1:
            sheet.delete_rows(rows)
            bot.send_message(message.chat.id, "Последняя запись удалена.")
        else:
            bot.send_message(message.chat.id, "Нет записей для удаления.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при удалении: {e}")

@bot.message_handler(func=lambda message: True)
def all_message_handler(message):
    key, amount = parse_message(message.text)
    if key and amount:
        if add_row(key, amount):
            bot.send_message(message.chat.id, f"Записано: {key} = {amount}")
        else:
            bot.send_message(message.chat.id, "Неверный формат данных.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте сообщение в формате: РФ 5 или МИР 3 или КО 4")

if __name__ == '__main__':
    print("Бот запущен")
    bot.polling(none_stop=True) 


