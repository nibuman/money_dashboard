"""Module to structure the data for the dashboard views. Does not deal with any data structures
specific to the source - e.g. piecash book objects. Takes data in standard python or pandas"""

import pandas as pd
import datetime
import json
from dataclasses import dataclass
from typing import Optional

from money_dashboard import gnucash_export

START_DATE = datetime.datetime(year=2018, month=1, day=1)
CURRENT_DATE = datetime.datetime.now()
RETURNS_YEARS = [1, 3, 5]

gnucash_data = gnucash_export.get_data()


@dataclass
class CommodityType:
    name: str
    mnemonic: str
    asset_type: str
    id: Optional[str] = None
    sector: Optional[str] = None
    data_source: Optional[bool] = False
    ocf: Optional[float] = None


def _load_data():
    with open(
        "/home/nick/Documents/Programming/money-dashboard/src/money_dashboard/data/commodities_data.json", "r"
    ) as f:
        data = json.load(f)
    return data


class Commodities:
    def __init__(self, commodity_prices: pd.DataFrame, quantities: pd.DataFrame, account: str = "investment") -> None:
        """commodity_prices: DataFrame with a datetime index and commodity names in the columns"""
        self.prices = commodity_prices
        self.quantities = quantities
        self.average_returns: list[dict[str, float]] = [{}]
        self.summary = self._set_summary_and_total()  # The summary table to be displayed on the dashboard
        self.account = account

    @classmethod
    def from_gnucash(
        cls, commodities: pd.DataFrame, quantities: pd.DataFrame, account: str = "investment"
    ) -> "Commodities":
        """commodities: expects a DataFrame with a column for dates (date - as strings), commodity names
        (commmodity.mnemonic), and commodity prices (value)"""
        commodity_prices = (
            commodities.assign(date=lambda df_: pd.to_datetime(df_.date))
            .pivot_table(index="date", columns="commodity.mnemonic", values="value")
            .astype(dtype="float64")  # Explicit casting from 'object' required for 'ffill'
            .ffill()  # Without filling NaN values will get 'divide by zero' errors
            .drop(columns=["EUR", "GBP"])
            .sort_index()  # Order by date
        )
        date_mask = commodity_prices.index >= START_DATE
        return cls(commodity_prices.loc[date_mask, :], quantities, account)

    @property
    def latest_prices(self) -> pd.DataFrame:
        return (
            self.prices.sort_index(ascending=True)
            .iloc[[-1], :]
            .T.reset_index()
            .set_axis(["commodity", "latest_price"], axis=1)
        )

    def _set_summary_and_total(self) -> pd.DataFrame:
        """Set up the summary table of values to be displayed in the dashboard and `self.total_value`
        commodity	latest_price	quantity	value	price_year1	year1	year1_percent	annualised1_percent ...
        AZN	        101.809700	    301.0000	30644	108.800000	0.935751	-0.064249	-0.064249 ...
        BARC	    1.455400	    303.0000	440 	1.746400	0.833372	-0.166628	-0.166628 ...
        """
        df_summary = self.latest_prices.copy()
        df_summary = df_summary.merge(self.quantities).assign(value=lambda df_: df_.quantity * df_.latest_price)
        self.total_value = df_summary.value.sum(axis=0)
        for dy in RETURNS_YEARS:
            base_prices = self.base_prices(dy=dy)
            df_summary = df_summary.merge(base_prices)
            df_summary[f"year{dy}"] = df_summary.latest_price / df_summary[f"price_year{dy}"]
            df_summary[f"year{dy}_percent"] = (df_summary[f"year{dy}"]) - 1
            df_summary[f"annualised{dy}_percent"] = (df_summary[f"year{dy}"] ** (1 / dy)) - 1
            df_summary[f"year{dy}_percent_value"] = df_summary[f"annualised{dy}_percent"] * df_summary.value
            self.average_returns[0][f"year{dy}"] = df_summary[f"year{dy}_percent_value"].sum(axis=0) / self.total_value

        df_summary = df_summary.assign(percent_value=df_summary.value / self.total_value)
        df_summary = add_commodity_data(df_summary)
        active_mask = df_summary.quantity > 0
        return df_summary.loc[active_mask]

    def base_prices(self, dy: int) -> pd.DataFrame:
        """Returns a dataframe with the last price of each commodity a given number of years ago,
        where the price column is dynamically named `price_year{dy}`, e.g for `dy = 3`:
        index    commodity    price_year3
        0        stock_name1  12.265670
        1        stock_name2  13.743852

        NOTE: Prices within the last `dy` years are filtered out and the most recent remaining is used.
        This could be considerably more than `dy` years ago depending on the regularity of price data.

        keyword arguments:
        dy -- year delta, the number of years before the current date
        """
        date_mask = self.prices.index >= datetime.datetime(
            year=CURRENT_DATE.year - dy, month=CURRENT_DATE.month, day=CURRENT_DATE.day
        )
        return (
            self.prices.loc[date_mask, :]
            .sort_index()
            .iloc[0, :]
            .T.reset_index()
            .set_axis(["commodity", f"price_year{dy}"], axis=1)
        )

    def sorted_summary(self, column: str, sort_ascending: bool = False):
        return self.summary.sort_values(by=column, ascending=sort_ascending).reset_index().drop(columns=["index"])

    def by_asset_type(self):
        return (
            self.summary.groupby('commodity_type')
            .agg(
                type_value=('value', 'sum'),
                commodities=('commodity', lambda x: ", ".join(x)),
            )
            .reset_index()
            .merge(get_investment_mix_data(f"{self.account}_mix"))
            .assign(
                actual_percent=lambda df_: df_.type_value / self.total_value,
                ideal_mix=lambda df_: df_.ideal_mix_percent * self.total_value,
                change_required=lambda df_: df_.ideal_mix - df_.type_value,
            )
        )


