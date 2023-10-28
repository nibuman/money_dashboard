import pandas as pd
import datetime

from money_dashboard import gnucash_export

START_DATE = datetime.datetime(year=2018, month=1, day=1)
CURRENT_DATE = datetime.datetime.now()
RETURNS_YEARS = [1, 3, 5]


class Commodities:
    def __init__(self, commodity_prices: pd.DataFrame) -> None:
        self.prices = commodity_prices
        self.summary = self._set_summary()

    @classmethod
    def from_gnucash(cls, commodities: pd.DataFrame):
        df = commodities.assign(date=lambda df_: pd.to_datetime(df_.date)).pivot_table(
            index="date", columns="commodity.mnemonic", values="value"
        )
        mask = df.index >= START_DATE
        df = (df
              .loc[mask]
              .ffill()
              .bfill()
              .drop(columns=["EUR", "GBP"])
        )
        return cls(df)

    @property
    def latest_prices(self) -> pd.DataFrame:
        return (self.prices
                .iloc[[-1], :]
                .T
                .reset_index()
                .set_axis(["commodity", "latest_price"], axis=1)
        )

    def _set_summary(self):
        df_summary = self.latest_prices.copy()
        for dy in RETURNS_YEARS:
            base_prices = self.base_prices(dy=dy)
            df_summary = df_summary.merge(base_prices)
            df_summary[f"year{dy}"] = df_summary.latest_price / df_summary[f"price_year{dy}"]
            df_summary[f"year{dy}_percent"] = (df_summary[f"year{dy}"]) - 1
            df_summary[f"annualised{dy}_percent"] = (df_summary[f"year{dy}"] ** (1 / dy)) - 1
        return df_summary.fillna(0)

    def base_prices(self, dy: int) -> pd.DataFrame:
        mask = self.prices.index >= datetime.datetime(year=CURRENT_DATE.year - dy, month=1, day=1)
        return self.prices.loc[mask, :].iloc[0].T.reset_index().set_axis(["commodity", f"price_year{dy}"], axis=1)

    def sort_summary(self, column: str, sort_ascending: bool = False):
        self.summary = (self.summary
                        .sort_values(by=column, ascending=sort_ascending)
                        .reset_index()
                        .drop(columns=['index']) 
        ) 


commodities = Commodities.from_gnucash(gnucash_export.get_commodity_prices())
