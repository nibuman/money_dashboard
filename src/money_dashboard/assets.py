import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, callback, dash_table, dcc, html
from money_dashboard.data import assets
from money_dashboard import dash_format


money = dash_format.money_format(0)
column_format = [
    dict(
        id=i,
        name=i,
        type="numeric",
        format=money,
    )
    for i in assets.asset_values.columns
][1:]


def _asset_table():
    return dash_table.DataTable(
        data=assets.latest_values.to_dict("records"),
        columns=column_format,
        page_size=10,
        style_table={"overflowX": "auto"},
    )


def _asset_graph():
    return dcc.Graph(figure={}, id="asset_overview_graph")


def _asset_checkboxgroup():
    return dmc.CheckboxGroup(
        _asset_checkbox(),
        id="asset_overview_checkboxes",
        value=[
            "Savings & Investments",
            "Current Assets",
            "Share Schemes",
            "available_total",
        ],
        size="sm",
        orientation="vertical",
    )


def _asset_checkbox():
    return [dmc.Checkbox(label=i, value=i) for i in assets.asset_values.columns][1:]


def _asset_tab():
    return [
        dmc.Container(
            [
                dmc.Title("Finance Overview", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col([_asset_table()], span=11),
                        dmc.Col([_asset_checkboxgroup()], span=2),
                        dmc.Col([_asset_graph()], span=8),
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
    fig = px.line(assets.asset_values, x="date", y=col_chosen)
    return fig
