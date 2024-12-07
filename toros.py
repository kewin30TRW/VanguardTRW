import os
import dash
import dash_bootstrap_components as dbc
from flask import Flask, request, jsonify
from datetime import datetime
from layout import create_layout
from callback_handler import CallbackHandler
from data_manager import DataManager
from scheduler_manager import SchedulerManager
from binance_fetcher import fetch_previous_close

ENV = os.getenv("ENV", "local")
BUCKET_NAME = os.getenv("BUCKET_NAME", "my-csv-storage")
DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))

server = Flask(__name__)

app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.DARKLY])

app.layout = create_layout()

data_manager = DataManager()

data_manager.initialize_csv("dominant_asset_tracker.csv", ["Date", "Coin"])
data_manager.initialize_csv("second_portfolio_tracker.csv", ["Date", "Asset"])

callback_handler = CallbackHandler(app, data_manager)

scheduler_manager = SchedulerManager(data_manager.update_all_data)

@server.route('/api/close_values', methods=['GET'])
def api_close_values():
    try:
        close_values = data_manager.get_all_latest_day_close_values()
        return jsonify(close_values)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/fetch_close/<symbol>', methods=['GET'])
def api_fetch_close(symbol):
    try:
        close_price = fetch_previous_close(symbol)
        return jsonify({"symbol": symbol, "close_price": close_price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/webhook', methods=['POST'])
def api_webhook():
    try:
        data = request.json
        if not data or "DominantAsset" not in data:
            return jsonify({"error": "Invalid data format"}), 400

        dominant_asset = data["DominantAsset"]

        if dominant_asset == "USDT":
            return jsonify({"status": "ignored", "reason": "USDT is not logged"}), 200

        current_date = datetime.now().strftime('%Y-%m-%d')
        data_manager.append_to_csv("dominant_asset_tracker.csv", [current_date, dominant_asset])

        return jsonify({
            "status": "success",
            "logged_asset": dominant_asset,
            "date": current_date
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/get_dominant_asset', methods=['GET'])
def get_dominant_asset():
    try:
        data = data_manager.read_csv("dominant_asset_tracker.csv")
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/add_second_portfolio', methods=['POST'])
def add_second_portfolio():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid data format"}), 400

        current_date = datetime.now().strftime('%Y-%m-%d')

        for _, value in data.items():
            if value == "USDT":
                continue
            data_manager.append_to_csv("second_portfolio_tracker.csv", [current_date, value])

        return jsonify({"status": "success", "logged_portfolio": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/get_second_portfolio', methods=['GET'])
def get_second_portfolio():
    try:
        data = data_manager.read_csv("second_portfolio_tracker.csv")
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run_server(debug=False)

server = app.server