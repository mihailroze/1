# user_interaction.py
from telegram import Update
from telegram.ext import CallbackContext
from db import SessionLocal, get_user, is_user_banned, create_user
from config import ADMIN_TELEGRAM_ID
from menu import show_menu
from registration import register_user
import logging

logger = logging.getLogger(__name__)

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> None:
    logger.info('Команда /start вызвана')
    telegram_id = update.message.from_user.id
    session = SessionLocal()
    user = get_user(session, telegram_id)
    session.close()
    logger.info(f'Пользователь с ID {telegram_id} найден: {user is not None}')

    # Проверка на бан
    if user and is_user_banned(user):
        await update.message.reply_text('Вы забанены и не можете пользоваться ботом.')
        logger.info(f'Пользователь {telegram_id} забанен')
        return

    # Определение администратора
    is_admin = str(telegram_id) == ADMIN_TELEGRAM_ID

    if user:
        if is_admin:
            await update.message.reply_text(
                'Добро пожаловать, Администратор! Вы можете управлять пользователями и услугами.',
                reply_markup=show_menu(update, context)
            )
        else:
            await update.message.reply_text(
                'Добро пожаловать! Вы уже зарегистрированы в системе.',
                reply_markup=show_menu(update, context)
            )
    else:
        await update.message.reply_text('Вы не зарегистрированы. Пожалуйста, введите ваш Steam ID для регистрации.')
        context.user_data['awaiting_steam_id'] = True
        logger.info(f'Пользователь {telegram_id} не зарегистрирован, предложена регистрация')
    logger.info('Завершение обработки команды /start')

# Функция для обработки незарегистрированных пользователей
async def handle_unregistered(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Вы еще не зарегистрированы. Пожалуйста, введите ваш Steam ID для регистрации.'
    )
    context.user_data['awaiting_steam_id'] = True

# Функция для обработки регистрации пользователя
async def handle_registration(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_steam_id'):
        await register_user(update, context)
    else:
        await update.message.reply_text('Неправильный формат. Пожалуйста, используйте команду /start для начала.')
