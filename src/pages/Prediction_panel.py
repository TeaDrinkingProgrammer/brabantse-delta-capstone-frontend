import dash
from dash import Dash, html, dcc, Input, Output, callback, State
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
import requests

# Register new page
dash.register_page(
    __name__,
    path="/Prediction_panel",
    title="Prediction Forecast",
    name="Prediction panel",
)

# Dash layout
layout = html.Div(
    [
        # Add a dcc.Store to your layout to share data between callbacks
        dcc.Store(id="shared-data"),
        dcc.Store(id="api-data"),
        dmc.Button("Download Table Data", id="btn_csv"),
        dcc.Download(id="download-dataframe-csv"),
        dmc.Space(h=10),
        dcc.Dropdown(
            id="dropdown",
            options=[
                {"label": "1 dag", "value": "1"},
                {"label": "3 dagen", "value": "3"},
                {"label": "7 dagen", "value": "7"},
                {"label": "14 dagen", "value": "14"},
                {"label": "16 dagen", "value": "16"},
            ],
            value="3",
        ),

        dcc.Loading(
            id="loading-new",
            type="default",
            children=[dcc.Graph(id="forecast-graph")],
        ),
    ]
)


# Callback for the download button to use the data from the store for downloading
@callback(
    Output("download-dataframe-csv", "data"),
    Input(
        "btn_csv", "n_clicks"
    ),  # Replace 'download-button' with the actual ID of your download button
    State("shared-data", "data"),  # The stored JSON data
)
def download_data(n_clicks, data):
    if n_clicks is None or data is None:
        # Prevent download from being triggered on page load or if there is no data
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(data, orient="split")
    return dcc.send_data_frame(df.to_csv, filename="data.csv")


@callback(
    Output("forecast-graph", "figure"),
    Output("shared-data", "data"),
    Input("dropdown", "value"),
)
def update_graph(day):
    # Fetch data from the API
    url = "http://127.0.0.1:5000/data/predict"
    response = requests.post(url, json={"days": day})
    data = response.json() if response.status_code == 200 else {}

    # Prepare the DataFrame from API data
    if data:
        # Create DataFrame from the extracted data
        df = pd.DataFrame(
            {
                "time": pd.to_datetime(data["timestamps"]),
                "precipitation": data["precipitation"],
                "results": data["predictions"],
            }
        )

        # Create Plotly figure
        fig = go.Figure()

        # Add line for percentage_current
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["results"],
                mode="lines",
                name="Capacity Percentage (%)",
            )
        )

        # Add line for rainfall_current
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["precipitation"],
                mode="lines",
                name="Rainfall (mm)",
                yaxis="y2",
            )
        )

        # Update layout with a secondary y-axis
        fig.update_layout(
            yaxis=dict(title="Capacity Percentage (%)", range=[0, 100]),
            yaxis2=dict(title="Rainfall (mm)", overlaying="y", side="right"),
            xaxis=dict(
                rangeslider_visible=True,
                rangeselector=dict(
                    buttons=list(
                        [
                            # Add your desired time range buttons
                        ]
                    )
                ),
            ),
        )

        # Add the time column, precipitation column and the results column to a new variable named data
        data = df[["time", "precipitation"]]
        data["results"] = df["results"]

        return fig, data.to_json(
            date_format="iso", orient="split"
        )  # Return the figure and the DataFrame as JSON
    else:
        return go.Figure()  # Return an empty figure if data is not available


