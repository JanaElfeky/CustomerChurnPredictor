from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Load config from config.py
    app.config.from_object('app.config.config.Config')

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # continue...
    return app
