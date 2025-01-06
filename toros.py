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
import requests
import logging

ENV = os.getenv("ENV", "local")
BUCKET_NAME = os.getenv("BUCKET_NAME", "my-csv-storage")
DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
print("Selected bucket name:", BUCKET_NAME)
print("Data dir:", DATA_DIR)
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

@server.route('/api/tradingview_total', methods=['POST'])
def api_tradingview_total():
    """
    """
    try:
        if request.is_json:
            data = request.get_json()
            time_str = data.get("time")
            open_str = str(data.get("open"))
            high_str = str(data.get("high"))
            low_str  = str(data.get("low"))
            close_str= str(data.get("close"))
        else:
            time_str = request.form.get("time")
            open_str = request.form.get("open")
            high_str = request.form.get("high")
            low_str  = request.form.get("low")
            close_str= request.form.get("close")

        if not all([time_str, open_str, high_str, low_str, close_str]):
            return jsonify({"error": "Missing required fields (time, open, high, low, close)."}), 400

        open_val  = float(open_str)
        high_val  = float(high_str)
        low_val   = float(low_str)
        close_val = float(close_str)

        data_manager.append_to_csv("TOTAL.csv", [time_str, open_val, high_val, low_val, close_val])

        return jsonify({
            "status": "success",
            "message": f"Appended row to TOTAL.csv => {time_str},{open_val},{high_val},{low_val},{close_val}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/get_total_csv', methods=['GET'])
def get_total_csv():
    try:
        data = data_manager.read_csv("TOTAL.csv")
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run_server(debug=False)

server = app.server