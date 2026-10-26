# Smart Expense Tracker (SmartSpend Pro) 💰✨

An intelligent, AI-powered Personal Finance & Expense Tracker web application built using **Python**, **Flask**, **SQLite / SQLAlchemy**, and **Chart.js**.

---

## 🌟 Key Features

### 1. 🤖 Smart AI Natural Language Logging
- **Natural Language Parsing**: Add expenses by typing plain English sentences, for example:
  - `"Spent $64.50 at Olive Garden yesterday via Credit Card"`
  - `"Paid $120 for electricity bill today"`
  - `"Starbucks coffee 6.50 with UPI"`
- The parser automatically detects **Amount**, **Merchant / Title**, **Category**, **Date**, and **Payment Method**.
- **Realtime Category Auto-Suggestion**: As you type descriptions in the manual entry modal, it detects and selects the category instantly.

### 2. 📊 Executive Financial Command Center
- **Key Metrics (KPIs)**:
  - Total Monthly Expenses
  - Total Inflows / Incomes
  - Net Cashflow / Savings with Savings Rate %
  - Monthly Budget Ceiling & Utilization Rate
- **Automated AI Insights & Diagnostics**:
  - Cashflow balance warning or praise
  - Category budget overrun alerts (80% warning and 100% breach)
  - Spending concentration breakdown
  - Projected end-of-month spend based on current daily velocity

### 3. 🎯 Monthly Category Budgets
- Set custom spending limits per category for any month.
- Interactive visual progress bars color-coded according to consumption:
  - 🟢 **Healthy** (< 80%)
  - 🟡 **Warning** (80% - 100%)
  - 🔴 **Over Budget** (> 100%)

### 4. 📈 Interactive Analytics & Visualizations (Chart.js)
- **6-Month Cashflow Trajectory**: Side-by-side comparison of Income vs. Expenses over time.
- **Category Share**: Responsive donut and polar area breakdowns.
- **Daily Spending Velocity**: Line chart tracing day-to-day expenditure patterns.
- **Payment Method Distribution**: Credit Card, Debit Card, UPI, Cash, and Net Banking distribution.

### 5. 🔄 Recurring Subscriptions Tracker
- Monitor monthly and yearly recurring commitments (e.g. Netflix, Spotify, Gym, Fiber Internet).
- Single-click active/paused toggle and billing cycle day reminder.

### 6. 📁 Data Import & Export
- **CSV Export**: Filter and export transactions anytime.
- **CSV Import with Auto-Categorization**: Import bank statements in standard CSV format with automated categorization.

### 7. 🎨 Premium UI / UX
- Sleek glassmorphic dark and light mode toggle.
- Built using **Bootstrap 5**, **FontAwesome 6**, and Google's **Plus Jakarta Sans** typography.
- Fully responsive layout for mobile, tablet, and desktop.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- `pip`

### 2. Setup Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
*Note: The application automatically initializes `expense_tracker.db` and populates realistic demo transactions, budget targets, and recurring subscriptions on the first run.*

---

## 📂 Project Architecture

```
Pythonpr/
├── app.py                  # Main Flask app, route controllers, and REST APIs
├── models.py               # SQLAlchemy database schema (Expense, Income, Budget, Category, Recurring)
├── smart_categorizer.py    # NLP rule engine, parser, and financial insights generator
├── requirements.txt        # Application dependencies (Flask, Flask-SQLAlchemy)
├── static/
│   ├── css/
│   │   └── style.css       # Custom styles, glassmorphism, responsive sidebar & animations
│   └── js/
│       └── main.js         # Chart.js initializers, AI parsing handler, theme manager
├── templates/
│   ├── base.html           # Master layout with sidebar navigation and global quick-add modal
│   ├── dashboard.html      # Main dashboard with KPI cards, charts, and budget bars
│   ├── expenses.html       # Full expense management table with filtering, search & CSV tools
│   ├── budgets.html        # Category budget planner with progress indicators
│   ├── incomes.html        # Incomes and cashflow inflow manager
│   └── analytics.html      # Deep financial charts and recurring subscriptions
└── README.md               # Documentation
```
