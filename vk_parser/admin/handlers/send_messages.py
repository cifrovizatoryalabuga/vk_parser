from random import choice
from aiohttp import ClientSession, web
from aiomisc import timeout
import asyncio

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class SendMessagesHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def post(self) -> web.Response:
        # Извлекаем JSON данные из POST запроса
        data = await self.request.json()
        print(data)
        # Проверяем, содержится ли ключ parser_id в данных
        if 'parser_id' in data:
            # Извлекаем значение parser_id
            parser_id = data['parser_id']
            # Продолжаем выполнение вашего кода
            redirector_task = asyncio.create_task(
                self.parser_request_storage.redirector(url="/")
            )
            send_messages_task = asyncio.create_task(self.send_messages(parser_id))

            await asyncio.gather(redirector_task, send_messages_task)

            return web.json_response({"status": "success"})
        else:
            # Если ключ parser_id отсутствует, возвращаем ошибку
            return web.json_response({"error": "Parser ID not found"}, status=400)

    async def send_messages(self, parser_request_id: int) -> None:
        users = await self.vk_storage.get_users_by_parser_request_id(parser_request_id)
        async with ClientSession() as session:
            for user in users:
                try:
                    await self.send_message_to_user(session, user)  # type: ignore
                except ConnectionError:
                    pass

                await asyncio.sleep(10)
        return None

    async def send_message_to_user(self, session, user: str) -> None:  # type: ignore
        async with session.post(
            "https://api.vk.com/method/messages.send",
            params={
                "user_id": user.vk_user_id,  # type: ignore
                "access_token": choice(
                    await self.parser_request_storage.get_random_account()
                ).secret_token,
                "message": choice(
                    await self.parser_request_storage.get_random_message()
                ).message,
                "random_id": 0,
                "v": "5.131",
            },
        ) as response:
            await response.json()
            print(response)

        return None
