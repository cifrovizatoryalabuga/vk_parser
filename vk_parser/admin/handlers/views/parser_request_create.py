from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
import jwt

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin
from vk_parser.generals.enums import ParserTypes, RequestStatus
from vk_parser.generals.models.parser_request import (
    ParsePostsVkForm,
    SimpleVkForm,
)


class ParserRequestCreateTemplateHandler(web.View, DependenciesMixin, CreateMixin):
    @aiohttp_jinja2.template("./parser_request/create.html.j2")
    async def get(self) -> Mapping[str, Any]:
        jwt_token = self.request.cookies.get('jwt_token')
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            return {
                "user_info": decoded_jwt,
                "ParserTypes": ParserTypes,
            }
        response = web.HTTPFound('/admin/login/')
        raise response

    @aiohttp_jinja2.template("./parser_request/create.html.j2")
    async def post(self) -> Mapping[str, Any]:
        input_data = await self.parse_form(schemas=[ParsePostsVkForm, SimpleVkForm])
        jwt_token = self.request.cookies.get('jwt_token')
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                response = web.HTTPFound('/admin/login/')
                raise response
        if input_data is None:
            return {
                "error": True,
                "ParserTypes": ParserTypes,
            }

        user = await self.auth_storage.get_user_by_login(decoded_jwt['login'])
        parser_request = await self.parser_request_storage.create(
            input_data=input_data.model_dump(mode="json"),
            user_id=user.id,
        )
        if parser_request is None:
            raise HTTPInternalServerError(reason="Can't create parser request")
        await self.amqp_master.create_task(
            input_data.parser_type,  # type: ignore[attr-defined]
            kwargs=dict(
                parser_request_id=parser_request.id,
                input_data=input_data.model_dump(),
            ),
        )
        parser_request = (
            await self.parser_request_storage.update_status(
                id_=parser_request.id,
                status=RequestStatus.QUEUED,
            )
            or parser_request
        )
        location = self.request.app.router["parser_request_detail_template"].url_for(
            id=str(parser_request.id)
        )
        raise web.HTTPFound(location=location)
