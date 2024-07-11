# profile.py
from telegram import Update
from telegram.ext import CallbackContext
from db import SessionLocal, get_user, is_user_banned

# Функция для отображения профиля
async def show_profile(update: Update, context: CallbackContext) -> None:
    telegram_id = update.message.from_user.id
    session = SessionLocal()
    user = get_user(session, telegram_id)

    if user:
        if is_user_banned(user):
            await update.message.reply_text('Вы забанены и не можете пользоваться ботом.')
            session.close()
            return

        services = "\n".join([f"{s.name} / {s.description} / {s.server} / {s.price}" for s in user.services])
        await update.message.reply_text(
            f"Ваш профиль:\n"
            f"Дата регистрации: {user.registration_date}\n"
            f"Чат ID: {user.telegram_id}\n"
            f"Ник в Steam: {user.steam_nickname}\n"
            f"Steam ID: {user.steam_id}\n"
            f"Ваши услуги:\n{services if services else 'Услуг нет'}"
        )
    else:
        await update.message.reply_text('Вы не зарегистрированы.')
    session.close()
