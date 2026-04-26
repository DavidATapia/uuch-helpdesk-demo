from app import app, reset_database


if __name__ == "__main__":
    with app.app_context():
        reset_database()
    print("Demo database reset and seeded.")
