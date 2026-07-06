# -*- coding: utf-8 -*-

import os
import json

from suppliers.logger import info


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data")


def save_json(filename, data):
    """
    ذخیره داده در یک فایل JSON داخل پوشه data
    """

    path = os.path.join(DATA_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    info("Saved %s", filename)
