import csv
import io
import os
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, Response
)
from models import db, Category, Expense, Income, Budget, RecurringExpense
from smart_categorizer import CATEGORY_DEFINITIONS, predict_category, parse_natural_expense, generate_insights

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-expense-tracker-secret-key-2026'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'expense_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def seed_database_if_empty():
    """Seed initial categories and realistic sample data if db is newly created."""
    if Category.query.first():
        return

    # 1. Seed Categories
    category_objs = {}
    for name, data in CATEGORY_DEFINITIONS.items():
        cat = Category(name=name, icon=data['icon'], color=data['color'])
        db.session.add(cat)
        category_objs[name] = cat
    db.session.commit()

    now = datetime.now()
    curr_month = now.strftime('%Y-%m')
    curr_day = now.day

    # 2. Seed Monthly Budgets
    default_budgets = {
        "Food & Dining": 600.0,
        "Housing & Rent": 1200.0,
        "Transportation": 250.0,
        "Utilities & Bills": 200.0,
        "Entertainment": 160.0,
        "Shopping": 350.0,
        "Health & Fitness": 120.0,
        "Education": 80.0
    }
    for cat_name, b_amt in default_budgets.items():
        if cat_name in category_objs:
            budget = Budget(
                category_id=category_objs[cat_name].id,
                amount=b_amt,
                month=curr_month
            )
            db.session.add(budget)

    # 3. Seed Income
    incomes = [
        Income(
            source="Tech Corp Software Salary",
            amount=4800.0,
            date=now.replace(day=1).strftime('%Y-%m-%d'),
            payment_method="Bank Transfer",
            notes="Monthly direct deposit salary"
        ),
        Income(
            source="Freelance Web Consultation",
            amount=750.0,
            date=now.replace(day=min(12, curr_day)).strftime('%Y-%m-%d'),
            payment_method="UPI",
            notes="Client project milestone"
        )
    ]
    for inc in incomes:
        db.session.add(inc)

    # 4. Seed Recurring Subscriptions
    recurring = [
        RecurringExpense(title="Netflix 4K Ultra", amount=22.99, frequency="Monthly", billing_day=5, category_id=category_objs["Entertainment"].id),
        RecurringExpense(title="Spotify Duo Plan", amount=14.99, frequency="Monthly", billing_day=10, category_id=category_objs["Entertainment"].id),
        RecurringExpense(title="Fiber Gigabit Internet", amount=70.00, frequency="Monthly", billing_day=15, category_id=category_objs["Utilities & Bills"].id),
        RecurringExpense(title="Equinox Gym Membership", amount=65.00, frequency="Monthly", billing_day=1, category_id=category_objs["Health & Fitness"].id)
    ]
    for rec in recurring:
        db.session.add(rec)

    # 5. Seed Realistic Expenses
    sample_expenses = [
        ("Whole Foods Organic Groceries", 134.50, max(1, curr_day - 1), "Food & Dining", "Credit Card", "Weekly pantry restock"),
        ("Shell Fuel Station", 48.00, max(1, curr_day - 2), "Transportation", "Credit Card", "Full tank refill"),
        ("Monthly Studio Rent", 1200.00, 1, "Housing & Rent", "Bank Transfer", "October monthly rent"),
        ("Starbucks Cold Brew & Bagel", 9.45, max(1, curr_day - 1), "Food & Dining", "UPI", "Morning breakfast"),
        ("Amazon Ergonomic Mouse Pad", 28.50, max(1, curr_day - 3), "Shopping", "Debit Card", "Desk accessories"),
        ("City Electric & Water Utility", 115.80, max(1, curr_day - 5), "Utilities & Bills", "Net Banking", "Utility statement"),
        ("Uber Ride to Airport", 32.40, max(1, curr_day - 4), "Transportation", "UPI", "Late night commute"),
        ("CVS Health Pharmacy Medicine", 24.20, max(1, curr_day - 6), "Health & Fitness", "Cash", "Vitamins & band-aids"),
        ("Olive Garden Italian Dinner", 68.75, max(1, curr_day - 2), "Food & Dining", "Credit Card", "Dinner with partner"),
        ("Udemy Python Mastery Course", 16.99, max(1, curr_day - 7), "Education", "Debit Card", "Flash sale discount"),
        ("Zara Autumn Jacket", 89.00, max(1, curr_day - 8), "Shopping", "Credit Card", "Seasonal wardrobe"),
        ("Movie Tickets & Popcorn", 34.00, max(1, curr_day - 3), "Entertainment", "Digital Wallet", "Weekend cinema outing")
    ]

    for title, amt, day, cat_name, method, notes in sample_expenses:
        if cat_name in category_objs:
            exp_date = now.replace(day=min(day, 28)).strftime('%Y-%m-%d')
            exp = Expense(
                title=title,
                amount=amt,
                date=exp_date,
                payment_method=method,
                notes=notes,
                category_id=category_objs[cat_name].id
            )
            db.session.add(exp)

    db.session.commit()


