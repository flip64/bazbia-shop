# -*- coding: utf-8 -*-

import os
import json

from .logger import info, warning


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


DATA_DIR = os.path.join(
    BASE_DIR,
    "scrap_abdisite",
    "data"
)


def get_latest_available_file():

    files = [
        f for f in os.listdir(DATA_DIR)
        if f.startswith("available") and f.endswith(".json")
    ]

    if not files:
        return None

    files.sort(
        key=lambda f: os.path.getmtime(
            os.path.join(DATA_DIR, f)
        ),
        reverse=True
    )

    return os.path.join(DATA_DIR, files[0])


def load_available_products():

    path = get_latest_available_file()

    if not path:
        warning("available_products.json پیدا نشد.")
        return []

    info("Loading {}".format(os.path.basename(path)))

    with open(path, "r", encoding="utf
