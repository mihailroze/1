import requests
from telegram import Update
from telegram.ext import CallbackContext
from commands import get_main_menu
from config import STEAM_API_KEY, ADMIN_TELEGRAM_ID
from db import SessionLocal, create_user, get_user, ban_user, is_user_banned, User

# Обработка сообщения с Steam ID
async def steam_id_handler(update: Update, context: CallbackContext) -> None:
    steam_id = update.message.text.strip()
    telegram_id = update.message.from_user.id

    # Пример запроса к Steam API
    response = requests.get(
        f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}')

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and 'players' in data['response'] and data['response']['players']:
            player = data['response']['players'][0]

            # Сохранение пользователя в базе данных
            session = SessionLocal()
            existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if existing_user:
                await update.message.reply_text('Этот Steam ID уже зарегистрирован.', reply_markup=get_main_menu())
            else:
                user = create_user(session, telegram_id, steam_id, player['personaname'])
                session.close()
                await update.message.reply_text(
                    f'Вы успешно зарегистрированы! Ваш никнейм в Steam: {player["personaname"]}.',
                    reply_markup=get_main_menu())
        else:
            await update.message.reply_text('Не удалось найти игрока с указанным Steam ID.',
                                            reply_markup=get_main_menu())
    else:
        await update.message.reply_text('Произошла ошибка при обращении к Steam API.', reply_markup=get_main_menu())

# Команда для проверки статуса
async def check_status(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    session = SessionLocal()
    user = get_user(session, user_id)
    if user:
        status = 'забанен' if is_user_banned(user) else 'активен'
        await update.message.reply_text(f'Ваш текущий статус: {status}', reply_markup=get_main_menu())
    else:
        await update.message.reply_text('Вы не зарегистрированы.', reply_markup=get_main_menu())
    session.close()

# Команда назначения администратора
async def set_admin(update: Update, context: CallbackContext) -> None:
    if str(update.message.from_user.id) == ADMIN_TELEGRAM_ID:
        session = SessionLocal()
        target_id = int(context.args[0])
        target_user = get_user(session, target_id)
        if target_user:
            target_user.role = 'admin'
            session.commit()
            await update.message.reply_text(f'Пользователь {target_id} назначен администратором.',
                                            reply_markup=get_main_menu())
        else:
            await update.message.reply_text('Пользователь не найден.', reply_markup=get_main_menu())
        session.close()
    else:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.', reply_markup=get_main_menu())

# Команда бана пользователей
async def ban_user_command(update: Update, context: CallbackContext) -> None:
    if str(update.message.from_user.id) == ADMIN_TELEGRAM_ID:
        session = SessionLocal()
        target_id = int(context.args[0])
        duration = int(context.args[1]) if len(context.args) > 1 else None
        target_user = ban_user(session, target_id, duration)
        if target_user:
            if duration:
                await update.message.reply_text(f'Пользователь {target_id} забанен на {duration} минут.',
                                                reply_markup=get_main_menu())
            else:
                await update.message.reply_text(f'Пользователь {target_id} забанен навсегда.',
                                                reply_markup=get_main_menu())
        else:
            await update.message.reply_text('Пользователь не найден.', reply_markup=get_main_menu())
        session.close()
    else:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.', reply_markup=get_main_menu())

# Команда бана пользователя по никнейму Steam
async def ban_user_by_nickname(update: Update, context: CallbackContext) -> None:
    if str(update.message.from_user.id) == ADMIN_TELEGRAM_ID:
        steam_nickname = ' '.join(context.args[:-1])
        duration = int(context.args[-1]) if len(context.args) > 1 else None
        session = SessionLocal()
        target_user = session.query(User).filter(User.steam_nickname.ilike(f"%{steam_nickname}%")).first()
        if target_user:
            target_user = ban_user(session, target_user.telegram_id, duration)
            if duration:
                await update.message.reply_text(f'Пользователь с никнеймом {steam_nickname} забанен на {duration} минут.',
                                                reply_markup=get_main_menu())
            else:
                await update.message.reply_text(f'Пользователь с никнеймом {steam_nickname} забанен навсегда.',
                                                reply_markup=get_main_menu())
        else:
            await update.message.reply_text('Пользователь не найден.', reply_markup=get_main_menu())
        session.close()
    else:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.', reply_markup=get_main_menu())

# Команда для отображения списка всех пользователей
async def list_users(update: Update, context: CallbackContext) -> None:
    if str(update.message.from_user.id) == ADMIN_TELEGRAM_ID:
        session = SessionLocal()
        users = get_all_users(session)
        response = "Список пользователей:\n"
        for user in users:
            response += f"ID: {user.id}, Steam ID: {user.steam_id}, Никнейм: {user.steam_nickname}, Статус: {'забанен' if is_user_banned(user) else 'активен'}\n"
        await update.message.reply_text(response, reply_markup=get_main_menu())
        session.close()
    else:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.', reply_markup=get_main_menu())
