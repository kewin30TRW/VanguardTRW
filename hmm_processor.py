import os
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from hmmlearn.hmm import GMMHMM
import ta
from ta.trend import EMAIndicator
from google.cloud import storage
import io
import logging

logging.basicConfig(level=logging.DEBUG)

ENV = os.getenv("ENV", "local")
BUCKET_NAME = os.getenv("BUCKET_NAME", "my-csv-storage")
DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
HMM_MODELS_DIR = 'hmmModels'

if ENV == "production":
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

def upload_blob(blob_name, data, content_type='application/octet-stream'):
    if ENV == "production":
        blob = bucket.blob(blob_name)
        blob.upload_from_string(data, content_type=content_type)
    else:
        local_path = os.path.join(DATA_DIR, blob_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(data)

def download_blob(blob_name):
    if ENV == "production":
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return None
        return blob.download_as_bytes()
    else:
        local_path = os.path.join(DATA_DIR, blob_name)
        if not os.path.exists(local_path):
            return None
        with open(local_path, 'rb') as f:
            return f.read()

def file_exists(blob_name):
    if ENV == "production":
        blob = bucket.blob(blob_name)
        return blob.exists()
    else:
        local_path = os.path.join(DATA_DIR, blob_name)
        return os.path.exists(local_path)

if ENV != "production":
    local_hmm_models_dir = os.path.join(DATA_DIR, HMM_MODELS_DIR)
    if not os.path.exists(local_hmm_models_dir):
        os.makedirs(local_hmm_models_dir)

market_conditions_colors = {
    'Strong Bullish': 'green',
    'Bullish': 'lightgreen',
    'Bearish': 'orange',
    'Strong Bearish': 'red'
}

def process_data(file_path, smoothing_on=True):
    data = pd.read_csv(file_path, parse_dates=['time'], dayfirst=True)
    data.sort_values('time', inplace=True)
    data.reset_index(drop=True, inplace=True)

    if 'btc2XPriceData.csv' in file_path:
        rsi_length = 14
        ema_length = 20
    elif 'btc3XPriceData.csv' in file_path:
        rsi_length = 14
        ema_length = 20
    elif 'btc4XPriceData.csv' in file_path:
        rsi_length = 14
        ema_length = 21
    elif 'eth2XPriceData.csv' in file_path:
        rsi_length = 13
        ema_length = 21
    elif 'eth3XPriceData.csv' in file_path:
        rsi_length = 14
        ema_length = 17
    elif 'sol2XPriceData.csv' in file_path:
        rsi_length = 14
        ema_length = 20
    elif 'sol3XPriceData.csv' in file_path:
        rsi_length = 10
        ema_length = 40
    else:
        rsi_length = 14
        ema_length = 20 

    data['log_return'] = np.log(data['close'] / data['close'].shift(1))
    data['RSI'] = ta.momentum.RSIIndicator(close=data['close'], window=rsi_length).rsi()

    if smoothing_on:
        data['Smoothed_RSI'] = EMAIndicator(close=data['RSI'], window=ema_length).ema_indicator()
        feature_rsi = 'Smoothed_RSI'
    else:
        feature_rsi = 'RSI'

    data.dropna(inplace=True)
    data.reset_index(drop=True, inplace=True)

    cutoff_date = pd.to_datetime('2024-10-01') 
    train_data = data[data['time'] <= cutoff_date].copy()
    test_data = data[data['time'] > cutoff_date].copy()

    features = ['log_return', feature_rsi]
    X_train = train_data[features].values

    n_states = 4
    if 'eth3XPriceData.csv' in file_path:
        covariance_type = 'spherical'
    elif 'btc4XPriceData.csv' in file_path or 'eth2XPriceData.csv' in file_path:
        covariance_type = 'diag'
    else:
        covariance_type = 'full'

    base_filename = os.path.basename(file_path)
    model_blob_name = f"{HMM_MODELS_DIR}/hmm_model_{base_filename}_{rsi_length}_{ema_length}_{smoothing_on}.pkl"
    scaler_blob_name = f"{HMM_MODELS_DIR}/scaler_{base_filename}_{rsi_length}_{ema_length}_{smoothing_on}.pkl"

    if file_exists(model_blob_name) and file_exists(scaler_blob_name):
        logging.debug(f"Ładowanie istniejącego scaler i modelu dla {base_filename}")
        scaler_bytes = download_blob(scaler_blob_name)
        model_bytes = download_blob(model_blob_name)
        scaler = joblib.load(io.BytesIO(scaler_bytes))
        model = joblib.load(io.BytesIO(model_bytes))
        X_train_scaled = scaler.transform(X_train)
    else:
        logging.debug(f"Trenowanie nowego scaler i modelu dla {base_filename}")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        scaler_buffer = io.BytesIO()
        joblib.dump(scaler, scaler_buffer)
        upload_blob(scaler_blob_name, scaler_buffer.getvalue())

        model = GMMHMM(n_components=n_states, n_mix=2, covariance_type=covariance_type,
                       n_iter=1000, random_state=42, tol=0.01)
        model.fit(X_train_scaled)

        model_buffer = io.BytesIO()
        joblib.dump(model, model_buffer)
        upload_blob(model_blob_name, model_buffer.getvalue())

    train_hidden_states = model.predict(X_train_scaled)
    train_data['HiddenState'] = train_hidden_states

    state_stats = train_data.groupby('HiddenState')['log_return'].mean()
    state_ranking = state_stats.sort_values(ascending=False).index.tolist()

    new_hiddenstate_mapping = {old_label: new_label for new_label, old_label in enumerate(state_ranking)}
    train_data['HiddenState'] = train_data['HiddenState'].map(new_hiddenstate_mapping)

    standard_state_market_conditions = {
        0: 'Strong Bullish',
        1: 'Bullish',
        2: 'Bearish',
        3: 'Strong Bearish'
    }

    if 'btc4XPriceData.csv' in file_path:
        state_market_conditions = {
            0: 'Strong Bullish',
            1: 'Strong Bearish',
            2: 'Strong Bearish',
            3: 'Strong Bearish'
        }
    elif 'btc3XPriceData.csv' in file_path:
        state_market_conditions = {  
            0: 'Strong Bullish',
            1: 'Strong Bearish',
            2: 'Strong Bearish',
            3: 'Strong Bullish'
        }
    elif 'btc2XPriceData.csv' in file_path:
        state_market_conditions = {
            0: 'Strong Bullish',
            1: 'Strong Bullish',
            2: 'Strong Bearish',
            3: 'Strong Bearish'
        }
    elif 'eth2XPriceData.csv' in file_path:
        state_market_conditions = {
            0: 'Strong Bullish',
            1: 'Strong Bearish',
            2: 'Strong Bullish',
            3: 'Strong Bearish'
        }
    elif 'eth3XPriceData.csv' in file_path:
        state_market_conditions = {
            0: 'Strong Bearish',
            1: 'Strong Bearish',
            2: 'Strong Bullish',
            3: 'Strong Bearish'
        }
    elif 'sol2XPriceData.csv' in file_path:
        state_market_conditions = {
            0: 'Strong Bearish',
            1: 'Strong Bullish',
            2: 'Strong Bearish',
            3: 'Strong Bearish'
        }
    elif 'sol3XPriceData.csv' in file_path:
        state_market_conditions = {
            0: 'Strong Bullish',
            1: 'Strong Bearish',
            2: 'Strong Bearish',
            3: 'Strong Bearish'
        }
    else:
        state_market_conditions = standard_state_market_conditions

    train_data['MarketCondition'] = train_data['HiddenState'].map(state_market_conditions)
    train_data['Color'] = train_data['MarketCondition'].map(market_conditions_colors)

    market_condition_to_state_index = {
        'Strong Bullish': 1,
        'Bullish': 2,
        'Bearish': 3,
        'Strong Bearish': 4
    }
    train_data['StateIndex'] = train_data['MarketCondition'].map(market_condition_to_state_index)

    X_test = test_data[features].values
    X_test_scaled = scaler.transform(X_test)
    test_hidden_states = model.predict(X_test_scaled)
    test_hidden_states_mapped = [new_hiddenstate_mapping[hs] for hs in test_hidden_states]
    test_data['HiddenState'] = test_hidden_states_mapped

    test_data['MarketCondition'] = test_data['HiddenState'].map(state_market_conditions)
    test_data['Color'] = test_data['MarketCondition'].map(market_conditions_colors)
    test_data['StateIndex'] = test_data['MarketCondition'].map(market_condition_to_state_index)

    combined_data = pd.concat([train_data, test_data], ignore_index=True)
    return combined_data
