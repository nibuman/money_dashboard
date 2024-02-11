import pathlib
import datetime

BASE_PATH = pathlib.Path(__file__).parent
DATA_PATH = BASE_PATH / "data"
START_DATE = datetime.datetime(year=2018, month=1, day=1)
CURRENT_DATE = datetime.datetime.now()
RETURNS_YEARS = [1, 3, 5]


def sort_df(df, column: str, sort_ascending: bool = False):
    return df.sort_values(by=column, ascending=sort_ascending).reset_index().drop(columns=["index"])
