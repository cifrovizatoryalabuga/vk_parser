import jwt
from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class DeleteAccountsBDHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def post(self) -> web.Response:
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            user = await self.auth_storage.get_user_by_login(decoded_jwt["login"])
            user_id = user.id

        await self.parser_request_storage.delete_accounts(user_id)

        location = self.request.app.router["parser_request_accounts_template"].url_for()
        raise web.HTTPFound(location=location)
