# -*- coding: utf-8 -*-

import os
import json

from suppliers.logger import info, warning


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data")


def load_json(filename):
    """
    بارگذاری یک فایل JSON از پوشه data
    """

    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        warning(f"{filename} پیدا نشد.")
        return []

    info(f"{filename} Loading %s")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_available_products():
    return load_json("available_products.json")


def load_productdata():
    return load_json("productdata.json")
