import datetime
import pathlib
import csv
import pandas as pd
import math
from functools import partial

BASE_PATH = pathlib.Path(__file__).parent
DATA_PATH = BASE_PATH / "data"
START_DATE = datetime.datetime(year=2018, month=1, day=1, tzinfo=datetime.UTC)
CURRENT_DATE = datetime.datetime.now(tz=datetime.UTC)
RETURNS_YEARS = [1, 3, 5]

table_data = list[dict[str, str | float]]


def sort_data(data: table_data, *, column: str, sort_ascending: bool = False) -> table_data:
    sort_key = partial(_sort_key, col=column)
    return sorted(data, key=sort_key, reverse=not sort_ascending)


def _sort_key(row: dict[str, float | str], col: str) -> float | str:
    if isinstance(row[col], str):
        return row[col]
    elif math.isnan(row[col]):
        return float("-inf")
    else:
        return row[col]


def csv_to_dict(file_name: str) -> table_data:
    with open(DATA_PATH / file_name, "r") as f:
        csv_data = list(csv.DictReader(f))
    for row in csv_data:
        for col, value in row.items():
            try:
                row[col] = float(value)
            except ValueError:
                if value == "":
                    row[col] = float("nan")

    return csv_data
