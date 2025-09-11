# File:      app.py
# Time:      2025-09-11
# Author:    Fuuraiko, Gemini
# Desc:      The main application for the Lab Instrument Control Panel.
#            It uses Dash to create a web UI for controlling lab instruments.

import os
import json
import logging
import importlib
import pandas as pd

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from flask import jsonify

# --- Logging Setup ---
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(os.path.join(log_dir, "app.log")), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Application Setup ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# This dictionary will hold all loaded instrument objects, keyed by their ID.
instruments = {}

def load_instruments():
    """
    Loads all instruments defined in instruments.csv and config.csv.
    """
    try:
        instruments_df = pd.read_csv("instruments.csv", quotechar="'")
        configs_df = pd.read_csv("config.csv", quotechar="'")
        merged_df = pd.merge(instruments_df, configs_df, on='instrument_id', how='left')

        for _, row in merged_df.iterrows():
            instrument_id = row['instrument_id']
            instrument_type = row['type']
            
            try:
                config_str = row['config'] if isinstance(row['config'], str) else '{}'
                specific_config = json.loads(config_str)
            except (json.JSONDecodeError, KeyError):
                specific_config = {}

            # Combine all config into one dictionary
            config = {
                "visa_address": row.get('visa_address'),
                **specific_config
            }

            logger.info(f"Loading instrument '{instrument_id}' of type '{instrument_type}'")
            module_path = f"src.instruments.{instrument_type}.interface"
            InstrumentClass = getattr(importlib.import_module(module_path), 'InstrumentInterface')
            
            instance = InstrumentClass(instrument_id, config)
            instance.register_callbacks(app)
            instruments[instrument_id] = instance
            
    except (FileNotFoundError, pd.errors.ParserError) as e:
        logger.error(f"Could not read or parse configuration files: {e}")
    except Exception as e:
        logger.error(f"Error loading instruments: {e}", exc_info=True)

# --- API Endpoint ---
@server.route('/api/v1/instrument/<instrument_id>/state')
def get_instrument_state_api(instrument_id):
    """Flask route to get the state of a specific instrument."""
    instrument = instruments.get(instrument_id)
    if instrument and instrument.is_connected:
        return jsonify(instrument.get_state())
    return jsonify({"error": "Instrument not found or not connected"}), 404

# --- Dash Layout and Callbacks ---
def create_app_layout():
    """
    Creates the main application layout with tabs for each instrument.
    """
    load_instruments()
    
    if not instruments:
        return dbc.Alert("No instruments loaded. Check configuration and logs.", color="danger")

    # Automatically connect to all loaded instruments
    for instrument in instruments.values():
        instrument.connect()

    return dbc.Container(
        [
            dcc.Interval(id='main-update-interval', interval=1000, n_intervals=0),
            dbc.NavbarSimple(brand="Lab Instrument Control Panel", color="primary", dark=True, className="mb-4"),
            dcc.Tabs(
                id="instrument-tabs",
                children=[
                    dcc.Tab(label=instr_id, value=instr_id, children=instr.get_layout()) 
                    for instr_id, instr in instruments.items()
                ],
                value=next(iter(instruments)) # Select the first instrument by default
            )
        ],
        fluid=True
    )

app.layout = create_app_layout

# --- Main Entry Point ---
if __name__ == '__main__':
    app.run(debug=True, port=8050)