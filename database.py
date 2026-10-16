from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    company  = db.Column(db.String(120), default='My Company')
    entries  = db.relationship('Entry', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Entry(db.Model):
    __tablename__ = 'entries'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month       = db.Column(db.String(20), nullable=False)
    year        = db.Column(db.String(10), nullable=False)
    income      = db.Column(db.Float, default=0)
    expense     = db.Column(db.Float, default=0)
    profit_loss = db.Column(db.Float, default=0)
    note        = db.Column(db.String(200), default='')

    def to_dict(self):
        return {
            'id':          self.id,
            'month':       self.month,
            'year':        self.year,
            'income':      self.income,
            'expense':     self.expense,
            'profit_loss': self.profit_loss,
            'status':      'Profit' if self.profit_loss >= 0 else 'Loss',
            'note':        self.note,
        }
