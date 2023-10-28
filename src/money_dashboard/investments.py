import dash_mantine_components as dmc
import plotly.express as px
from dash import Dash, Input, Output, callback, dash_table, dcc, html

from money_dashboard import dash_format
from money_dashboard.data import commodities, RETURNS_YEARS


money = dash_format.money_format(2)
percent = dash_format.percent_format(1)
column_format = [
    dict(
        id=i,
        name=i,
        type="numeric",
        format=money,
    )
    for i in commodities.prices.columns
][1:]


def _investment_performance_table():
    return dash_table.DataTable(
        data=commodities.summary.to_dict("records"),
        columns=investment_performance_columns(),
        id="investment_performance_table",
        page_size=50,
        style_table={"overflowX": "auto"},
        style_data_conditional=dash_format.conditional_format_percent_change([f"year{y}_percent" for y in RETURNS_YEARS]),
        style_cell={
            "height": "auto",
            # all three widths are needed
            "minWidth": "70px",
            "width": "70px",
            "maxWidth": "180px",
            "whiteSpace": "normal",
        },
    )


def investment_performance_columns():
    commodity = {"id": "commodity", "name": "Commodity"}
    latest = {"id": "latest_price", "name": "Latest Price", "type": "numeric", "format": money}
    quantity = {"id": "quantity", "name": "Quantity"}
    value = {"id": "value", "name": "Value"}
    returns = []
    for y in reversed(RETURNS_YEARS):
        returns.extend(
            [
                {"id": f"year{y}_percent", "name": f"{y} Year Returns", "type": "numeric", "format": percent},
                {"id": f"annualised{y}_percent", "name": f"{y} Year Annualised", "type": "numeric", "format": percent},
            ]
        )
    return [commodity, latest, *returns, quantity, value]


def _investments_graph():
    return dcc.Graph(figure={}, id="investments_price_graph")


def _investments_radiogroup():
    return dmc.RadioGroup(
        _investments_radios(),
        id="investment_performance_radio",
        value="radio_year3_percent",
        size="sm",
        orientation="horizontal",
    )


def _investments_radios() -> list[dmc.Radio]:
    radios = [dmc.Radio(label=f"{y} Year Returns", value=f"radio_year{y}_percent") for y in reversed(RETURNS_YEARS)]
    radios.extend([dmc.Radio(label="Current Value", value="radio_value")])
    return radios


def _investment_tab():
    return [
        dmc.Container(
            [
                dmc.Title("Investments", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col([_investments_graph()], span=8),
                        dmc.Col([_investments_radiogroup()], span=7),
                        dmc.Col([_investment_performance_table()], span=7),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


@callback(
    Output(component_id="investments_price_graph", component_property="figure"),
    Input(component_id="investment_performance_table", component_property="active_cell"),
)
def update_graph(active_cell):
    if active_cell:
        data_row = active_cell["row"]
        cell_value = commodities.summary.loc[data_row, "commodity"]
    else:
        cell_value = ["AZN"]
    fig = px.line(commodities.prices, x=commodities.prices.index, y=cell_value)
    return fig


@callback(Output("investment_performance_table", "data"), Input("investment_performance_radio", "value"))
def update_table(sort_col: str):
    commodities.sort_summary(column=sort_col.removeprefix("radio_"))
    return commodities.summary.to_dict("records")
