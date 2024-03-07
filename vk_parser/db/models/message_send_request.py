from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin
from vk_parser.db.utils import make_pg_enum
from vk_parser.generals.enums import MessagesStatus


class MessageSendRequest(TimestampMixin, Base):
    """Запрос на рассылку сообщений"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    status: Mapped[MessagesStatus] = mapped_column(
        make_pg_enum(
            MessagesStatus,
            name="status",
            schema=None,
        ),
        nullable=False,
        server_default=MessagesStatus.SENDING.value,
    )
    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSON(),
        nullable=False,
    )
    result_data: Mapped[dict[str, Any]] = mapped_column(
        JSON(),
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
