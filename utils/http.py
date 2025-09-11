# utils / http.py
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class BackoffConfig:
    """Configuration for exponential backoff."""


    def __init__(
        self,
            initial_delay: float = 1.0,
            max_delay: float = 60.0,
            multiplier: float = 2.0,
            jitter: bool = True,
            max_retries: int = 3,
            ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.max_retries = max_retries


def calculate_backoff_delay(attempt: int, config: BackoffConfig) -> float:
    """Calculate the delay for a given attempt using exponential backoff."""
    if attempt <= 0:
        return 0

    # Calculate exponential delay
    delay = config.initial_delay * (config.multiplier ** (attempt - 1))

    # Cap at max_delay
    delay = min(delay, config.max_delay)

    # Add jitter to prevent thundering herd
    if config.jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def with_backoff(
    config: Optional[BackoffConfig] = None,
        exceptions: tuple = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """Decorator to add exponential backoff to a function.

    Args:
        config: BackoffConfig instance. If None, uses default config.
        exceptions: Tuple of exception types to retry on.
        on_retry: Optional callback called on each retry with (attempt, exception).
    """
    if config is None:
        config = BackoffConfig()


    def decorator(func: Callable) -> Callable:
        @wraps(func)


        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt >= config.max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_retries + 1} attempts: {e}"
                        )
                        raise e

                    delay = calculate_backoff_delay(attempt + 1, config)

                    if on_retry:
                        on_retry(attempt + 1, e)

                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{config.max_retries + 1}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            # This should never be reached, but just in case
            raise last_exception or Exception("Unknown error in backoff wrapper")

        return wrapper

    return decorator


def retry_with_backoff(
    func: Callable,
        *args,
        config: Optional[BackoffConfig] = None,
        exceptions: tuple = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs,
) -> Any:
    """Execute a function with exponential backoff retry logic.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        config: BackoffConfig instance. If None, uses default config.
        exceptions: Tuple of exception types to retry on.
        on_retry: Optional callback called on each retry with (attempt, exception).
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function call.

    Raises:
        The last exception if all retries are exhausted.
    """
    if config is None:
        config = BackoffConfig()

    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e

            if attempt >= config.max_retries:
                logger.error(
                    f"Function {func.__name__} failed after {config.max_retries + 1} attempts: {e}"
                )
                raise e

            delay = calculate_backoff_delay(attempt + 1, config)

            if on_retry:
                on_retry(attempt + 1, e)

            logger.warning(
                f"Function {func.__name__} failed on attempt {attempt + 1}/{config.max_retries + 1}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            time.sleep(delay)

    # This should never be reached, but just in case
    raise last_exception or Exception("Unknown error in retry_with_backoff")

# Predefined configurations for common use cases
HTTP_BACKOFF_CONFIG = BackoffConfig(
    initial_delay = 0.5, max_delay = 30.0, multiplier = 2.0, jitter = True, max_retries = 3
)

API_BACKOFF_CONFIG = BackoffConfig(
    initial_delay = 1.0, max_delay = 60.0, multiplier = 1.5, jitter = True, max_retries = 5
)

DATABASE_BACKOFF_CONFIG = BackoffConfig(
    initial_delay = 0.1, max_delay = 10.0, multiplier = 2.0, jitter = True, max_retries = 3
)

# Convenience functions for common HTTP scenarios


def http_request_with_backoff(
    request_func: Callable, *args, config: Optional[BackoffConfig] = None, **kwargs
) -> Any:
    """Execute an HTTP request with backoff on common HTTP errors."""
    import requests

    if config is None:
        config = HTTP_BACKOFF_CONFIG

    # Common HTTP exceptions to retry on
    http_exceptions = (
        requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
            requests.exceptions.RequestException,
            )


    def on_retry(attempt: int, exception: Exception):
        logger.info(
            f"HTTP request retry {attempt}: {type(exception).__name__}: {exception}"
        )

    return retry_with_backoff(
        request_func,
            *args,
            config = config,
            exceptions = http_exceptions,
            on_retry = on_retry,
            **kwargs,
            )


def http_get_with_backoff(
    url: str, config: Optional[BackoffConfig] = None, **kwargs
) -> Any:
    """Execute an HTTP GET request with backoff on common HTTP errors."""
    import requests

    if config is None:
        config = HTTP_BACKOFF_CONFIG


    def make_request():
        response = requests.get(url, **kwargs)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response

    return http_request_with_backoff(make_request, config = config)

# Example usage and testing functions
if __name__ == "__main__":
    # Example: Function that fails randomly
    @with_backoff(config = BackoffConfig(max_retries = 3))


    def flaky_function():
        if random.random() < 0.7:  # 70% chance of failure
            raise Exception("Random failure")
        return "Success!"

    # Example: HTTP request with backoff


    def example_http_request():
        import requests

        return http_request_with_backoff(
            requests.get,
                "https://httpbin.org / status / 500",  # This will always return 500
            timeout = 5,
                )

    print("Testing backoff functionality...")
    try:
        result = flaky_function()
        print(f"Flaky function result: {result}")
    except Exception as e:
        print(f"Flaky function failed: {e}")