# Helper to get current month expenses and totals
def get_month_summary(target_month=None):
    if not target_month:
        target_month = datetime.now().strftime('%Y-%m')

    expenses = Expense.query.filter(Expense.date.startswith(target_month)).all()
    incomes = Income.query.filter(Income.date.startswith(target_month)).all()
    budgets = Budget.query.filter(Budget.month == target_month).all()

    total_spent = sum(e.amount for e in expenses)
    total_income = sum(i.amount for i in incomes)
    net_savings = total_income - total_spent
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

    total_budget = sum(b.amount for b in budgets)
    budget_usage_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    return {
        'target_month': target_month,
        'total_spent': total_spent,
        'total_income': total_income,
        'net_savings': net_savings,
        'savings_rate': round(savings_rate, 1),
        'total_budget': total_budget,
        'budget_usage_pct': round(budget_usage_pct, 1),
        'expenses_count': len(expenses)
    }


# ==========================================
# WEB ROUTES
# ==========================================

@app.route('/')
def dashboard():
    curr_month = datetime.now().strftime('%Y-%m')
    summary = get_month_summary(curr_month)

    # Recent transactions
    recent_expenses = Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).limit(7).all()
    categories = Category.query.order_by(Category.name).all()
    budgets = Budget.query.filter_by(month=curr_month).all()
    incomes = Income.query.filter(Income.date.startswith(curr_month)).all()
    expenses = Expense.query.filter(Expense.date.startswith(curr_month)).all()

    # Budget progress calculation
    cat_spent = {}
    for exp in expenses:
        cat_spent[exp.category_id] = cat_spent.get(exp.category_id, 0.0) + exp.amount

    budget_status = []
    for b in budgets:
        spent = cat_spent.get(b.category_id, 0.0)
        pct = min(round((spent / b.amount * 100) if b.amount > 0 else 0, 1), 100)
        status = 'danger' if spent > b.amount else ('warning' if spent >= 0.8 * b.amount else 'success')
        budget_status.append({
            'category': b.category,
            'budget': b.amount,
            'spent': spent,
            'remaining': max(0.0, b.amount - spent),
            'percentage': pct,
            'status': status
        })

    # AI & Rule Insights
    insights = generate_insights(expenses, budgets, incomes, curr_month)

    # Active recurring count
    recurring_items = RecurringExpense.query.filter_by(is_active=True).all()
    total_recurring = sum(r.amount for r in recurring_items)

    return render_template(
        'dashboard.html',
        summary=summary,
        recent_expenses=recent_expenses,
        categories=categories,
        budget_status=budget_status,
        insights=insights,
        curr_month=curr_month,
        recurring_items=recurring_items,
        total_recurring=total_recurring
    )


