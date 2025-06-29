#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
from app import app, db
import os

if os.environ.get("FLASK_ENV") == "development":
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    app.run() 