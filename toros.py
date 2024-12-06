import os
import dash
import csv
import dash_bootstrap_components as dbc
from flask import Flask, request, jsonify
from datetime import datetime
from layout import create_layout
from data_paths import get_addresses
from callback_handler import CallbackHandler
from data_manager import DataManager
from scheduler_manager import SchedulerManager
from fetchData import fetch_all_latest_day_close_values
from binance_fetcher import fetch_previous_close

DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CSV_FILE_PATH = os.path.join(DATA_DIR, "dominant_asset_tracker.csv")
if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Coin"])

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
    
@server.route('/api/fetch_close/<symbol>', methods=['GET'])
def api_fetch_close(symbol):
    """
    API endpoint to fetch the previous day's CLOSE value for a given symbol.
    """
    try:
        close_price = fetch_previous_close(symbol)
        return jsonify({"symbol": symbol, "close_price": close_price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@server.route('/api/webhook', methods=['POST'])
def api_webhook():
    """
    API endpoint to handle incoming TradingView alerts and log them in CSV.
    """
    try:
        data = request.json
        if not data or "DominantAsset" not in data:
            return jsonify({"error": "Invalid data format"}), 400

        dominant_asset = data["DominantAsset"]

        current_date = datetime.now().strftime('%Y-%m-%d')

        with open(CSV_FILE_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_date, dominant_asset])

        return jsonify({
            "status": "success",
            "logged_asset": dominant_asset,
            "date": current_date
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@server.route('/api/dominant_asset', methods=['GET'])
def get_dominant_asset():
    """
    API endpoint to return the content of the dominant asset tracker CSV.
    """
    try:
        with open(CSV_FILE_PATH, mode='r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run_server(debug=False)

server = app.server