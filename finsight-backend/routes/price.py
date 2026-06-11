from flask import Blueprint, jsonify
import yfinance as yf

price_bp = Blueprint("price", __name__)


def format_price_data(ticker_obj, symbol):
    info = ticker_obj.info
    return {
        "symbol": symbol.upper(),
        "name": info.get("longName", symbol),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "change": info.get("regularMarketChange"),
        "change_percent": round(info.get("regularMarketChangePercent", 0), 2),
        "high": info.get("dayHigh"),
        "low": info.get("dayLow"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency", "USD"),
    }


@price_bp.route("/price/<symbol>")
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        data = format_price_data(ticker, symbol)
        if data["price"] is None:
            return jsonify({"error": f"Symbol '{symbol}' not found"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@price_bp.route("/history/<symbol>")
def get_history(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period="1mo")
        if hist.empty:
            return jsonify({"error": f"No history found for '{symbol}'"}), 404
        history = [
            {
                "date": str(index.date()),
                "close": round(row["Close"], 2),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "volume": int(row["Volume"]),
            }
            for index, row in hist.iterrows()
        ]
        return jsonify({"symbol": symbol.upper(), "period": "1mo", "data": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@price_bp.route("/price/batch/<symbols>")
def get_batch_prices(symbols):
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        results = []
        for symbol in symbol_list:
            try:
                ticker = yf.Ticker(symbol)
                data = format_price_data(ticker, symbol)
                results.append(data)
            except Exception:
                results.append({"symbol": symbol, "error": "Failed to fetch"})
        return jsonify({"stocks": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500