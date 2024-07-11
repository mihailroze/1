# chat.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from db import SessionLocal, get_user_by_id, create_message, get_order_by_id, get_user_by_telegram_id
import logging


async def start_service_chat(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split('_')[1])
    context.user_data['current_order_id'] = order_id  # Сохраняем order_id для чата

    with SessionLocal() as session:
        order = get_order_by_id(session, order_id)
        user = get_user_by_telegram_id(session, query.from_user.id)
        if not order or not user:
            await query.edit_message_text("Ошибка: заказ или пользователь не найден.")
            return

        buyer = get_user_by_id(session, order.user_id)
        executor = user

        await context.bot.send_message(
            chat_id=buyer.telegram_id,
            text=f"Исполнитель {executor.steam_nickname} начал выполнение услуги. Вы можете общаться напрямую для уточнения деталей."
        )

        await context.bot.send_message(
            chat_id=executor.telegram_id,
            text=f"Вы начали выполнение услуги для {buyer.steam_nickname}. Вы можете общаться напрямую для уточнения деталей."
        )

        create_message(session, executor.id, buyer.id, "Начало выполнения услуги.")
        create_message(session, buyer.id, executor.id, "Начало выполнения услуги.")

        await query.edit_message_text("Чат между пользователями начат.")


async def send_chat_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    sender_id = update.message.from_user.id

    with SessionLocal() as session:
        sender = get_user_by_telegram_id(session, sender_id)
        order = get_order_by_id(session, context.user_data['current_order_id'])
        if not sender or not order:
            await update.message.reply_text("Ошибка: пользователь или заказ не найден.")
            return

        receiver_id = order.user_id if sender.id != order.user_id else order.executor.id
        receiver = get_user_by_id(session, receiver_id)

        await context.bot.send_message(
            chat_id=receiver.telegram_id,
            text=f"Новое сообщение от {sender.steam_nickname}: {text}"
        )

        create_message(session, sender.id, receiver.id, text)
