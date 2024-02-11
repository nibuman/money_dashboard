import dash_mantine_components as dmc
from dash import Dash, dcc

# from money_dashboard import investments, retirement
from pages import assets, investments, retirement

# Initialize the app - incorporate a Dash Mantine theme
external_stylesheets = [dmc.theme.DEFAULT_COLORS]
app = Dash(__name__, external_stylesheets=external_stylesheets, title="Finances")

app.layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Assets", value="1"),
                dmc.Tab("Investments", value="2"),
                dmc.Tab("Retirement", value="3"),
            ]
        ),
        dmc.TabsPanel(assets.create_layout(), value="1"),
        dmc.TabsPanel(investments.create_layout(), value="2"),
        dmc.TabsPanel(retirement.create_layout(), value="3"),
        dcc.Store(id="sorted_data"),
    ],
    value="1",
)

# Run the App
if __name__ == "__main__":
    app.run(debug=True)
