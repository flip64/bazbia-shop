from contextlib import contextmanager
from functools import wraps

from core.logging_config import (
    clear_run_id,
    generate_run_id,
    get_logger,
    set_run_id,
)


logger = get_logger(__name__)


@contextmanager
def rubika_run(operation, options=None):
    run_id = generate_run_id("rubika")
    set_run_id(run_id)
    safe_options = {
        key: value
        for key, value in (options or {}).items()
        if key not in {"settings", "pythonpath", "traceback", "stdout", "stderr"}
    }
    logger.info(
        "شروع عملیات روبیکا | operation=%s | options=%s",
        operation,
        safe_options,
    )
    try:
        yield
    except Exception:
        logger.exception("عملیات روبیکا ناموفق بود | operation=%s", operation)
        raise
    else:
        logger.info("پایان موفق عملیات روبیکا | operation=%s", operation)
    finally:
        clear_run_id()


def logged_rubika_command(operation):
    def decorator(handle):
        @wraps(handle)
        def wrapper(self, *args, **options):
            with rubika_run(operation, options):
                return handle(self, *args, **options)

        return wrapper

    return decorator
