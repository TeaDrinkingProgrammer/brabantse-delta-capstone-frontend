import dash
from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import plotly.graph_objects as go
import requests
import pickle
from datetime import datetime, timedelta


# Corrected function to calculate rainfall for the previous 2 hours for each record
def calculate_rainfall_previous_2_hours_corrected(df):
    # Set the index to the time for rolling window calculations
    df = df.set_index('time')
    
    #for loop 
    for i in range(0, len(df)):
        #get the rainfall of 8 records before the current record before the current record, if out of range, set to 0  
        if i < 8:
            df.loc[df.index[i], 'rainfall_previous_2_hours'] = 0
        else:
            df.loc[df.index[i], 'rainfall_previous_2_hours'] = df.loc[df.index[i-8], 'precipitation']
        
    #reset the index
    df = df.reset_index()
    
    return df

#drop the first day of the df (yessterday's data)
def drop_first_day(df):
    df = df[96:]
    return df

def init_lag_features(df, model, scaler):
    # Initialize the lag features with default values
    default_value = 0  # Replace with a sensible default if applicable
    df['percentage_previous_1'] = default_value
    df['percentage_previous_2'] = default_value
    df['percentage_previous_3'] = default_value
    df['percentage_previous_4'] = default_value
    df['percentage_previous_5'] = default_value
    df['percentage_previous_6'] = default_value

    # Iterate through the DataFrame and predict the percentage for each record
    for index, row in df.iterrows():
        # Scale the entire row
        scaled_row = scaler.transform([row.values])

        # Predict using the model
        predicted_percentage = model.predict(scaled_row)[0]

        # Update the lag features for the next record
        if index + 1 < len(df):
            df.loc[index + 1, 'percentage_previous_1'] = predicted_percentage
            if index + 1 >= 2:
                df.loc[index + 1, 'percentage_previous_2'] = df.loc[index, 'percentage_previous_1']
            if index + 1 >= 3:
                df.loc[index + 1, 'percentage_previous_3'] = df.loc[index, 'percentage_previous_2']
            if index + 1 >= 4:
                df.loc[index + 1, 'percentage_previous_4'] = df.loc[index, 'percentage_previous_3']
            if index + 1 >= 5:
                df.loc[index + 1, 'percentage_previous_5'] = df.loc[index, 'percentage_previous_4']
            if index + 1 >= 6:
                df.loc[index + 1, 'percentage_previous_6'] = df.loc[index, 'percentage_previous_5']

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

@callback(
    Output('forecast-graph', 'figure'),
    Input('dropdown', 'value')
)
def update_graph(day):
    # Fetch data from the API
    url = f'https://api.open-meteo.com/v1/forecast?latitude=51.55202&longitude=4.586668&minutely_15=precipitation&past_days=1&forecast_days={day}'
    response = requests.get(url)
    data = response.json() if response.status_code == 200 else {}

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
        df_copy = df.copy()

        # Drop time
        df = df.drop(columns=['time'])
        df = df.drop(columns=['precipitation'])

        # Initialize the lag features
        df = init_lag_features(df, model, scaler)
        results = model.predict(df)

        # Create Plotly figure
        fig = go.Figure()

        # Add line for percentage_current
        fig.add_trace(
            go.Scatter(
                x=df_copy["time"],
                y=results,
                mode="lines",
                name="Capacity Percentage (%)"
            )
        )

        # Add line for rainfall_current
        fig.add_trace(
            go.Scatter(
                x=df_copy["time"],
                y=df["rainfall_current"],
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

        return fig
    else:
        return go.Figure()  # Return an empty figure if data is not available

