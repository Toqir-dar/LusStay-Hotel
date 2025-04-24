from flask import Flask
from models import db  
from routes import app
from flask_migrate import Migrate


migrate = Migrate(app, db)


if __name__ == '__main__':
    app.run(debug=True)
