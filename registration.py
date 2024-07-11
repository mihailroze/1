# registration.py
import requests
from telegram import Update
from telegram.ext import CallbackContext
from config import STEAM_API_KEY
from db import SessionLocal, create_user, get_user, is_user_banned
from menu import show_menu

# Функция для регистрации пользователя по Steam ID
async def register_user(update: Update, context: CallbackContext) -> None:
    steam_id = update.message.text.strip()
    telegram_id = update.message.from_user.id

    # Проверка на бан
    session = SessionLocal()
    user = get_user(session, telegram_id)
    if user and is_user_banned(user):
        await update.message.reply_text('Вы забанены и не можете пользоваться ботом.')
        session.close()
        return
    session.close()

    # Пример запроса к Steam API
    response = requests.get(
        f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}')

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and 'players' in data['response'] and data['response']['players']:
            player = data['response']['players'][0]

            # Сохранение пользователя в базе данных
            session = SessionLocal()
            existing_user = get_user(session, telegram_id)
            if existing_user:
                await update.message.reply_text('Этот Steam ID уже зарегистрирован.')
            else:
                create_user(session, telegram_id, steam_id, player['personaname'])
                await update.message.reply_text(
                    f'Вы успешно зарегистрированы! Ваш никнейм в Steam: {player["personaname"]}.',
                    reply_markup=show_menu(update, context)
                )
                context.user_data['awaiting_steam_id'] = False
            session.close()
        else:
            await update.message.reply_text('Не удалось найти игрока с указанным Steam ID.')
    else:
        await update.message.reply_text('Произошла ошибка при обращении к Steam API.')
