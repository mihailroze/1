from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    keyboard = [
        [KeyboardButton("Профиль"), KeyboardButton("Список услуг")],
        [KeyboardButton("Добавить услугу")],
        [KeyboardButton("Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
