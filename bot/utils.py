from functools import wraps
from typing import Any, Callable


def errors_wrapper(default_error_response: bool) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            try:
                return await func(self, *args, **kwargs)
            except Exception:
                return default_error_response

        return wrapper

    return decorator


handle_auth_errors = errors_wrapper(False)
