import logging
import sys

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"


class ColoredFormatter(logging.Formatter):
    def __init__(self, *args, use_color: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if not self.use_color:
            return message
        if record.levelno >= logging.ERROR:
            return f"{_RED}{message}{_RESET}"
        if record.levelno >= logging.WARNING:
            return f"{_YELLOW}{message}{_RESET}"
        return message


def _is_tty(stream) -> bool:
    return hasattr(stream, "isatty") and stream.isatty()


def setup_logging(level: int = logging.INFO) -> None:
    use_color = _is_tty(sys.stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        ColoredFormatter(
            "%(levelname)s %(name)s: %(message)s",
            use_color=use_color,
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(level)