@app.route('/expenses')
def expenses_list():
    categories = Category.query.order_by(Category.name).all()
    
    # Filter parameters
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '')
    payment_method = request.args.get('payment_method', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort_by = request.args.get('sort_by', 'date_desc')

    query = Expense.query

    if search:
        query = query.filter((Expense.title.ilike(f'%{search}%')) | (Expense.notes.ilike(f'%{search}%')))
    if category_id and category_id.isdigit():
        query = query.filter(Expense.category_id == int(category_id))
    if payment_method:
        query = query.filter(Expense.payment_method == payment_method)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    if sort_by == 'amount_desc':
        query = query.order_by(Expense.amount.desc())
    elif sort_by == 'amount_asc':
        query = query.order_by(Expense.amount.asc())
    elif sort_by == 'date_asc':
        query = query.order_by(Expense.date.asc(), Expense.id.asc())
    else:
        query = query.order_by(Expense.date.desc(), Expense.id.desc())

    expenses = query.all()
    total_filtered_amount = sum(e.amount for e in expenses)

    return render_template(
        'expenses.html',
        expenses=expenses,
        categories=categories,
        total_filtered_amount=total_filtered_amount,
        search=search,
        selected_category=int(category_id) if category_id and category_id.isdigit() else '',
        selected_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by
    )


@app.route('/expenses/add', methods=['POST'])
def add_expense():
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', type=float)
    category_id = request.form.get('category_id', type=int)
    date_val = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    payment_method = request.form.get('payment_method', 'Credit Card')
    notes = request.form.get('notes', '').strip()

    if not title or not amount:
        flash('Please provide both a description and a valid amount.', 'danger')
        return redirect(request.referrer or url_for('dashboard'))

    # If category not provided or "auto", predict it
    if not category_id:
        predicted_name = predict_category(title)
        cat_match = Category.query.filter_by(name=predicted_name).first()
        if not cat_match:
            cat_match = Category.query.filter_by(name='Miscellaneous').first()
        category_id = cat_match.id if cat_match else 1

    expense = Expense(
        title=title,
        amount=amount,
        date=date_val,
        payment_method=payment_method,
        notes=notes,
        category_id=category_id
    )
    db.session.add(expense)
    db.session.commit()

    flash(f'Expense "${amount:.2f}" for "{title}" added successfully!', 'success')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/expenses/<int:id>/edit', methods=['POST'])
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    expense.title = request.form.get('title', expense.title).strip()
    expense.amount = float(request.form.get('amount', expense.amount))
    expense.category_id = int(request.form.get('category_id', expense.category_id))
    expense.date = request.form.get('date', expense.date)
    expense.payment_method = request.form.get('payment_method', expense.payment_method)
    expense.notes = request.form.get('notes', expense.notes).strip()

    db.session.commit()
    flash(f'Updated expense "{expense.title}".', 'success')
    return redirect(request.referrer or url_for('expenses_list'))


@app.route('/expenses/<int:id>/delete', methods=['POST'])
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    title = expense.title
    db.session.delete(expense)
    db.session.commit()
    flash(f'Deleted expense "{title}".', 'info')
    return redirect(request.referrer or url_for('expenses_list'))


@app.route('/budgets', methods=['GET', 'POST'])
def budgets_view():
    target_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        amount = request.form.get('amount', type=float)
        month = request.form.get('month', target_month)

        if category_id and amount is not None:
            existing = Budget.query.filter_by(category_id=category_id, month=month).first()
            if existing:
                existing.amount = amount
                flash(f'Budget updated to ${amount:,.2f} for {existing.category.name}.', 'success')
            else:
                new_budget = Budget(category_id=category_id, amount=amount, month=month)
                db.session.add(new_budget)
                flash('New category budget limit created!', 'success')
            db.session.commit()
        return redirect(url_for('budgets_view', month=month))

    budgets = Budget.query.filter_by(month=target_month).all()
    expenses = Expense.query.filter(Expense.date.startswith(target_month)).all()

    cat_spent = {}
    for exp in expenses:
        cat_spent[exp.category_id] = cat_spent.get(exp.category_id, 0.0) + exp.amount

    budget_items = []
    total_budget = 0
    total_spent = 0

    for b in budgets:
        spent = cat_spent.get(b.category_id, 0.0)
        total_budget += b.amount
        total_spent += spent
        pct = (spent / b.amount * 100) if b.amount > 0 else 0
        status = 'danger' if spent > b.amount else ('warning' if pct >= 80 else 'success')
        budget_items.append({
            'budget': b,
            'category': b.category,
            'limit': b.amount,
            'spent': spent,
            'remaining': b.amount - spent,
            'pct': min(round(pct, 1), 100),
            'actual_pct': round(pct, 1),
            'status': status
        })

    # Find categories without budgets
    budgeted_cat_ids = {b.category_id for b in budgets}
    unbudgeted_categories = [c for c in categories if c.id not in budgeted_cat_ids]

    return render_template(
        'budgets.html',
        target_month=target_month,
        budget_items=budget_items,
        categories=categories,
        unbudgeted_categories=unbudgeted_categories,
        total_budget=total_budget,
        total_spent=total_spent,
        net_budget_remaining=total_budget - total_spent
    )


@app.route('/budgets/<int:id>/delete', methods=['POST'])
def delete_budget(id):
    budget = Budget.query.get_or_404(id)
    month = budget.month
    db.session.delete(budget)
    db.session.commit()
    flash('Budget target removed.', 'info')
    return redirect(url_for('budgets_view', month=month))


@app.route('/incomes', methods=['GET', 'POST'])
def incomes_view():
    curr_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        amount = request.form.get('amount', type=float)
        date_val = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
        payment_method = request.form.get('payment_method', 'Bank Transfer')
        notes = request.form.get('notes', '').strip()

        if source and amount:
            inc = Income(
                source=source,
                amount=amount,
                date=date_val,
                payment_method=payment_method,
                notes=notes
            )
            db.session.add(inc)
            db.session.commit()
            flash(f'Income of ${amount:,.2f} from "{source}" logged!', 'success')
            return redirect(url_for('incomes_view', month=date_val[:7]))

    incomes = Income.query.filter(Income.date.startswith(curr_month)).order_by(Income.date.desc()).all()
    total_income = sum(i.amount for i in incomes)
    all_incomes = Income.query.order_by(Income.date.desc()).all()

    return render_template(
        'incomes.html',
        incomes=incomes,
        all_incomes=all_incomes,
        curr_month=curr_month,
        total_income=total_income
    )


@app.route('/incomes/<int:id>/delete', methods=['POST'])
def delete_income(id):
    income = Income.query.get_or_404(id)
    db.session.delete(income)
    db.session.commit()
    flash('Income entry deleted.', 'info')
    return redirect(request.referrer or url_for('incomes_view'))


@app.route('/analytics')
def analytics():
    curr_month = datetime.now().strftime('%Y-%m')
    categories = Category.query.all()
    expenses = Expense.query.order_by(Expense.date.asc()).all()
    recurring_items = RecurringExpense.query.all()

    return render_template(
        'analytics.html',
        curr_month=curr_month,
        categories=categories,
        recurring_items=recurring_items
    )


# ==========================================
# RECURRING SUBSCRIPTIONS ROUTES
# ==========================================

@app.route('/recurring/add', methods=['POST'])
def add_recurring():
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', type=float)
    frequency = request.form.get('frequency', 'Monthly')
    billing_day = request.form.get('billing_day', type=int) or 1
    category_id = request.form.get('category_id', type=int)

    if title and amount and category_id:
        rec = RecurringExpense(
            title=title,
            amount=amount,
            frequency=frequency,
            billing_day=billing_day,
            category_id=category_id,
            is_active=True
        )
        db.session.add(rec)
        db.session.commit()
        flash(f'Recurring subscription "{title}" added!', 'success')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/recurring/<int:id>/toggle', methods=['POST'])
def toggle_recurring(id):
    rec = RecurringExpense.query.get_or_404(id)
    rec.is_active = not rec.is_active
    db.session.commit()
    state = "activated" if rec.is_active else "paused"
    flash(f'Subscription "{rec.title}" {state}.', 'info')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/recurring/<int:id>/delete', methods=['POST'])
def delete_recurring(id):
    rec = RecurringExpense.query.get_or_404(id)
    db.session.delete(rec)
    db.session.commit()
    flash(f'Subscription "{rec.title}" removed.', 'info')
    return redirect(request.referrer or url_for('dashboard'))


# ==========================================
# REST API & SMART AI ENDPOINTS
# ==========================================

@app.route('/api/smart-parse', methods=['POST'])
def api_smart_parse():
    """Parse human natural language query into expense fields."""
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'No input text provided'}), 400

    parsed = parse_natural_expense(query)

    # Resolve category_id
    cat = Category.query.filter_by(name=parsed['category']).first()
    if not cat:
        cat = Category.query.filter_by(name='Miscellaneous').first()

    parsed['category_id'] = cat.id if cat else 1
    parsed['category_name'] = cat.name if cat else 'Miscellaneous'
    parsed['category_icon'] = cat.icon if cat else 'fa-tag'
    parsed['category_color'] = cat.color if cat else '#64748b'

    return jsonify(parsed)


