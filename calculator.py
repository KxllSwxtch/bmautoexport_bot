import pickle
import os
import re
import requests
import time
import logging

from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from dotenv import load_dotenv
from telebot import types
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoAlertPresentException

# utils.py import
from config import bot
from utils import calculate_age, format_number


load_dotenv()

CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH_LOCAL")
COOKIES_FILE = "cookies.pkl"

# Переменные
car_data = {}
car_id_external = None
usd_rate = 0


# Функция для отправки меню выбора страны
def show_country_selection(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_russia = types.KeyboardButton("🇷🇺 Россия")
    btn_kazakhstan = types.KeyboardButton("🇰🇿 Казахстан")
    btn_kyrgyzstan = types.KeyboardButton("🇰🇬 Кыргызстан")

    # Добавление кнопок в меню
    markup.add(btn_russia, btn_kazakhstan, btn_kyrgyzstan)

    # Отправка сообщения с меню выбора страны
    bot.send_message(
        chat_id, "Пожалуйста, выберите страну для расчёта:", reply_markup=markup
    )


def get_currency_rates():
    global usd_rate

    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    response = requests.get(url)
    data = response.json()

    # Получаем курсы валют
    eur_rate = data["Valute"]["EUR"]["Value"]
    usd_rate = data["Valute"]["USD"]["Value"]
    krw_rate = data["Valute"]["KRW"]["Value"] / data["Valute"]["KRW"]["Nominal"]
    cny_rate = data["Valute"]["CNY"]["Value"]

    # Форматируем текст
    rates_text = (
        f"Курс валют ЦБ:\n\n"
        f"EUR {eur_rate:.4f} ₽\n"
        f"USD {usd_rate:.4f} ₽\n"
        f"KRW {krw_rate:.4f} ₽\n"
        f"CNY {cny_rate:.4f} ₽"
    )

    return rates_text


def save_cookies(driver):
    with open(COOKIES_FILE, "wb") as file:
        pickle.dump(driver.get_cookies(), file)


# Load cookies from file
def load_cookies(driver):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)


def send_error_message(message, error_text):
    global last_error_message_id

    # Remove previous error message if it exists
    if last_error_message_id.get(message.chat.id):
        try:
            bot.delete_message(message.chat.id, last_error_message_id[message.chat.id])
        except Exception as e:
            logging.error(f"Error deleting message: {e}")

    # Send new error message and store its ID
    error_message = bot.reply_to(message, error_text)
    last_error_message_id[message.chat.id] = error_message.id
    logging.error(f"Error sent to user {message.chat.id}: {error_text}")


def check_and_handle_alert(driver):
    try:
        WebDriverWait(driver, 4).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"Обнаружено всплывающее окно: {alert.text}")
        alert.accept()  # Закрывает alert
        print("Всплывающее окно было закрыто.")
    except TimeoutException:
        print("Нет активного всплывающего окна.")
    except Exception as alert_exception:
        print(f"Ошибка при обработке alert: {alert_exception}")


