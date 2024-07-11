# payment.py
from sqlalchemy.orm import Session, joinedload
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db import SessionLocal, get_order_by_id, get_user_by_telegram_id, Order
import logging

async def pay_order(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split('_')[1])
    telegram_id = query.from_user.id

    logging.info(f"Processing payment for order_id: {order_id}, telegram_id: {telegram_id}")

    with SessionLocal() as session:
        # Загружаем order с joinedload для user и service
        order = session.query(Order).options(joinedload(Order.user), joinedload(Order.service)).filter(Order.id == order_id).first()
        user = get_user_by_telegram_id(session, telegram_id)

        if not order:
            await query.edit_message_text("Ошибка: заказ не найден.")
            logging.error(f"Order with id {order_id} not found.")
            return

        if not user:
            await query.edit_message_text("Ошибка: пользователь не найден.")
            logging.error(f"User with telegram_id {telegram_id} not found.")
            return

        logging.info(f"Order details: {order}")
        logging.info(f"User details: {user}")

        if not order.user:
            await query.edit_message_text("Ошибка: пользователь, связанный с заказом, не найден.")
            logging.error(f"User associated with order id {order_id} not found. Order details: {order}, Service details: {order.service}")
            return

        logging.info(f"Order user details: {order.user}")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Получен новый заказ от {user.steam_nickname} на сумму {order.amount}. Пожалуйста, выполните услугу."
        )

        order.status = 'paid'
        session.commit()
        logging.info(f"Order {order_id} status updated to 'paid'.")

        # Кнопка для подтверждения выполнения услуги
        keyboard = [
            [InlineKeyboardButton("Подтвердить выполнение", callback_data=f'confirm_{order_id}')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=order.user.telegram_id,
            text=f"Исполнитель {order.service.user.steam_nickname} выполнил услугу. Пожалуйста, подтвердите выполнение.",
            reply_markup=reply_markup
        )
        await context.bot.send_message(
            chat_id=order.service.user.telegram_id,
            text=f"Вы выполнили услугу для {order.user.steam_nickname}. Пожалуйста, подтвердите выполнение.",
            reply_markup=reply_markup
        )

async def confirm_service_completion(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split('_')[1])
    telegram_id = query.from_user.id

    logging.info(f"Confirming service completion for order_id: {order_id}, telegram_id: {telegram_id}")

    with SessionLocal() as session:
        order = get_order_by_id(session, order_id)
        user = get_user_by_telegram_id(session, telegram_id)

        if not order:
            await query.edit_message_text("Ошибка: заказ не найден.")
            logging.error(f"Order with id {order_id} not found.")
            return

        if not user:
            await query.edit_message_text("Ошибка: пользователь не найден.")
            logging.error(f"User with telegram_id {telegram_id} not found.")
            return

        if user.id == order.user_id:
            order.status = 'buyer_confirmed'
        else:
            order.status = 'executor_confirmed'

        session.commit()
        logging.info(f"Order {order_id} status updated to '{order.status}'.")

        await query.edit_message_text(f"Вы подтвердили выполнение услуги. Текущий статус: {order.status}")

        if order.status == 'buyer_confirmed' and order.status == 'executor_confirmed':
            await transfer_payment(session, order_id)
            await context.bot.send_message(
                chat_id=order.executor.telegram_id,
                text=f"Выполнение услуги подтверждено обеими сторонами. Оплата переведена."
            )

async def transfer_payment(session: Session, order_id: int):
    order = get_order_by_id(session, order_id)
    if not order:
        logging.error(f"Order with id {order_id} not found for payment transfer.")
        return

    logging.info(f"Transferring payment for order {order_id} to executor {order.executor.steam_nickname}.")
    order.status = 'paid'
    session.commit()
