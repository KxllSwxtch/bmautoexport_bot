import locale
import threading

from telebot import types
from calculator import (
    calculate_cost,
    get_currency_rates,
    show_country_selection,
    get_nbk_currency_rates,
    get_nbkr_currency_rates,
    calculate_cost_manual,
)
from config import bot


# Переменные
user_data = {}
current_country = "Russia"
current_car_type = "sedan"

# Set locale for number formatting
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")


# Обработчик callback
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    global current_car_type, current_country

    user_id = call.message.chat.id

    if call.data == "calculate_another":
        # Сбрасываем данные пользователя
        user_data[user_id] = {}
        current_country = None
        current_car_type = None

        show_country_selection(user_id)
    elif call.data in ["sedan", "crossover"]:
        handle_car_type_selection(call)

    elif call.data == "main_menu":
        main_menu(call.message)


# Функция для установки команд меню
def set_bot_commands():
    commands = [
        types.BotCommand("start", "Запустить бота"),
        types.BotCommand("cbr", "Курс ЦБ Российской Федерации"),
        types.BotCommand("nbk", "Курс Национального Банка Республики Казахстан"),
        types.BotCommand("nbkr", "Курс Национального Банка Республики Кыргызстан"),
    ]
    bot.set_my_commands(commands)


@bot.message_handler(commands=["nbkr"])
def nbkr_command(message):
    try:
        rates_text = get_nbkr_currency_rates()

        # Создаем клавиатуру с кнопкой для расчета автомобиля
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                "🔍 Рассчитать стоимость автомобиля", callback_data="calculate_another"
            )
        )

        # Отправляем сообщение с курсами и клавиатурой
        bot.send_message(message.chat.id, rates_text, reply_markup=keyboard)
    except Exception as e:
        bot.send_message(
            message.chat.id, "Не удалось получить курсы валют. Попробуйте позже."
        )
        print(f"Ошибка при получении курсов валют: {e}")


@bot.message_handler(commands=["nbk"])
def nbk_command(message):
    try:
        rates_text = get_nbk_currency_rates()

        # Создаем клавиатуру с кнопкой для расчета автомобиля
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                "🔍 Рассчитать стоимость автомобиля", callback_data="calculate_another"
            )
        )

        # Отправляем сообщение с курсами и клавиатурой
        bot.send_message(message.chat.id, rates_text, reply_markup=keyboard)
    except Exception as e:
        bot.send_message(
            message.chat.id, "Не удалось получить курсы валют. Попробуйте позже."
        )
        print(f"Ошибка при получении курсов валют: {e}")


@bot.message_handler(commands=["cbr"])
def cbr_command(message):
    try:
        rates_text = get_currency_rates()

        # Создаем клавиатуру с кнопкой для расчета автомобиля
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                "🔍 Рассчитать стоимость автомобиля", callback_data="calculate_another"
            )
        )

        # Отправляем сообщение с курсами и клавиатурой
        bot.send_message(message.chat.id, rates_text, reply_markup=keyboard)
    except Exception as e:
        bot.send_message(
            message.chat.id, "Не удалось получить курсы валют. Попробуйте позже."
        )
        print(f"Ошибка при получении курсов валют: {e}")


# Самый старт
@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.first_name

    # Приветственное сообщение
    greeting = f"👋 Здравствуйте, {user_name}!\n Я бот компании BMAutoExport для расчета стоимости авто из Южной Кореи до стран СНГ! 🚗 \n\n💰 Пожалуйста, выберите действие из меню ниже:"

    # Создание кнопочного меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_calc = types.KeyboardButton("Расчёт")
    btn_instagram = types.KeyboardButton("Instagram")
    btn_whatsapp = types.KeyboardButton("WhatsApp")
    btn_telegram = types.KeyboardButton("Telegram-канал")
    btn_manager = types.KeyboardButton("Написать менеджеру")

    # Добавление кнопок в меню
    markup.add(btn_calc, btn_instagram, btn_whatsapp, btn_telegram, btn_manager)

    # Отправка приветствия с кнопочным меню
    bot.send_message(message.chat.id, greeting, reply_markup=markup)


