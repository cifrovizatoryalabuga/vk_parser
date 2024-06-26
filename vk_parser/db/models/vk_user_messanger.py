from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin
from vk_parser.db.utils import make_pg_enum
from vk_parser.generals.enums import SendAccountStatus

MAX_SUCCESSFUL_MESSAGES = 10


class SendAccounts(TimestampMixin, Base):
    """Аккаунты с которых будет производиться рассылка"""

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    login: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        unique=True,
    )
    password: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    secret_token: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    proxy: Mapped[str] = mapped_column(String(1024), nullable=False)
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
    status: Mapped[SendAccountStatus] = mapped_column(
        make_pg_enum(
            SendAccountStatus,
            schema=None,
        ),
        nullable=False,
        server_default=SendAccountStatus.ACTIVE.value,
    )


class Messages(TimestampMixin, Base):
    """Сообщения для массовой рассылки пользователям"""

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
