import datetime

import pandas as pd
import piecash
from dateutil.relativedelta import relativedelta

GNUCASH_STARTDATE = datetime.date(year=2018, month=1, day=1)

book = piecash.open_book("/home/nick/Documents/Money/GnuCash/NB_accounts_2023.gnucash")
root = book.root_account  # select the root_account

assets = root.children(name="Assets")  # select child account by name
savings = assets.children(name="Savings & Investments")


def get_assets_time_series() -> pd.DataFrame:
    dates = get_time_series(relativedelta(months=1))
    asset_values = {"date": dates}
    asset_accounts = [acc.name for acc in assets.children if acc.get_balance(recurse=True) and not acc.hidden]
    for account in asset_accounts:
        asset_values[account] = [
            assets.children(name=account).get_balance(recurse=True, at_date=date) for date in asset_values["date"]
        ]
    return pd.DataFrame(asset_values)


def get_time_series(time_delta: relativedelta) -> list[datetime.date]:
    current_date = datetime.datetime.now().date()
    time_series = []
    while current_date >= GNUCASH_STARTDATE:
        time_series.append(current_date)
        current_date -= time_delta
    return time_series
