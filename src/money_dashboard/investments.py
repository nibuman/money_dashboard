import datetime

import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, callback, dash_table, dcc, html

from money_dashboard import gnucash_export, dash_format

YEARS = [1, 3, 5]


def get_commodity_prices():
    return gnucash_export.get_commodity_prices().ffill().drop(columns=["EUR", "GBP"])


def get_latest_prices():
    return df_prices.iloc[[-1], :].T.reset_index().set_axis(["commodity", "latest_price"], axis=1)


def normalise_prices(start_year: datetime.datetime, df_prices: pd.DataFrame):
    mask = df_prices.index > start_year
    for col in df_prices.columns:
        base_price = df_prices.loc[mask, col].iloc[0]
        df_prices.loc[mask, col] = ((df_prices.loc[mask, col] / base_price) - 1) * 100
    return df_prices.loc[mask]


df_prices = get_commodity_prices()
latest_prices = get_latest_prices()
df_normalised = normalise_prices(start_year=datetime.datetime(2020, 1, 1), df_prices=df_prices.copy())

money = dash_format.money_format(2)
percent = dash_format.percent_format(1)
column_format = [
    dict(
        id=i,
        name=i,
        type="numeric",
        format=money,
    )
    for i in df_prices.columns
][1:]


def _commodity_performance():
    return (
        df_normalised.iloc[[-1], :]
        .T.reset_index()
        .set_axis(["commodity", "change"], axis=1)
        .sort_values(by="change", ascending=False)
        .to_dict("records")
    )


def get_base_prices(year: datetime.datetime, df: pd.DataFrame, change_dy: int) -> pd.DataFrame:
    mask = df.index > year
    return df.loc[mask, :].iloc[0].T.reset_index().set_axis(["commodity", f"price_year{change_dy}"], axis=1)


def get_commodity_data():
    df_commodity_data = latest_prices.copy()
    for dy in YEARS:
        start_year = datetime.datetime(year=2023 - dy, month=1, day=1)
        base_prices = get_base_prices(year=start_year, df=df_prices.copy(), change_dy=dy)
        df_commodity_data = df_commodity_data.merge(base_prices)
        df_commodity_data[f"change_year{dy}"] = df_commodity_data.latest_price / df_commodity_data[f"price_year{dy}"]
        df_commodity_data[f"change_year{dy}_percent"] = (df_commodity_data[f"change_year{dy}"]) - 1
        df_commodity_data[f"annualised{dy}_percent"] = (df_commodity_data[f"change_year{dy}"] ** (1 / dy)) - 1
    commodity_dict = df_commodity_data.fillna(0).to_dict("records")
    return commodity_dict


def _investment_performance_table():
    return dash_table.DataTable(
        data=get_commodity_data(),
        columns=investment_performance_columns(),
        page_size=50,
        style_table={"overflowX": "auto"},
        style_data_conditional=dash_format.conditional_format_percent_change(
            [f"change_year{y}_percent" for y in YEARS]
        ),
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
    for y in reversed(YEARS):
        returns.extend(
            [
                {"id": f"change_year{y}_percent", "name": f"{y} Year Returns", "type": "numeric", "format": percent},
                {"id": f"annualised{y}_percent", "name": f"{y} Year Annualised", "type": "numeric", "format": percent},
            ]
        )
    return [commodity, latest, *returns, quantity, value]


def _investments_graph():
    return dcc.Graph(figure={}, id="investments_overview_graph")


def _investments_radiogroup():
    return dmc.RadioGroup(
        _investments_radios(),
        id="investments_overview_checkboxes",
        value="radio_year3",
        size="sm",
        orientation="horizontal",
    )


def _investments_radios() -> list[dmc.Radio]:
    radios = [dmc.Radio(label=f"{y} Year Returns", value=f"radio_year{y}") for y in reversed(YEARS)]
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
    Output(component_id="investments_overview_graph", component_property="figure"),
    Input(component_id="investments_overview_checkboxes", component_property="value"),
)
def update_graph(col_chosen):
    fig = px.line(df_normalised, x=df_normalised.index, y=col_chosen)
    return fig
