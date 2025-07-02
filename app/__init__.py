from flask import Flask
from app.extensions import mongo
from app.webhook.routes import webhook
import os
template_dir = os.path.abspath('templates')
static_dir = os.path.abspath('static')

# Creating our flask app
def create_app():
    app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)

    # Configure MongoDB connection
    app.config["MONGO_URI"] = "mongodb://localhost:27017/github_events"

    # Initialize PyMongo with this app
    mongo.init_app(app)

    # Register blueprints (routes)
    app.register_blueprint(webhook)

    print("Flask template folder:", app.template_folder)
    print("Absolute path:", os.path.abspath(app.template_folder))

    return app