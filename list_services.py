# list_services.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from db import SessionLocal, get_service_by_id, create_order, get_user_by_telegram_id, get_all_services

# Количество услуг на одной странице
SERVICES_PER_PAGE = 10

# Функция для отображения списка услуг с пагинацией
async def list_services(update: Update, context: CallbackContext) -> None:
    with SessionLocal() as session:
        services = get_all_services(session)

    if not services:
        await update.message.reply_text("Доступных услуг нет.")
        return

    context.user_data['services'] = services
    context.user_data['page'] = 0
    await send_service_page(update, context)

# Функция для отправки страницы с услугами
async def send_service_page(update: Update, context: CallbackContext) -> None:
    page = context.user_data['page']
    services = context.user_data['services']
    start_index = page * SERVICES_PER_PAGE
    end_index = start_index + SERVICES_PER_PAGE
    page_services = services[start_index:end_index]

    for service in page_services:
        service_text = (f"Название: {service.name}\n"
                        f"Описание: {service.description}\n"
                        f"Сервер: {service.server}\n"
                        f"Стоимость: {service.price}\n")
        keyboard = [[InlineKeyboardButton("Выбрать", callback_data=f'service_{service.id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(service_text, reply_markup=reply_markup)

    # Добавление кнопок "Вперед" и "Назад"
    navigation_buttons = []
    if start_index > 0:
        navigation_buttons.append(InlineKeyboardButton("Назад", callback_data='previous_page'))
    if end_index < len(services):
        navigation_buttons.append(InlineKeyboardButton("Вперед", callback_data='next_page'))

    if navigation_buttons:
        reply_markup = InlineKeyboardMarkup([navigation_buttons])
        await update.message.reply_text("Навигация по услугам:", reply_markup=reply_markup)

# Функция для обработки выбора услуги и начала процесса создания заказа
async def service_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    service_id = int(query.data.split('_')[1])
    telegram_id = query.from_user.id

    with SessionLocal() as session:
        service = get_service_by_id(session, service_id)
        user = get_user_by_telegram_id(session, telegram_id)

        # Проверка, что service и user были загружены корректно
        if not service:
            await query.edit_message_text("Ошибка: услуга не найдена.")
            return
        if not user:
            await query.edit_message_text("Ошибка: пользователь не найден.")
            return

        order_id = create_order(session, user.id, service_id, service.price)

    keyboard = [[InlineKeyboardButton("Оплатить", callback_data=f'pay_{order_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Вы выбрали услугу '{service.name}'.\nСумма оплаты: {service.price}.\n\nПожалуйста, оплатите заказ.",
        reply_markup=reply_markup
    )

# Обработчик для кнопок "Вперед" и "Назад"
async def navigate_services(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query_data = query.data

    if query_data == 'next_page':
        context.user_data['page'] += 1
    elif query_data == 'previous_page':
        context.user_data['page'] -= 1

    await query.answer()
    await query.delete_message()
    await send_service_page(update, context)
