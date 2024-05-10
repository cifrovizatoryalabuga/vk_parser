import asyncio
import math
from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from vk_parser.db.utils import inject_session
from vk_parser.generals.models.pagination import (
    ItemType,
    PaginationMeta,
    PaginationResponse,
)


class PaginationMixin:
    async def _paginate(
        self,
        query: Select,
        page: int,
        page_size: int,
        model_type: type[ItemType],
    ) -> PaginationResponse[ItemType]:
        items, total = await asyncio.gather(
            self._paginate_items(
                query=query,
                page=page,
                page_size=page_size,
            ),
            self._paginate_count(query=query),
        )

        return PaginationResponse[model_type](  # type: ignore[valid-type]
            items=items,
            meta=PaginationMeta(
                page=page,
                pages=int(math.ceil(total / page_size)) or 1,
                total=total,
                page_size=page_size,
            ),
        )

    @inject_session
    async def _paginate_items(self, session: AsyncSession, query: Select, page: int, page_size: int) -> Sequence:
        return (await session.scalars(query.limit(page_size).offset((page - 1) * page_size))).all()

    @inject_session
    async def _paginate_count(self, session: AsyncSession, query: Select) -> int:
        return (await session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