class Assets:
    def __init__(self, asset_values: pd.DataFrame) -> None:
        self.asset_values = asset_values

    @classmethod
    def from_gnucash(cls, assets_time_series: pd.DataFrame):
        assets_time_series = assets_time_series.assign(
            available_total=lambda df_: df_.loc[:, ["Savings & Investments", "Current Assets"]].sum(axis=1),
            total=lambda df_: df_.loc[:, "Savings & Investments":"Retirement"].sum(axis=1),
        )
        return cls(assets_time_series)

    @property
    def latest_values(self):
        return self.asset_values.iloc[[0], 1:]


class Retirement_Model:
    def __init__(self, asset_values: pd.DataFrame, historic_data: dict) -> None:
        """asset_values: the current data, expects the full Assets.asset_values dataframe
        historic_data: expects the dict of years/values from the json datafile
        """
        actual_values = self.merge_current_historic_data(asset_values, historic_data)
        self.model = self.create_model(actual_values)

    def merge_current_historic_data(self, asset_values, historic_data):
        current_data = asset_values.loc[:, ["date", "Retirement"]].rename(columns={"Retirement": "actual_values"})
        historic_data = pd.DataFrame(
            {
                "date": [datetime.date(year=int(k), month=1, day=1) for k in historic_data.keys()],
                "actual_values": [float(v) for v in historic_data.values()],
            }
        )
        return pd.concat([current_data, historic_data]).sort_values(by="date")

    def create_model(self, actual_values):
        return actual_values.assign(date=pd.to_datetime(actual_values.date), age=lambda df_: df_.date.dt.year - 1975)


def get_commodity_data() -> list[dict]:
    return _load_data()["commodities"]


def get_historic_retirement_data() -> dict:
    return _load_data()["retirement_historic_data"]


def get_investment_mix_data(account: str = "investment_mix") -> pd.DataFrame:
    investment_mix = _load_data()[account]
    return pd.DataFrame(
        {
            "commodity_type": [commodity_type for commodity_type in investment_mix.keys()],
            "ideal_mix_percent": [mix for mix in investment_mix.values()],
        }
    )


def get_commodity(mnemonic: str) -> CommodityType:
    for commodity in all_commodities:
        if commodity.mnemonic == mnemonic:
            return commodity
    return CommodityType(name="unknown", mnemonic=mnemonic, asset_type="unknown", id="unknown")


def add_commodity_data(df_commodity: pd.DataFrame):
    df_commodity = df_commodity.assign(
        commodity_name="",
        commodity_type="",
        commodity_sector="",
        commodity_id="",
        commodity_ocf=0.0,
    )
    for mnemonic in df_commodity.commodity.values:
        commodity = get_commodity(mnemonic=mnemonic)
        mask = df_commodity.commodity.values == mnemonic
        df_commodity.loc[mask, "commodity_name"] = commodity.name
        df_commodity.loc[mask, "commodity_ocf"] = commodity.ocf
        df_commodity.loc[mask, "commodity_type"] = commodity.asset_type
        df_commodity.loc[mask, "commodity_id"] = commodity.id

    return df_commodity


def get_commodities(account: str) -> Commodities:
    """Return a Commodities object of the given account type such as investments, or retirement"""
    account_quantity_map = {"investment": "Savings & Investments", "retirement": "Retirement"}
    if account == "investment":
        quantities = gnucash_data.investment_quantities
    elif account == "retirement":
        quantities = gnucash_data.retirement_quantities
    else:
        raise ValueError(f"{account} is not a known account type")
    return Commodities.from_gnucash(
        commodities=gnucash_data.commodity_prices,
        quantities=quantities,
        account=account,
    )


def get_assets() -> Assets:
    return Assets.from_gnucash(gnucash_data.assets_time_series)


all_commodities = [CommodityType(**c) for c in get_commodity_data()]
investments = get_commodities("investment")
retirement = get_commodities("retirement")
assets = get_assets()
retirement_model = Retirement_Model(assets.asset_values, get_historic_retirement_data())
