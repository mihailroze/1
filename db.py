# db.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, joinedload
from datetime import datetime

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    steam_id = Column(String, unique=True, index=True)
    steam_nickname = Column(String, index=True)
    role = Column(String, default="user")
    banned_until = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    services = relationship("Service", back_populates="user")
    orders = relationship("Order", back_populates="user")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, index=True)
    description = Column(String, index=True)
    server = Column(String, index=True)
    price = Column(Integer)
    user = relationship("User", back_populates="services")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    service_id = Column(Integer, ForeignKey('services.id'))
    amount = Column(Integer)
    status = Column(String, default='created')
    user = relationship("User", back_populates="orders")
    service = relationship("Service")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    receiver_id = Column(Integer, ForeignKey('users.id'))
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def create_user(db: Session, telegram_id: int, steam_id: str, steam_nickname: str):
    new_user = User(telegram_id=telegram_id, steam_id=steam_id, steam_nickname=steam_nickname)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def add_user_service(db: Session, telegram_id: int, name: str, description: str, server: str, price: float):
    user = get_user(db, telegram_id)
    if user:
        new_service = Service(name=name, description=description, server=server, price=price, user_id=user.id)
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        return new_service
    return None

def get_user(db: Session, telegram_id: int) -> User:
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_services_by_criteria(db: Session, criteria: str, query: str) -> list:
    if criteria == "Пользователь":
        return db.query(Service).join(User).options(joinedload(Service.user)).filter(User.steam_nickname.ilike(f"%{query}%")).all()
    elif criteria == "Название услуги":
        return db.query(Service).options(joinedload(Service.user)).filter(Service.name.ilike(f"%{query}%")).all()
    elif criteria == "Название сервера":
        return db.query(Service).options(joinedload(Service.user)).filter(Service.server.ilike(f"%{query}%")).all()
    return []

def get_all_services(db: Session) -> list:
    return db.query(Service).options(joinedload(Service.user)).all()

def get_service_by_id(session: Session, service_id: int) -> Service:
    return session.query(Service).options(joinedload(Service.user)).filter(Service.id == service_id).first()

def create_order(session: Session, user_id: int, service_id: int, amount: float) -> int:
    order = Order(user_id=user_id, service_id=service_id, amount=amount)
    session.add(order)
    session.commit()
    return order.id

def get_order_by_id(session: Session, order_id: int) -> Order:
    return session.query(Order).options(joinedload(Order.user), joinedload(Order.service)).filter(Order.id == order_id).first()

def confirm_payment(session: Session, order_id: int):
    order = session.query(Order).get(order_id)
    order.status = 'paid'
    session.commit()

def complete_order(session: Session, order_id: int):
    order = session.query(Order).get(order_id)
    order.status = 'completed'
    session.commit()

def confirm_order(session: Session, order_id: int):
    order = session.query(Order).get(order_id)
    order.status = 'confirmed'
    session.commit()

def get_user_by_id(session: Session, user_id: int) -> User:
    return session.query(User).filter(User.id == user_id).first()

def get_user_by_telegram_id(session: Session, telegram_id: int) -> User:
    return session.query(User).filter(User.telegram_id == telegram_id).first()

def is_user_banned(user: User) -> bool:
    if user.is_banned and (user.banned_until is None or user.banned_until > datetime.utcnow()):
        return True
    return False

def create_message(session: Session, sender_id: int, receiver_id: int, content: str):
    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    session.add(message)
    session.commit()
