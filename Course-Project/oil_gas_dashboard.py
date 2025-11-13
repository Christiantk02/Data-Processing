# ---------------------------------------------
# Requirements:
# pip install dash plotly pandas scikit-learn
# ---------------------------------------------

import dash
import pandas as pd
import numpy as np
import plotly.express as px
from dash import html, dcc, Input, Output
from sklearn.linear_model import LinearRegression


# === DATA PREPARATION ===
df_co2 = pd.read_csv('Course-Project/data/owid-co2-data.csv')
df_oil = pd.read_csv('Course-Project/data/Europe_Brent_Spot_Price_FOB.csv', skiprows=4)

# Clean and align data
df_oil.columns = ['date', 'brent_price_usd']
df_oil['date'] = pd.to_datetime(df_oil['date'], errors='coerce')
df_oil['year'] = df_oil['date'].dt.year
df_oil = df_oil.dropna(subset=['year', 'brent_price_usd'])
df_oil = df_oil.groupby('year', as_index=False)['brent_price_usd'].mean()
df_oil['country'] = 'World' 

df_co2 = df_co2[['country', 'year', 'co2', 'methane']]
df_co2 = df_co2.dropna(subset=['country', 'year', 'co2']) 

# Merge the datasets
df = pd.merge(df_co2, df_oil, on='year', how='left')
df = df.rename(columns={'country_x': 'country'})
df = df.drop(columns=['country_y'])
df = df[df['year'] >= 1987]


# === DASH APP SETUP ===
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True # IDEK
app.title = "Oil & Gas Dashboard"


# === LAYOUT ===
app.layout = html.Div([
    html.Div([
        html.H1("Oil and Gas Dashboard"),
        html.P("Interactive analysis of CO₂ emissions and Brent oil price."),
        html.P("By Christian T. Kvernland"),
        html.Hr(style={'borderColor': '#1b263b'})
    ]),

    dcc.Dropdown(
        id='plot-selector',
        options=[
            {'label': 'Oil Price and CO₂ Emissions over Time', 'value': 'time'},
            {'label': 'Oil Price vs CO₂ (Correlation)', 'value': 'corr'},
            {'label': 'Methane vs CO₂ (Gas Comparison)', 'value': 'methane_corr'},
            {'label': 'Top 10 Countries by CO₂ Emissions', 'value': 'top10'},
            {'label': 'Predicted CO₂ Emissions (Trend Forecast)', 'value': 'predict'}
        ],
        placeholder='Select what to plot...',
        style={'width': '60%', 'color': 'black'}
    ),

    html.Br(),
    html.Div(id='control-section'),
    html.Div(id='plot-section'),

], style={'backgroundColor': '#0d1b2a', 'minHeight': '100vh', 'padding': '20px', 'fontFamily': 'verdana','color': 'white'})


# === CALLBACKS ===
@app.callback(
    Output('control-section', 'children'),
    Input('plot-selector', 'value')
)
def update_controls(selected_plot):
    if selected_plot is None:
        return ""
    if selected_plot == 'time' or selected_plot == 'corr' or selected_plot == 'methane_corr':
        html_output = html.Div([
            html.Label('Select Country:'),
            dcc.Dropdown(
                id='country-selector',
                options=[{'label': c, 'value': c} for c in sorted(df['country'].unique())],
                value='Norway',
                multi=False,
                style={'width': '60%', 'color': 'black'}
            ),
            html.Br(),
            html.Label('Select Year Range:'),
            dcc.RangeSlider(
                id='year-slider',
                min=df['year'].min(),
                max=df['year'].max(),
                step=1,
                value=[1987, df['year'].max()],
                marks={year: str(year) for year in range(1987, 2025, 5)}
            ),
        ], style={'margin': '30px'})
   
    return html_output

@app.callback(
    Output('plot-section', 'children'),
    Input('plot-selector', 'value'),
    Input('country-selector', 'value'),
    Input('year-slider', 'value'),
    prevent_initial_call=True
)
def update_plot(selected_plot, country, years):
    if not selected_plot:
        return ""

    if not country or not years:
        return html.P('Select a country and year range.')
    
    if selected_plot == 'time':
        dff = df[(df['country'] == country) & (df['year'].between(years[0], years[1]))]

        fig = px.line()
        fig.add_scatter(x=dff['year'], y=dff['co2'], name='CO₂ emissions (Mt)', mode='lines')
        fig.add_scatter(x=dff['year'], y=dff['brent_price_usd'], name='Oil price (USD)', mode='lines', yaxis='y2')

        fig.update_layout(
            title=f'Oil Price and CO₂ Emissions over Time – {country}',
            yaxis_title='CO₂ emissions (Mil Tonnes)',
            yaxis2=dict(title='Oil price (USD/barrel)', overlaying='y', side='right'),
            paper_bgcolor='#0d1b2a',
            plot_bgcolor='#1b263b',
            font_color='white',
            legend=dict(orientation='h')
        )
    
    if selected_plot == 'corr':
        dff = df[(df['country'] == country) & (df['year'].between(years[0], years[1]))]

        fig = px.scatter(
            dff,
            x='brent_price_usd',
            y='co2',
            trendline='ols',
            color_discrete_sequence=['#00bfff'],
            title=f'Oil Price vs CO₂ Emissions – {country}',
            labels={'brent_price_usd': 'Oil price (USD/barrel)', 'co2': 'CO₂ emissions (million tonnes)'}
        )

        fig.update_layout(
            paper_bgcolor='#0d1b2a',
            plot_bgcolor='#1b263b',
            font_color='white'
        )

    if selected_plot == 'methane_corr':
        dff = df[(df['country'] == country) & (df['year'].between(years[0], years[1]))]

        fig = px.scatter(
            dff,
            x='methane',
            y='co2',
            color='year',
            color_continuous_scale='turbo',
            trendline='ols',
            title=f'Methane vs CO₂ Emissions – {country}',
            labels={
                'methane': 'Methane emissions (million tonnes)',
                'co2': 'CO₂ emissions (million tonnes)',
                'year': 'Year'
            }
        )

        fig.update_layout(
            paper_bgcolor='#0d1b2a',
            plot_bgcolor='#1b263b',
            font_color='white',
            title_font=dict(size=20),
            coloraxis_colorbar=dict(title='Year')
        )

    return dcc.Graph(figure=fig)


# === RUN APP ===
app.run(debug=True)
