# add_service.py
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from db import SessionLocal, get_user, is_user_banned, add_user_service

SERVICE_NAME, SERVICE_DESCRIPTION, SERVICE_SERVER, SERVICE_PRICE = range(4)

async def add_service(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    session = SessionLocal()
    user = get_user(session, telegram_id)

    if not user:
        await update.message.reply_text('Вы не зарегистрированы.')
        session.close()
        return ConversationHandler.END

    if is_user_banned(user):
        await update.message.reply_text('Вы забанены и не можете пользоваться ботом.')
        session.close()
        return ConversationHandler.END

    await update.message.reply_text('Пожалуйста, введите название услуги:')
    session.close()
    return SERVICE_NAME

async def handle_service_name(update: Update, context: CallbackContext) -> int:
    context.user_data['service_name'] = update.message.text
    await update.message.reply_text('Пожалуйста, введите описание услуги:')
    return SERVICE_DESCRIPTION

async def handle_service_description(update: Update, context: CallbackContext) -> int:
    context.user_data['service_description'] = update.message.text
    await update.message.reply_text('Пожалуйста, введите сервер услуги:')
    return SERVICE_SERVER

async def handle_service_server(update: Update, context: CallbackContext) -> int:
    context.user_data['service_server'] = update.message.text
    await update.message.reply_text('Пожалуйста, введите стоимость услуги:')
    return SERVICE_PRICE

async def handle_service_price(update: Update, context: CallbackContext) -> int:
    context.user_data['service_price'] = update.message.text

    telegram_id = update.message.from_user.id
    name = context.user_data['service_name']
    description = context.user_data['service_description']
    server = context.user_data['service_server']
    price = context.user_data['service_price']

    session = SessionLocal()
    user = get_user(session, telegram_id)

    if not user:
        await update.message.reply_text('Вы не зарегистрированы.')
        session.close()
        return ConversationHandler.END

    if is_user_banned(user):
        await update.message.reply_text('Вы забанены и не можете пользоваться ботом.')
        session.close()
        return ConversationHandler.END

    add_user_service(session, telegram_id, name, description, server, price)
    await update.message.reply_text('Услуга успешно добавлена в ваш профиль!')
    session.close()
    return ConversationHandler.END
