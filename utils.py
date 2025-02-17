import requests
import gc
import datetime
import locale
from kgs_customs_table import KGS_CUSTOMS_TABLE


def clean_number(value):
    """Очищает строку от пробелов и преобразует в число"""
    return int(float(value.replace(" ", "").replace(",", ".")))


# Очищение памяти
def clear_memory():
    gc.collect()


def get_customs_fees_russia(
    engine_volume, car_price, car_year, car_month, engine_type=1
):
    """
    Запрашивает расчёт таможенных платежей с сайта calcus.ru.
    :param engine_volume: Объём двигателя (куб. см)
    :param car_price: Цена авто в вонах
    :param car_year: Год выпуска авто
    :param engine_type: Тип двигателя (1 - бензин, 2 - дизель, 3 - гибрид, 4 - электромобиль)
    :return: JSON с результатами расчёта
    """
    url = "https://calcus.ru/calculate/Customs"

    payload = {
        "owner": 1,  # Физлицо
        "age": calculate_age_calcus(car_year, car_month),  # Возрастная категория
        "engine": engine_type,  # Тип двигателя (по умолчанию 1 - бензин)
        "power": 1,  # Лошадиные силы (можно оставить 1)
        "power_unit": 1,  # Тип мощности (1 - л.с.)
        "value": int(engine_volume),  # Объём двигателя
        "price": int(car_price),  # Цена авто в KRW
        "curr": "KRW",  # Валюта
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://calcus.ru/",
        "Origin": "https://calcus.ru",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при запросе к calcus.ru: {e}")
        return None


def calculate_customs_fee_kg(engine_volume, car_year):
    """
    Рассчитывает таможенную пошлину для Кыргызстана на основе таблицы KGS_CUSTOMS_TABLE.

    :param engine_volume: Объём двигателя в см³.
    :param car_year: Год выпуска автомобиля.
    :return: Таможенная пошлина в KGS.
    """

    engine_volume = int(engine_volume)

    # Если год не найден, подбираем ближайший предыдущий год
    while car_year not in KGS_CUSTOMS_TABLE:
        car_year -= 1
        if car_year < min(KGS_CUSTOMS_TABLE.keys()):
            raise ValueError("Год выпуска автомобиля слишком старый для расчёта.")

    year_table = KGS_CUSTOMS_TABLE[car_year]

    # Найти соответствующий диапазон объёма двигателя
    for volume_limit in sorted(year_table.keys()):
        if engine_volume <= volume_limit:
            return year_table[volume_limit]

    # Если объём двигателя превышает все лимиты
    return year_table[max(year_table.keys())]


# Функция для расчёта возраста автомобиля для расчёта утильсбора
def calculate_age_for_utilization_fee(year):
    current_year = datetime.datetime.now().year
    age = current_year - int(year)
    return age


def calculate_duty(price_in_euro, engine_volume, age):
    """
    Рассчитывает таможенную пошлину в зависимости от стоимости автомобиля, объема двигателя и возраста.
    """

    engine_volume = int(engine_volume)

    if age <= 3:
        if price_in_euro <= 8500:
            duty = max(price_in_euro * 0.54, engine_volume * 2.5)
        elif price_in_euro <= 16700:
            duty = max(price_in_euro * 0.48, engine_volume * 3.5)
        elif price_in_euro <= 42300:
            duty = max(price_in_euro * 0.48, engine_volume * 5.5)
        elif price_in_euro <= 84500:
            duty = max(price_in_euro * 0.48, engine_volume * 7.5)
        elif price_in_euro <= 169000:
            duty = max(price_in_euro * 0.48, engine_volume * 15)
        else:
            duty = max(price_in_euro * 0.48, engine_volume * 20)
    else:
        if engine_volume <= 1000:
            duty = engine_volume * 1.5
        elif engine_volume <= 1500:
            duty = engine_volume * 1.7
        elif engine_volume <= 1800:
            duty = engine_volume * 2.5
        elif engine_volume <= 2300:
            duty = engine_volume * 2.7
        elif engine_volume <= 3000:
            duty = engine_volume * 3.0
        else:
            duty = engine_volume * 3.6

    return round(duty, 2)


# Функция для расчёта утилизационного сбора для России
def calculate_utilization_fee(engine_volume: int, year: int) -> int:
    """
    Расчёт утилизационного сбора для физических лиц в России на основе объёма двигателя и года выпуска авто.

    :param engine_volume: Объём двигателя в куб. см (см³).
    :param year: Год выпуска автомобиля.
    :return: Размер утилизационного сбора в рублях.
    """
    base_rate = 3400  # Базовая ставка для физлиц

    # Рассчитываем возраст автомобиля
    age = calculate_age_for_utilization_fee(year)

    # Определяем коэффициент в зависимости от объёма двигателя и возраста авто
    if engine_volume <= 1000:
        coefficient = 1.54 if age <= 3 else 2.82
    elif engine_volume <= 2000:
        coefficient = 3.08 if age <= 3 else 5.56
    elif engine_volume <= 3000:
        coefficient = 4.58 if age <= 3 else 8.69
    elif engine_volume <= 3500:
        coefficient = 6.08 if age <= 3 else 11.49
    else:
        coefficient = 9.12 if age <= 3 else 16.41

    # Расчёт утилизационного сбора
    utilization_fee = round(base_rate * coefficient)
    return utilization_fee


def calculate_age_calcus(year, month):
    """
    Рассчитывает возрастную категорию автомобиля по классификации calcus.ru.

    :param year: Год выпуска автомобиля
    :param month: Месяц выпуска автомобиля
    :return: Возрастная категория ("0-3", "3-5", "5-7", "7-0")
    """
    # Убираем ведущий ноль у месяца, если он есть
    month = int(month.lstrip("0")) if isinstance(month, str) else int(month)

    current_date = datetime.datetime.now()
    car_date = datetime.datetime(year=int(year), month=month, day=1)

    age_in_months = (
        (current_date.year - car_date.year) * 12 + current_date.month - car_date.month
    )

    if age_in_months < 36:
        return "0-3"
    elif 36 <= age_in_months < 60:
        return "3-5"
    elif 60 <= age_in_months < 84:
        return "5-7"
    else:
        return "7-0"


def calculate_age(year, month):
    # Убираем ведущий ноль у месяца, если он есть
    month = int(month.lstrip("0")) if isinstance(month, str) else int(month)

    current_date = datetime.datetime.now()
    car_date = datetime.datetime(year=int(year), month=month, day=1)

    age_in_months = (
        (current_date.year - car_date.year) * 12 + current_date.month - car_date.month
    )

    if age_in_months < 36:
        return f"До 3 лет"
    elif 36 <= age_in_months < 60:
        return f"от 3 до 5 лет"
    else:
        return f"от 5 лет"


def format_number(number):
    number = float(number) if isinstance(number, str) else number
    return locale.format_string("%d", number, grouping=True)


def print_message(message: str):
    print("\n\n#######################")
    print(message)
    print("#######################\n\n")
    return None
