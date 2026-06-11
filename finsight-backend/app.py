from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from routes.price    import price_bp
from routes.health   import health_bp
from routes.news     import news_bp
from routes.analysis import analysis_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(price_bp,    url_prefix="/api")
app.register_blueprint(health_bp,   url_prefix="/api")
app.register_blueprint(news_bp,     url_prefix="/api")
app.register_blueprint(analysis_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(debug=True, port=5000)