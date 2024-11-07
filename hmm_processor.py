import os
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from hmmlearn.hmm import GMMHMM
import ta  

DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

market_conditions_colors = {
    'Strong Bullish': 'green',
    'Bullish': 'lightgreen',
    'Bearish': 'orange',
    'Strong Bearish': 'red'
}

def process_data(file_path):
    data = pd.read_csv(file_path, parse_dates=['time'], dayfirst=True)
    data.sort_values('time', inplace=True)
    data.reset_index(drop=True, inplace=True)

    data['log_return'] = np.log(data['close'] / data['close'].shift(1))
    data['RSI'] = ta.momentum.RSIIndicator(close=data['close'], window=14).rsi()
    data.dropna(inplace=True)
    data.reset_index(drop=True, inplace=True)

    cutoff_date = pd.to_datetime('01-10-2024', dayfirst=True)
    train_data = data[data['time'] <= cutoff_date].copy()
    test_data = data[data['time'] > cutoff_date].copy()

    features = ['log_return', 'RSI']
    X_train = train_data[features].values

    n_states = 4
    covariance_type = 'spherical' if 'eth3XPriceData.csv' in file_path else 'diag' if 'btc4XPriceData.csv' in file_path or 'eth2XPriceData.csv' in file_path else 'full'

    model_filename = os.path.join(DATA_DIR, f'hmm_model_{os.path.basename(file_path)}.pkl')
    scaler_filename = os.path.join(DATA_DIR, f'scaler_{os.path.basename(file_path)}.pkl')

    if os.path.exists(model_filename) and os.path.exists(scaler_filename):
        model = joblib.load(model_filename)
        scaler = joblib.load(scaler_filename)
        X_train_scaled = scaler.transform(X_train)
    else:
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        joblib.dump(scaler, scaler_filename)

        model = GMMHMM(n_components=n_states, n_mix=2, covariance_type=covariance_type,
                           n_iter=1000, random_state=42, tol=0.01)
        model.fit(X_train_scaled)
        joblib.dump(model, model_filename)

    train_data['HiddenState'] = model.predict(X_train_scaled)
    state_means = train_data.groupby('HiddenState')['log_return'].mean()
    state_ranking = state_means.sort_values(ascending=False).index.tolist()

    state_market_conditions = {
        state_ranking[0]: 'Strong Bullish',
        state_ranking[1]: 'Bullish',
        state_ranking[2]: 'Bearish',
        state_ranking[3]: 'Strong Bearish'
    }

    train_data['MarketCondition'] = train_data['HiddenState'].map(state_market_conditions)
    train_data['Color'] = train_data['MarketCondition'].map(market_conditions_colors)

    X_test = test_data[features].values
    X_test_scaled = scaler.transform(X_test)
    test_data['HiddenState'] = model.predict(X_test_scaled)
    test_data['MarketCondition'] = test_data['HiddenState'].map(state_market_conditions)
    test_data['Color'] = test_data['MarketCondition'].map(market_conditions_colors)

    combined_data = pd.concat([train_data, test_data], ignore_index=True)
    return combined_data