def get_car_info(url):
    global car_id_external

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")  # Необходим для работы в Heroku
    chrome_options.add_argument("--disable-dev-shm-usage")  # Решает проблемы с памятью
    chrome_options.add_argument("--window-size=1920,1080")  # Устанавливает размер окна
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")  # Уровень логирования
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    )

    # Инициализация драйвера
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Загружаем страницу
        driver.get(url)
        check_and_handle_alert(driver)  # Обработка alert, если присутствует
        load_cookies(driver)

        # Проверка на reCAPTCHA
        if "reCAPTCHA" in driver.page_source:
            logging.info("Обнаружена reCAPTCHA. Пытаемся решить...")
            driver.refresh()
            logging.info("Страница обновлена после reCAPTCHA.")
            check_and_handle_alert(driver)  # Перепроверка после обновления страницы

        save_cookies(driver)
        logging.info("Куки сохранены.")

        # Парсим URL для получения carid
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        car_id = query_params.get("carid", [None])[0]
        car_id_external = car_id

        # Проверка элемента areaLeaseRent
        try:
            lease_area = driver.find_element(By.ID, "areaLeaseRent")
            title_element = lease_area.find_element(By.CLASS_NAME, "title")

            if "리스정보" in title_element.text or "렌트정보" in title_element.text:
                logging.info("Данная машина находится в лизинге.")
                return [
                    "",
                    "Данная машина находится в лизинге. Свяжитесь с менеджером.",
                ]
        except NoSuchElementException:
            logging.warning("Элемент areaLeaseRent не найден.")

        # Инициализация переменных
        car_title, car_date, car_engine_capacity, car_price = "", "", "", ""

        # Проверка элемента product_left
        try:
            product_left = WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product_left"))
            )
            product_left_splitted = product_left.text.split("\n")

            car_title = product_left.find_element(
                By.CLASS_NAME, "prod_name"
            ).text.strip()

            car_date = (
                product_left_splitted[3] if len(product_left_splitted) > 3 else ""
            )
            car_engine_capacity = (
                product_left_splitted[6] if len(product_left_splitted) > 6 else ""
            )
            car_price = re.sub(r"\D", "", product_left_splitted[1])

            # Форматирование
            formatted_price = car_price.replace(",", "")
            formatted_engine_capacity = (
                car_engine_capacity.replace(",", "")[:-2]
                if car_engine_capacity
                else "0"
            )
            cleaned_date = "".join(filter(str.isdigit, car_date))
            formatted_date = (
                f"01{cleaned_date[2:4]}{cleaned_date[:2]}" if cleaned_date else "010101"
            )

            # Создание URL
            new_url = f"https://plugin-back-versusm.amvera.io/car-ab-korea/{car_id}?price={formatted_price}&date={formatted_date}&volume={formatted_engine_capacity}"
            logging.info(f"Данные о машине получены: {new_url}, {car_title}")
            return [new_url, car_title]
        except NoSuchElementException as e:
            logging.error(f"Ошибка при обработке product_left: {e}")
        except Exception as e:
            logging.error(f"Неизвестная ошибка при обработке product_left: {e}")

        # Проверка элемента gallery_photo
        try:
            gallery_element = driver.find_element(By.CSS_SELECTOR, "div.gallery_photo")
            car_title = gallery_element.find_element(By.CLASS_NAME, "prod_name").text

            items = gallery_element.find_elements(By.XPATH, ".//*")
            if len(items) > 10:
                car_date = items[10].text
            if len(items) > 18:
                car_engine_capacity = items[18].text

            # Извлечение информации о ключах
            try:
                keyinfo_element = driver.find_element(
                    By.CSS_SELECTOR, "div.wrap_keyinfo"
                )
                keyinfo_items = keyinfo_element.find_elements(By.XPATH, ".//*")
                keyinfo_texts = [
                    item.text for item in keyinfo_items if item.text.strip()
                ]

                # Извлекаем цену, если элемент существует
                car_price = (
                    re.sub(r"\D", "", keyinfo_texts[12])
                    if len(keyinfo_texts) > 12
                    else None
                )
            except NoSuchElementException:
                logging.warning("Элемент wrap_keyinfo не найден.")
        except NoSuchElementException:
            logging.warning("Элемент gallery_photo также не найден.")

        # Форматирование значений для URL
        if car_price:
            formatted_price = car_price.replace(",", "")
        else:
            formatted_price = "0"  # Задаем значение по умолчанию

        formatted_engine_capacity = (
            car_engine_capacity.replace(",", "")[:-2] if car_engine_capacity else "0"
        )
        cleaned_date = "".join(filter(str.isdigit, car_date))
        formatted_date = (
            f"01{cleaned_date[2:4]}{cleaned_date[:2]}" if cleaned_date else "010101"
        )

        # Конечный URL
        new_url = f"https://plugin-back-versusm.amvera.io/car-ab-korea/{car_id}?price={formatted_price}&date={formatted_date}&volume={formatted_engine_capacity}"

        logging.info(f"Данные о машине получены: {new_url}, {car_title}")
        return [new_url, car_title]

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        return None, None

    finally:
        # Обработка всплывающих окон (alerts)
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
            logging.info("Всплывающее окно отклонено.")
        except NoAlertPresentException:
            logging.info("Нет активного всплывающего окна.")
        except Exception as alert_exception:
            logging.error(f"Ошибка при обработке alert: {alert_exception}")

        driver.quit()


