import datetime

import pandas as pd
import piecash
from dateutil.relativedelta import relativedelta

GNUCASH_STARTDATE = datetime.datetime(year=2018, month=1, day=1)

book = piecash.open_book("/home/nick/Documents/Money/GnuCash/NB_accounts_2023.gnucash")
root = book.root_account  # select the root_account


def get_commodity_prices() -> pd.DataFrame:
    return book.prices_df()


def get_assets_time_series() -> pd.DataFrame:
    assets = root.children(name="Assets")
    dates = get_time_series(relativedelta(months=1))
    asset_values = {"date": dates}
    asset_accounts = [acc.name for acc in assets.children if acc.get_balance(recurse=True) and not acc.hidden]
    for account in asset_accounts:
        asset_values[account] = [
            assets.children(name=account).get_balance(recurse=True, at_date=date) for date in asset_values["date"]
        ]
    return pd.DataFrame(asset_values)


def get_time_series(time_delta: relativedelta) -> list[datetime.date]:
    current_date = datetime.datetime.now()
    time_series = []
    while current_date >= GNUCASH_STARTDATE:
        time_series.append(current_date.date())
        current_date -= time_delta
    return time_series


commodity_prices = get_commodity_prices()
