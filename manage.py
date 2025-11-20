from app import create_app
from extensions import db, migrate

app = create_app()
migrate.init_app(app, db)

if __name__ == "__main__":
    app.run(debug=True)