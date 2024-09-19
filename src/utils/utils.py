import csv
import datetime
import math
import pathlib
from functools import partial

BASE_PATH = pathlib.Path(__file__).parents[1]
DATA_PATH = BASE_PATH.parent / "data"
START_DATE = datetime.datetime(year=2018, month=1, day=1, tzinfo=datetime.UTC)
CURRENT_DATE = datetime.datetime.now(tz=datetime.UTC)
RETURNS_YEARS = [1, 3, 5]

table_data = list[dict[str, str | float]]


def sort_data(
    data: table_data, *, column: str, sort_ascending: bool = False
) -> table_data:
    sort_key = partial(_sort_key, col=column)
    return sorted(data, key=sort_key, reverse=not sort_ascending)


def _sort_key(row: dict[str, float | str], col: str) -> float | str:
    value = row[col]
    if isinstance(value, float) and math.isnan(value):
        return float("-inf")
    else:
        return value


def csv_to_dict(file_name: str) -> table_data:
    with open(DATA_PATH / file_name) as f:
        csv_data = list(csv.DictReader(f))
    for row in csv_data:
        for col, value in row.items():
            try:
                row[col] = float(value)
            except ValueError:
                if value == "":
                    row[col] = float("nan")

    return csv_data
