from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_mantine_components as dmc
from dash.dash_table.Format import Format, Group, Scheme, Symbol
from money_dashboard import gnucash_export


def get_asset_values():
    df = gnucash_export.get_assets_time_series()
    df["Available Total"] = df.loc[:, ["Savings & Investments", "Current Assets", "Share Schemes"]].sum(axis=1)
    df["Total"] = df.loc[:, "Savings & Investments":"Retirement"].sum(axis=1)
    return df


df_asset_values = get_asset_values()
df_latest = df_asset_values.iloc[[0], 1:]

money = Format(
    scheme=Scheme.fixed,
    precision=0,
    group=Group.yes,
    groups=3,
    group_delimiter=" ",
    decimal_delimiter=".",
    symbol=Symbol.yes,
    symbol_prefix="£",
)
column_format = [
    dict(
        id=i,
        name=i,
        type="numeric",
        format=money,
    )
    for i in df_asset_values.columns
][1:]


def _asset_table():
    return dash_table.DataTable(
        data=df_latest.to_dict("records"),
        columns=column_format,
        page_size=10,
        style_table={"overflowX": "auto"},
    )


def _asset_graph():
    return dcc.Graph(figure={}, id="asset_overview_graph")


def _asset_checkboxgroup():
    return dmc.CheckboxGroup(
        [*_asset_checkbox()],
        id="asset_overview_checkboxes",
        value=[
            "Savings & Investments",
            "Current Assets",
            "Share Schemes",
            "Available Total",
        ],
        size="sm",
        orientation="vertical",
    )


def _asset_checkbox():
    return [dmc.Checkbox(label=i, value=i) for i in df_asset_values.columns][1:]


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
    fig = px.line(df_asset_values, x="date", y=col_chosen)
    return fig
