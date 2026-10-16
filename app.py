from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from database import db, Entry, User
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'fintrack_secret_2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fintrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

MONTHS = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']

# ── AUTH ──────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            session['company']  = user.company
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials!')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            return render_template('register.html', error='Username already exists!')
        user = User(username=request.form['username'], company=request.form['company'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── HELPER ────────────────────────────────────────────────
def get_year():
    return request.args.get('year', str(datetime.now().year))

def get_entries(year):
    return Entry.query.filter_by(
        user_id=session['user_id'],
        year=str(year)
    ).all()

# ── PAGES ─────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    year    = get_year()
    entries = get_entries(year)
    total_income  = sum(e.income for e in entries)
    total_expense = sum(e.expense for e in entries)
    net           = total_income - total_expense
    profit_months = sum(1 for e in entries if e.profit_loss >= 0)
    loss_months   = len(entries) - profit_months
    return render_template('dashboard.html',
        year=year, total_income=total_income,
        total_expense=total_expense, net=net,
        months=len(entries), profit_months=profit_months,
        loss_months=loss_months,
        username=session['username'], company=session['company'])

@app.route('/add-entry', methods=['GET','POST'])
@login_required
def add_entry():
    error = success = None
    if request.method == 'POST':
        month   = request.form['month'].strip()
        year    = request.form['year'].strip()
        income  = float(request.form['income'])
        expense = float(request.form['expense'])
        note    = request.form.get('note','').strip()
        exists  = Entry.query.filter_by(user_id=session['user_id'], month=month, year=year).first()
        if exists:
            error = f'Entry for {month} {year} already exists!'
        else:
            entry = Entry(user_id=session['user_id'], month=month, year=year,
                          income=income, expense=expense,
                          profit_loss=round(income-expense, 2), note=note)
            db.session.add(entry)
            db.session.commit()
            pl = income - expense
            success = f'Entry added! {"Profit" if pl>=0 else "Loss"}: ₹{abs(pl):,.0f}'
    return render_template('add_entry.html',
        error=error, success=success, year=get_year(),
        username=session['username'], company=session['company'])

@app.route('/records')
@login_required
def records():
    year    = get_year()
    entries = get_entries(year)
    sorted_entries = sorted(entries, key=lambda e: MONTHS.index(e.month) if e.month in MONTHS else 0)
    return render_template('records.html',
        entries=sorted_entries, year=year,
        username=session['username'], company=session['company'])

@app.route('/delete/<int:entry_id>')
@login_required
def delete_entry(entry_id):
    year  = request.args.get('year', str(datetime.now().year))
    entry = Entry.query.filter_by(id=entry_id, user_id=session['user_id']).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('records', year=year))

@app.route('/charts')
@login_required
def charts():
    year    = get_year()
    entries = get_entries(year)
    sorted_entries = sorted(entries, key=lambda e: MONTHS.index(e.month) if e.month in MONTHS else 0)
    return render_template('charts.html',
        year=year,
        labels  =[e.month[:3] for e in sorted_entries],
        incomes =[e.income for e in sorted_entries],
        expenses=[e.expense for e in sorted_entries],
        pls     =[e.profit_loss for e in sorted_entries],
        username=session['username'], company=session['company'])

@app.route('/reports')
@login_required
def reports():
    year    = get_year()
    entries = get_entries(year)
    sorted_entries = sorted(entries, key=lambda e: MONTHS.index(e.month) if e.month in MONTHS else 0)
    total_income  = sum(e.income for e in entries)
    total_expense = sum(e.expense for e in entries)
    net           = total_income - total_expense
    best          = max(entries, key=lambda e: e.profit_loss, default=None)
    worst         = min(entries, key=lambda e: e.profit_loss, default=None)
    return render_template('reports.html',
        year=year, entries=sorted_entries,
        total_income=total_income, total_expense=total_expense,
        net=net, best=best, worst=worst,
        username=session['username'], company=session['company'])

if __name__ == '__main__':
    app.run(debug=True)