# Главное меню
@bot.message_handler(func=lambda message: message.text == "Вернуться в главное меню")
def main_menu(message):
    user_id = message.chat.id

    user_data[user_id] = {}

    # Приветственное сообщение
    user_name = message.from_user.first_name
    greeting = f"Здравствуйте, {user_name}!\n Я бот компании Glory Traders для расчета стоимости авто из Южной Кореи до стран СНГ! 🚗 \n\n💰 Пожалуйста, выберите действие из меню ниже:"

    # Создание кнопочного меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_calc = types.KeyboardButton("Расчёт")
    btn_instagram = types.KeyboardButton("Instagram")
    btn_whatsapp = types.KeyboardButton("WhatsApp")
    btn_telegram = types.KeyboardButton("Telegram-канал")
    btn_manager = types.KeyboardButton("Написать менеджеру")

    # Добавление кнопок в меню
    markup.add(btn_calc, btn_instagram, btn_whatsapp, btn_telegram, btn_manager)

    # Отправка приветствия с кнопочным меню
    bot.send_message(message.chat.id, greeting, reply_markup=markup)


# Выбор страны для расчёта
@bot.message_handler(func=lambda message: message.text in ["Расчёт", "Изменить страну"])
def handle_calculation(message):
    show_country_selection(message.chat.id)


# Расчёт по ссылке с encar
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def process_encar_link(message):
    # Проверяем, выбрана ли страна
    if message.chat.id not in user_data or "country" not in user_data[message.chat.id]:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, выберите страну из меню перед отправкой ссылки на автомобиль.",
        )
        return

    # Проверяем, что ссылка содержит encar.com или fem.encar.com
    if "encar.com" not in message.text or "fem.encar.com" not in message.text:
        bot.send_message(
            message.chat.id,
            "🚫 Введите корректную ссылку с encar.com",
        )
        return

    # Получаем выбранную страну
    country = user_data[message.chat.id]["country"]

    # Отправляем сообщение о начале обработки
    processing_message = bot.send_message(message.chat.id, "⏳ Обработка данных...")

    # Пытаемся рассчитать стоимость
    try:
        calculate_cost(country, message)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "🚫 Произошла ошибка при расчёте. Пожалуйста, попробуйте снова.",
        )
        print(f"Ошибка при расчёте: {e}")
    finally:
        # Удаляем сообщение о процессе
        bot.delete_message(message.chat.id, processing_message.message_id)


@bot.message_handler(func=lambda message: message.text == "По ссылке с encar")
def handle_link_input(message):
    bot.send_message(
        message.chat.id,
        "Отправьте ссылку на автомобиль с сайта encar.com или мобильного приложения Encar.",
    )


# Ручной расчёт
@bot.message_handler(func=lambda message: message.text == "Ручной ввод")
def handle_manual_input(message):
    user_data[message.chat.id] = {"step": "year"}
    bot.send_message(
        message.chat.id,
        "📅 Укажите год выпуска автомобиля (например: 2022):",
    )


