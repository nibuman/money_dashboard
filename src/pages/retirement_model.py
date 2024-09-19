import math

import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html

from utils.utils import csv_to_dict


class RetirementModel:
    "Models growth of retirement fund starting from the last year that money was paid in"

    def __init__(self, model_data: list[dict[str, str | float]]) -> None:
        self.year = [int(row["year"]) for row in model_data]
        self.age = [int(row["age"]) for row in model_data]
        self.actual_values = [float(row["actual_values"]) for row in model_data]
        self.target = [0] * len(self.year)
        self.model_values = [float("nan")] * len(self.year)

    def calculate_model_value(self, net_returns, contributions):
        model_value = self.actual_values[self.start_year_index]
        for idx, _ in enumerate(self.model_values):
            if idx < self.start_year_index:
                continue
            elif idx == self.start_year_index:
                pass
            else:
                model_value = (model_value * net_returns) + contributions
            self.model_values[idx] = model_value

    @property
    def start_year_index(self) -> int:
        for idx, value in enumerate(self.actual_values):
            if math.isnan(value):
                return idx - 1
        raise ValueError

    def set_target(self, target_value):
        self.target = [target_value] * len(self.year)

    @property
    def target_met_year(self) -> int:
        for year, value in zip(self.year, self.model_values):
            if value >= self.target[0]:
                return year
        raise ValueError

    @property
    def target_met_age(self) -> int:
        for age, value in zip(self.age, self.model_values):
            if value >= self.target[0]:
                return age
        raise ValueError

    def as_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Year": self.year,
                "Actual Values": self.actual_values,
                "Target": self.target,
                "Model Values": self.model_values,
                "Age": self.age,
            }
        )


summary = csv_to_dict("retirement_summary.csv")
prices = csv_to_dict("retirement_price_time_series.csv")
avg_returns = csv_to_dict("retirement_average_returns.csv")
grouped_assets = csv_to_dict("retirement_grouped_by_type.csv")
value_model = csv_to_dict("retirement_value_model.csv")
total_value = sum(float(row["value"]) for row in summary)
model = RetirementModel(value_model)
dcc.Store(id="memory_value_model", data=value_model)


