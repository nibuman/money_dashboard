import dash_mantine_components as dmc
import plotly.express as px
import numpy as np
from dash import Dash, Input, Output, callback, dash_table, dcc, html
import plotly.graph_objects as go
from money_dashboard import dash_format
from money_dashboard.data import retirement, RETURNS_YEARS


money = dash_format.money_format(2)
percent = dash_format.percent_format(1)
percent_pos = dash_format.percent_format_pos(1)


#  Tab layout


def _retirement_tab():
    return [
        dmc.Container(
            [
                dmc.Title("retirements", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col(
                            [
                                _retirements_graph(),
                                _retirement_average_returns_table(),
                            ],
                            span=7,
                        ),
                        dmc.Col(_retirements_performance_graph(), span=5),
                        dmc.Col(_retirements_radiogroup(), span=7),
                        dmc.Col(_retirement_performance_table(), span=11),
                        dmc.Col(_retirement_mix_bar(), span=7),
                        dmc.Col(_retirement_mix_pie(), span=5),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


#  retirement performance table


def _retirement_performance_table():
    return dash_table.DataTable(
        data=retirement.summary.to_dict("records"),
        columns=retirement_performance_columns(),
        id="retirement_performance_table",
        page_size=50,
        style_table={"overflowX": "auto"},
        style_data_conditional=dash_format.conditional_format_percent_change(
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
            {'selector': '.dash-table-tooltip', 'rule': 'background-color: grey; font-family: monospace; color: white'}
        ],
    )


def update_tooltips(col: str):
    sorted_summary = retirement.sorted_summary(column=col)
    return [
        {key: {'value': f"({row['commodity']})\n{row['commodity_name']}"} for key, value in row.items()}
        for row in sorted_summary.to_dict("records")
    ]


def update_table(col: str):
    sorted_summary = retirement.sorted_summary(column=col)
    return sorted_summary.to_dict("records")


def retirement_performance_columns():
    commodity = {"id": "commodity", "name": "Commodity"}
    latest = {"id": "latest_price", "name": "Latest Price", "type": "numeric", "format": money}
    quantity = {"id": "quantity", "name": "Quantity"}
    identifier = {"id": "commodity_id", "name": "ISIN"}
    ocf = {"id": "commodity_ocf", "name": "ocf"}
    value = {"id": "value", "name": "Value", "type": "numeric", "format": money}
    returns = []
    percent_value = {"id": "percent_value", "name": "Value (%)", "type": "numeric", "format": percent}
    for y in reversed(RETURNS_YEARS):
        returns.extend(
            [
                # {"id": f"year{y}_percent", "name": f"{y} Year Returns", "type": "numeric", "format": percent},
                {
                    "id": f"annualised{y}_percent",
                    "name": f"{y} Year Annualised",
                    "type": "numeric",
                    "format": percent_pos,
                },
            ]
        )
    return [commodity, latest, identifier, ocf, *returns, quantity, value, percent_value]


#  Average returns table


def _retirement_average_returns_table():
    return dash_table.DataTable(
        data=retirement.average_returns,
        columns=average_returns_columns(),
        id="retirement_average_returns_table",
        page_size=2,
        style_table={"overflowX": "auto"},
        style_data_conditional=dash_format.conditional_format_percent_change(
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
                {"id": f"retirement_year{y}", "name": f"{y} Year Returns", "type": "numeric", "format": percent},
            ]
        )
    return returns


#  Line graph of individual stock performance


def _retirements_graph():
    return dcc.Graph(
        figure=px.line(retirement.prices, x=retirement.prices.index, y="AZ Diversified"), id="retirements_price_graph"
    )


#  Horizontal bar chart of performance comparisons
def _retirements_performance_graph():
    return [
        dcc.Graph(
            figure=px.bar(retirement.summary, x="value", y="commodity", title="Long-Form Input", orientation="h"),
            id="retirement_performance_bar_chart",
        )
    ]


def update_bar_chart(col):
    sorted_summary = retirement.sorted_summary(column=col, sort_ascending=True)
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
            color=col,
            color_continuous_scale=['Crimson', 'OrangeRed', 'PaleGreen', 'green'],
            color_continuous_midpoint=0,
        )
        fig.update_xaxes(tickformat=".0%")
    return fig


# retirement mix bar chart


def _retirement_mix_bar():
    return [
        dcc.Graph(
            figure=px.bar(
                retirement.by_asset_type(),
                x="commodity_type",
                y=["type_value", "ideal_mix"],
                title="Long-Form Input",
                barmode="group",
            ),
            id="retirement_mix_bar",
        )
    ]


#  retirement mix pie chart


def _retirement_mix_pie():
    return [
        dcc.Graph(
            figure=px.pie(
                retirement.by_asset_type(),
                names="commodity_type",
                values="type_value",
                title=f"Current mix. Total value = £{retirement.total_value:,.0f}",
                hover_data="commodities",
            ),
            id="retirement_mix_pie",
        )
    ]


#  Radio buttons


def _retirements_radiogroup():
    return [
        dmc.RadioGroup(
            _retirements_radios(),
            id="retirement_performance_radio",
            value="radio_year3_percent",
            size="sm",
            orientation="horizontal",
        )
    ]


def _retirements_radios() -> list[dmc.Radio]:
    radios = [dmc.Radio(label=f"{y} Year Returns", value=f"radio_year{y}_percent") for y in reversed(RETURNS_YEARS)]
    radios.extend([dmc.Radio(label="Current Value", value="radio_value")])
    return radios


#  Callbacks


@callback(
    Output(component_id="retirements_price_graph", component_property="figure"),
    # Output(component_id="retirements_price_graph", component_property="title"),
    Input(component_id="retirement_performance_table", component_property="active_cell"),
    Input("retirement_performance_radio", "value"),
)
def update_graph(active_cell, sort_col):
    col = sort_col.removeprefix("radio_")
    sorted_summary = retirement.sorted_summary(column=col)
    if active_cell:
        data_row = active_cell["row"]
        cell_value = sorted_summary.loc[data_row, "commodity"]
        title = sorted_summary.loc[data_row, "commodity_name"]
    else:
        cell_value = "AZ Diversified"
        mask = sorted_summary.commodity.values == cell_value
        title = sorted_summary.loc[mask, "commodity_name"].item()
    fig = px.line(retirement.prices, x=retirement.prices.index, y=cell_value, title=title)

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
