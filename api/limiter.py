from fastapi import Request, Response
from fastapi.responses import ORJSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from .utils import get_remote_address


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Replaces the default slowapi handler with a detailed JSON response."""
    response = ORJSONResponse({"detail": f"Rate limit exceeded: {exc.detail}"}, status_code=429)
    response = request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)

    return response


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
