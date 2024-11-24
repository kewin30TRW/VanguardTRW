import os
import dash
import dash_bootstrap_components as dbc
from flask import Flask, jsonify
from layout import create_layout
from data_paths import get_addresses
from callback_handler import CallbackHandler
from data_manager import DataManager
from scheduler_manager import SchedulerManager
from fetchData import fetch_all_latest_day_close_values

DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

addresses = get_addresses(DATA_DIR)

server = Flask(__name__)

app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.DARKLY])
app.layout = create_layout()

data_manager = DataManager(addresses)
data_manager.update_all_data()

callback_handler = CallbackHandler(app, addresses)

scheduler_manager = SchedulerManager(data_manager.update_all_data)

@server.route('/api/close_values', methods=['GET'])
def api_close_values():
    """
    API endpoint to fetch the latest day's `close` values for all token addresses.
    """
    try:
        close_values = fetch_all_latest_day_close_values()
        return jsonify(close_values)  
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run_server(debug=False)

server = app.server