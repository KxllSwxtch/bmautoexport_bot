import gc
import datetime
import locale
from kgs_customs_table import KGS_CUSTOMS_TABLE


# Очищение памяти
def clear_memory():
    gc.collect()


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


def calculate_excise_russia(horse_power):
    """
    Расчет акциза на автомобиль на основе мощности двигателя в л.с.
    """
    if horse_power <= 90:
        return 0
    elif horse_power <= 150:
        return horse_power * 61
    elif horse_power <= 200:
        return horse_power * 583
    elif horse_power <= 300:
        return horse_power * 955
    elif horse_power <= 400:
        return horse_power * 1628
    elif horse_power <= 500:
        return horse_power * 1685
    else:
        return horse_power * 1740


def calculate_excise_by_volume(engine_volume):
    """
    Рассчитывает акцизный сбор на основе объёма двигателя в куб. см.
    """
    engine_volume_liters = engine_volume / 1000  # Переводим в литры

    if engine_volume_liters <= 1.0:
        return 0
    elif 1.0 < engine_volume_liters <= 1.5:
        return 61 * engine_volume_liters * 100  # Примерное количество л.с.
    elif 1.5 < engine_volume_liters <= 2.0:
        return 583 * engine_volume_liters * 100
    elif 2.0 < engine_volume_liters <= 3.0:
        return 955 * engine_volume_liters * 100
    elif 3.0 < engine_volume_liters <= 4.0:
        return 1628 * engine_volume_liters * 100
    elif 4.0 < engine_volume_liters <= 5.0:
        return 1685 * engine_volume_liters * 100
    else:
        return 1740 * engine_volume_liters * 100


def calculate_customs_duty(car_price_euro, engine_volume, euro_to_rub_rate, age):
    """
    Рассчитывает таможенную пошлину в зависимости от стоимости автомобиля в евро,
    объёма двигателя, курса евро к рублю и возраста автомобиля.
    """
    # Проверяем возраст автомобиля
    print(car_price_euro, engine_volume, euro_to_rub_rate, age)

    if age == "До 3 лет":
        if car_price_euro <= 8500:
            duty = max(car_price_euro * 0.54, engine_volume * 2.5)
        elif car_price_euro <= 16700:
            duty = max(car_price_euro * 0.48, engine_volume * 3.5)
        elif car_price_euro <= 42300:
            duty = max(car_price_euro * 0.48, engine_volume * 5.5)
        elif car_price_euro <= 84500:
            duty = max(car_price_euro * 0.48, engine_volume * 7.5)
        elif car_price_euro <= 169000:
            duty = max(car_price_euro * 0.48, engine_volume * 15)
        else:
            duty = max(car_price_euro * 0.48, engine_volume * 20)
    else:
        # Для автомобилей старше 3 лет
        if engine_volume <= 1000:
            duty = engine_volume * 3
        elif engine_volume <= 1500:
            duty = engine_volume * 3.2
        elif engine_volume <= 1800:
            duty = engine_volume * 3.5
        elif engine_volume <= 2300:
            duty = engine_volume * 4.8
        elif engine_volume <= 3000:
            duty = engine_volume * 5
        else:
            duty = engine_volume * 5.7

    return round(duty * euro_to_rub_rate, 2)


def calculate_recycling_fee(engine_volume, age):
    """
    Рассчитывает утилизационный сбор в России для физических лиц.

    :param engine_volume: Объём двигателя в куб. см.
    :param age: Возраст автомобиля.
    :return: Утилизационный сбор в рублях.
    """
    base_rate = 20000  # Базовая ставка для легковых авто

    # Коэффициенты для физических лиц в зависимости от объема двигателя
    if engine_volume <= 1000:
        coefficient = 0.17 if age == "До 3 лет" else 0.26
    elif engine_volume <= 2000:
        coefficient = 0.17 if age == "До 3 лет" else 0.26
    elif engine_volume <= 3000:
        coefficient = 0.17 if age == "До 3 лет" else 0.26
    elif engine_volume <= 3500:
        coefficient = 89.73 if age == "До 3 лет" else 137.36
    else:
        coefficient = 114.26 if age == "До 3 лет" else 150.2

    recycling_fee = base_rate * coefficient
    return round(recycling_fee, 2)


def calculate_customs_fee(car_price_rub):
    """
    Рассчитывает таможенный сбор в зависимости от стоимости автомобиля в рублях.
    """
    if car_price_rub <= 200000:
        return 1067
    elif car_price_rub <= 450000:
        return 2134
    elif car_price_rub <= 1200000:
        return 4269
    elif car_price_rub <= 2700000:
        return 11746
    elif car_price_rub <= 4200000:
        return 16524
    elif car_price_rub <= 5500000:
        return 21344
    elif car_price_rub <= 7000000:
        return 27540
    else:
        return 30000


def calculate_horse_power(engine_volume):
    """
    Рассчитывает мощность двигателя в лошадиных силах (л.с.).
    """
    engine_volume = int(engine_volume)
    horse_power = round(engine_volume / 15)
    return horse_power


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
