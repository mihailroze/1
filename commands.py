import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from config import STEAM_API_KEY, ADMIN_TELEGRAM_ID
from db import SessionLocal, is_user_banned, User
from services import show_services, add_service

# Проверка на бан пользователя
def is_banned(telegram_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()

    if user and is_user_banned(user):
        return True
    return False

# Основные команды
async def start(update: Update, context: CallbackContext) -> None:
    telegram_id = update.message.from_user.id
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()

    # Определение администратора
    is_admin = str(telegram_id) == ADMIN_TELEGRAM_ID

    if user and is_user_banned(user) and not is_admin:
        await update.message.reply_text('Вы забанены и не можете пользоваться ботом.', reply_markup=get_main_menu())
    else:
        if is_admin:
            await update.message.reply_text(
                'Добро пожаловать, Администратор! Вы можете управлять пользователями и услугами.',
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                'Привет! Пожалуйста, отправьте ваш Steam ID или профильную ссылку для регистрации.',
                reply_markup=get_main_menu()
            )

# Хендлер для проверки забаненных пользователей
async def handle_all(update: Update, context: CallbackContext) -> None:
    telegram_id = update.message.from_user.id

    if is_banned(telegram_id):
        await update.message.reply_text('Вы забанены и не можете пользоваться ботом.')
        return

# Функция для создания меню
def get_main_menu():
    keyboard = [
        [KeyboardButton("Профиль"), KeyboardButton("Список услуг")],
        [KeyboardButton("Добавить услугу")],
        [KeyboardButton("Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработка нажатий на кнопки меню
async def menu_button(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text == "Профиль":
        await show_profile(update, context)
    elif text == "Список услуг":
        await show_services(update, context)
    elif text == "Добавить услугу":
        await update.message.reply_text('Введите информацию об услуге в формате: <название> / <описание> / <цена>')
    elif text == "Поддержка":
        await update.message.reply_text('Для поддержки свяжитесь с нами по email: support@example.com')

# Показ профиля пользователя
async def show_profile(update: Update, context: CallbackContext) -> None:
    telegram_id = update.message.from_user.id
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        status = 'забанен' if is_user_banned(user) else 'активен'
        response = f'Ваш профиль:\nSteam ID: {user.steam_id}\nСтатус: {status}'
        await update.message.reply_text(response, reply_markup=get_main_menu())
    else:
        await update.message.reply_text('Вы не зарегистрированы.', reply_markup=get_main_menu())
    session.close()
