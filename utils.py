import datetime
import locale


def calculate_age(year):
    current_year = datetime.datetime.now().year
    age = current_year - int(year)

    if age < 3:
        return f"До 3 лет"
    elif 3 <= age < 5:
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
