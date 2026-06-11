from flask import Blueprint, jsonify
import yfinance as yf
import numpy as np
from sklearn.linear_model import LinearRegression

predict_bp = Blueprint("predict", __name__)


def train_and_predict(symbol):
    # Step 1 — Get 3 months of historical closing prices
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="3mo")

    if hist.empty:
        return None, "No data found"

    closes = hist["Close"].values  # Array of closing prices
    dates = np.arange(len(closes))  # [0, 1, 2, 3, ... 90]

    # Step 2 — Train the model
    # X = day numbers (0, 1, 2...), Y = closing prices
    # The model learns: "as day number increases, price tends to go up/down by X"
    X = dates.reshape(-1, 1)  # sklearn needs 2D array
    Y = closes

    model = LinearRegression()
    model.fit(X, Y)

    # Step 3 — Predict next 7 days
    # Day numbers continue after the last known day
    last_day = len(closes)
    future_days = np.arange(last_day, last_day + 7).reshape(-1, 1)
    predictions = model.predict(future_days)

    # Step 4 — Check how accurate the model is on known data
    # R² score: 1.0 = perfect, 0.0 = useless, negative = worse than guessing
    r2_score = round(model.score(X, Y), 3)

    # Step 5 — Build the last 30 days of actual prices for the chart
    recent_dates = hist.index[-30:]
    recent_closes = closes[-30:]
    actual = [
        {"date": str(d.date()), "actual": round(float(p), 2)}
        for d, p in zip(recent_dates, recent_closes)
    ]

    # Step 6 — Build the 7 day prediction with dates
    from datetime import timedelta
    last_date = hist.index[-1]
    predicted = []
    for i, price in enumerate(predictions):
        next_date = last_date + timedelta(days=i + 1)
        # Skip weekends — markets are closed
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)
        predicted.append({
            "date": str(next_date.date()),
            "predicted": round(float(price), 2),
        })

    # Step 7 — Simple signal based on prediction direction
    current_price = float(closes[-1])
    predicted_price = float(predictions[-1])
    change_percent = round(((predicted_price - current_price) / current_price) * 100, 2)

    if change_percent > 1.5:
        signal = "buy"
    elif change_percent < -1.5:
        signal = "sell"
    else:
        signal = "hold"

    return {
        "symbol": symbol.upper(),
        "current_price": round(current_price, 2),
        "predicted_price_7d": round(predicted_price, 2),
        "change_percent_7d": change_percent,
        "signal": signal,
        "model_accuracy": r2_score,
        "actual": actual,
        "predictions": predicted,
    }, None


@predict_bp.route("/predict/<symbol>")
def get_prediction(symbol):
    """
    Returns a 7-day price prediction using Linear Regression.
    Example: GET /api/predict/AAPL
    """
    try:
        result, error = train_and_predict(symbol.upper())

        if error:
            return jsonify({"error": error}), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500