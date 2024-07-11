from telegram import Update
from telegram.ext import CallbackContext
from db import SessionLocal, confirm_order, get_order_by_id


async def confirm_order(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    order_id = int(query.data.split('_')[1])

    session = SessionLocal()
    order = get_order_by_id(session, order_id)

    confirm_order(session, order_id)

    seller_id = order.service.user_id
    await context.bot.send_message(seller_id,
                                   f"Пользователь подтвердил выполнение заказа на услугу '{order.service.name}'. Деньги переведены.")
    await query.message.reply_text("Выполнение заказа подтверждено. Деньги переведены продавцу.")
    session.close()