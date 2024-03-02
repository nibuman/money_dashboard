import dash_mantine_components as dmc
import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc, html
import math

import dash_format
import utils
from dash_format import money_format, number_format, percent_format, percent_format_pos

summary = utils.csv_to_dict("retirement_summary.csv")
prices = utils.csv_to_dict("retirement_price_time_series.csv")
avg_returns = utils.csv_to_dict("retirement_average_returns.csv")
grouped_assets = utils.csv_to_dict("retirement_grouped_by_type.csv")
value_model = utils.csv_to_dict("retirement_value_model.csv")
total_value = sum(float(row["value"]) for row in summary)

dcc.Store(id="memory_value_model", data=value_model)


#  Tab layout
def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Retirement Investments", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col(
                            [
                                dmc.Col(retirements_graph(), span=12),
                                dmc.Col(retirement_average_returns_table(), span=12),
                                dmc.Col(retirements_radiogroup(), span=12),
                                dmc.Col(retirement_performance_table(), span=12),
                                dmc.Col(retirements_modelling_graph(), span=12),
                            ],
                            span=7,
                        ),
                        dmc.Col(
                            [
                                dmc.Col(retirements_performance_graph(), span=12),
                                # dmc.Col(retirement_mix_pie(), span=10),
                                dmc.Col(retirements_modelling_parameters(), span=12),
                            ],
                            span=5,
                        ),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


#  retirement performance table
def retirement_performance_table():
    return dash_table.DataTable(
        data=summary,
        columns=retirement_performance_columns(),
        id="retirement_performance_table",
        page_size=50,
        style_table={"overflowX": "auto"},
        style_data_conditional=dash_format.conditional_format_percent_change(
            [f"annualised{y}_percent" for y in utils.RETURNS_YEARS]
        ),
        style_cell={
            "height": "auto",
            # all three widths are needed
            "minWidth": "70px",
            "width": "70px",
            "maxWidth": "180px",
            "whiteSpace": "normal",
        },
        tooltip_delay=0,
        css=[
            {"selector": ".dash-table-tooltip", "rule": "background-color: grey; font-family: monospace; color: white"}
        ],
    )


def update_tooltips(col: str):
    sorted_summary = utils.sort_data(summary, column=col)
    return [
        {key: {"value": f"({row['commodity']})\n{row['commodity_name']}"} for key, value in row.items()}
        for row in sorted_summary
    ]


def update_table(col: str):
    sorted_summary = utils.sort_data(summary, column=col)
    return sorted_summary


def retirement_performance_columns():
    commodity = {"id": "commodity", "name": "Commodity"}
    latest = {"id": "latest_price", "name": "Latest Price", "type": "numeric", "format": money_format(2)}
    quantity = {"id": "quantity", "name": "Quantity", "type": "numeric", "format": number_format(0)}
    identifier = {"id": "commodity_id", "name": "ISIN"}
    ocf = {"id": "commodity_ocf", "name": "ocf"}
    value = {"id": "value", "name": "Value", "type": "numeric", "format": money_format(0)}
    returns = []
    percent_value = {"id": "percent_value", "name": "Value (%)", "type": "numeric", "format": percent_format(1)}
    for y in reversed(utils.RETURNS_YEARS):
        returns.extend(
            [
                # {"id": f"year{y}_percent", "name": f"{y} Year Returns", "type": "numeric", "format": percent},
                {
                    "id": f"annualised{y}_percent",
                    "name": f"{y} Year Annualised",
                    "type": "numeric",
                    "format": percent_format_pos(1),
                },
            ]
        )
    return [commodity, latest, identifier, ocf, *returns, quantity, value, percent_value]


#  Average returns table


