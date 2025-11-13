from app import app
from extensions import db, migrate

# Bind Flask-Migrate explicitly so CLI commands like "flask db init" work
migrate.init_app(app, db)

if __name__ == "__main__":
    app.run(debug=True)