@app.route('/api/predict-category', methods=['POST'])
def api_predict_category():
    data = request.get_json() or {}
    text = data.get('text', '')
    cat_name = predict_category(text)
    cat = Category.query.filter_by(name=cat_name).first()
    return jsonify({
        'category_name': cat_name,
        'category_id': cat.id if cat else 1
    })


@app.route('/api/stats/monthly-chart', methods=['GET'])
def api_monthly_chart():
    """Provides spending vs income for the past 6 months."""
    months = []
    now = datetime.now()
    for i in range(5, -1, -1):
        dt = (now.replace(day=1) - timedelta(days=i * 30))
        months.append(dt.strftime('%Y-%m'))

    expense_data = []
    income_data = []

    for m in months:
        exp_sum = db.session.query(db.func.sum(Expense.amount)).filter(Expense.date.startswith(m)).scalar() or 0.0
        inc_sum = db.session.query(db.func.sum(Income.amount)).filter(Income.date.startswith(m)).scalar() or 0.0
        expense_data.append(round(exp_sum, 2))
        income_data.append(round(inc_sum, 2))

    # Format labels e.g. "May 2026"
    month_labels = [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in months]

    return jsonify({
        'labels': month_labels,
        'expenses': expense_data,
        'incomes': income_data
    })


@app.route('/api/stats/category-breakdown', methods=['GET'])
def api_category_breakdown():
    target_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    expenses = Expense.query.filter(Expense.date.startswith(target_month)).all()

    cats = Category.query.all()
    cat_lookup = {c.id: {'name': c.name, 'color': c.color} for c in cats}

    tally = {}
    for exp in expenses:
        c_info = cat_lookup.get(exp.category_id, {'name': 'Other', 'color': '#94a3b8'})
        c_name = c_info['name']
        tally[c_name] = tally.get(c_name, {'amount': 0.0, 'color': c_info['color']})
        tally[c_name]['amount'] += exp.amount

    labels = []
    data = []
    colors = []

    for name, info in tally.items():
        if info['amount'] > 0:
            labels.append(name)
            data.append(round(info['amount'], 2))
            colors.append(info['color'])

    return jsonify({
        'labels': labels,
        'data': data,
        'colors': colors
    })


