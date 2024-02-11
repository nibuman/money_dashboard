"""Module to extract data from GnuCash. Gets the data into the simplest possible python standard
data structure or DataFrame
"""

import datetime

import pandas as pd
import piecash  # Need to install latest piecash from GitHub. Pypi version gives 'cannot find imp' error
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass

GNUCASH_STARTDATE = datetime.datetime(year=2018, month=1, day=1)


@dataclass
class GNUCashData:
    commodity_prices: pd.DataFrame
    assets_time_series: pd.DataFrame
    investment_quantities: pd.DataFrame
    retirement_quantities: pd.DataFrame


def get_data() -> GNUCashData:
    with piecash.open_book("/home/nick/Documents/Money/GnuCash/NB_accounts_2023.gnucash") as book:
        root = book.root_account  # select the root_account
        return GNUCashData(
            commodity_prices=get_commodity_prices(book),
            assets_time_series=get_assets_time_series(root),
            investment_quantities=get_commodity_quantities("Savings & Investments", root),
            retirement_quantities=get_commodity_quantities("Retirement", root),
        )


def get_commodity_prices(book) -> pd.DataFrame:
    return book.prices_df()


def get_assets_time_series(root, refresh: bool = True) -> pd.DataFrame:
    """Returns a time series of every Assets account which currently has a balance and is not hidden

    This is SLOW. ~10 seconds with time delta of 1 month so by default loads a cached value
    """
    if refresh:
        assets = root.children(name="Assets")
        dates = get_time_series(relativedelta(months=1))
        asset_values = {"date": dates}
        asset_accounts = [acc.name for acc in assets.children if acc.get_balance(recurse=True) and not acc.hidden]
        for account in asset_accounts:
            asset_values[account] = [
                assets.children(name=account).get_balance(recurse=True, at_date=date) for date in asset_values["date"]
            ]
        time_series = pd.DataFrame(asset_values)
        time_series.to_feather(
            "/home/nick/Documents/Programming/money-dashboard/src/money_dashboard/data/assets_time_series_cache"
        )
    else:
        time_series = pd.read_feather(
            "/home/nick/Documents/Programming/money-dashboard/src/money_dashboard/data/assets_time_series_cache"
        )
    return time_series


def get_commodity_quantities(account_section: str, root) -> pd.DataFrame:
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
