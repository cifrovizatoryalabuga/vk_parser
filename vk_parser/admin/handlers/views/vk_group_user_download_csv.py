import csv
import io
from collections.abc import Sequence

from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest

from vk_parser.admin.handlers.base import DependenciesMixin
from vk_parser.generals.models.vk_group_user import VkGroupUser


class VkGroupUserDownloadCsvHandler(web.View, DependenciesMixin):
    async def get(self) -> web.Response:
        parser_request_id = self._get_id()

        users = await self.vk_storage.get_users_by_parser_request_id(parser_request_id)
        csv_data = users_to_csv(users)
        file_name = f"users_{parser_request_id}.csv"
        headers = {"Content-disposition": f"attachment; filename={file_name}"}
        return web.Response(
            body=csv_data,
            headers=headers,
        )

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")


def users_to_csv(users: Sequence[VkGroupUser]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(
        ["vk_id", "first_name", "last_name", "birth_date", "last_visit_vk_date"]
    )
    for user in users:
        writer.writerow(
            [
                user.vk_user_id,
                user.first_name,
                user.last_name,
                user.birth_date.strftime("%d.%m.%Y") if user.birth_date else "",
                user.last_visit_vk_date.strftime("%d.%m.%Y")
                if user.last_visit_vk_date
                else "",
            ]
        )
    return output.getvalue()
