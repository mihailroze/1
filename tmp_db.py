# tmp_db.py
from sqlalchemy.orm import joinedload

from db import SessionLocal, Order, User


def correct_user_ids():
    with SessionLocal() as session:
        users = session.query(User).all()
        user_map = {user.telegram_id: user.id for user in users}

        orders = session.query(Order).all()
        for order in orders:
            if order.user_id in user_map:
                correct_user_id = user_map[order.user_id]
                order.user_id = correct_user_id
                session.commit()
                print(f"Order {order.id} updated with User {correct_user_id}")
            else:
                print(f"No matching user for order {order.id}")


correct_user_ids()


# Проверка данных
def check_data():
    with SessionLocal() as session:
        orders = session.query(Order).options(joinedload(Order.user), joinedload(Order.service)).all()

        print("Orders:")
        for order in orders:
            print(
                f"Order ID: {order.id}, User ID: {order.user_id}, Service ID: {order.service_id}, User: {order.user}, Service: {order.service}")

        users = session.query(User).all()

        print("\nUsers:")
        for user in users:
            print(f"User ID: {user.id}, Telegram ID: {user.telegram_id}, Steam Nickname: {user.steam_nickname}")


check_data()