@app.route('/api/stats/daily-trend', methods=['GET'])
def api_daily_trend():
    """Daily spending trend for current month."""
    target_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    expenses = Expense.query.filter(Expense.date.startswith(target_month)).order_by(Expense.date.asc()).all()

    daily_map = {}
    for exp in expenses:
        day_str = exp.date  # 'YYYY-MM-DD'
        daily_map[day_str] = daily_map.get(day_str, 0.0) + exp.amount

    labels = sorted(list(daily_map.keys()))
    data = [round(daily_map[d], 2) for d in labels]

    formatted_labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%d %b') for d in labels]

    return jsonify({
        'labels': formatted_labels,
        'data': data
    })


@app.route('/api/stats/payment-methods', methods=['GET'])
def api_payment_methods():
    target_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    expenses = Expense.query.filter(Expense.date.startswith(target_month)).all()

    methods = {}
    for exp in expenses:
        m = exp.payment_method or 'Other'
        methods[m] = methods.get(m, 0.0) + exp.amount

    return jsonify({
        'labels': list(methods.keys()),
        'data': [round(v, 2) for v in methods.values()]
    })


# ==========================================
# CSV EXPORT & IMPORT
# ==========================================

@app.route('/export/csv')
def export_csv():
    category_id = request.args.get('category_id')
    month = request.args.get('month')

    query = Expense.query
    if category_id and category_id.isdigit():
        query = query.filter_by(category_id=int(category_id))
    if month:
        query = query.filter(Expense.date.startswith(month))

    expenses = query.order_by(Expense.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Description', 'Category', 'Amount', 'Payment Method', 'Notes'])

    for e in expenses:
        cat_name = e.category.name if e.category else 'Unknown'
        writer.writerow([e.id, e.date, e.title, cat_name, e.amount, e.payment_method, e.notes or ''])

    output.seek(0)
    filename = f"smart_expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


@app.route('/import/csv', methods=['POST'])
def import_csv():
    if 'csv_file' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('expenses_list'))

    file = request.files['csv_file']
    if not file.filename.endswith('.csv'):
        flash('Only CSV format is supported.', 'danger')
        return redirect(url_for('expenses_list'))

    stream = io.StringIO(file.stream.read().decode("utf-8-sig", errors="replace"))
    reader = csv.reader(stream)

    header = next(reader, None)
    imported_count = 0

    cats = {c.name.lower(): c.id for c in Category.query.all()}
    misc_id = cats.get('miscellaneous', 1)

    for row in reader:
        if not row or len(row) < 3:
            continue
        try:
            # Expected flexible columns: Date, Title, Category(optional), Amount, Method(optional), Notes(optional)
            date_val = row[1].strip() if len(row) > 1 and row[1].strip() else datetime.now().strftime('%Y-%m-%d')
            title = row[2].strip() if len(row) > 2 else row[0].strip()
            
            # Find amount
            amount = 0.0
            cat_name = ""
            for item in row:
                try:
                    val = float(item.replace('$', '').replace(',', '').strip())
                    if val > 0:
                        amount = val
                        break
                except ValueError:
                    continue

            if not title or amount <= 0:
                continue

            # Predict or find category
            cat_predicted = predict_category(title)
            cat_id = cats.get(cat_predicted.lower(), misc_id)

            exp = Expense(
                title=title,
                amount=amount,
                date=date_val[:10],
                payment_method="Credit Card",
                notes="Imported via CSV",
                category_id=cat_id
            )
            db.session.add(exp)
            imported_count += 1
        except Exception:
            continue

    db.session.commit()
    flash(f'Successfully imported {imported_count} expenses with automatic categorization!', 'success')
    return redirect(url_for('expenses_list'))


# Initialize database and seed sample data
with app.app_context():
    db.create_all()
    seed_database_if_empty()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
