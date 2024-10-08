import dash_mantine_components as dmc
import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc

import dash_format
import utils

assets_time_series = utils.csv_to_dict("assets_time_series.csv")
latest_values = utils.csv_to_dict("assets_latest_summary.csv")
asset_names = tuple(latest_values[0].keys())[1:]

money = dash_format.money_format(0)
column_format = [
    {
        "id": i,
        "name": i,
        "type": "numeric",
        "format": money,
    }
    for i in latest_values[0].keys()
][1:]


def asset_table():
    return dash_table.DataTable(
        data=latest_values,
        columns=column_format,
        page_size=10,
        style_table={"overflowX": "auto"},
    )


def asset_graph():
    return dcc.Graph(figure={}, id="asset_overview_graph")


def asset_checkboxgroup():
    return dmc.CheckboxGroup(
        children=dmc.Stack(asset_checkbox()),
        id="asset_overview_checkboxes",
        size="sm",
        persistence=False,
        persistence_type="local",
        value=asset_names,  # set all selected at load
    )


def asset_checkbox():
    return [dmc.Checkbox(label=asset_name, value=asset_name) for asset_name in asset_names]


def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Finance Overview", order=3),
                dmc.Grid(
                    [
                        dmc.GridCol([asset_table()], span=11),
                        dmc.GridCol([asset_checkboxgroup()], span=2),
                        dmc.GridCol([asset_graph()], span=8),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


@callback(
    Output(component_id="asset_overview_graph", component_property="figure"),
    Input(component_id="asset_overview_checkboxes", component_property="value"),
)
def update_graph(col_chosen):
    return px.line(assets_time_series, x="date", y=col_chosen)
