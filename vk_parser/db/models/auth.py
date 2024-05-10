from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin


class AuthUser(TimestampMixin, Base):
    """Аккаунты с которых будет производиться рассылка"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    login: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(1024), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    role: Mapped[str] = mapped_column(String(1024), nullable=False, default="user")
