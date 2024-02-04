from money_dashboard import data
from typing import Generator, Final
import pytest
import datetime
import pandas as pd
from pytest_mock import MockFixture

REFERENCE_DATE: Final[datetime.datetime] = datetime.datetime(2024, 1, 1, 0, 0, 0)


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


@pytest.fixture
def datetime_fixture(mocker: MockFixture):
    mocked_datetime = mocker.patch(
        "money_dashboard.data.datetime",
    )
    mocked_datetime.datetime.now.return_value = REFERENCE_DATE
    yield mocked_datetime


def test_Commodity_total_value(commodities: data.Commodities):
    assert commodities.total_value == pytest.approx(63841.012545484904)


def test_base_prices(commodities):
    assert commodities == 4
