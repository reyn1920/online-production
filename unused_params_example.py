def func(*args: object, **kwargs: object) -> None:  # noqa: ARG001  (if you use Ruff)
    _ = (args, kwargs)  # mark as used for Pyright

# Alternative approaches for handling unused parameters:

def callback_handler(event: str, *args: object, **kwargs: object) -> None:
    """Example callback that only uses the event parameter."""
    print(f"Handling event: {event}")
    # Explicitly ignore unused parameters
    _ = (args, kwargs)

def interface_implementation(*_args: object, **_kwargs: object) -> None:
    """Implementation that doesn't need the parameters but must match interface."""
    # Using underscore prefix to indicate intentionally unused
    pass

def logging_wrapper(func_name: str, *args: object, **kwargs: object) -> None:
    """Wrapper function that logs calls but doesn't use all parameters."""
    print(f"Calling {func_name}")
    # Mark parameters as used to satisfy type checkers
    _ = (args, kwargs)