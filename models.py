from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False)
    email = db.Column(db.String, unique=True, nullable = False)
    password = db.Column(db.String, nullable = False)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nameP = db.Column(db.String)
    qty = db.Column(db.Integer, default = 1)
    price = db.Column(db.Numeric(precision=10,scale=2), nullable = False)
    category = db.Column(db.String)
    date = db.Column(db.DateTime, default = datetime.now())

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'