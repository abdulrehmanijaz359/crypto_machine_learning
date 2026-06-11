from flask import Blueprint, jsonify
import yfinance as yf
import pandas as pd

analysis_bp = Blueprint("analysis", __name__)

def calculate_moving_averages(df):
    df["ma7"]  = df["Close"].rolling(window=7).mean().round(2)
    df["ma30"] = df["Close"].rolling(window=30).mean().round(2)
    return df

def detect_signals(df):
    signals = []
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        if pd.isna(prev["ma7"]) or pd.isna(prev["ma30"]):
            continue
        if prev["ma7"] <= prev["ma30"] and curr["ma7"] > curr["ma30"]:
            signals.append({
                "date": str(curr.name.date()),
                "type": "buy",
                "label": "Golden Cross",
                "price": round(float(curr["Close"]), 2),
            })
        elif prev["ma7"] >= prev["ma30"] and curr["ma7"] < curr["ma30"]:
            signals.append({
                "date": str(curr.name.date()),
                "type": "sell",
                "label": "Death Cross",
                "price": round(float(curr["Close"]), 2),
            })
    return signals

@analysis_bp.route("/analysis/<symbol>")
def get_analysis(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period="6mo")

        if hist.empty:
            return jsonify({"error": f"No data for '{symbol}'"}), 404

        hist = calculate_moving_averages(hist)
        signals = detect_signals(hist)

        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "date":  str(index.date()),
                "close": round(float(row["Close"]), 2),
                "ma7":   float(row["ma7"])  if not pd.isna(row["ma7"])  else None,
                "ma30":  float(row["ma30"]) if not pd.isna(row["ma30"]) else None,
                "volume": int(row["Volume"]),
            })

        latest = hist.dropna(subset=["ma7", "ma30"]).iloc[-1]
        trend = "bullish" if latest["ma7"] > latest["ma30"] else "bearish"

        daily_returns = hist["Close"].pct_change().dropna()
        volatility = round(float(daily_returns.std() * 100), 2)

        return jsonify({
            "symbol": symbol.upper(),
            "current_price": round(float(hist["Close"].iloc[-1]), 2),
            "trend": trend,
            "volatility": volatility,
            "signals": signals[-5:],
            "chart_data": chart_data,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500