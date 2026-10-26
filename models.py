from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    icon = db.Column(db.String(64), default='fa-tag')
    color = db.Column(db.String(24), default='#6366f1')
    
    expenses = db.relationship('Expense', backref='category', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='category', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name, icon='fa-tag', color='#6366f1'):
        self.name = name
        self.icon = icon
        self.color = color

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'color': self.color
        }


class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d'))
    payment_method = db.Column(db.String(32), default='Credit Card')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    def __init__(self, title, amount, category_id, date=None, payment_method='Credit Card', notes=None):
        self.title = title
        self.amount = amount
        self.category_id = category_id
        self.date = date if date else datetime.now().strftime('%Y-%m-%d')
        self.payment_method = payment_method
        self.notes = notes

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'amount': round(self.amount, 2),
            'date': self.date,
            'payment_method': self.payment_method,
            'notes': self.notes or '',
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Unknown',
            'category_icon': self.category.icon if self.category else 'fa-tag',
            'category_color': self.category.color if self.category else '#64748b'
        }


class Income(db.Model):
    __tablename__ = 'incomes'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d'))
    payment_method = db.Column(db.String(32), default='Bank Transfer')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, source, amount, date=None, payment_method='Bank Transfer', notes=None):
        self.source = source
        self.amount = amount
        self.date = date if date else datetime.now().strftime('%Y-%m-%d')
        self.payment_method = payment_method
        self.notes = notes

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'amount': round(self.amount, 2),
            'date': self.date,
            'payment_method': self.payment_method,
            'notes': self.notes or ''
        }


class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False, default=lambda: datetime.now().strftime('%Y-%m'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    def __init__(self, category_id, amount, month=None):
        self.category_id = category_id
        self.amount = amount
        self.month = month if month else datetime.now().strftime('%Y-%m')

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Unknown',
            'category_icon': self.category.icon if self.category else 'fa-tag',
            'category_color': self.category.color if self.category else '#64748b',
            'amount': round(self.amount, 2),
            'month': self.month
        }


class RecurringExpense(db.Model):
    __tablename__ = 'recurring_expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(24), default='Monthly')  # Monthly, Weekly, Yearly
    billing_day = db.Column(db.Integer, default=1)  # Day of month (1-31)
    is_active = db.Column(db.Boolean, default=True)
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category = db.relationship('Category', lazy=True)

    def __init__(self, title, amount, category_id, frequency='Monthly', billing_day=1, is_active=True):
        self.title = title
        self.amount = amount
        self.category_id = category_id
        self.frequency = frequency
        self.billing_day = billing_day
        self.is_active = is_active

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'amount': round(self.amount, 2),
            'frequency': self.frequency,
            'billing_day': self.billing_day,
            'is_active': self.is_active,
            'category_name': self.category.name if self.category else 'Unknown',
            'category_icon': self.category.icon if self.category else 'fa-tag'
        }
