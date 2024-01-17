import dash
from dash import html

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('Brabantse Delta Sewage prediction'),
    html.P('This is a demo-application that can predict the amount of sewage water that will be in the sewer-system in a specific area in Rucphen.'),
    html.P('The predictions are quite accurate, but can miss some small peaks in rainfall.')
])