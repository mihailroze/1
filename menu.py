# menu.py
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import CallbackContext

def show_menu(update: Update, context: CallbackContext) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton('Профиль')],
        [KeyboardButton('Список услуг')],
        [KeyboardButton('Добавить услугу')],
        [KeyboardButton('Поддержка')],
        [KeyboardButton('Поиск услуг')]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
