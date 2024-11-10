import telebot
from telebot import types
from config import BOT_TOKEN
from calculator import calculate_car_cost

bot = telebot.TeleBot(BOT_TOKEN)

# Переменные
user_data = {}


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


# Обработчик для кнопки "Расчёт"
@bot.message_handler(func=lambda message: message.text == "Расчёт")
def handle_calculation(message):
    # Создание меню выбора страны
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_russia = types.KeyboardButton("🇷🇺 Россия")
    btn_kazakhstan = types.KeyboardButton("🇰🇿 Казахстан")
    btn_kyrgyzstan = types.KeyboardButton("🇰🇬 Кыргзыстан")

    # Добавление кнопок в меню
    markup.add(btn_russia, btn_kazakhstan, btn_kyrgyzstan)

    # Отправка сообщения с меню выбора страны
    bot.send_message(
        message.chat.id, "Пожалуйста, выберите страну для расчёта:", reply_markup=markup
    )


###############
# РОССИЯ НАЧАЛО
###############
# Обработчики для выбора страны
@bot.message_handler(func=lambda message: message.text == "🇷🇺 Россия")
def handle_russia(message):
    user_data[message.chat.id] = {"country": "Russia"}  # Сохраняем страну

    # Создание меню с вариантами расчета
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_link = types.KeyboardButton("Расчёт по ссылке с Encar")
    btn_manual = types.KeyboardButton("Указать данные вручную")

    # Добавление кнопок в меню
    markup.add(btn_link, btn_manual)

    # Отправка сообщения с меню вариантов расчета
    bot.send_message(
        message.chat.id,
        "Вы выбрали расчёт для России. Пожалуйста, выберите способ расчёта:",
        reply_markup=markup,
    )


# Обработчик для варианта "Расчёт по ссылке с Encar"
@bot.message_handler(func=lambda message: message.text == "Расчёт по ссылке с Encar")
def handle_link_calculation(message):
    country = user_data.get(message.chat.id, {}).get("country")
    if country:
        bot.send_message(
            message.chat.id,
            f"Вы выбрали расчёт для {country}. Пожалуйста, отправьте ссылку на автомобиль с сайта или мобильного приложения Encar для расчета.",
        )
    else:
        bot.send_message(
            message.chat.id,
            "Не удалось определить страну. Пожалуйста, выберите страну из меню.",
        )


###############
# РОССИЯ КОНЕЦ
###############


##############
# КАЗАХСТАН НАЧАЛО
##############
@bot.message_handler(func=lambda message: message.text == "🇰🇿 Казахстан")
def handle_kazakhstan(message):
    user_data[message.chat.id] = {"country": "Kazakhstan"}  # Сохраняем страну

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_link = types.KeyboardButton("Расчёт по ссылке с Encar")
    btn_manual = types.KeyboardButton("Указать данные вручную")

    markup.add(btn_link, btn_manual)

    bot.send_message(
        message.chat.id,
        "Вы выбрали расчёт для Казахстана. Пожалуйста, выберите способ расчёта:",
        reply_markup=markup,
    )


##############
# КАЗАХСТАН КОНЕЦ
##############


##############
# КЫРГЫЗСТАН НАЧАЛО
##############
@bot.message_handler(func=lambda message: message.text == "🇰🇬 Кыргзыстан")
def handle_kyrgyzstan(message):
    user_data[message.chat.id] = {"country": "Kyrgyzstan"}  # Сохраняем страну

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_link = types.KeyboardButton("Расчёт по ссылке с Encar")
    btn_manual = types.KeyboardButton("Указать данные вручную")

    markup.add(btn_link, btn_manual)

    bot.send_message(
        message.chat.id,
        "Вы выбрали расчёт для Кыргызстана. Пожалуйста, выберите способ расчёта:",
        reply_markup=markup,
    )


##############
# КЫРГЫЗСТАН КОНЕЦ
##############


# Обработчики для других кнопок
@bot.message_handler(func=lambda message: message.text == "Instagram")
def handle_instagram(message):
    bot.send_message(
        message.chat.id,
        "Наш Instagram: https://www.instagram.com/big.motors.export?igsh=eTF6amRmanV5ZWxq",
    )


@bot.message_handler(func=lambda message: message.text == "WhatsApp")
def handle_whatsapp(message):
    bot.send_message(
        message.chat.id, "Связаться в WhatsApp: https://wa.me/821075834466"
    )


@bot.message_handler(func=lambda message: message.text == "Telegram-канал")
def handle_telegram_channel(message):
    bot.send_message(
        message.chat.id,
        "Подписывайтесь на наш Telegram-канал: https://t.me/your_channel",
    )


@bot.message_handler(func=lambda message: message.text == "Написать менеджеру")
def handle_manager(message):
    bot.send_message(message.chat.id, "Свяжитесь с нашим менеджером: @your_manager")


# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
