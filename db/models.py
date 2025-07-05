from sqlalchemy import Column, Integer, String, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    username = Column(String(50), nullable=False)
    balance = Column(Integer, default=0)
    status = Column(String(20), default='user', nullable=False)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, balance={self.balance})>"


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    telegram_payment_charge_id = Column(
        String, nullable=False)
    payload = Column(String)
    status = Column(Enum("completed", "refunded"),
                    default="completed", nullable=False)
    time = Column(String)

    def __repr__(self):
        return f"<Transaction(user_id={self.user_id}, amount={self.amount}, status={self.status})>"


class AutoBuySettings(Base):
    __tablename__ = "auto_buy_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    status = Column(
        Enum("enabled", "disabled"),
        default="disabled",
        nullable=False
    )
    price_limit_from = Column(Integer, default=0.0, nullable=False)
    price_limit_to = Column(Integer, default=10**9, nullable=False)
    supply_limit = Column(Integer, default=10**9)
    cycles = Column(Integer, default=1, nullable=False)
    
    # Новое поле для фильтрации unlimited подарков
    skip_unlimited = Column(Boolean, default=True, nullable=False)  # По умолчанию пропускаем unlimited
    
    def __repr__(self):
        return (f"<AutoBuySettings(user_id={self.user_id}, status={self.status}, "
                f"price_limit_from={self.price_limit_from}, price_limit_to={self.price_limit_to}, "
                f"supply_limit={self.supply_limit}, cycles={self.cycles}, "
                f"skip_unlimited={self.skip_unlimited})>")

class Gift(Base):
    __tablename__ = "gifts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gift_id = Column(String, unique=True, nullable=False)
    price = Column(Integer, nullable=False)
    remaining_count = Column(Integer, nullable=True)
    total_count = Column(Integer, nullable=True)
    is_new = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Gift(gift_id={self.gift_id}, price={self.price}, remaining_count={self.remaining_count}, is_new={self.is_new})>"
