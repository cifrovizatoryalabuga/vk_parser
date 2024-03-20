from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin
from vk_parser.db.utils import make_pg_enum
from vk_parser.generals.enums import MessagesStatus


class SendAccounts(TimestampMixin, Base):
    """Аккаунты с которых будет производиться рассылка"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    login: Mapped[str] = mapped_column(String(1024), nullable=False)
    password: Mapped[str] = mapped_column(String(1024), nullable=False)
    secret_token: Mapped[str] = mapped_column(String(1024), nullable=False)
    user_link: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    successful_messages: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    error_status: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    expire_timestamp: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )


class Messages(TimestampMixin, Base):
    """Сообщения для массовой рассылки пользователям"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
