from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class GiftModel(Base):
    __tablename__ = "gifts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)

    gift_id: Mapped[int] = mapped_column(BigInteger, index=True, unique=True)

    emoji: Mapped[str] = mapped_column(String, nullable=False)

    star_count: Mapped[int] = mapped_column(Integer, nullable=False)

    remaining_count: Mapped[int] = mapped_column(
        Integer, nullable=True, default=None)

    total_count: Mapped[int] = mapped_column(
        Integer, nullable=True, default=None)

    is_new: Mapped[bool] = mapped_column(default=True, nullable=False)