@bot.message_handler(
    func=lambda message: message.chat.id in user_data
    and "step" in user_data[message.chat.id]
)
def process_manual_input(message):
    global current_country, current_car_type

    user_id = message.chat.id

    # Проверка, если шаг - выбор типа кузова
    if user_data[user_id].get("step") == "car_type":
        if message.text.lower() in ["седан", "кроссовер"]:
            current_car_type = (
                "sedan" if message.text.lower() == "седан" else "crossover"
            )
            user_data[user_id]["step"] = None

            # Получаем данные для расчёта
            year = user_data[user_id]["year"]
            month = user_data[user_id]["month"]
            engine_volume = user_data[user_id]["engine_volume"]
            price = user_data[user_id]["price"]

            # Выполняем расчёт стоимости
            calculate_manual_cost(
                message,
                year,
                month,
                engine_volume,
                price,
                current_country,
                current_car_type,
            )
        else:
            bot.send_message(
                user_id,
                "🚫 Пожалуйста, выберите корректный тип кузова: Седан или Кроссовер.",
            )
        return

    # Далее логика обработки остальных шагов
    step = user_data[user_id].get("step")

    if step == "year":
        if message.text.isdigit() and 1900 <= int(message.text) <= 2025:
            user_data[user_id]["year"] = int(message.text)
            user_data[user_id]["step"] = "month"
            bot.send_message(
                user_id,
                "📅 Укажите месяц выпуска автомобиля (например: 8 для августа):",
            )
        else:
            bot.send_message(
                user_id,
                "🚫 Пожалуйста, введите корректный год (например: 2022).",
            )

    elif step == "month":
        try:
            month = int(message.text)
            if 1 <= month <= 12:
                user_data[user_id]["month"] = month
                user_data[user_id]["step"] = "engine_volume"
                bot.send_message(
                    user_id,
                    "🔧 Укажите объём двигателя в куб. см (например: 2497):",
                )
            else:
                bot.send_message(
                    user_id,
                    "🚫 Пожалуйста, введите корректный месяц (от 1 до 12).",
                )
        except ValueError:
            bot.send_message(
                user_id,
                "🚫 Пожалуйста, введите корректный месяц (от 1 до 12).",
            )

    elif step == "engine_volume":
        if message.text.isdigit() and int(message.text) > 0:
            user_data[user_id]["engine_volume"] = int(message.text)
            user_data[user_id]["step"] = "price"
            bot.send_message(
                user_id,
                "💰 Укажите цену автомобиля в Корее (в вонах) (например: 25000000):",
            )
        else:
            bot.send_message(
                user_id,
                "🚫 Пожалуйста, введите корректный объём двигателя (например: 2497).",
            )

    elif step == "price":
        if message.text.isdigit() and int(message.text) > 0:
            user_data[user_id]["price"] = int(message.text)

            # Если страна — Кыргызстан, запрашиваем тип кузова
            if current_country == "Kyrgyzstan":
                user_data[user_id]["step"] = "car_type"

                # Создаем клавиатуру с кнопками для выбора типа кузова
                keyboard = types.ReplyKeyboardMarkup(
                    resize_keyboard=True, one_time_keyboard=True
                )
                keyboard.add("Седан", "Кроссовер")

                bot.send_message(
                    user_id,
                    "Пожалуйста, выберите тип кузова автомобиля:",
                    reply_markup=keyboard,
                )
            else:
                user_data[user_id]["step"] = None
                year = user_data[user_id]["year"]
                month = user_data[user_id]["month"]
                engine_volume = user_data[user_id]["engine_volume"]
                price = user_data[user_id]["price"]
                calculate_manual_cost(
                    message, year, month, engine_volume, price, current_country
                )
        else:
            bot.send_message(
                user_id,
                "🚫 Пожалуйста, введите корректную цену (например: 25000000).",
            )


# Обработка выбора типа кузова
def handle_car_type_selection(call):
    global current_car_type, current_country

    user_id = call.message.chat.id

    # Сохраняем выбранный тип кузова
    current_car_type = call.data
    user_data[user_id]["step"] = None

    # Получаем данные для расчёта
    year = user_data[user_id]["year"]
    month = user_data[user_id]["month"]
    engine_volume = user_data[user_id]["engine_volume"]
    price = user_data[user_id]["price"]

    # Выполняем расчёт стоимости
    calculate_manual_cost(
        call.message,
        year,
        month,
        engine_volume,
        price,
        current_country,
        current_car_type,
    )


