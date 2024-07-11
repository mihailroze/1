# create_order.py
from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db import SessionLocal, get_user_by_telegram_id, create_order as create_order_in_db, Service
import logging

async def create_order_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    logging.info("create_order_handler called")

    service_id = int(query.data.split('_')[2])
    telegram_id = query.from_user.id

    logging.info(f"Creating order for service_id: {service_id}, telegram_id: {telegram_id}")

    with SessionLocal() as session:
        user = get_user_by_telegram_id(session, telegram_id)
        service = session.query(Service).filter(Service.id == service_id).first()

        if not user:
            await query.edit_message_text("Ошибка: пользователь не найден.")
            logging.error(f"User with telegram_id {telegram_id} not found.")
            return

        if not service:
            await query.edit_message_text("Ошибка: услуга не найдена.")
            logging.error(f"Service with id {service_id} not found.")
            return

        logging.info(f"User found: {user}, Service found: {service}")

        # Убедитесь, что используется user.id, а не telegram_id
        order_id = create_order_in_db(session, user.id, service.id, service.price)

        logging.info(f"Order created with ID: {order_id}, user_id: {user.id}")

        await query.edit_message_text(
            f"Вы выбрали услугу '{service.name}'.\nСумма оплаты: {service.price}.\n\nПожалуйста, оплатите заказ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Оплатить", callback_data=f'pay_{order_id}')]
            ])
        )
