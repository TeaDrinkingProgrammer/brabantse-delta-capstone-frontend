import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

app = Dash(use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Sidebar setup
sidebar = dbc.Nav(
    [
        html.Div(
            [
                # Include an image tag at the top of the sidebar
                html.Img(src="/assets/logo-wsbd.png", className="d-inline-block align-top p-3"),
                # Optionally, add a title or some text below the image
                html.Hr(),
            ],
            className="sidebar-header",
        ),
        # Navigation links - wrapped in a list
        *[dbc.NavLink(f"{page['name']}", href=page["relative_path"]) for page in dash.page_registry.values()]
    ],
    vertical=True,
    pills=True,  # This is optional, adds highlighting to the active link
)



# App layout with sidebar and page content
app.layout = dbc.Container(
    dbc.Row([
        dbc.Col(sidebar, width=2, className="sidebar"),  # Adjust width as needed
        dbc.Col(dash.page_container, width=10, className="p-5"),
    ]),
    fluid=True,
)

if __name__ == '__main__':
    app.run(debug=True)