def calculate_manual_cost(
    message, year, month, engine_volume, price, country, car_type=None
):
    global current_car_type, current_country

    try:
        # Вызываем функцию расчёта стоимости из calculator.py
        result_message = calculate_cost_manual(
            country, year, month, engine_volume, price, car_type
        )

        # Создаём клавиатуру с кнопками
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                "Рассчитать стоимость другого автомобиля",
                callback_data="calculate_another",
            )
        )
        keyboard.add(
            types.InlineKeyboardButton(
                "Вернуться в главное меню", callback_data="main_menu"
            )
        )

        # Отправляем сообщение с результатом и клавиатурой
        bot.send_message(
            message.chat.id, result_message, parse_mode="HTML", reply_markup=keyboard
        )

        # Сбрасываем данные пользователя
        user_id = message.chat.id
        user_data[user_id] = {}
        current_country = None
        current_car_type = None

    except Exception as e:
        bot.send_message(
            message.chat.id,
            "🚫 Произошла ошибка при расчёте. Попробуйте снова.",
        )
        print(f"Ошибка при расчёте: {e}")


def show_calculation_options(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_link = types.KeyboardButton("По ссылке с encar")
    btn_manual = types.KeyboardButton("Ручной ввод")
    btn_main_menu = types.KeyboardButton("Вернуться в главное меню")
    markup.add(btn_link, btn_manual, btn_main_menu)

    bot.send_message(chat_id, "Выберите способ расчёта:", reply_markup=markup)


###############
# РОССИЯ НАЧАЛО
###############
@bot.message_handler(func=lambda message: message.text == "🇷🇺 Россия")
def handle_russia(message):
    global current_country

    current_country = "Russia"
    user_data[message.chat.id] = {"country": "Russia"}
    print(f"Сохранена страна: {user_data[message.chat.id]['country']}")  # Логирование
    show_calculation_options(message.chat.id)


###############
# РОССИЯ КОНЕЦ
###############


##############
# КАЗАХСТАН НАЧАЛО
##############
@bot.message_handler(func=lambda message: message.text == "🇰🇿 Казахстан")
def handle_kazakhstan(message):
    global current_country
    current_country = "Kazakhstan"
    user_data[message.chat.id] = {"country": "Kazakhstan"}
    print(f"Сохранена страна: {user_data[message.chat.id]['country']}")  # Логирование
    show_calculation_options(message.chat.id)


##############
# КАЗАХСТАН КОНЕЦ
##############


##############
# КЫРГЫЗСТАН НАЧАЛО
##############
@bot.message_handler(func=lambda message: message.text == "🇰🇬 Кыргызстан")
def handle_kyrgyzstan(message):
    global current_country

    current_country = "Kyrgyzstan"
    user_data[message.chat.id] = {"country": "Kyrgyzstan"}
    print(f"Сохранена страна: {user_data[message.chat.id]['country']}")  # Логирование
    show_calculation_options(message.chat.id)


##############
# КЫРГЫЗСТАН КОНЕЦ
##############


# Обработчики для других кнопок
@bot.message_handler(func=lambda message: message.text == "Instagram")
def handle_instagram(message):
    bot.send_message(
        message.chat.id,
        "Наш Instagram: https://www.instagram.com/big.motors.export",
    )


@bot.message_handler(func=lambda message: message.text == "WhatsApp")
def handle_whatsapp(message):
    bot.send_message(
        message.chat.id, "Напишите нам в WhatsApp: https://wa.me/821075834466"
    )


@bot.message_handler(func=lambda message: message.text == "Telegram-канал")
def handle_telegram_channel(message):
    bot.send_message(
        message.chat.id,
        "Наш Telegram-канал: https://t.me/GLORYTRADERS",
    )


@bot.message_handler(func=lambda message: message.text == "Написать менеджеру")
def handle_manager(message):
    bot.send_message(message.chat.id, "Напишите нам напрямую: @GLORY_TRADERS")


def run_in_thread(target):
    """Запуск функции в отдельном потоке"""
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    # Запуск длительных задач в отдельных потоках
    run_in_thread(set_bot_commands)
    run_in_thread(get_nbkr_currency_rates)
    run_in_thread(get_nbk_currency_rates)
    run_in_thread(get_currency_rates)

    # Основной поток выполняет бот
    bot.polling(none_stop=True, timeout=60, long_polling_timeout=20)
