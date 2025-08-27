# File:      layout.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Defines the Dash UI layout for the simulated PID cooler.

import dash_bootstrap_components as dbc
from dash import dcc, html

def get_layout(instrument_id: str, instrument_ref: object) -> dbc.Container:
    """
    Generates the Dash UI layout for a single PID cooler simulator instance.

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
                            dbc.Button("Next Setpoint", id=f"{instrument_id}-next-btn", color="primary", className="me-2"),
                            dbc.Button("Auto Mode", id=f"{instrument_id}-auto-btn", color="secondary"),
                        ])
                    ], color="light"),
                ], width=4)
            ])
        ]
    )