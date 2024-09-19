import os

os.environ["REACT_VERSION"] = "18.2.0"  # Required for dmc v0.14, set before dmc and Dash imported

import dash_mantine_components as dmc
from dash import Dash, dcc

from pages import assets, info, investments, retirement, retirement_model

app = Dash(__name__, external_stylesheets=dmc.styles.ALL, title="Finances")
server = app.server  # server points to the Flask server behind Dash. Gunicorn needs a reference to this
app.layout = dmc.MantineProvider(
    dmc.Tabs(
        [
            dmc.TabsList(
                [
                    dmc.TabsTab("Assets", value="1"),
                    dmc.TabsTab("Investments", value="2"),
                    dmc.TabsTab("Retirement Investments", value="3"),
                    dmc.TabsTab("Retirement Model", value="4"),
                    dmc.TabsTab("Info", value="5"),
                ]
            ),
            dmc.TabsPanel(assets.create_layout(), value="1"),
            dmc.TabsPanel(investments.create_layout(), value="2"),
            dmc.TabsPanel(retirement.create_layout(), value="3"),
            dmc.TabsPanel(retirement_model.create_layout(), value="4"),
            dmc.TabsPanel(info.create_layout(), value="5"),
            dcc.Store(id="sorted_data"),
        ],
        value="1",
    )
)

if __name__ == "__main__":
    # Debug mode will automatically refresh web pages when changes to files are made
    app.run(debug=True)
