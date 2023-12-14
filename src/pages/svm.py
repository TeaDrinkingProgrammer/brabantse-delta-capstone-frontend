import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # Importing graph_objects for more control

dash.register_page(
    __name__,
    path="/water-dashboard",
    title="Our Analytics Dashboard",
    name="Vullingsgraad Rucphen",
)

# Incorporate data
df = pd.read_parquet("./data/rucphen_precipitation_clean.parquet")

start_timestamp = pd.to_datetime("2022-01-01 08:00:00")
end_timestamp = pd.to_datetime("2022-12-01 08:00:00")

# Create a boolean mask for the specified time range
mask = (df["timestamp"] >= start_timestamp) & (df["timestamp"] < end_timestamp)

# Apply the mask to get the desired slice of the DataFrame
df = df[mask]

# App layout
layout = html.Div(
    [
        html.H1(children="Vullingsgraad Rucphen", style={"textAlign": "center"}),
        html.Hr(),
        dcc.Checklist(
            id="checklist", options=["Rucphen"], value=["Rucphen-11"], inline=True
        ),
        dcc.Loading(
            id="loading-1",
            type="default",  # You can choose other types like 'circle', 'dot', etc.
            children=[dcc.Graph(id="graph-content")],
        ),
    ]
)


@callback(Output("graph-content", "figure"), Input("checklist", "value"))
def update_graph(value):
    # Create an empty figure
    fig = go.Figure()

    # Add line for percentage
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"], y=df["percentage"], mode="lines", name="Percentage"
        )
    )

    # Add line for precipitation
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["precipitation"],
            mode="lines",
            name="Rainfall",
            yaxis="y2",
        )
    )

    # Update layout with a secondary y-axis
    fig.update_layout(
        yaxis=dict(title="Percentage"),
        yaxis2=dict(title="Rainfall (mm)", overlaying="y", side="right"),
        xaxis=dict(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=3, label="3m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
        ),
    )

    return fig
