#!/bin/bash

# Production startup script for Recipe App

echo "Starting Recipe App in production mode..."

# Load environment variables if .env file exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set production environment
export FLASK_ENV=production

# Create necessary directories
mkdir -p instance
mkdir -p chrome_profile

# Initialize database if it doesn't exist
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wsgi:app 