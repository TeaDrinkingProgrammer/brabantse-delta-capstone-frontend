import dash
from dash import Dash, html, dcc, Input, Output, callback, State
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import date

# Register new page
dash.register_page(
    __name__,
    path="/History_panel",
    title="History panel",
    name="History panel",
)

# Dash layout
layout = html.Div(
    [
        # Add a dcc.Store to your layout to share data between callbacks
        html.H1(children="Geschiedenis paneel", style={"textAlign": "center"}),
        html.Hr(),
        dmc.Space(h=10),
        dcc.DatePickerSingle(
            id='my-date-picker-single',
            min_date_allowed=date(2020, 8, 5),
            max_date_allowed=date(2023, 9, 19),
            initial_visible_month=date(2023, 8, 5),
            date=date(2023, 8, 25)
        ),

        dcc.Loading(
            id="loading-new",
            type="default",
            children=[dcc.Graph(id="day-graph")],
        ),
    ]
)


@callback(
    Output("day-graph", "figure"),
    Input('my-date-picker-single', 'date')
)
def update_day_graph(date_value):
    # Fetch data from the API
    url = "http://127.0.0.1:5000/data/day_data"
    response = requests.post(url, json={"date": date_value})
    data = response.json() if response.status_code == 200 else {}

    # Prepare the DataFrame from API data
    if data:
       # Create DataFrame from the extracted data
        df = pd.DataFrame(
            {
                "time": pd.to_datetime(data["timestamps"]),
                "precipitation": data["precipitation"],
                "results": data["percentage"],
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

        return fig
    else:
        return go.Figure()  # Return an empty figure if data is not available