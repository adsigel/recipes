from app import app, db

with app.app_context():
    print("Creating database tables for tags...")
    db.create_all()
    print("Done.") 