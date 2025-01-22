import json

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import plotly.express as px
from flask import Flask

API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhNTFkM2M2ZGY1Yjk2YTdkOWMyMzUzMTI3NjM1NmEwNCIsIm5iZiI6MTY5OTQ3MzEyNi44MDQ5OTk4LCJzdWIiOiI2NTRiZTZlNjFhYzI5MjdiMzAyOWNlYzciLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.eFK5Ect3ShyuR4iwAgZwYeORljQ1Gq1bE4eEJHierkM'
BASE_URL = 'https://api.themoviedb.org/3/'

# GET Kaggle dataset
# ==============================================================================
# movies_1 = pd.read_csv("assets/top_5000_popular_movies_tmdb_1.csv", index_col=0)
# movies_2 = pd.read_csv("assets/top_5000_popular_movies_tmdb_2.csv", index_col=0)

movies_1 = pd.read_csv("assets/top_5000_popular_movies_tmdb_1.csv", index_col=0)
movies_2 = pd.read_csv("assets/top_5000_popular_movies_tmdb_2.csv", index_col=0)
movies_languages = pd.read_csv("assets/movies_countries_languages.csv")

movies_df = pd.concat([movies_1, movies_2])
movies_df = pd.merge(movies_df, movies_languages, on='id_film')

movies_df['production_year'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year
movies_df[['budget', 'vote_average', 'revenue']] = movies_df[['budget', 'vote_average', 'revenue']].apply(pd.to_numeric, errors='coerce')

movies_df = movies_df.convert_dtypes()

# GET Unique genres with TMDB API
# ==============================================================================
GENRES = {}

url = f"{BASE_URL}genre/movie/list?language=en-US"
headers = {
    'Authorization': f"Bearer {API_KEY}",
    'accept': 'application/json'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    GENRES = response.json()['genres']
    print('Genres fetched successfully')
else:
    print(f'Error: {response.status_code}')

# GET Unique locations names with TMDB API
# ==============================================================================
COUNTRIES = {}

url = f"{BASE_URL}configuration/countries?language=en-US"
headers = {
    'Authorization': f"Bearer {API_KEY}",
    'accept': 'application/json'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    COUNTRIES = response.json()
    print('Countries fetched successfully')
else:
    print(f'Error: {response.status_code}')


# Initial toast
# ==============================================================================
initial_toast = dbc.Toast(
    [
        html.P(
            "In this dashboard you can explore the TMDB dataset and API with filter movies like genre and release year and see the results in the graphs.",
            className="mb-0"),
        html.Div([
            html.Img(src="assets/TMDB-logo.png", style={"width": "100px", "height": "auto", "margin": "15px"}),
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
    ],
    id="initial_toast",
    header="TMDB Dashboard",
    icon="info",
    dismissable=True,
    duration=5000
)

# DASH APP
# ==============================================================================
server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP, "assets/styles.css"])

# DASH LAYOUT
# ==============================================================================
app.layout = dbc.Container(
    [
        initial_toast,
        html.Div(id='toast-container'),
        dbc.Row([
            html.Div(id='title_container', children = [
                html.H1("TMDB Dashboard", className="textCenter my-4", style={"marginRight": "10px"}),
                html.Img(src="assets/TMDB-logo.png", style={"width": "100px", "height": "auto"}),
            ])
        ], style={"margin": "20px"}),

        # Gráficas en un layout responsive
        dbc.Row([
            dbc.Col(
                html.Div(id='filters_container', children = [
                    html.H1("Filters", className="textCenter"),
                    dbc.Row([
                        html.Label("Select genres:", style={'fontSize': '18px'}),
                        dcc.Dropdown(
                            id='genre-filter',
                            options=[{'label': genre['name'], 'value': genre['name']} for genre in GENRES],
                            multi=True
                        )
                    ]),
                    dbc.Row([
                        html.Label("Select range of years:", style={'fontSize': '18px'}, id='slider-output'),
                        dcc.RangeSlider(
                            id='year-filter',
                            step=1,
                            value=[1920, 2025],
                            marks={i: str(i) for i in range(1920, 2021, 10)}
                        )
                    ]),
                    dbc.Row([
                        html.Label("Select country:", style={'fontSize': '18px'}),
                        dcc.Dropdown(
                            id='country-filter',
                            options=[{'label': country['english_name'], 'value': country['english_name']} for country in COUNTRIES],
                            multi=True
                        )
                    ]),
                    html.Div(id='buttons_container', children = [
                        dbc.Button('Reset', id='reset-button', n_clicks=0),
                        dbc.Button('Apply', id='apply-button', n_clicks=0)
                    ])
                ])
                , md=5),
            dbc.Col(html.Div(id='graphs_container1', children = dcc.Graph(id='bar_chart')), md=7),
        ]),
        dbc.Row([
            dbc.Col(html.Div(id='graphs_container2', children = dcc.Graph(id='pie_chart')), md=6),
            dbc.Col(html.Div(id='graphs_container3', children = dcc.Graph(id='map_chart')), md=6),
        ]),
    ],
    fluid=True,
)


@app.callback(
    [Output('bar_chart', 'figure'),
     Output('map_chart', 'figure')],
    [Input('apply-button', 'n_clicks')],
    [State('year-filter', 'value'),
     State('genre-filter', 'value'),
     State('country-filter', 'value')]
)
def update_bar_chart(n_clicks, selected_years, selected_genres, selected_countries):
    filtered_df = movies_df[
        (movies_df['production_year'] >= selected_years[0]) & (movies_df['production_year'] <= selected_years[1])]

    if selected_genres:
        filtered_df = filtered_df[
            filtered_df['genres'].apply(lambda x: any(genre in x for genre in selected_genres))
        ]

    if selected_countries:
        filtered_df = filtered_df[
            filtered_df['production_countries'].apply(lambda x: any(country == x for country in selected_countries))
        ]

    count_per_year = filtered_df['production_year'].value_counts().sort_index()
    total_budget_per_year = (
        filtered_df.groupby('production_year')['budget'].sum()
    )

    count_df = pd.DataFrame({
        'Year': count_per_year.index,
        'Movies Released': count_per_year.values,
        'Total (sum) of Budget': total_budget_per_year.values
    })

    fig = px.bar(count_df, x='Year', y='Movies Released',
                 title="Movies Released per Year",
                 color='Total (sum) of Budget')

    country_counts = filtered_df['production_countries'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Movie Count']

    fig2 = px.scatter_geo(country_counts,
                         locations="Country",
                         locationmode="country names",
                         color="Country",
                         hover_name="Country",
                         size="Movie Count")

    return fig, fig2


@app.callback(
    Output('pie_chart', 'figure'),
    Input('apply-button', 'n_clicks'),
    [State('year-filter', 'value'),
     State('country-filter', 'value')]
)
def update_pie_chart(n_clicks, selected_years, selected_countries):
    filtered_df = movies_df[
        (movies_df['production_year'] >= selected_years[0]) & (
                    movies_df['production_year'] <= selected_years[1])].copy()

    if selected_countries:
        filtered_df = filtered_df[
            filtered_df['production_countries'].apply(lambda x: any(country == x for country in selected_countries))
        ]

    filtered_df['genres'] = filtered_df['genres'].apply(eval)

    genres_exploded = filtered_df.explode('genres')

    genre_counts = genres_exploded['genres'].value_counts()

    fig = px.pie(
        names=genre_counts.index,
        values=genre_counts.values,
        title='Number of movies by genre',
        labels={'values': 'Count', 'names': 'Genre'},
    )

    return fig

@app.callback(
    [Output('genre-filter', 'value'),
     Output('year-filter', 'value'),
     Output('country-filter', 'value')],
    [Input('reset-button', 'n_clicks')]
)
def reset_filters(n_clicks):
    if n_clicks > 0:
        return None, [1920, 2025], None
    return dash.no_update

@app.callback(
    Output('toast-container', 'children'),  # Output per als toasts
    Input('map_chart', 'clickData')        # Input del clic al gràfic
)
def display_click_data(click_data):
    if click_data:
        country_name = click_data['points'][0].get('location', 'Desconegut')
        longitude = click_data['points'][0].get('lon', 'N/A')
        latitude = click_data['points'][0].get('lat', 'N/A')

        filtered_df = movies_df[movies_df['production_countries'] == country_name]

        country_counts = filtered_df['production_countries'].value_counts().reset_index()
        country_counts.columns = ['Country', 'Movie Count']

        if not country_counts.empty:
            movies_count = country_counts.iloc[0]['Movie Count']
        else:
            movies_count = "No disponible"

        # Contingut del toast
        content = html.Div([
            html.P(f"Name of country: {country_name}"),
            html.P(f"Coordinates: ({latitude}, {longitude})"),
            html.P(f"Total count of films: {movies_count}"),
            html.P(f"Total renueve: {filtered_df['revenue'].sum()}"),
            html.P(f"Total budget: {filtered_df['budget'].sum()}"),
        ])

        # Crea un toast amb la informació
        return dbc.Toast(
            content,
            header="Information about the country",
            is_open=True,
            duration=5000,
            dismissable=True,
            style={
                "position": "fixed",
                "top": "50%",
                "left": "50%",
                "transform": "translate(-50%, -50%)",
                "zIndex": 1050,
                "width": "400px"
            }
        )
    return None

@app.callback(
    Output('slider-output', 'children'),
    Input('year-filter', 'value')
)
def update_slider_output(value):
    return f"Select range of years: {value[0]} - {value[1]}"


if __name__ == '__main__':
    app.run_server(debug=True)
