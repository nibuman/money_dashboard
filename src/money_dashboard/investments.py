from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import datetime
import plotly.express as px
import dash_mantine_components as dmc
from dash.dash_table.Format import Format, Group, Scheme, Symbol
from money_dashboard import gnucash_export

def get_commodity_prices():
    return (gnucash_export.get_commodity_prices()
        .ffill()
        .drop(columns=["EUR", "GBP"])
    )

def get_latest_prices():
    return df_prices.iloc[[-1], :]

def normalise_prices(start_year: datetime.datetime, df_prices: pd.DataFrame):
    mask = df_prices.index > start_year
    df_prices = df_prices.loc[mask]
    for col in df_prices.columns:
        base_price = df_prices.loc[:, col].iloc[0]
        df_prices[col] = df_prices[col] / base_price
    return df_prices

df_prices = get_commodity_prices()
df_latest = get_latest_prices()
df_normalised = normalise_prices(start_year=datetime.datetime(2020, 1, 1), df_prices=df_prices)

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
    for i in df_prices.columns
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
    return [dmc.Checkbox(label=i, value=i) for i in df_prices.columns]


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
    fig = px.line(df_normalised, x=df_normalised.index, y=col_chosen)
    return fig
