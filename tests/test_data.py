from money_dashboard import data
from typing import Final
import pytest
from unittest.mock import patch, MagicMock
import datetime
import pandas as pd

REFERENCE_DATE: Final[datetime.datetime] = datetime.datetime(2024, 2, 4, 0, 0, 0)


@pytest.fixture
def quantities():
    csv_file = pd.read_feather("./tests/2024-02-04_GNUCash_quantities")
    return csv_file


@pytest.fixture
def commodity_prices():
    """Reads in data that has been exported from GNUCash then saved in Feather format to preserve types"""
    return pd.read_feather("./tests/2024-02-04_GNUCash_prices")


@pytest.fixture
def commodities(commodity_prices, quantities):
    return data.Commodities.from_gnucash(commodity_prices, quantities)


def test_Commodity_total_value(commodities: data.Commodities):
    """Value from GNUCash on 2024-02-04 = 63841.02"""
    assert pytest.approx(63841.02) == commodities.total_value


@pytest.mark.parametrize(
    ["commodity_name", "actual_price"], [("MDHAAJ", 9 + 2244 / 2449), ("VVDVWE", 589.145195), ("SMT", 7.77)]
)
def test_latest_prices(commodities: data.Commodities, commodity_name, actual_price):
    latest_price = commodities.latest_prices.set_index("commodity").at[commodity_name, "latest_price"]
    assert pytest.approx(actual_price) == latest_price


@pytest.mark.parametrize(["commodity_name", "dy", "actual_price"], [("SMT", 1, 7.134)])
def test_base_prices(commodities, commodity_name, dy, actual_price):
    data.CURRENT_DATE = REFERENCE_DATE
    base_price = commodities.base_prices(dy).set_index("commodity").at[commodity_name, f"price_year{dy}"]
    assert pytest.approx(actual_price) == base_price