def retirement_average_returns_table():
    return dash_table.DataTable(
        data=avg_returns,
        columns=average_returns_columns(),
        id="retirement_average_returns_table",
        page_size=2,
        style_table={"overflowX": "auto"},
        style_data_conditional=dash_format.conditional_format_percent_change([f"year{y}" for y in utils.RETURNS_YEARS]),
        style_cell={
            "height": "auto",
            # all three widths are needed
            "minWidth": "70px",
            "width": "70px",
            "maxWidth": "70px",
            "whiteSpace": "normal",
        },
    )


def average_returns_columns():
    returns = []
    for y in reversed(utils.RETURNS_YEARS):
        returns.extend(
            [
                {
                    "id": f"year{y}",
                    "name": f"{y} Year Returns",
                    "type": "numeric",
                    "format": percent_format_pos(1),
                },
            ]
        )
    return returns


#  Line graph of individual stock performance


def retirements_graph():
    return dcc.Graph(figure=px.line(prices, x="date", y="AZ Diversified"), id="retirements_price_graph")


#  Horizontal bar chart of performance comparisons
def retirements_performance_graph():
    return [
        dcc.Graph(
            figure=px.bar(summary, x="value", y="commodity", title="Long-Form Input", orientation="h"),
            id="retirement_performance_bar_chart",
        )
    ]


def update_bar_chart(col):
    sorted_summary = utils.sort_data(summary, column=col, sort_ascending=True)
    if col == "value":
        fig = px.bar(
            sorted_summary,
            x="value",
            y="commodity",
            title="Current Value of retirements",
            orientation="h",
        )
    else:
        year = col.removeprefix("annualised").removesuffix("_percent")
        fig = px.bar(
            sorted_summary,
            x=col,
            y="commodity",
            title=f"{year} Year Change in Value (annualised %)",
            orientation="h",
        )
        fig.update_xaxes(tickformat=".0%")
    return fig


# retirement mix bar chart


def retirement_mix_bar():
    return [
        dcc.Graph(
            figure=px.bar(
                grouped_assets,
                x="commodity_type",
                y=["type_value", "ideal_mix"],
                title="Long-Form Input",
                barmode="group",
            ),
            id="retirement_mix_bar",
        )
    ]


#  retirement mix pie chart


def retirement_mix_pie():
    return [
        dcc.Graph(
            figure=px.pie(
                grouped_assets,
                names="commodity_type",
                values="type_value",
                # title=f"Current mix. Total value = £{total_value:,.0f}",
                hover_data="commodities",
            ),
            id="retirement_mix_pie",
        )
    ]


#  Retirement modelling
def retirements_modelling_graph():
    for year in value_model:
        year["target"] = 850_000
    return dcc.Graph(
        figure=px.line(
            value_model,
            x="year",
            y=["actual_values", "target"],
        ),
        id="retirements_model_graph",
    )


