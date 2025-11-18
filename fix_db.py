from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():
    print('Dropping alembic_version...')
    db.session.execute(text('DROP TABLE IF EXISTS alembic_version;'))
    db.session.commit()
    print('Done.')
