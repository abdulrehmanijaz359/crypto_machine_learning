from flask import Blueprint, jsonify
import requests
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

news_bp = Blueprint("news", __name__)
analyzer = SentimentIntensityAnalyzer()

def get_sentiment_label(score):
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    else:
        return "neutral"

def analyze_headline(headline):
    scores = analyzer.polarity_scores(headline)
    compound = round(scores["compound"], 3)
    return {
        "score": compound,
        "label": get_sentiment_label(compound),
    }

@news_bp.route("/news/<symbol>")
def get_news(symbol):
    api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        return jsonify(_mock_news(symbol))

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": symbol,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10,
            "apiKey": api_key,
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get("status") != "ok":
            return jsonify({"error": data.get("message")}), 500

        articles = data.get("articles", [])
        results = []

        for article in articles:
            headline = article.get("title", "")
            if not headline or headline == "[Removed]":
                continue
            sentiment = analyze_headline(headline)
            results.append({
                "headline": headline,
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt", ""),
                "url": article.get("url", ""),
                "sentiment": sentiment,
            })

        avg_score = round(sum(r["sentiment"]["score"] for r in results) / len(results), 3) if results else 0

        return jsonify({
            "symbol": symbol.upper(),
            "overall_sentiment": {
                "score": avg_score,
                "label": get_sentiment_label(avg_score),
            },
            "articles": results,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _mock_news(symbol):
    headlines = [
        (f"{symbol} reports record quarterly earnings", 0.7),
        (f"Analysts raise price target for {symbol}", 0.4),
        (f"{symbol} faces regulatory scrutiny", -0.5),
        (f"Market volatility affects {symbol} shares", -0.2),
        (f"{symbol} announces new product launch", 0.6),
    ]
    articles = []
    for headline, score in headlines:
        articles.append({
            "headline": headline,
            "source": "Mock — add NEWS_API_KEY to .env for real data",
            "published_at": "",
            "url": "#",
            "sentiment": {"score": score, "label": get_sentiment_label(score)},
        })
    return {
        "symbol": symbol.upper(),
        "overall_sentiment": {"score": 0.2, "label": "positive"},
        "articles": articles,
    }