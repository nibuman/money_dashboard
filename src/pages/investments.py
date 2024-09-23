from typing import Any

import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects
from dash import Input, Output, callback, dash_table, dcc

from data.ids import ID
from utils.dash_format import (
    conditional_format_percent_change,
    money_format,
    number_format,
    percent_format,
    percent_format_pos,
)
from utils.utils import RETURNS_YEARS, TableData, csv_to_dict, sort_data

type FormattingData = list[dict[str, Any]]
summary = csv_to_dict("investments_summary.csv")
prices = csv_to_dict("investments_price_time_series.csv")
avg_returns = csv_to_dict("investments_average_returns.csv")
grouped_assets = csv_to_dict("investments_grouped_by_type.csv")
total_value = sum(float(row["value"]) for row in summary)


def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Investments", order=3),
                dmc.Grid(
                    [
                        dmc.GridCol(
                            [
                                investments_graph(),
                                investment_average_returns_table(),
                            ],
                            span=7,
                        ),
                        dmc.GridCol(investments_performance_bar_chart(), span=5),
                        dmc.GridCol(investments_radiogroup(), span=7),
                        dmc.GridCol(investment_performance_table(), span=11),
                        dmc.GridCol(investment_mix_bar(), span=7),
                        dmc.GridCol(investment_mix_pie(), span=5),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


def investment_performance_table() -> dash_table.DataTable:
    """The main table that lists each commodity and associated prices / values / changes"""
    return dash_table.DataTable(
        data=summary,
        columns=investment_performance_columns(),
        id=ID.INVESTMENTS_PERFORMANCE_TABLE,
        page_size=50,
        style_table={"overflowX": "auto"},
        style_data_conditional=conditional_format_percent_change(
            [f"annualised{y}_percent" for y in RETURNS_YEARS]
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
            {
                "selector": ".dash-table-tooltip",
                "rule": "background-color: grey; font-family: monospace; color: white",
            }
        ],
    )


def update_tooltips(col: str) -> FormattingData:
    """Provide updated tooltips for the investments performance table based on what the table has
    been sorted by"""
    sorted_summary = sort_data(summary, column=col)
    return [
        {
            key: {"value": f"({row['commodity']})\n{row['commodity_name']}"}
            for key, value in row.items()
        }
        for row in sorted_summary
    ]


def update_table(col: str) -> TableData:
    """Return the updated data for the investments performance table based the selected sort value"""
    return sort_data(summary, column=col)


def investment_performance_columns() -> FormattingData:
    """Returns a list of the columns for the datatable with the formatting information for each"""
    commodity = {"id": "commodity", "name": "Commodity"}
    latest = {
        "id": "latest_price",
        "name": "Latest Price",
        "type": "numeric",
        "format": money_format(2),
    }
    quantity = {
        "id": "quantity",
        "name": "Quantity",
        "type": "numeric",
        "format": number_format(1),
    }
    identifier = {"id": "commodity_id", "name": "ISIN"}
    ocf = {"id": "commodity_ocf", "name": "ocf"}
    value = {
        "id": "value",
        "name": "Value",
        "type": "numeric",
        "format": money_format(0),
    }
    percent_value = {
        "id": "percent_value",
        "name": "Value (%)",
        "type": "numeric",
        "format": percent_format(1),
    }
    returns = []
    for y in reversed(RETURNS_YEARS):
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
    return [
        commodity,
        latest,
        identifier,
        ocf,
        *returns,
        quantity,
        value,
        percent_value,
    ]


def investment_average_returns_table() -> dash_table.DataTable:
    """Display the average returns for the whole investment portfolio"""
    return dash_table.DataTable(
        data=avg_returns,
        columns=average_returns_columns(),
        id=ID.INVESTMENTS_AVERAGE_RETURNS_TABLE,
        page_size=2,
        style_table={"overflowX": "auto"},
        style_data_conditional=conditional_format_percent_change(
            [f"year{y}_percent" for y in RETURNS_YEARS]
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
    for y in reversed(RETURNS_YEARS):
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


def investments_graph() -> dcc.Graph:
    """Line graph of individual stock / fund performance"""
    return dcc.Graph(
        figure=px.line(prices, x="date", y="AZN"), id=ID.INVESTMENTS_PRICE_GRAPH
    )


def investments_performance_bar_chart() -> dcc.Graph:
    """Horizontal bar chart of performance comparisons"""
    return dcc.Graph(
        figure=px.bar(
            summary,
            x="value",
            y="commodity",
            title="Long-Form Input",
            orientation="h",
        ),
        id=ID.INVESTMENTS_PERFORMANCE_BAR_CHART,
    )


def update_bar_chart(col) -> plotly.graph_objects.Figure:
    """Returns a new Figure object for the investments performance bar chart based on either the
    value or the percentage change of the investments"""
    sorted_summary = sort_data(summary, column=col, sort_ascending=True)
    if col == "value":
        return px.bar(
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


def investment_mix_bar() -> dcc.Graph:
    """Compares the relative values of different types of investment, compared to an ideal mixture"""
    return dcc.Graph(
        figure=px.bar(
            grouped_assets,
            x="commodity_type",
            y=["type_value", "ideal_mix"],
            title="Investment Mix - Current v. Ideal",
            barmode="group",
        ),
        id=ID.INVESTMENTS_MIX_BAR,
    )


def investment_mix_pie() -> dcc.Graph:
    """Pie chart of the current mix of investment types"""
    return dcc.Graph(
        figure=px.pie(
            grouped_assets,
            names="commodity_type",
            values="type_value",
            title=f"Current mix. Total value = £{total_value:,.0f}",
            hole=0.3,
            hover_data="commodities",
        ),
        id=ID.INVESTMENTS_MIX_PIE,
    )


def investments_radiogroup() -> dmc.RadioGroup:
    """Group of radio buttons for changing the ordering of the datatable and graphs"""
    return dmc.RadioGroup(
        children=dmc.Group(investments_radios()),
        id=ID.INVESTMENTS_PERFORMANCE_RADIO,
        value="radio_year3_percent",
        size="sm",
    )


def investments_radios() -> list[dmc.Radio]:
    """Return a list of radio buttons that form part of the radio group"""
    radios = [
        dmc.Radio(label=f"{y} Year Returns", value=f"radio_year{y}_percent")
        for y in reversed(RETURNS_YEARS)
    ]
    radios.extend([dmc.Radio(label="Current Value", value="radio_value")])
    return radios


@callback(
    Output(ID.INVESTMENTS_PRICE_GRAPH, "figure"),
    Input(ID.INVESTMENTS_PERFORMANCE_TABLE, "active_cell"),
    Input(ID.INVESTMENTS_PERFORMANCE_RADIO, "value"),
)
def update_graph(active_cell, sort_col) -> plotly.graph_objects.Figure:
    """Callback to update the investment prices graph based on the selection of the radio
    buttons or selecting a row in the main table"""
    col = sort_col.removeprefix("radio_")
    sorted_summary = sort_data(summary, column=col)
    if active_cell:
        data_row = active_cell["row"]
        cell_value = sorted_summary[data_row]["commodity"]
    else:
        cell_value = "AZN"
    title = next(
        row["commodity_name"]
        for row in sorted_summary
        if row["commodity"] == cell_value
    )
    fig = px.line(prices, x="date", y=cell_value, title=title)
    return fig


@callback(
    Output(ID.INVESTMENTS_PERFORMANCE_BAR_CHART, "figure"),
    Output(ID.INVESTMENTS_PERFORMANCE_TABLE, "data"),
    Output(ID.INVESTMENTS_PERFORMANCE_TABLE, "tooltip_data"),
    Input(ID.INVESTMENTS_PERFORMANCE_RADIO, "value"),
)
def radio_button_actions(
    sort_col,
) -> tuple[plotly.graph_objects.Figure, TableData, FormattingData]:
    """Callback to update the main table and bar chart based on the selection of the radio buttons"""
    if sort_col == "radio_value":
        col = "value"
    else:
        year = sort_col.removeprefix("radio_year").removesuffix("_percent")
        col = f"annualised{year}_percent"
    return update_bar_chart(col), update_table(col), update_tooltips(col)
