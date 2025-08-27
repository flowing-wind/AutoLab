# File:      app.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      The main application entry point for the instrument control panel.
#            This application uses Dash to create a web-based UI and provides
#            a REST API for external access to instrument data.

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import importlib
import json
from flask import jsonify
import logging
import os

# --- Logging Setup ---
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Application Setup ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# --- Instrument Loading and Caching ---
# This dictionary will hold all loaded instrument objects, keyed by mode.
instruments = {}

def load_all_instruments():
    """
    Loads all instruments defined in instruments.csv and config.csv,
    registers their callbacks, and stores them in the `instruments` dictionary.
    """
    try:
        # Load instrument connection details
        instruments_df = pd.read_csv("instruments.csv", quotechar="'")
        # Load instrument specific configurations
        configs_df = pd.read_csv("config.csv", quotechar="'")

        # Merge the two dataframes on instrument_id
        merged_df = pd.merge(instruments_df, configs_df, on='instrument_id', how='left')

        for _, instrument_row in merged_df.iterrows():
            instrument_id = instrument_row['instrument_id']
            instrument_type = instrument_row['type']
            
            # Determine mode from type
            mode = 'SIMULATED' if 'simulator' in instrument_type else 'REAL'

            # Skip if we already have an instrument for this mode (based on current logic)
            if mode in instruments:
                logger.warning(f"Already have an instrument for {mode} mode. Skipping {instrument_id}.")
                continue

            visa_address = instrument_row['visa_address']
            try:
                config_str = instrument_row['config'] if isinstance(instrument_row['config'], str) else '{}'
                specific_config = json.loads(config_str)
            except (json.JSONDecodeError, KeyError):
                specific_config = {}

            # Combine visa_address with specific config
            config = {"visa_address": visa_address, **specific_config}

            logger.info(f"Loading instrument for {mode} mode: {instrument_id}")
            module_path = f"src.instruments.{instrument_type}.interface"
            InstrumentClass = getattr(importlib.import_module(module_path), 'InstrumentInterface')
            
            instance = InstrumentClass(instrument_id, config)
            
            # We register callbacks for all at the start but only connect when active.
            instance.register_callbacks(app)
            instruments[mode] = instance
            
    except (FileNotFoundError, IndexError) as e:
        logger.error(f"Could not read or parse configuration files: {e}")
    except Exception as e:
        logger.error(f"Error loading instruments: {e}", exc_info=True)

# --- API Endpoints ---
@server.route('/api/v1/instrument/<instrument_id>/state')
def get_instrument_state_api(instrument_id):
    """
    Flask route to get the state of a specific instrument.
    """
    instrument = next((inst for inst in instruments.values() if inst.instrument_id == instrument_id), None)
    if instrument and instrument.is_connected:
        return jsonify(instrument.get_state())
    else:
        return jsonify({"error": "Instrument not found or not active"}), 404

# --- Dash Layout ---
def create_app_layout():
    """
    Loads all instruments and creates the main layout.
    The layout includes containers for each instrument's UI.
    """
    load_all_instruments()
    
    sim_instrument = instruments.get('SIMULATED')
    real_instrument = instruments.get('REAL')

    # Connect to the default instrument (SIMULATED)
    if sim_instrument:
        sim_instrument.connect()

    return dbc.Container(
        [
            dcc.Interval(
                id='main-update-interval',
                interval=500,
                n_intervals=0
            ),
            dbc.NavbarSimple(
                brand="Lab Instrument Control Panel",
                color="primary",
                dark=True,
                className="mb-4",
                children=[
                    dbc.RadioItems(
                        id="mode-select-radio",
                        options=[
                            {'label': 'Simulated Mode', 'value': 'SIMULATED'},
                            {'label': 'Real Mode', 'value': 'REAL'},
                        ],
                        value='SIMULATED', # Default value
                        inline=True,
                        className="text-light"
                    )
                ]
            ),
            # Container for the simulated instrument UI
            html.Div(
                id='instrument-container-SIMULATED',
                children=sim_instrument.get_layout() if sim_instrument else dbc.Alert("Simulated instrument failed to load.", color="warning"),
                style={'display': 'block'} # Show by default
            ),
            # Container for the real instrument UI
            html.Div(
                id='instrument-container-REAL',
                children=real_instrument.get_layout() if real_instrument else dbc.Alert("Real instrument failed to load.", color="warning"),
                style={'display': 'none'} # Hide by default
            )
        ],
        fluid=True
    )

app.layout = create_app_layout

# --- Dash Callbacks ---
@app.callback(
    [
        Output('instrument-container-SIMULATED', 'style'),
        Output('instrument-container-REAL', 'style')
    ],
    [Input('mode-select-radio', 'value')],
    prevent_initial_call=True
)
def update_instrument_display(mode):
    """
    This callback shows/hides the instrument UIs based on the selected mode.
    It also handles connecting/disconnecting the instruments.
    """
    sim_instrument = instruments.get('SIMULATED')
    real_instrument = instruments.get('REAL')

    if mode == 'SIMULATED':
        logger.info("Switching to SIMULATED mode.")
        if real_instrument and real_instrument.is_connected:
            real_instrument.disconnect()
        if sim_instrument and not sim_instrument.is_connected:
            sim_instrument.connect()
        return {'display': 'block'}, {'display': 'none'}
    
    elif mode == 'REAL':
        logger.info("Switching to REAL mode.")
        if sim_instrument and sim_instrument.is_connected:
            sim_instrument.disconnect()
        if real_instrument and not real_instrument.is_connected:
            real_instrument.connect()
        return {'display': 'none'}, {'display': 'block'}
    
    # Default case, hide both if something is wrong
    return {'display': 'none'}, {'display': 'none'}

# --- Main Entry Point ---
if __name__ == '__main__':
    app.run(debug=True, port=8050)
