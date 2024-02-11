import datetime
import pathlib

import pandas as pd

BASE_PATH = pathlib.Path(__file__).parent
DATA_PATH = BASE_PATH / "data"
START_DATE = datetime.datetime(year=2018, month=1, day=1, tzinfo=datetime.UTC)
CURRENT_DATE = datetime.datetime.now(tz=datetime.UTC)
RETURNS_YEARS = [1, 3, 5]


def sort_df(df: pd.DataFrame, *, column: str, sort_ascending: bool = False):
    return df.sort_values(by=column, ascending=sort_ascending).reset_index().drop(columns=["index"])
