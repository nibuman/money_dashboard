import os

import dash_mantine_components as dmc
from dash import Dash, dcc

# from money_dashboard import investments, retirement
from pages import assets, info, investments, retirement, retirement_model

os.environ["REACT_VERSION"] = "18.2.0"  # Required for dmc v0.14

# Initialize the app - incorporate a Dash Mantine theme
# external_stylesheets = [dmc.theme.DEFAULT_COLORS]
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
# Run the App
if __name__ == "__main__":
    # Need these settings for the server to be visible to other computers on the network
    # app.run_server(host="0.0.0.0", port="8050")
    app.run()
