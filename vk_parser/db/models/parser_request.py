from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin
from vk_parser.db.utils import make_pg_enum
from vk_parser.generals.enums import RequestStatus


class ParserRequest(TimestampMixin, Base):
    """Запрос на парсинг"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[RequestStatus] = mapped_column(
        make_pg_enum(
            RequestStatus,
            name="status",
            schema=None,
        ),
        nullable=False,
        server_default=RequestStatus.PENDING.value,
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
