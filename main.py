# main.py
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from config import TELEGRAM_API_TOKEN
from user_interaction import start, handle_unregistered, handle_registration
from profile import show_profile
from registration import register_user
from add_service import add_service, handle_service_name, handle_service_description, handle_service_server, handle_service_price
from list_services import list_services, service_callback as list_service_callback, navigate_services
from search_services import search_services, handle_criteria, handle_query, cancel, navigate_search_results, search_service_callback
from create_order import create_order_handler
from payment import pay_order, confirm_service_completion
from chat import send_chat_message, start_service_chat
from menu import show_menu
from db import is_user_banned, SessionLocal, get_user

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для проверки на бан
def check_ban(update, context):
    telegram_id = update.message.from_user.id
    session = SessionLocal()
    user = get_user(session, telegram_id)
    session.close()
    if user and is_user_banned(user):
        update.message.reply_text('Вы забанены и не можете пользоваться ботом.')
        return True
    return False

# Обработчик для всех команд кроме /start
def handle_all(update, context):
    if check_ban(update, context):
        return
    telegram_id = update.message.from_user.id
    session = SessionLocal()
    user = get_user(session, telegram_id)
    session.close()
    if not user:
        context.user_data['new_user'] = True
        handle_unregistered(update, context)
        return
    # Здесь можно добавить обработку других команд

# Основная функция для запуска бота
def main():
    app = Application.builder().token(TELEGRAM_API_TOKEN).build()

    # Определение состояний для ConversationHandler
    SERVICE_NAME, SERVICE_DESCRIPTION, SERVICE_SERVER, SERVICE_PRICE = range(4)
    SEARCH_CRITERIA, SEARCH_QUERY, SEARCH_RESULTS = range(3)

    # Добавление обработчиков команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('^Профиль$'), show_profile))

    # Добавление ConversationHandler для добавления услуг
    service_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Добавить услугу$'), add_service)],
        states={
            SERVICE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service_name)],
            SERVICE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service_description)],
            SERVICE_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service_server)],
            SERVICE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service_price)]
        },
        fallbacks=[],
        per_chat=True  # Следим за состояниями на уровне чата
    )

    # Добавление ConversationHandler для поиска услуг
    search_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Поиск услуг$'), search_services)],
        states={
            SEARCH_CRITERIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_criteria)],
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query)],
            SEARCH_RESULTS: [CallbackQueryHandler(navigate_search_results, pattern=r'^(search_next_page|search_previous_page)$')]
        },
        fallbacks=[MessageHandler(filters.Regex('^/cancel$'), cancel), CommandHandler("start", start)],
        per_chat=True  # Следим за состояниями на уровне чата
    )

    app.add_handler(service_handler)
    app.add_handler(search_handler)
    app.add_handler(MessageHandler(filters.Regex('^Список услуг$'), list_services))
    app.add_handler(CallbackQueryHandler(list_service_callback, pattern=r'^service_\d+$'))
    app.add_handler(CallbackQueryHandler(navigate_services, pattern=r'^(next_page|previous_page)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))
    app.add_handler(CallbackQueryHandler(create_order_handler, pattern=r'^create_order_\d+$'))  # Исправлено
    app.add_handler(CallbackQueryHandler(pay_order, pattern=r'^pay_\d+$'))
    app.add_handler(CallbackQueryHandler(confirm_service_completion, pattern=r'^confirm_\d+$'))
    app.add_handler(CallbackQueryHandler(start_service_chat, pattern=r'^start_chat_\d+$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_chat_message))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Regex('^start$'), handle_all))

    logging.info("Starting bot...")
    # Запуск бота
    app.run_polling()

if __name__ == "__main__":
    main()
