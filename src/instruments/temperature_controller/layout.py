# File:      layout.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Defines the Dash UI layout for the temperature controller.

import dash_bootstrap_components as dbc
from dash import dcc, html

def get_layout(instrument_id: str, instrument_ref: object) -> dbc.Container:
    """
    Generates the Dash UI layout for a single temperature controller instance.

    Args:
        instrument_id (str): The unique ID of the instrument instance.
        instrument_ref (object): A reference to the instrument object itself,
                                 used to get initial values.

    Returns:
        dbc.Container: A Dash Bootstrap Container with the instrument's UI.
    """
    return dbc.Container(
        fluid=True,
        className="instrument-card mb-4",
        children=[
            # Hidden div for callbacks that don't need a visible output
            html.Div(id=f"{instrument_id}-dummy-output", style={'display': 'none'}),
            dbc.Row([
                # Left side: Graph
                dbc.Col(
                    dcc.Graph(
                        id=f"{instrument_id}-graph",
                        # Animate graph for smoother updates
                        animate=True,
                        config={
                            'scrollZoom': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['select2d', 'lasso2d']
                        }
                    ),
                    width=8
                ),
                # Right side: Status and Controls
                dbc.Col([
                    dbc.Card(
                        id=f"{instrument_id}-status-card",
                        children=[
                            dbc.CardHeader("Live Status"),
                            dbc.CardBody([
                                html.H5("Loading...", className="card-title"),
                                html.P("Setpoint: N/A"),
                                html.P("Status: Unknown"),
                                html.P("Time Stable: 0.0s"),
                            ])
                        ],
                        color="light",
                        className="mb-3"
                    ),
                    dbc.Card([
                        dbc.CardHeader("Controls"),
                        dbc.CardBody([
                            dbc.Button("Next Setpoint", id=f"{instrument_id}-next-btn", color="primary", className="me-2", disabled=False),
                            dbc.Switch(
                                id=f"{instrument_id}-auto-switch",
                                label="Auto Mode: ON",
                                value=True,
                                className="mt-2"
                            ),
                        ])
                    ], color="light"),
                    dbc.Card([
                        dbc.CardHeader("Export Data"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(dcc.DatePickerSingle(
                                    id=f'{instrument_id}-start-date-picker',
                                    display_format='YYYY-MM-DD',
                                    placeholder='Start Date',
                                    className="w-100"
                                ), width=5),
                                dbc.Col(dcc.Input(
                                    id=f'{instrument_id}-start-time-input',
                                    type='text',
                                    placeholder='HH:MM',
                                    className="w-100"
                                ), width=3),
                                dbc.Col(html.Div('->', style={'textAlign': 'center', 'paddingTop': '8px'}), width=1),
                                dbc.Col(dcc.DatePickerSingle(
                                    id=f'{instrument_id}-end-date-picker',
                                    display_format='YYYY-MM-DD',
                                    placeholder='End Date',
                                    className="w-100"
                                ), width=5),
                                dbc.Col(dcc.Input(
                                    id=f'{instrument_id}-end-time-input',
                                    type='text',
                                    placeholder='HH:MM',
                                    className="w-100"
                                ), width=3),
                            ], className="g-2 align-items-center"),
                            dbc.Button(
                                "Download CSV",
                                id=f'{instrument_id}-download-btn',
                                color="success",
                                className="mt-2 w-100"
                            ),
                        ])
                    ], color="light", className="mt-3"),
                    dcc.Download(id=f'{instrument_id}-download-csv'),
                ], width=4)
            ])
        ]
    )