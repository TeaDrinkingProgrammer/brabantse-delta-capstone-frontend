import dash
from dash import Dash, html, dcc
import pandas as pd
import plotly.graph_objects as go

# Register new page
dash.register_page(
    __name__,
    path="/prediction",
    title="Dag verwachting",
    name="Dag verwachting",
)

# Read the Excel file
df = pd.read_excel("./data/pred_df_20231218-114140_randomforest_14.xlsx")  # Replace with the correct file path

# Ensure Timestamp is a datetime type
df['Timestamp'] = pd.to_datetime(df['timestamp'])

# Create the figure
fig = go.Figure()

# Add line for percentage_current
fig.add_trace(
    go.Scatter(
        x=df["Timestamp"],
        y=df["percentage_current"],
        mode="lines",
        name="Capacity Percentage"
    )
)

# Add line for rainfall_current
fig.add_trace(
    go.Scatter(
        x=df["Timestamp"],
        y=df["rainfall_current"],
        mode="lines",
        name="Rainfall (mm)",
        yaxis="y2",
    )
)

# Update layout with a secondary y-axis
fig.update_layout(
    yaxis=dict(title="Capacity Percentage (%)"),
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

# App layout for the new page
layout = html.Div(
    [
        html.H1(children="New Water Dashboard", style={"textAlign": "center"}),
        html.Hr(),
        dcc.Loading(
            id="loading-new",
            type="default",
            children=[dcc.Graph(id="new-graph-content", figure=fig)],
        ),
    ]
)
