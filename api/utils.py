import logging
from typing import Any, Mapping, Optional, Union

from fastapi import Request
from rich.console import Console
from rich.logging import RichHandler


def slugify(string: str) -> str:
    return string.lower().replace(" ", "_")


class Handler(RichHandler):
    """Logger extension to configure the Console directly with it."""

    def __init__(
        self,
        level: Union[int, str] = logging.NOTSET,
        console: Optional[Union[Console, Mapping[str, Any]]] = None,
        **kwargs,
    ) -> None:
        super().__init__(level=level, **kwargs)

        if console:
            if isinstance(console, Console):
                self.console = console
            else:
                self.console = Console(**console)


def get_remote_address(request: Request):
    """Get the actual ip address using headers."""
    ip = (
        request.headers.get("CF-CONNECTING-IP")
        or request.headers.get("X-REAL-IP")
        or request.headers.get("X-FORWARDED-FOR")
        or request.client.host
        or "127.0.0.1"
    )
    return ip


logger = logging.getLogger("gunicorn.fastapi")
