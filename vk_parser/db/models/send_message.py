from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin
from vk_parser.db.utils import make_pg_enum
from vk_parser.generals.enums import SendMessageStatus


class SendMessages(TimestampMixin, Base):
    """Отправленные сообщения для рассылки"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parser_request_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("parser_request.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[SendMessageStatus] = mapped_column(
        make_pg_enum(
            SendMessageStatus,
            name="status",
            schema=None,
        ),
        nullable=False,
        server_default=SendMessageStatus.PROCESSING.value,
    )
    successful_messages: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    necessary_messages: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
