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
    def __init__(self, commodity_prices: pd.DataFrame, quantities: pd.DataFrame) -> None:
        """commodity_prices: DataFrame with a datetime index and commodity names in the columns"""
        self.prices = commodity_prices
        self.quantities = quantities
        self.average_returns: list[dict[str, float]] = [{}]
        self.summary = self._set_summary()
        print(self.summary.to_dict("records"))

    @classmethod
    def from_gnucash(cls, commodities: pd.DataFrame, quantities: pd.DataFrame):
        """commodities: expects a DataFrame with a column for dates (date - as strings), commodity names
        (commmodity.mnemonic), and commodity prices (value)"""
        df = commodities.assign(date=lambda df_: pd.to_datetime(df_.date)).pivot_table(
            index="date", columns="commodity.mnemonic", values="value"
        )
        mask = df.index >= START_DATE
        df = df.loc[mask].ffill().drop(columns=["EUR", "GBP"]).sort_index()
        return cls(df, quantities)

    @property
    def latest_prices(self) -> pd.DataFrame:
        return (
            self.prices.sort_index(ascending=True)
            .iloc[[-1], :]
            .T.reset_index()
            .set_axis(["commodity", "latest_price"], axis=1)
        )

    def _set_summary(self):
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
        date_mask = self.prices.index >= datetime.datetime(
            year=CURRENT_DATE.year - dy, month=CURRENT_DATE.month, day=CURRENT_DATE.day
        )
        return (
            self.prices.loc[date_mask, :]
            .sort_index()
            .iloc[0]
            .T.reset_index()
            .set_axis(["commodity", f"price_year{dy}"], axis=1)
        )

    def sorted_summary(self, column: str, sort_ascending: bool = False):
        return self.summary.sort_values(by=column, ascending=sort_ascending).reset_index().drop(columns=["index"])


class Assets:
    def __init__(self) -> None:
        pass


def get_commodity_data() -> list[dict]:
    return _load_data()["commodities"]


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

    return df_commodity


all_commodities = [CommodityType(**c) for c in get_commodity_data()]
commodities = Commodities.from_gnucash(
    gnucash_export.get_commodity_prices(),
    gnucash_export.get_commodity_quantities("Savings & Investments"),
)
