from datetime import date
from typing import Any, Optional

from sqlalchemy import BigInteger, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin


class VkGroupUser(TimestampMixin, Base):
    """Данные пользователя в определенной группе ВК"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    parser_request_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("parser_request.id", ondelete="CASCADE"),
        nullable=False,
    )

    vk_group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vk_group.id", ondelete="CASCADE"),
        nullable=False,
    )
    vk_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    first_name: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, index=True
    )
    last_name: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, index=True
    )
    sex: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, index=True
    )
    mobile_phone: Mapped[str | None] = mapped_column(
        String(1024), nullable=True,
    )
    home_phone: Mapped[str | None] = mapped_column(
        String(1024), nullable=True,
    )
    university_name: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, index=True
    )
    photo_100: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, index=True
    )
    city: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, index=True
    )
    last_visit_vk_date: Mapped[date | None] = mapped_column(Date, nullable=True)