#  Tab layout
def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Retirement Model", order=3),
                dmc.Grid(
                    [
                        dmc.GridCol(
                            [
                                dmc.GridCol(retirements_modelling_graph(), span=12),
                                dmc.GridCol(
                                    retirements_modelling_parameters(), span=12
                                ),
                            ],
                            span=12,
                        ),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


def retirements_modelling_graph():
    return dcc.Graph(
        figure=px.line(
            model.as_df(),
            x="Year",
            y=["Actual Values", "Target", "Model Values"],
        ),
        id="retirements_model_graph",
    )


NUMBER_INPUT_SETTINGS = {
    "style": {"width": 300},
    "type": "number",
    "persistence_type": "local",
    "persistence": True,
}


def retirements_modelling_parameters():
    return dmc.Grid(
        [
            dmc.GridCol(
                children=[
                    dmc.NumberInput(
                        **NUMBER_INPUT_SETTINGS,
                        id="retirement_monthly_income",
                        label="Monthly income (present prices):",
                        value=2000,
                        min=0,
                        step=10,
                        max=10000,
                    ),
                    dcc.Store(
                        id="memory_annual_income_net", storage_type="local", data=0
                    ),
                    dcc.Store(
                        id="memory_annual_income_gross", storage_type="local", data=0
                    ),
                    html.Div(
                        id="retirement_annual_income",
                        children=[
                            dmc.Text("Annual income (net, present value): £0"),
                            dmc.TextInput("Annual income (gross, present value): £0"),
                        ],
                    ),
                ],
                span=4,
            ),
            dmc.GridCol(
                children=[
                    dmc.NumberInput(
                        **NUMBER_INPUT_SETTINGS,
                        id="retirement_removal_rate",
                        label="Removal rate (%)",
                        value=3,
                        min=0.05,
                        step=0.05,
                        decimalScale=2,
                        max=10,
                    ),
                    dcc.Store(id="memory_income_sum", storage_type="local", data=0),
                    html.Div(
                        id="retirement_income_sum",
                        children=[
                            dmc.Text("Required sum to produce income: £0"),
                        ],
                    ),
                    dmc.NumberInput(
                        **NUMBER_INPUT_SETTINGS,
                        id="retirement_lump_sum",
                        label="Lump sum",
                        value=0,
                        min=0,
                        step=1_000,
                    ),
                    dcc.Store(id="memory_total_sum", storage_type="local", data=0),
                    html.Div(
                        id="retirement_total_sum",
                        children=[
                            dmc.Text("Total sum required: £0"),
                        ],
                    ),
                ],
                span=4,
            ),
            dmc.GridCol(
                children=[
                    dmc.NumberInput(
                        **NUMBER_INPUT_SETTINGS,
                        id="retirement_expected_returns",
                        label="Expected returns (%)",
                        value=8,
                        step=0.05,
                        decimalScale=2,
                    ),
                    dmc.NumberInput(
                        **NUMBER_INPUT_SETTINGS,
                        id="retirement_inflation_rate",
                        label="Inflation rate (%)",
                        value=3.5,
                        step=0.05,
                        decimalScale=2,
                    ),
                    dmc.NumberInput(
                        **NUMBER_INPUT_SETTINGS,
                        id="retirement_annual_contribution",
                        label="Annual contribution (present prices):",
                        value=0,
                        min=0,
                        step=1000,
                    ),
                    html.Div(
                        id="retirement_target_met_year",
                        children=[dmc.Text("Target met at age N/A in N/A")],
                    ),
                ],
                span=4,
            ),
        ]
    )


def calculate_gross_income(
    annual_income_net: float, tax_free_fraction: float = 0.25
) -> float | int:
    """Estimate the gross income required to give a certain net income. Based on current income
    tax bands

    Parameters
    ----------
    annual_income_net : float
        Annual net income

    Returns
    -------
    float
        Annual gross income
    """
    tax_rate_lower = 0.2
    personal_allowance = 12_570
    taxable_fraction = 1 - tax_free_fraction
    tax_payable = (
        (taxable_fraction * annual_income_net - personal_allowance) * tax_rate_lower
    ) / (1 - taxable_fraction * tax_rate_lower)
    tax_payable = max(0, tax_payable)
    return annual_income_net + tax_payable


#  Callbacks
@callback(
    Output(component_id="retirement_income_sum", component_property="children"),
    Output(component_id="memory_income_sum", component_property="data"),
    Input(component_id="memory_annual_income_gross", component_property="data"),
    Input(component_id="retirement_removal_rate", component_property="value"),
)
def update_income_sum(gross_income, removal_rate):
    income_sum = int(gross_income / (removal_rate / 100))
    return (
        [
            dmc.Text(f"Sum required to provide income: £{income_sum}"),
        ],
        income_sum,
    )


@callback(
    Output(component_id="retirement_total_sum", component_property="children"),
    Input(component_id="memory_total_sum", component_property="data"),
)
def update_total_sum(total_sum):
    return [
        dmc.Text(f"Total sum required: £{total_sum}"),
    ]


@callback(
    Output(component_id="memory_total_sum", component_property="data"),
    Input(component_id="memory_income_sum", component_property="data"),
    Input(component_id="retirement_lump_sum", component_property="value"),
)
def store_lump_sum(income_sum, lump_sum):
    return lump_sum + income_sum


@callback(
    Output(component_id="retirement_annual_income", component_property="children"),
    Input(component_id="memory_annual_income_net", component_property="data"),
    Input(component_id="memory_annual_income_gross", component_property="data"),
)
def update_annual_income(net_income, gross_income):
    return [
        dmc.Text(f"Annual income (net, present value): £{net_income}"),
        dmc.Text(f"Annual income (gross, present value): £{gross_income:.0f}"),
        dmc.Text("(Assumes 25% of income is taken from pension pot tax-free)"),
    ]


@callback(
    Output(component_id="memory_annual_income_net", component_property="data"),
    Output(component_id="memory_annual_income_gross", component_property="data"),
    Input(component_id="retirement_monthly_income", component_property="value"),
)
def store_annual_income(monthly_income: int):
    annual_income_net = monthly_income * 12
    annual_income_gross = calculate_gross_income(annual_income_net)
    return annual_income_net, annual_income_gross


@callback(
    Output(component_id="retirements_model_graph", component_property="figure"),
    Output(component_id="retirement_target_met_year", component_property="children"),
    Input(component_id="memory_total_sum", component_property="data"),
    Input(component_id="retirement_expected_returns", component_property="value"),
    Input(component_id="retirement_inflation_rate", component_property="value"),
    Input(component_id="retirement_annual_contribution", component_property="value"),
)
def update_model_graph(target, returns, inflation, contributions):
    color = px.colors.qualitative.Set1
    net_returns = 1 + (returns - inflation) / 100
    model.calculate_model_value(net_returns=net_returns, contributions=contributions)
    model.set_target(target_value=target)
    return (
        px.line(
            model.as_df().melt(
                id_vars=["Year"], value_vars=["Actual Values", "Target", "Model Values"]
            ),
            x="Year",
            y="value",
            color="variable",
            color_discrete_sequence=[color[1], color[0], color[1]],
            line_dash="variable",
            line_dash_map={
                "Actual Values": "solid",
                "Target": "dash",
                "Model Values": "dot",
            },
            # hover_data=["Age"],
        ),
        [
            dmc.Text(
                f"Target met at age {model.target_met_age} in {model.target_met_year}"
            ),
        ],
    )
