import dash_mantine_components as dmc
from dash import html

import utils
import json

with open(utils.DATA_PATH / "update_log.json", 'r') as f:
    update_data = json.load(f)

update_date = update_data["time"]
update_files = [{"No.": n, "File name": file} for n, file in enumerate(update_data["files"], start=1)]


def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Info", color="blue", size="h3"),
                dmc.Grid(
                    [
                        dmc.Col(
                            [
                                last_update_time(),
                            ],
                            span=11,
                        ),
                        dmc.Col(data_file_table(), span=3),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


def last_update_time():
    return html.Div(
        [
            html.P("Data last updated: ", style={'font-family': "monospace", 'color': 'black', 'fontSize': 14}),
            html.P(update_date, style=data_style()),
        ]
    )


def data_style():
    return {'font-family': "monospace", 'color': 'gray', 'fontSize': 14}


def data_file_table():
    html_table_body = []
    for row in update_files:
        html_table_body.append(
            html.Tr(
                [
                    html.Td(row["No."], style=data_style()),
                    html.Td(row["File name"], style=data_style()),
                ]
            )
        )
    return html.Table(html_table_body)
