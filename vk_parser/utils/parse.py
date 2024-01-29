import re
from collections.abc import Sequence

VK_USER_ID_PATTERN = r"\[id(\d*)\|"


def search_user_vk_ids(post_text: str) -> Sequence[int]:
    founds = re.findall(VK_USER_ID_PATTERN, post_text)
    if not founds:
        return tuple()
    return tuple(map(int, founds))
