import dash_mantine_components as dmc

import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc
import dash_format
import utils
from dash_format import money_format, number_format, percent_format, percent_format_pos


summary = utils.csv_to_dict("investments_summary.csv")
prices = utils.csv_to_dict("investments_price_time_series.csv")
avg_returns = utils.csv_to_dict("investments_average_returns.csv")
grouped_assets = utils.csv_to_dict("investments_grouped_by_type.csv")
total_value = sum(float(row["value"]) for row in summary)


def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Investments", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col(
                            [
                                investments_graph(),
                                investment_average_returns_table(),
                            ],
                            span=7,
                        ),
                        dmc.Col(investments_performance_graph(), span=5),
                        dmc.Col(investments_radiogroup(), span=7),
                        dmc.Col(investment_performance_table(), span=11),
                        dmc.Col(investment_mix_bar(), span=7),
                        dmc.Col(investment_mix_pie(), span=5),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


#  Investment performance table
def investment_performance_table():
    return dash_table.DataTable(
        data=summary,
        columns=investment_performance_columns(),
        id="investment_performance_table",
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


def investment_performance_columns():
    commodity = {"id": "commodity", "name": "Commodity"}
    latest = {"id": "latest_price", "name": "Latest Price", "type": "numeric", "format": money_format(2)}
    quantity = {"id": "quantity", "name": "Quantity", "type": "numeric", "format": number_format(1)}
    identifier = {"id": "commodity_id", "name": "ISIN"}
    ocf = {"id": "commodity_ocf", "name": "ocf"}
    value = {"id": "value", "name": "Value", "type": "numeric", "format": money_format(0)}
    returns = []
    percent_value = {"id": "percent_value", "name": "Value (%)", "type": "numeric", "format": percent_format(1)}
    for y in reversed(utils.RETURNS_YEARS):
        returns.extend(
            [
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
def investment_average_returns_table():
    return dash_table.DataTable(
        data=avg_returns,
        columns=average_returns_columns(),
        id="investment_average_returns_table",
        page_size=2,
        style_table={"overflowX": "auto"},
        style_data_conditional=dash_format.conditional_format_percent_change(
            [f"year{y}_percent" for y in utils.RETURNS_YEARS]
        ),
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
                {"id": f"year{y}", "name": f"{y} Year Returns", "type": "numeric", "format": percent_format_pos(1)},
            ]
        )
    return returns


#  Line graph of individual stock performance
def investments_graph():
    return dcc.Graph(figure=px.line(prices, x="date", y="AZN"), id="investments_price_graph")


#  Horizontal bar chart of performance comparisons
def investments_performance_graph():
    return [
        dcc.Graph(
            figure=px.bar(summary, x="value", y="commodity", title="Long-Form Input", orientation="h"),
            id="performance_bar_chart",
        )
    ]


def update_bar_chart(col):
    sorted_summary = utils.sort_data(summary, column=col, sort_ascending=True)
    if col == "value":
        fig = px.bar(
            sorted_summary,
            x="value",
            y="commodity",
            title="Current Value of Investments",
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


# Investment mix bar chart
def investment_mix_bar():
    return [
        dcc.Graph(
            figure=px.bar(
                grouped_assets,
                x="commodity_type",
                y=["type_value", "ideal_mix"],
                title="Investment Mix - Current v. Ideal",
                barmode="group",
            ),
            id="investment_mix_bar",
        )
    ]


#  Investment mix pie chart
def investment_mix_pie():
    return [
        dcc.Graph(
            figure=px.pie(
                grouped_assets,
                names="commodity_type",
                values="type_value",
                title=f"Current mix. Total value = £{total_value:,.0f}",
                hole=0.3,
                hover_data="commodities",
            ),
            id="investment_mix_pie",
        )
    ]


#  Radio buttons
def investments_radiogroup():
    return [
        dmc.RadioGroup(
            investments_radios(),
            id="investment_performance_radio",
            value="radio_year3_percent",
            size="sm",
            orientation="horizontal",
        )
    ]


def investments_radios() -> list[dmc.Radio]:
    radios = [
        dmc.Radio(label=f"{y} Year Returns", value=f"radio_year{y}_percent") for y in reversed(utils.RETURNS_YEARS)
    ]
    radios.extend([dmc.Radio(label="Current Value", value="radio_value")])
    return radios


#  Callbacks
@callback(
    Output(component_id="investments_price_graph", component_property="figure"),
    # Output(component_id="investments_price_graph", component_property="title"),
    Input(component_id="investment_performance_table", component_property="active_cell"),
    Input("investment_performance_radio", "value"),
)
def update_graph(active_cell, sort_col):
    col = sort_col.removeprefix("radio_")
    sorted_summary = utils.sort_data(summary, column=col)
    if active_cell:
        data_row = active_cell["row"]
        cell_value = sorted_summary[data_row]["commodity"]
    else:
        cell_value = "AZN"
    title = [row["commodity_name"] for row in sorted_summary if row["commodity"] == cell_value][0]
    fig = px.line(prices, x="date", y=cell_value, title=title)
    return fig


@callback(
    Output("performance_bar_chart", "figure"),
    Output("investment_performance_table", "data"),
    Output("investment_performance_table", "tooltip_data"),
    Input("investment_performance_radio", "value"),
)
def radio_button_actions(sort_col):
    if sort_col == "radio_value":
        col = "value"
    else:
        year = sort_col.removeprefix("radio_year").removesuffix("_percent")
        col = f"annualised{year}_percent"
    return update_bar_chart(col), update_table(col), update_tooltips(col)