def calculate_car_cost(country, message):
    global car_data

    link = message.text

    # Russia
    if country == "Russia":
        if link:
            print("\n\n#################")
            print("НОВЫЙ ЗАПРОС")
            print("#################\n\n")

            # Check if the link is from the mobile version
            if "fem.encar.com" in link:
                # Extract all digits from the mobile link
                car_id_match = re.findall(r"\d+", link)
                if car_id_match:
                    car_id = car_id_match[0]  # Use the first match of digits
                    # Create the new URL
                    link = (
                        f"https://www.encar.com/dc/dc_cardetailview.do?carid={car_id}"
                    )
                else:
                    send_error_message(
                        message, "🚫 Не удалось извлечь carid из ссылки."
                    )
                    return

            # Get car info and new URL
            result = get_car_info(link)
            time.sleep(5)

            if result is None:
                send_error_message(
                    message,
                    "🚫 Произошла ошибка при получении данных. Проверьте ссылку и попробуйте снова.",
                )
                return

            new_url, car_title = result

            # Проверка на наличие информации о лизинге
            if not new_url and car_title:
                # Inline buttons for further actions
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton(
                        "Написать менеджеру", url="https://t.me/manager"
                    ),
                )
                keyboard.add(
                    types.InlineKeyboardButton(
                        "Рассчитать стоимость другого автомобиля",
                        callback_data="calculate_another",
                    ),
                )
                bot.send_message(
                    message.chat.id,
                    car_title,  # сообщение что машина лизинговая
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
                return  # Завершаем функцию, чтобы избежать дальнейшей обработки

            if new_url:
                response = requests.get(new_url)

                if response.status_code == 200:
                    json_response = response.json()
                    car_data = json_response

                    # Extract year from the car date string
                    year = json_response.get("result")["car"]["date"].split()[-1]
                    engine_volume = json_response.get("result")["car"]["engineVolume"]
                    price = json_response.get("result")["price"]["car"]["krw"]

                    if year and engine_volume and price:
                        engine_volume_formatted = (
                            f"{format_number(int(engine_volume))} cc"
                        )
                        age_formatted = calculate_age(year)

                        # Car's price in KRW
                        price_formatted = format_number(price)

                        # Price in USD
                        total_cost_rub = json_response.get("result")["price"][
                            "grandTotal"
                        ]

                        result_message = (
                            f"Возраст: {age_formatted}\n"
                            f"Стоимость: {price_formatted} KRW\n"
                            f"Объём двигателя: {engine_volume_formatted}\n\n"
                            f"Стоимость автомобиля под ключ до Владивостока: \n**{format_number(total_cost_rub)}₽**\n\n"
                            f"🔗 [Ссылка на автомобиль]({link})\n\n"
                            "Если данное авто попадает под санкции, пожалуйста уточните возможность отправки в вашу страну у менеджера @MANAGER\n\n"
                            "🔗[Официальный телеграм канал](https://t.me/telegram_channel)\n"
                        )

                        bot.send_message(
                            message.chat.id, result_message, parse_mode="Markdown"
                        )

                        # Inline buttons for further actions
                        keyboard = types.InlineKeyboardMarkup()
                        keyboard.add(
                            types.InlineKeyboardButton(
                                "Детализация расчёта", callback_data="detail"
                            ),
                        )
                        keyboard.add(
                            types.InlineKeyboardButton(
                                "Технический отчёт об автомобиле",
                                callback_data="technical_report",
                            ),
                        )
                        keyboard.add(
                            types.InlineKeyboardButton(
                                "Связаться с менеджером", url="https://t.me/alekseyan85"
                            ),
                        )
                        keyboard.add(
                            types.InlineKeyboardButton(
                                "Рассчитать стоимость другого автомобиля",
                                callback_data="calculate_another",
                            ),
                        )

                        bot.send_message(
                            message.chat.id, "Что делаем дальше?", reply_markup=keyboard
                        )
                    else:
                        bot.send_message(
                            message.chat.id,
                            "🚫 Не удалось извлечь все необходимые данные. Проверьте ссылку.",
                        )
                else:
                    send_error_message(
                        message,
                        "🚫 Произошла ошибка при получении данных. Проверьте ссылку и попробуйте снова.",
                    )
            else:
                send_error_message(
                    message,
                    "🚫 Произошла ошибка при получении данных. Проверьте ссылку и попробуйте снова.",
                )
        else:
            return f"Стоимость доставки и растаможки для России по введённым данным {car_data} составляет 400,000 рублей."

    ############
    # Kazakhstan
    ############
    elif country == "Kazakhstan":
        if "encar" in car_data:
            return f"Стоимость доставки и растаможки для Казахстана по ссылке {car_data} составляет 450,000 тенге."
        else:
            return f"Стоимость доставки и растаможки для Казахстана по введённым данным {car_data} составляет 380,000 тенге."

    ############
    # Kyrgyzstan
    ############
    elif country == "Kyrgyzstan":
        if "encar" in car_data:
            return f"Стоимость доставки и растаможки для Кыргызстана по ссылке {car_data} составляет 300,000 сом."
        else:
            return f"Стоимость доставки и растаможки для Кыргызстана по введённым данным {car_data} составляет 250,000 сом."

    else:
        return "Извините, мы не можем рассчитать стоимость для выбранной страны."


def get_insurance_total():
    print("\n\n####################")
    print("[ЗАПРОС] ТЕХНИЧЕСКИЙ ОТЧËТ ОБ АВТОМОБИЛЕ")
    print("####################\n\n")

    global car_id_external

    # Настройка WebDriver с нужными опциями
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    service = Service(CHROMEDRIVER_PATH)

    # Формируем URL
    url = f"https://fem.encar.com/cars/report/accident/{car_id_external}"

    try:
        # Запускаем WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)

        # Пробуем найти элемент 'smlist' без явного ожидания
        time.sleep(2)
        try:
            report_accident_summary_element = WebDriverWait(driver, 6).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "ReportAccidentSummary_list_accident__q6vLx")
                )
            )
        except NoSuchElementException:
            print("Элемент 'ReportAccidentSummary_list_accident__q6vLx' не найден.")
            return ["Нет данных", "Нет данных"]

        report_accident_summary_element_splitted = (
            report_accident_summary_element.text.split("\n")
        )

        # Извлекаем данные
        damage_to_my_car = (
            report_accident_summary_element_splitted[4]
            if len(report_accident_summary_element.text) > 4
            else "0"
        )
        damage_to_other_car = (
            report_accident_summary_element_splitted[5]
            if len(report_accident_summary_element.text) > 5
            else "0"
        )

        # Упрощенная функция для извлечения числа
        def extract_large_number(damage_text):
            if "없음" in damage_text:
                return "0"
            numbers = re.findall(r"[\d,]+(?=\s*원)", damage_text)
            return numbers[0] if numbers else "0"

        # Форматируем данные
        damage_to_my_car_formatted = extract_large_number(damage_to_my_car)
        damage_to_other_car_formatted = extract_large_number(damage_to_other_car)

        return [damage_to_my_car_formatted, damage_to_other_car_formatted]

    except Exception as e:
        print(f"Произошла ошибка при получении данных: {e}")
        return ["Ошибка при получении данных", ""]

    finally:
        driver.quit()


# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    global car_data, car_id_external

    if call.data.startswith("detail"):
        print("\n\n####################")
        print("[ЗАПРОС] ДЕТАЛИЗАЦИЯ РАСЧËТА")
        print("####################\n\n")

        details = {
            "car_price_korea": car_data.get("result")["price"]["car"]["rub"],
            "dealer_fee": car_data.get("result")["price"]["korea"]["ab"]["rub"],
            "korea_logistics": car_data.get("result")["price"]["korea"]["logistic"][
                "rub"
            ],
            "customs_fee": car_data.get("result")["price"]["korea"]["dutyCleaning"][
                "rub"
            ],
            "delivery_fee": car_data.get("result")["price"]["korea"]["delivery"]["rub"],
            "dealer_commission": car_data.get("result")["price"]["korea"][
                "dealerCommission"
            ]["rub"],
            "russiaDuty": car_data.get("result")["price"]["russian"]["duty"]["rub"],
            "recycle_fee": car_data.get("result")["price"]["russian"]["recyclingFee"][
                "rub"
            ],
            "registration": car_data.get("result")["price"]["russian"]["registration"][
                "rub"
            ],
            "sbkts": car_data.get("result")["price"]["russian"]["sbkts"]["rub"],
            "svhAndExpertise": car_data.get("result")["price"]["russian"][
                "svhAndExpertise"
            ]["rub"],
            "delivery": car_data.get("result")["price"]["russian"]["delivery"]["rub"],
        }

        car_price_formatted = format_number(details["car_price_korea"])
        dealer_fee_formatted = format_number(details["dealer_fee"])
        korea_logistics_formatted = format_number(details["korea_logistics"])
        delivery_fee_formatted = format_number(details["delivery_fee"])
        dealer_commission_formatted = format_number(details["dealer_commission"])
        russia_duty_formatted = format_number(details["russiaDuty"])
        registration_formatted = format_number(details["registration"])
        sbkts_formatted = format_number(details["sbkts"])
        svh_expertise_formatted = format_number(details["svhAndExpertise"])

        # Construct cost breakdown message
        detail_message = (
            "📝 Детализация расчёта:\n\n"
            f"Стоимость авто: <b>{car_price_formatted}₽</b>\n\n"
            f"Услуги BMAutoExport: <b>{dealer_fee_formatted}₽</b>\n\n"
            f"Логистика по Южной Корее: <b>{korea_logistics_formatted}₽</b>\n\n"
            f"Доставка до Владивостока: <b>{delivery_fee_formatted}₽</b>\n\n"
            f"Комиссия дилера: <b>{dealer_commission_formatted}₽</b>\n\n"
            f"Единая таможенная ставка (ЕТС): <b>{russia_duty_formatted}₽</b>\n\n"
            f"Оформление: <b>{registration_formatted}₽</b>\n\n"
            f"СБКТС: <b>{sbkts_formatted}₽</b>\n\n"
            f"СВХ + Экспертиза: <b>{svh_expertise_formatted}₽</b>\n\n"
        )

        bot.send_message(call.message.chat.id, detail_message, parse_mode="HTML")

        # Inline buttons for further actions
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                "Рассчитать стоимость другого автомобиля",
                callback_data="calculate_another",
            )
        )
        keyboard.add(
            types.InlineKeyboardButton(
                "Связаться с менеджером", url="https://t.me/MANAGER"
            )
        )

        bot.send_message(
            call.message.chat.id, "Что делаем дальше?", reply_markup=keyboard
        )

    elif call.data == "technical_report":
        # Retrieve insurance information
        insurance_info = get_insurance_total()

        # Проверка на наличие ошибки
        if "Ошибка" in insurance_info[0] or "Ошибка" in insurance_info[1]:
            error_message = (
                "Страховая история недоступна. \n\n"
                f'<a href="https://fem.encar.com/cars/detail/{car_id_external}">🔗 Ссылка на автомобиль 🔗</a>'
            )

            # Inline buttons for further actions
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    "Рассчитать стоимость другого автомобиля",
                    callback_data="calculate_another",
                )
            )
            keyboard.add(
                types.InlineKeyboardButton(
                    "Связаться с менеджером", url="https://t.me/MANAGER"
                )
            )

            # Отправка сообщения об ошибке
            bot.send_message(
                call.message.chat.id,
                error_message,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            current_car_insurance_payments = (
                "0" if len(insurance_info[0]) == 0 else insurance_info[0]
            )
            other_car_insurance_payments = (
                "0" if len(insurance_info[1]) == 0 else insurance_info[1]
            )

            # Construct the message for the technical report
            tech_report_message = (
                f"Страховые выплаты по представленному автомобилю: \n<b>{current_car_insurance_payments} ₩</b>\n\n"
                f"Страховые выплаты другим участникам ДТП: \n<b>{other_car_insurance_payments} ₩</b>\n\n"
                f'<a href="https://fem.encar.com/cars/report/inspect/{car_id_external}">🔗 Ссылка на схему повреждений кузовных элементов 🔗</a>'
            )

            # Inline buttons for further actions
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    "Рассчитать стоимость другого автомобиля",
                    callback_data="calculate_another",
                )
            )
            keyboard.add(
                types.InlineKeyboardButton(
                    "Связаться с менеджером", url="https://t.me/MANAGER"
                )
            )

            bot.send_message(
                call.message.chat.id,
                tech_report_message,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

    elif call.data == "calculate_another":
        # user_data[call.message.chat.id] = {}  # Сброс страны
        show_country_selection(call.message.chat.id)
