from typing import Any

import orjson


def dumps(*args: Any, **kwargs: Any) -> str:
    return orjson.dumps(*args, **kwargs).decode()
