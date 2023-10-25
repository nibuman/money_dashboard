from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import datetime
import plotly.express as px
import dash_mantine_components as dmc
from dash.dash_table.Format import Format, Group, Scheme, Symbol

df = (
    pd.read_csv("gnucash_commodity_prices.csv")
    .assign(date=lambda df_: pd.to_datetime(df_.date))
    .pivot_table(index="date", columns="commodity.mnemonic", values="value")
    .fillna(method="ffill")
    .drop(columns=["EUR", "GBP"])
)
# df = df.loc[:, ["AZN", "BARC"]]
df_latest = df.iloc[[-1], :]
mask = df.index > datetime.datetime(2020, 1, 1)
df = df.loc[mask]
for col in df.columns:
    base_price = df.loc[:, col].iloc[0]
    df[col] = df[col] / base_price
# base_price = df.loc[mask, "AZN"].iloc[0]
# df_new["AZN"] = df_new["AZN"] / base_price
# df_new.loc[mask]


money = Format(
    scheme=Scheme.fixed,
    precision=2,
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
    for i in df.columns
][1:]


def _investments_table():
    return dash_table.DataTable(
        data=df_latest.to_dict("records"),
        columns=column_format,
        page_size=10,
        style_table={"overflowX": "auto"},
    )


def _investments_graph():
    return dcc.Graph(figure={}, id="investments_overview_graph")


def _investments_checkboxgroup():
    return dmc.CheckboxGroup(
        [*_investments_checkbox()],
        id="investments_overview_checkboxes",
        value=[
            "AZN",
        ],
        size="sm",
        orientation="vertical",
    )


def _investments_checkbox():
    return [dmc.Checkbox(label=i, value=i) for i in df.columns]


def _investment_tab():
    return [
        dmc.Container(
            [
                dmc.Title("Investments", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col([_investments_table()], span=11),
                        dmc.Col([_investments_checkboxgroup()], span=2),
                        dmc.Col([_investments_graph()], span=8),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


@callback(
    Output(component_id="investments_overview_graph", component_property="figure"),
    Input(component_id="investments_overview_checkboxes", component_property="value"),
)
def update_graph(col_chosen):
    fig = px.line(df, x=df.index, y=col_chosen)
    return fig
