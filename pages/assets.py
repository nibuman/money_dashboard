import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc

import dash_format
from utils import DATA_PATH

df_assets_time_series = pd.read_csv(DATA_PATH / "assets_time_series.csv")
df_latest_values = pd.read_csv(DATA_PATH / "assets_latest_summary.csv")

money = dash_format.money_format(0)
column_format = [
    {
        "id": i,
        "name": i,
        "type": "numeric",
        "format": money,
    }
    for i in df_assets_time_series.columns
][1:]


def asset_table():
    return dash_table.DataTable(
        data=df_latest_values.to_dict("records"),
        columns=column_format,
        page_size=10,
        style_table={"overflowX": "auto"},
    )


def asset_graph():
    return dcc.Graph(figure={}, id="asset_overview_graph")


def asset_checkboxgroup():
    return dmc.CheckboxGroup(
        asset_checkbox(),
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


def asset_checkbox():
    value_label_map = {
        "Savings & Investments": "Savings & Investments",
        "Current Assets": "Current Assets",
        "Share Schemes": "Share Schemes",
        "available_total": "Available Total",
        "3 Thorold Grove": "3 Thorold Grove",
        "total": "Total",
        "Retirement": "Retirement",
    }
    return [dmc.Checkbox(label=label, value=value) for value, label in value_label_map.items()]


def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Finance Overview", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col([asset_table()], span=11),
                        dmc.Col([asset_checkboxgroup()], span=2),
                        dmc.Col([asset_graph()], span=8),
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
    fig = px.line(df_assets_time_series, x="date", y=col_chosen)
    return fig
