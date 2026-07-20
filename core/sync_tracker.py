# -*- coding: utf-8 -*-

import time

from dataclasses import dataclass, field
from typing import Any

from core.logging_config import (
    clear_run_id,
    generate_run_id,
    get_logger,
    set_run_id,
)


logger = get_logger(__name__)


@dataclass
class SyncStats:
    """
    آمار یک اجرای همگام‌سازی.
    """

    received: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    failed: int = 0
    skipped: int = 0

    started_at: float = field(
        default_factory=time.monotonic
    )

    def increment(
        self,
        field_name: str,
        count: int = 1,
    ) -> None:
        """
        یکی از شمارنده‌ها را افزایش می‌دهد.
        """

        if not hasattr(self, field_name):
            raise ValueError(
                f"شمارنده نامعتبر است: {field_name}"
            )

        current_value = getattr(self, field_name)

        setattr(
            self,
            field_name,
            current_value + count,
        )

    @property
    def duration_seconds(self) -> float:
        """
        مدت اجرای عملیات برحسب ثانیه.
        """

        return round(
            time.monotonic() - self.started_at,
            2,
        )

    def as_dict(self) -> dict[str, Any]:
        """
        آمار را به دیکشنری تبدیل می‌کند.
        """

        return {
            "received": self.received,
            "created": self.created,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
        }


class SyncRun:
    """
    مدیریت شروع، پایان و آمار یک عملیات همگام‌سازی.
    """

    def __init__(
        self,
        name: str,
        supplier: str | None = None,
    ):
        self.name = name
        self.supplier = supplier
        self.run_id = generate_run_id(
            prefix=supplier or "sync"
        )
        self.stats = SyncStats()

    def __enter__(self) -> "SyncRun":
        set_run_id(self.run_id)

        logger.info(
            "شروع عملیات همگام‌سازی | "
            "name=%s | supplier=%s",
            self.name,
            self.supplier or "-",
        )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> bool:
        if exc_type is not None:
            self.stats.failed += 1

            logger.exception(
                "عملیات همگام‌سازی با خطا متوقف شد | "
                "name=%s | supplier=%s | stats=%s",
                self.name,
                self.supplier or "-",
                self.stats.as_dict(),
            )

            clear_run_id()

            # خطا دوباره به لایه بالاتر منتقل می‌شود
            return False

        logger.info(
            "پایان عملیات همگام‌سازی | "
            "name=%s | supplier=%s | stats=%s",
            self.name,
            self.supplier or "-",
            self.stats.as_dict(),
        )

        clear_run_id()

        return False
