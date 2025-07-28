"""
Decorators module for input validation and error handling.
"""
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from .logger import logger

F = TypeVar('F', bound=Callable[..., Any])


def validate_input(validator: Callable[[Any], bool], error_message: str) -> Callable[[F], F]:
    """
    Decorator for input validation.

    Args:
        validator (Callable[[Any], bool]): Function that validates the input
        error_message (str): Error message to raise if validation fails

    Returns:
        Callable: Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                if not validator(result):
                    raise ValueError(error_message)
                return result
            except Exception as e:
                logger.error(f"Validation error in {func.__name__}: {str(e)}")
                raise
        return cast(F, wrapper)
    return decorator


def log_exceptions(func: F) -> F:
    """
    Decorator to log exceptions.

    Args:
        func (Callable): Function to decorate

    Returns:
        Callable: Decorated function
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}")
            raise
    return cast(F, wrapper)
