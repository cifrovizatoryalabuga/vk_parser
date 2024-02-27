import re
from collections.abc import Mapping, Sequence

from vk_parser.clients.vk import VkWallPost

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
