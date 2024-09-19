import dash_mantine_components as dmc
import plotly.colors
import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc

from data.ids import ID
from utils.dash_format import money_format
from utils.utils import csv_to_dict

assets_time_series = csv_to_dict("assets_time_series.csv")
latest_values = csv_to_dict("assets_latest_summary.csv")
asset_names = tuple(latest_values[0].keys())[1:]
color_scheme = dict(zip(asset_names, plotly.colors.qualitative.G10))
money = money_format(0)
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
        id=ID.ASSET_CHECKBOX_GROUP,
        size="sm",
        persistence=False,
        persistence_type="local",
        value=asset_names,  # set all selected at load
    )


def asset_split_barchart():
    assets_to_display = [
        "Retirement",
        "Houses",
        "Investments",
        "Savings",
        "Current Assets",
    ]
    assets_with_values = {a: latest_values[0][a] for a in assets_to_display}
    assets_sorted = dict(
        sorted(assets_with_values.items(), key=lambda item: item[1], reverse=True)
    )
    return dcc.Graph(
        figure=px.bar(
            x=assets_sorted.keys(),
            y=assets_sorted.values(),
            title="Current Asset Mix",
        ),
        id="asset_mix_bar",
    )


def asset_checkbox():
    return [
        dmc.Checkbox(label=asset_name, value=asset_name) for asset_name in asset_names
    ]


def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Finance Overview", order=3),
                dmc.Grid(
                    [
                        dmc.GridCol([asset_table()], span=11),
                        dmc.GridCol([asset_checkboxgroup()], span=2),
                        dmc.GridCol([asset_graph()], span=7),
                        dmc.GridCol([asset_split_barchart()], span=2),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


@callback(
    Output(component_id="asset_overview_graph", component_property="figure"),
    Input(
        component_id=ID.ASSET_CHECKBOX_GROUP,
        component_property="value",
    ),
)
def update_graph(col_chosen):
    return px.line(
        assets_time_series, x="date", y=col_chosen, color_discrete_map=color_scheme
    )
