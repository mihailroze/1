# search_services.py
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler
from db import SessionLocal, get_services_by_criteria, get_service_by_id, create_order

# Определение состояний для ConversationHandler
SEARCH_CRITERIA, SEARCH_QUERY, SEARCH_RESULTS = range(3)
SERVICES_PER_PAGE = 10

async def search_services(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()  # Сброс состояния пользователя
    keyboard = [
        [KeyboardButton("Пользователь"), KeyboardButton("Название услуги")],
        [KeyboardButton("Название сервера")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите критерий поиска:", reply_markup=reply_markup)
    return SEARCH_CRITERIA

async def handle_criteria(update: Update, context: CallbackContext) -> int:
    context.user_data['search_criteria'] = update.message.text
    await update.message.reply_text(
        "Введите запрос для поиска:\n\n"
        "Пример:\n\n"
        "*Пользователь*: введите имя пользователя.\n"
        "*Название услуги*: введите часть или полное название услуги.\n"
        "*Название сервера*: введите имя сервера.\n\n"
        "*Команда /cancel* - отменить поиск.\n"
        "*Команда /start* - перезапустить поиск. \n"
        "*ВНИМАНИЕ!* Если вы воспользовались поиском по одному из критериев и вам необходимо снова провести поиск по другому критерию, обязательно напишите команду */cancel*, затем напишите */start* и повторите поиск.",
        parse_mode='Markdown'
    )
    return SEARCH_QUERY

async def handle_query(update: Update, context: CallbackContext) -> int:
    criteria = context.user_data['search_criteria']
    query = update.message.text
    with SessionLocal() as session:
        services = get_services_by_criteria(session, criteria, query)
        context.user_data['search_services'] = services
        context.user_data['search_page'] = 0

    if not services:
        await update.message.reply_text("Услуги не найдены.")
        return SEARCH_CRITERIA

    await send_search_page(update, context)
    return SEARCH_RESULTS

async def send_search_page(update: Update, context: CallbackContext) -> None:
    page = context.user_data['search_page']
    services = context.user_data['search_services']
    start_index = page * SERVICES_PER_PAGE
    end_index = start_index + SERVICES_PER_PAGE
    page_services = services[start_index:end_index]

    for service in page_services:
        service_text = (f"Название: {service.name}\n"
                        f"Описание: {service.description}\n"
                        f"Сервер: {service.server}\n"
                        f"Стоимость: {service.price}\n"
                        f"Пользователь: {service.user.steam_nickname}\n")
        keyboard = [[InlineKeyboardButton("Выбрать", callback_data=f'service_{service.id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(service_text, reply_markup=reply_markup)

    # Добавление кнопок "Вперед" и "Назад"
    navigation_buttons = []
    if start_index > 0:
        navigation_buttons.append(InlineKeyboardButton("Назад", callback_data='search_previous_page'))
    if end_index < len(services):
        navigation_buttons.append(InlineKeyboardButton("Вперед", callback_data='search_next_page'))

    if navigation_buttons:
        reply_markup = InlineKeyboardMarkup([navigation_buttons])
        await update.message.reply_text("Навигация по результатам поиска:", reply_markup=reply_markup)

# Функция для обработки выбора услуги и начала процесса создания заказа
async def search_service_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    service_id = int(query.data.split('_')[1])
    user_id = query.from_user.id

    with SessionLocal() as session:
        service = get_service_by_id(session, service_id)

        # Проверка, что service был загружен корректно
        if not service:
            await query.edit_message_text("Ошибка: услуга не найдена.")
            return

        order_id = create_order(session, user_id, service_id, service.price)

    keyboard = [[InlineKeyboardButton("Оплатить", callback_data=f'pay_{order_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Вы выбрали услугу '{service.name}'.\nСумма оплаты: {service.price}.\n\nПожалуйста, оплатите заказ.",
        reply_markup=reply_markup
    )

async def navigate_search_results(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query_data = query.data

    if query_data == 'search_next_page':
        context.user_data['search_page'] += 1
    elif query_data == 'search_previous_page':
        context.user_data['search_page'] -= 1

    await query.answer()
    await query.delete_message()
    await send_search_page(update, context)

async def cancel(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()  # Сброс состояния пользователя
    await update.message.reply_text("Поиск отменен.")
    return ConversationHandler.END
