"""
Monthly Budget Planner - Flask + SQLite (with optional MongoDB support)
A complete web application for managing personal finances with user authentication.
Uses SQLite by default for easy setup without MongoDB.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import csv
import io
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'budget-planner-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget_planner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    incomes = db.relationship('Income', backref='user', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    budget = db.relationship('Budget', backref='user', lazy=True, uselist=False, cascade='all, delete-orphan')


class Income(db.Model):
    __tablename__ = 'incomes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Budget(db.Model):
    __tablename__ = 'budgets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    monthly_budget = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# User model for Flask-Login
class UserModel(UserMixin):
    def __init__(self, id, username, email):
        self.id = str(id)
        self.username = username
        self.email = email

    def get_id(self):
        return str(self.id)


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return UserModel(user.id, user.username, user.email)
    return None


# Helper function to get user's documents
def get_user_incomes():
    """Get all income records for the current user."""
    return Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()


def get_user_expenses():
    """Get all expense records for the current user."""
    return Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()


def get_user_budget():
    """Get the budget for the current user."""
    return Budget.query.filter_by(user_id=current_user.id).first()


def get_user_totals():
    """Calculate total income and expenses for the current user."""
    from sqlalchemy import func
    
    total_income = db.session.query(func.sum(Income.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    
    return total_income, total_expenses


# Routes

@app.route('/')
@login_required
def dashboard():
    """Dashboard page showing financial summary and charts."""
    total_income, total_expenses = get_user_totals()
    remaining_balance = total_income - total_expenses
    
    budget = get_user_budget()
    monthly_budget = budget.monthly_budget if budget else 0
    budget_remaining = monthly_budget - total_expenses if monthly_budget > 0 else 0
    budget_percentage = (total_expenses / monthly_budget * 100) if monthly_budget > 0 else 0
    
    # Get recent transactions
    recent_incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).limit(5).all()
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    
    # Get expense breakdown by category for the current month
    current_month_start = datetime.now().replace(day=1).date()
    expense_by_category = db.session.query(
        Expense.category, 
        db.func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start
    ).group_by(Expense.category).order_by(db.desc('total')).all()
    
    return render_template('index.html',
                          total_income=total_income,
                          total_expenses=total_expenses,
                          remaining_balance=remaining_balance,
                          monthly_budget=monthly_budget,
                          budget_remaining=budget_remaining,
                          budget_percentage=min(budget_percentage, 100),
                          recent_incomes=recent_incomes,
                          recent_expenses=recent_expenses,
                          expense_by_category=expense_by_category)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return render_template('register.html')
        
        if '@' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            user_obj = UserModel(user.id, user.username, user.email)
            login_user(user_obj, remember=remember)
            flash('Welcome back, {}!'.format(user.username), 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    """Add a new income record."""
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        source = request.form.get('source', '').strip()
        date_str = request.form.get('date')
        
        if amount <= 0:
            flash('Amount must be greater than 0.', 'danger')
            return render_template('add_income.html')
        
        if not source:
            flash('Source is required.', 'danger')
            return render_template('add_income.html')
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
        
        income = Income(user_id=current_user.id, amount=amount, source=source, date=date)
        db.session.add(income)
        db.session.commit()
        flash('Income added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_income.html')


@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add a new expense record."""
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        category = request.form.get('category', '').strip()
        date_str = request.form.get('date')
        
        if amount <= 0:
            flash('Amount must be greater than 0.', 'danger')
            return render_template('add_expense.html')
        
        if not category:
            flash('Category is required.', 'danger')
            return render_template('add_expense.html')
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
        
        expense = Expense(user_id=current_user.id, amount=amount, category=category, date=date)
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_expense.html')


@app.route('/transactions')
@login_required
def transactions():
    """View all transactions."""
    incomes = get_user_incomes()
    expenses = get_user_expenses()
    total_income, total_expenses = get_user_totals()
    
    return render_template('transactions.html',
                          incomes=incomes,
                          expenses=expenses,
                          total_income=total_income,
                          total_expenses=total_expenses)


@app.route('/edit_income/<int:income_id>', methods=['GET', 'POST'])
@login_required
def edit_income(income_id):
    """Edit an income record."""
    income = Income.query.get_or_404(income_id)
    
    if income.user_id != current_user.id:
        flash('You do not have permission to edit this record.', 'danger')
        return redirect(url_for('transactions'))
    
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        source = request.form.get('source', '').strip()
        date_str = request.form.get('date')
        
        if amount <= 0:
            flash('Amount must be greater than 0.', 'danger')
            return render_template('edit_income.html', income=income)
        
        if not source:
            flash('Source is required.', 'danger')
            return render_template('edit_income.html', income=income)
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else income.date
        
        income.amount = amount
        income.source = source
        income.date = date
        db.session.commit()
        flash('Income updated successfully!', 'success')
        return redirect(url_for('transactions'))
    
    return render_template('edit_income.html', income=income)


