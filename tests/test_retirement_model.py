import pytest

from pages import retirement_model


@pytest.mark.parametrize(
    "net_income, gross_income_required",
    [(0, 0), (10_000, 10_000), (19_514, 20_000), (28_014, 30_000), (36_514, 40_000), (45_014, 50_000)],
)
def test_calculate_gross_income(net_income: float | int, gross_income_required: float | int):
    """Testing against values calculated by Aviva 2024-05-26
    https://www.direct.aviva.co.uk/myfuture/PensionWithdrawalTaxCalculator/TaxResults"""

    answer = retirement_model.calculate_gross_income(net_income)
    assert answer == gross_income_required
