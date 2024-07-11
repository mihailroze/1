from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from db import SessionLocal, complete_order, get_order_by_id


async def complete_order(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    order_id = int(query.data.split('_')[1])

    session = SessionLocal()
    order = get_order_by_id(session, order_id)

    complete_order(session, order_id)

    user_id = order.user_id
    await context.bot.send_message(user_id,
                                   f"Ваш заказ на услугу '{order.service.name}' выполнен. Пожалуйста, подтвердите выполнение.")

    keyboard = [[InlineKeyboardButton("Подтвердить", callback_data=f'confirm_{order_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text("Заказ выполнен. Ожидается подтверждение от пользователя.",
                                   reply_markup=reply_markup)
    session.close()