@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    """Edit an expense record."""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id != current_user.id:
        flash('You do not have permission to edit this record.', 'danger')
        return redirect(url_for('transactions'))
    
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        category = request.form.get('category', '').strip()
        date_str = request.form.get('date')
        
        if amount <= 0:
            flash('Amount must be greater than 0.', 'danger')
            return render_template('edit_expense.html', expense=expense)
        
        if not category:
            flash('Category is required.', 'danger')
            return render_template('edit_expense.html', expense=expense)
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else expense.date
        
        expense.amount = amount
        expense.category = category
        expense.date = date
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('transactions'))
    
    return render_template('edit_expense.html', expense=expense)


@app.route('/delete_income/<int:income_id>')
@login_required
def delete_income(income_id):
    """Delete an income record."""
    income = Income.query.get_or_404(income_id)
    
    if income.user_id == current_user.id:
        db.session.delete(income)
        db.session.commit()
        flash('Income deleted successfully!', 'success')
    else:
        flash('You do not have permission to delete this record.', 'danger')
    
    return redirect(url_for('transactions'))


@app.route('/delete_expense/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    """Delete an expense record."""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    else:
        flash('You do not have permission to delete this record.', 'danger')
    
    return redirect(url_for('transactions'))


@app.route('/set_budget', methods=['POST'])
@login_required
def set_budget():
    """Set or update monthly budget."""
    amount = float(request.form.get('monthly_budget', 0))
    
    if amount <= 0:
        flash('Budget must be greater than 0.', 'danger')
        return redirect(url_for('dashboard'))
    
    budget = Budget.query.filter_by(user_id=current_user.id).first()
    
    if budget:
        budget.monthly_budget = amount
    else:
        budget = Budget(user_id=current_user.id, monthly_budget=amount)
        db.session.add(budget)
    
    db.session.commit()
    flash('Monthly budget set successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/delete_budget', methods=['POST'])
@login_required
def delete_budget():
    """Delete the monthly budget."""
    budget = Budget.query.filter_by(user_id=current_user.id).first()
    if budget:
        db.session.delete(budget)
        db.session.commit()
        flash('Monthly budget removed!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/export_csv')
@login_required
def export_csv():
    """Export monthly transactions as CSV."""
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Monthly Budget Report'])
    writer.writerow(['Generated on', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['User', current_user.username])
    writer.writerow([])
    
    # Write Income header
    writer.writerow(['INCOME'])
    writer.writerow(['Date', 'Source', 'Amount'])
    
    # Write income records
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    for income in incomes:
        writer.writerow([
            income.date.strftime('%Y-%m-%d') if income.date else '',
            income.source,
            f"{income.amount:.2f}"
        ])
    
    writer.writerow([])
    
    # Write Expense header
    writer.writerow(['EXPENSES'])
    writer.writerow(['Date', 'Category', 'Amount'])
    
    # Write expense records
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    for expense in expenses:
        writer.writerow([
            expense.date.strftime('%Y-%m-%d') if expense.date else '',
            expense.category,
            f"{expense.amount:.2f}"
        ])
    
    writer.writerow([])
    
    # Write Summary
    total_income, total_expenses = get_user_totals()
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Income', f"{total_income:.2f}"])
    writer.writerow(['Total Expenses', f"{total_expenses:.2f}"])
    writer.writerow(['Net Balance', f"{total_income - total_expenses:.2f}"])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=budget_report_{datetime.now().strftime("%Y%m")}.csv'
    
    return response


# API Routes for Charts
@app.route('/api/expense_chart')
@login_required
def expense_chart_data():
    """Get expense data for charts (JSON)."""
    current_month_start = datetime.now().replace(day=1).date()
    expense_by_category = db.session.query(
        Expense.category,
        db.func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start
    ).group_by(Expense.category).order_by(db.desc('total')).all()
    
    labels = [item.category for item in expense_by_category]
    data = [item.total for item in expense_by_category]
    
    return jsonify({'labels': labels, 'data': data})


@app.route('/api/monthly_trend')
@login_required
def monthly_trend_data():
    """Get monthly income/expense trend (JSON)."""
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Get monthly income
    income_data = db.session.query(
        db.func.strftime('%Y-%m', Income.date).label('month'),
        db.func.sum(Income.amount).label('total')
    ).filter(
        Income.user_id == current_user.id,
        Income.date >= six_months_ago.date()
    ).group_by(db.func.strftime('%Y-%m', Income.date)).all()
    
    # Get monthly expenses
    expense_data = db.session.query(
        db.func.strftime('%Y-%m', Expense.date).label('month'),
        db.func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= six_months_ago.date()
    ).group_by(db.func.strftime('%Y-%m', Expense.date)).all()
    
    # Format months
    months = []
    income_totals = []
    expense_totals = []
    
    income_dict = {item.month: item.total for item in income_data}
    expense_dict = {item.month: item.total for item in expense_data}
    
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=i*30)
        month_key = date.strftime('%Y-%m')
        month_name = date.strftime('%b')
        months.append(month_name)
        
        income_totals.append(income_dict.get(month_key, 0))
        expense_totals.append(expense_dict.get(month_key, 0))
    
    return jsonify({
        'labels': months,
        'income': income_totals,
        'expenses': expense_totals
    })


# Create tables
with app.app_context():
    db.create_all()


# Vercel compatibility - expose the WSGI app
app = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
