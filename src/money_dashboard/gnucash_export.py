"""Module to extract data from GnuCash. Gets the data into the simplest possible python standard
data structure or DataFrame
"""
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


def get_commodity_quantities(account_section: str):
    assets = root.children(name="Assets")
    section = assets.children(name=account_section)
    commodity_amounts = {}
    for account in section.children:
        for investment in account.children:
            try:
                commodity_amounts[investment.commodity.mnemonic] += investment.get_balance()
            except KeyError:
                commodity_amounts[investment.commodity.mnemonic] = investment.get_balance()
    return pd.DataFrame(
        dict(commodity=[k for k in commodity_amounts.keys()], quantity=[float(v) for v in commodity_amounts.values()])
    )


def get_time_series(time_delta: relativedelta) -> list[datetime.date]:
    current_date = datetime.datetime.now()
    time_series = []
    while current_date >= GNUCASH_STARTDATE:
        time_series.append(current_date.date())
        current_date -= time_delta
    return time_series
