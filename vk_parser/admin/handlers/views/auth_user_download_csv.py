import csv
import io
from collections import defaultdict
from collections.abc import Sequence

from aiohttp import web

from vk_parser.admin.handlers.base import DependenciesMixin
from vk_parser.db.models.auth import AuthUser as AuthUserDb
from vk_parser.generals.enums import RequestStatus
from vk_parser.utils.parsers import get_conversations_for_account


class AuthUserDownloadCsvHandler(web.View, DependenciesMixin):
    async def _auth_users_to_csv(
        self,
        auth_users: Sequence[AuthUserDb],
    ) -> str:
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(
            [
                "user",
                "parser_count",
                "success_parser_count",
                "finished_date",
                "successful_message_count",
                "conversation_count",
            ],
        )

        for auth_user in auth_users:
            writer.writerow([auth_user.login])

            accounts = await self.parser_request_storage.get_all_account_by_user(user_id=auth_user.id)
            successful_message_count = sum(account.successful_messages for account in accounts)
            conversation_count = sum(get_conversations_for_account(account) for account in accounts)
            writer.writerow(
                [
                    "",
                    "",
                    "",
                    "",
                    successful_message_count,
                    conversation_count,
                ],
            )

            parsers = await self.vk_storage.get_parser_by_auth_user(user_id=auth_user.id)
            parser_count_by_date = defaultdict(int)
            success_parser_count_by_date = defaultdict(int)
            for parser in parsers:
                if parser.finished_at is not None:
                    finished_date = parser.finished_at.date()
                    parser_count_by_date[finished_date] += 1
                    if parser.status == RequestStatus.SUCCESSFUL:
                        success_parser_count_by_date[finished_date] += 1
            for finished_date in sorted(set(parser_count_by_date.keys()) | set(success_parser_count_by_date.keys())):
                parser_count = parser_count_by_date[finished_date]
                success_parser_count = success_parser_count_by_date[finished_date]
                writer.writerow(
                    [
                        "",
                        parser_count,
                        success_parser_count,
                        finished_date.isoformat(),
                        "",
                        "",
                    ],
                )

        return output.getvalue()

    async def get(self) -> web.Resource:
        auth_users = await self.auth_storage.get_all_users()
        csv_data = await self._auth_users_to_csv(auth_users=auth_users)
        file_name = "auth_user_statistics.csv"
        headers = {"Content-disposition": f"attachment; filename={file_name}"}
        return web.Response(
            body=csv_data,
            headers=headers,
        )