def retirements_modelling_parameters():
    return dmc.Stack(
        children=[
            dmc.Title("Model Parameters", color="blue", size="h2"),
            dcc.Store(id="memory_monthly_income", storage_type="local", data=0),
            dmc.NumberInput(
                id="retirement_monthly_income",
                label="Monthly income (present prices):",
                style={"width": 300},
                type="number",
                value=2000,
                min=0,
                step=10,
                max=10000,
            ),
            dcc.Store(id="memory_annual_income_net", storage_type="local", data=0),
            dcc.Store(id="memory_annual_income_gross", storage_type="local", data=0),
            html.Div(
                id="retirement_annual_income",
                children=[
                    dmc.Text("Annual income (net, present value): £0"),
                    dmc.TextInput("Annual income (gross, present value): £0"),
                ],
            ),
            dcc.Store(id="memory_removal_rate", storage_type="local", data=0),
            dmc.NumberInput(
                id="retirement_removal_rate",
                label="Removal rate (%)",
                style={"width": 300},
                value=3,
                min=0.05,
                step=0.05,
                precision=2,
                max=10,
            ),
            dcc.Store(id="memory_income_sum", storage_type="local", data=0),
            html.Div(
                id="retirement_income_sum",
                children=[
                    dmc.Text("Required sum to produce income: £0"),
                ],
            ),
            dcc.Store(id="memory_lump_sum", storage_type="local", data=0),
            dmc.NumberInput(
                id="retirement_lump_sum",
                label="Lump sum",
                style={"width": 300},
                value=100_000,
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
            dcc.Store(id="memory_expected_returns", storage_type="local", data=0),
            dmc.NumberInput(
                id="retirement_expected_returns",
                label="Expected returns (%)",
                style={"width": 300},
                value=8,
                step=0.05,
                precision=2,
            ),
            dcc.Store(id="memory_inflation_rate", storage_type="local", data=0),
            dmc.NumberInput(
                id="retirement_inflation_rate",
                label="Inflation rate (%)",
                style={"width": 300},
                value=3.5,
                step=0.05,
                precision=2,
            ),
            dcc.Store(id="memory_annual_contribution", storage_type="local", data=0),
            dmc.NumberInput(
                id="retirement_annual_contribution",
                label="Annual contribution (present prices):",
                style={"width": 300},
                type="number",
                value=0,
                min=0,
                step=1000,
            ),
            dcc.Store(id="memory_target_met_year", storage_type="local", data={"year": "NA", "age": "NA"}),
            html.Div(
            id="retirement_target_met_year",
            children=[
                dmc.Text("Target met at age N/A in N/A")
            ],
        ),
        ],
    )


#  Radio buttons
def retirements_radiogroup():
    return [
        dmc.RadioGroup(
            retirements_radios(),
            id="retirement_performance_radio",
            value="radio_year3_percent",
            size="sm",
            orientation="horizontal",
        )
    ]


def retirements_radios() -> list[dmc.Radio]:
    radios = [
        dmc.Radio(label=f"{y} Year Returns", value=f"radio_year{y}_percent") for y in reversed(utils.RETURNS_YEARS)
    ]
    radios.extend([dmc.Radio(label="Current Value", value="radio_value")])
    return radios


#  Callbacks
@callback(
    Output(component_id="retirement_income_sum", component_property="children"),
    Output(component_id="memory_income_sum", component_property="data"),
    Input(component_id="memory_annual_income_gross", component_property="data"),
    Input(component_id="memory_removal_rate", component_property="data"),
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
    Output(component_id="retirement_target_met_year", component_property="children"),
    Input(component_id="memory_target_met_year", component_property="data"),
)
def update_target_met_year(target_met_year):
    return [
        dmc.Text(f"Target met at age {target_met_year["age"]} in {target_met_year["year"]}"),
    ]

@callback(
    Output(component_id="memory_monthly_income", component_property="data"),
    Input(component_id="retirement_monthly_income", component_property="value"),
)
def store_monthly_income(monthly_income):
    return int(monthly_income)

@callback(
    Output(component_id="memory_expected_returns", component_property="data"),
    Input(component_id="retirement_expected_returns", component_property="value"),
)
def store_expected_returns(expected_returns):
    return expected_returns

@callback(
    Output(component_id="memory_inflation_rate", component_property="data"),
    Input(component_id="retirement_inflation_rate", component_property="value"),
)
def store_inflation_rate(inflation_rate):
    return inflation_rate

@callback(
    Output(component_id="memory_removal_rate", component_property="data"),
    Input(component_id="retirement_removal_rate", component_property="value"),
)
def store_removal_rate(removal_rate):
    return float(removal_rate)

@callback(
    Output(component_id="memory_annual_contribution", component_property="data"),
    Input(component_id="retirement_annual_contribution", component_property="value"),
)
def store_annual_contribution(annual_contribution):
    return annual_contribution


@callback(
    Output(component_id="memory_lump_sum", component_property="data"),
    Output(component_id="memory_total_sum", component_property="data"),
    Input(component_id="memory_income_sum", component_property="data"),
    Input(component_id="retirement_lump_sum", component_property="value"),
)
def store_lump_sum(income_sum, lump_sum):
    lump_sum = int(lump_sum)
    return (lump_sum, lump_sum + income_sum)


@callback(
    Output(component_id="retirement_annual_income", component_property="children"),
    Input(component_id="memory_annual_income_net", component_property="data"),
    Input(component_id="memory_annual_income_gross", component_property="data"),
)
def update_annual_income(net_income, gross_income):
    return [
        dmc.Text(f"Annual income (net, present value): £{net_income}"),
        dmc.Text(f"Annual income (gross, present value): £{gross_income}"),
    ]


@callback(
    Output(component_id="memory_annual_income_net", component_property="data"),
    Output(component_id="memory_annual_income_gross", component_property="data"),
    Input(component_id="memory_monthly_income", component_property="data"),
)
def store_annual_income(monthly_income):
    annual_income_net = int(monthly_income) * 12
    LOWER_RATE_TAX = 0.2
    PERSONAL_ALLOWANCE = 12_000
    if annual_income_net > PERSONAL_ALLOWANCE:
        annual_income_gross = ((annual_income_net - PERSONAL_ALLOWANCE) / (1 - LOWER_RATE_TAX)) + PERSONAL_ALLOWANCE
    else:
        annual_income_gross = annual_income_net
    return (annual_income_net, annual_income_gross)


@callback(
    Output(component_id="retirements_price_graph", component_property="figure"),
    Input(component_id="retirement_performance_table", component_property="active_cell"),
    Input("retirement_performance_radio", "value"),
)
def update_graph(active_cell, sort_col):
    col = sort_col.removeprefix("radio_")
    sorted_summary = utils.sort_data(summary, column=col)
    if active_cell:
        data_row = active_cell["row"]
        cell_value = sorted_summary[data_row]["commodity"]
    else:
        cell_value = "AZ Diversified"
    title = [row["commodity_name"] for row in sorted_summary if row["commodity"] == cell_value][0]
    fig = px.line(prices, x="date", y=cell_value, title=title)

    return fig


@callback(
    Output("retirement_performance_bar_chart", "figure"),
    Output("retirement_performance_table", "data"),
    Output("retirement_performance_table", "tooltip_data"),
    Input("retirement_performance_radio", "value"),
)
def radio_button_actions(sort_col):
    if sort_col == "radio_value":
        col = "value"
    else:
        year = sort_col.removeprefix("radio_year").removesuffix("_percent")
        col = f"annualised{year}_percent"
    return update_bar_chart(col), update_table(col), update_tooltips(col)


@callback(
    Output(component_id="retirements_model_graph", component_property="figure"),
    Output(component_id="memory_target_met_year", component_property="data"),
    Input(component_id="memory_total_sum", component_property="data"),
    Input(component_id="memory_expected_returns", component_property="data"),
    Input(component_id="memory_inflation_rate", component_property="data"),
    Input(component_id="memory_annual_contribution", component_property="data"),
)
def update_model_graph(target, returns, inflation, contributions):
    net_returns = 1 + (returns - inflation) / 100
    start_year_idx, start_value = get_model_start(value_model=value_model)
    model_value = start_value
    target_met_year = None
    for idx, year in enumerate(value_model):
        if idx == start_year_idx-1:
            year["model"] = model_value
        elif idx >= start_year_idx:
            print(f"{model_value=}, {year["model"]=}, {net_returns=}, {contributions=}, {idx=}")
            model_value = (model_value * net_returns) + contributions
            year["model"] = model_value

    for year in value_model:
        year["target"] = target
    for year in value_model:
        if year["model"] >= target:
            target_met_year = year
            break
    return (px.line(
        value_model,
        x="year",
        y=["actual_values", "target", "model"],
    ), target_met_year)


def get_model_start(value_model):
    current_value = 0
    for idx, year in enumerate(value_model):
        if math.isnan(year["actual_values"]):
            return idx, current_value
        current_value = year["actual_values"]
    return idx, current_value
