from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin
from vk_parser.db.utils import make_pg_enum
from vk_parser.generals.enums import MessagesStatus


class SendAccounts(TimestampMixin, Base):
    """Аккаунты с которых будет производиться рассылка"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
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
    message: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )


class SendMessagesDetail(TimestampMixin, Base):
    """Статус массовой рассылки сообщений"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    status_message: Mapped[MessagesStatus] = mapped_column(
        make_pg_enum(
            MessagesStatus,
            name="status_messages",
            schema=None,
        ),
        nullable=False,
        server_default=MessagesStatus.SENDING.value,
    )
    success_message: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
    )
