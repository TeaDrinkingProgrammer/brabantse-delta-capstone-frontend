import grequests
import dash
from dash import html, dcc, Input, Output, callback
import pandas as pd
import plotly.graph_objects as go
import pickle
import time
import numpy as np
import asyncio
import plotly.express as px

def calculate_rainfall_previous_2_hours_corrected(df):
    # Set the index to the time for rolling window calculations
    df = df.set_index('time')
    
    # get the rainfall of 8 records before the current record before the current record, if out of range, set to 0  
    df['rainfall_previous_2_hours'] = 0
    df['rainfall_previous_2_hours'].iloc[8:] = df['precipitation'].iloc[:-8].values
    
    # Reset the index
    df = df.reset_index()
    
    return df

# drop the first day of the df (yessterday's data)
def drop_first_day(df):
    df = df[96:]
    return df

def initialize_and_update_lag_features(df, model, scaler):
    # Vectorized initialization of lag features
    default_value = 0  # Replace with a sensible default if applicable
    lag_columns = [f'percentage_previous_{i}' for i in range(1, 7)]
    df[lag_columns] = default_value

    # Vectorized prediction and lag update
    scaled_df = scaler.transform(df.values)
    predicted_percentages = model.predict(scaled_df)

    for i in range(1, 7):
        df[f'percentage_previous_{i}'] = predicted_percentages
        predicted_percentages = np.roll(predicted_percentages, shift=1)
        df[f'percentage_previous_{i}'].iloc[0] = default_value

    return df


# Register new page
dash.register_page(
    __name__,
    path="/Prediction_panel",
    title="Prediction Forecast",
    name="Prediction panel",
)


# Load the scaler and the model from the pickle files
scaler_file = './data/scaler.pkl'
model_file = './data/model_randomforest_14.pkl'

with open(scaler_file, 'rb') as file:
    scaler = pickle.load(file)

with open(model_file, 'rb') as file:
    model = pickle.load(file)

scaler, model


# Dash layout
layout = html.Div([
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': '1 dag', 'value': '1'},
            {'label': '3 dagen', 'value': '3'},
            {'label': '7 dagen', 'value': '7'},
            {'label': '14 dagen', 'value': '14'},
            {'label': '16 dagen', 'value': '16'},
        ],
        value='3'
    ),
    dcc.Loading(
            id="loading-new",
            type="default",
            children=[dcc.Graph(id="forecast-graph")],
    ),
])

def fetch_data(day):
    url = f'https://api.open-meteo.com/v1/forecast?latitude=51.55202&longitude=4.586668&minutely_15=precipitation&past_days=1&forecast_days={day}'
    return grequests.get(url)

@callback(
    Output('forecast-graph', 'figure'),
    Input('dropdown', 'value')
)
def update_graph(day):
    
    start_time = time.time()
    # Use grequests to send asynchronous requests
    responses = grequests.map([fetch_data(day)])
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Check if the response is successful
    data = responses[0].json() if responses[0] and responses[0].status_code == 200 else {}

    # Prepare the DataFrame from API data
    if data:
        # Extract minutely_15 data
        minutely_data = data['minutely_15']

        # Create DataFrame from the extracted data
        df = pd.DataFrame({
            'time': pd.to_datetime(minutely_data['time']),
            'precipitation': minutely_data['precipitation']
        })

        # Add columns for 'day', 'month', 'dayofweek', 'hour', 'rainfall_current'
        df['day'] = df['time'].dt.day
        df['month'] = df['time'].dt.month
        df['dayofweek'] = df['time'].dt.dayofweek
        df['hour'] = df['time'].dt.hour
        df['rainfall_current'] = df['precipitation']

        # Calculate rainfall for 2 hours ago
        df = calculate_rainfall_previous_2_hours_corrected(df)
        df = drop_first_day(df)

        filtered_df = df.loc[:, ~df.columns.isin(['time', 'precipitation'])]


        # Filter out time and precipitation columns and initialize the lag features
        filtered_df = initialize_and_update_lag_features(filtered_df, model, scaler)
        results = model.predict(filtered_df)

        df_time = time.time()

        # Add line for percentage_current
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=results,
                mode="lines",
                name="Capacity Percentage (%)"
            )
        )

        # Add line for rainfall_current
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=filtered_df["rainfall_current"],
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
        end_time = time.time()
        
        execution_time = end_time - start_time
        df_time_measurement = df_time - start_time
        print(f"Execution time total: {execution_time} seconds")
        print(f"Execution time df: {df_time_measurement} seconds")
        
        return fig

    else:
        return go.Figure()  # Return an empty figure if data is not available

