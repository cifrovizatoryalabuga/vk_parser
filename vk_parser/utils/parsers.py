import logging
import re
from collections.abc import Mapping, Sequence

from aiohttp import ClientError

from vk_parser.clients.vk import VK_API_BASE_URL, Vk, VkWallPost
from vk_parser.db.models.vk_user_messanger import SendAccounts
from vk_parser.utils.http import create_web_session

log = logging.getLogger(__name__)

VK_USER_ID_PATTERN = r"\[id(\d*)\|"


def search_user_vk_ids(post_text: str) -> Sequence[int]:
    founds = re.findall(VK_USER_ID_PATTERN, post_text)
    if not founds:
        return tuple()
    return tuple(map(int, founds))


def map_users_in_posts(posts: Sequence[VkWallPost]) -> Mapping[int, int]:
    users_in_posts: dict[int, int] = {}
    for post in posts:
        for user_vk_id in post.user_vk_ids:
            users_in_posts[user_vk_id] = users_in_posts.get(user_vk_id, 0) + 1
    return users_in_posts


async def get_conversations_for_account(account: SendAccounts) -> int:
    async with create_web_session() as session:
        vk_client = Vk(
            url=VK_API_BASE_URL,
            session=session,
            vk_api_service_token=account.secret_token,
            vk_api_version="5.81",
        )
        try:
            conversations = await vk_client.get_conversations(
                messages_filter="unread",
                count=0,
            )
            return conversations.unread_count
        except ClientError as e:
            log.error("Get conversation for %s: %s", account, e)
            return 0
