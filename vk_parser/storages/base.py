import math

from sqlalchemy import ScalarResult, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from vk_parser.db.utils import inject_session
from vk_parser.generals.models.pagination import (
    ItemType,
    PaginationMeta,
    PaginationResponse,
)


class PaginationMixin:
    @inject_session
    async def _paginate(
        self,
        session: AsyncSession,
        query: Select,
        page: int,
        page_size: int,
        model_type: type[ItemType],
    ) -> PaginationResponse[ItemType]:
        result: ScalarResult = await session.scalars(
            query.limit(page_size).offset((page - 1) * page_size)
        )
        total: int = (
            await session.execute(select(func.count()).select_from(query.subquery()))
        ).scalar_one()
        return PaginationResponse[model_type](  # type: ignore[valid-type]
            items=result.all(),
            meta=PaginationMeta(
                page=page,
                pages=int(math.ceil(total / page_size)) or 1,
                total=total,
                page_size=page_size,
            ),
        )
