import json
import platform

import dash_mantine_components as dmc
from dash import html

import utils

DATA_OUTPUT_FORMAT = {"font-family": "monospace", "color": "gray", "fontSize": 14}

with open(utils.DATA_PATH / "update_log.json") as f:
    update_data = json.load(f)

update_date = update_data["time"]
update_files = update_data["files"]


def create_layout():
    return [
        dmc.Container(
            [
                dmc.Title("Info", order=3),
                dmc.Grid(
                    [
                        dmc.GridCol(
                            [
                                platform_info(),
                                os_info(),
                                python_info(),
                                last_update_time(),
                            ],
                            span=11,
                        ),
                        dmc.GridCol(data_file_table(), span=3),
                    ]
                ),
            ],
            fluid=True,
        ),
    ]


def data_file_table():
    html_table_body = []
    for num, file in enumerate(update_files, start=1):
        html_table_body.append(
            html.Tr(
                [
                    html.Td(num, style=DATA_OUTPUT_FORMAT),
                    html.Td(file, style=DATA_OUTPUT_FORMAT),
                ]
            )
        )
    return html.Table(html_table_body)


def last_update_time():
    return output_format(f"Data last updated: {update_date}")


def platform_info():
    return output_format(f"Machine architecture: {platform.machine()} {platform.architecture()[0]}")


def os_info():
    return output_format(f"Operating system: {platform.freedesktop_os_release()['PRETTY_NAME']}")


def python_info():
    return output_format(f"Python version: {platform.python_version()}")


def data_update_time():
    return output_format(f"Date last updated: {update_date}")


def output_format(text: str):
    return html.P(text, style=DATA_OUTPUT_FORMAT)
