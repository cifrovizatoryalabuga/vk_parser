from typing import NoReturn

from aiohttp import web


class RedirectToAdminHandler(web.View):
    async def get(self) -> NoReturn:
        location = self.request.app.router["admin"].url_for()
        raise web.HTTPFound(location=location)
