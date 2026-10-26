"""
Smart Categorization & Natural Language Parser for Smart Expense Tracker.
Includes rule-based NLP parser, category predictor, and financial insight engine.
"""

import re
from datetime import datetime, timedelta

# Default categories with icons, colors, and keywords
CATEGORY_DEFINITIONS = {
    "Food & Dining": {
        "icon": "fa-utensils",
        "color": "#f97316",  # orange
        "keywords": [
            "food", "dining", "restaurant", "cafe", "coffee", "starbucks", "mcdonalds",
            "burger", "pizza", "subway", "kfc", "dominos", "swiggy", "zomato", "uber eats",
            "doordash", "grubhub", "lunch", "dinner", "breakfast", "brunch", "snack",
            "supermarket", "grocery", "groceries", "walmart", "trader joe", "whole foods",
            "bakery", "bar", "pub", "bistro", "tea", "olive garden", "chipotle", "wendy"
        ]
    },
    "Transportation": {
        "icon": "fa-car",
        "color": "#06b6d4",  # cyan
        "keywords": [
            "uber", "lyft", "ola", "grab", "taxi", "cab", "gas", "fuel", "petrol", "diesel",
            "shell", "chevron", "bp", "exxon", "subway", "metro", "train", "flight", "airline",
            "ticket", "bus", "parking", "toll", "transit", "railway", "amtrak", "car wash", "auto"
        ]
    },
    "Shopping": {
        "icon": "fa-bag-shopping",
        "color": "#ec4899",  # pink
        "keywords": [
            "amazon", "ebay", "target", "walmart", "clothes", "clothing", "shoes", "fashion",
            "zara", "h&m", "nike", "adidas", "electronics", "apple", "best buy", "mall",
            "purchase", "store", "boutique", "watch", "gadget", "headphones"
        ]
    },
    "Entertainment": {
        "icon": "fa-film",
        "color": "#8b5cf6",  # violet
        "keywords": [
            "netflix", "spotify", "hulu", "disney", "prime video", "cinema", "movie", "theater",
            "steam", "playstation", "xbox", "nintendo", "game", "gaming", "concert", "ticketmaster",
            "youtube", "audible", "event", "amusement", "bowling", "club"
        ]
    },
    "Utilities & Bills": {
        "icon": "fa-bolt",
        "color": "#eab308",  # yellow
        "keywords": [
            "electricity", "power", "water", "gas bill", "utility", "internet", "wifi", "broadband",
            "verizon", "at&t", "t-mobile", "airtel", "jio", "phone", "mobile recharge", "bill",
            "trash", "sewer", "recharge", "subscription"
        ]
    },
    "Housing & Rent": {
        "icon": "fa-house",
        "color": "#3b82f6",  # blue
        "keywords": [
            "rent", "mortgage", "apartment", "landlord", "maintenance", "furniture", "ikea",
            "home depot", "lowes", "plumber", "electrician", "repair", "hardware", "property"
        ]
    },
    "Health & Fitness": {
        "icon": "fa-heart-pulse",
        "color": "#10b981",  # emerald
        "keywords": [
            "pharmacy", "medicine", "cvs", "walgreens", "chemist", "doctor", "dentist", "dental",
            "clinic", "hospital", "gym", "fitness", "crossfit", "yoga", "protein", "supplements",
            "therapy", "optician", "health", "workout"
        ]
    },
    "Education": {
        "icon": "fa-graduation-cap",
        "color": "#6366f1",  # indigo
        "keywords": [
            "course", "udemy", "coursera", "edx", "books", "bookstore", "tuition", "school",
            "college", "university", "seminar", "workshop", "training", "library", "exam"
        ]
    },
    "Personal Care": {
        "icon": "fa-spa",
        "color": "#14b8a6",  # teal
        "keywords": [
            "salon", "haircut", "barber", "spa", "massage", "cosmetics", "skincare", "beauty",
            "parlour", "shaving", "manicure", "pedicure"
        ]
    },
    "Investments & Savings": {
        "icon": "fa-chart-line",
        "color": "#10b981",  # green
        "keywords": [
            "investment", "stock", "shares", "crypto", "bitcoin", "etf", "mutual fund", "deposit",
            "vanguard", "fidelity", "robinhood", "savings", "gold", "real estate"
        ]
    },
    "Miscellaneous": {
        "icon": "fa-tags",
        "color": "#64748b",  # slate
        "keywords": ["other", "misc", "gift", "donation", "charity", "fine", "fee", "tax"]
    }
}


def predict_category(text: str) -> str:
    """Predict the best matching category based on description and merchant keywords."""
    if not text:
        return "Miscellaneous"
    
    clean_text = text.lower()
    scores = {}
    
    for category, meta in CATEGORY_DEFINITIONS.items():
        score = 0
        for kw in meta["keywords"]:
            # Exact word boundary or substring match
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, clean_text):
                score += 3
            elif kw in clean_text:
                score += 1
        if score > 0:
            scores[category] = score
            
    if scores:
        return max(scores, key=scores.get)
    return "Miscellaneous"


def parse_natural_expense(prompt: str):
    """
    Parse a natural language text query into expense details:
    e.g. 'Spent $45.50 on dinner at Olive Garden yesterday via Credit Card'
    or '35 for taxi to airport today'
    """
    clean_prompt = prompt.strip()
    result = {
        "amount": None,
        "title": clean_prompt,
        "category": "Miscellaneous",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "payment_method": "Credit Card",
        "notes": ""
    }

    # 1. Extract Amount ($45.50, 45.50$, 45.50, INR 500, Rs. 500, etc.)
    amount_pattern = r"(?:[\$€£₹]|rs\.?|inr|usd)?\s*(\d+(?:[.,]\d{1,2})?)\s*(?:[\$€£₹]|usd|inr|rs\.?)?"
    matches = list(re.finditer(amount_pattern, clean_prompt, re.IGNORECASE))
    
    extracted_amount = None
    for match in matches:
        val_str = match.group(1).replace(",", "")
        try:
            val = float(val_str)
            if val > 0:
                extracted_amount = val
                # remove amount part from prompt to clean up title
                span = match.span()
                clean_prompt = clean_prompt[:span[0]] + " " + clean_prompt[span[1]:]
                break
        except ValueError:
            continue
    result["amount"] = extracted_amount

    # 2. Extract Date (yesterday, today, days ago, or YYYY-MM-DD)
    lower_prompt = clean_prompt.lower()
    if "yesterday" in lower_prompt:
        result["date"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        clean_prompt = re.sub(r"\byesterday\b", "", clean_prompt, flags=re.IGNORECASE)
    elif "today" in lower_prompt:
        result["date"] = datetime.now().strftime("%Y-%m-%d")
        clean_prompt = re.sub(r"\btoday\b", "", clean_prompt, flags=re.IGNORECASE)
    else:
        # Check for '2 days ago'
        ago_match = re.search(r"(\d+)\s+days?\s+ago", lower_prompt)
        if ago_match:
            days = int(ago_match.group(1))
            result["date"] = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            clean_prompt = re.sub(r"\d+\s+days?\s+ago", "", clean_prompt, flags=re.IGNORECASE)

    # 3. Extract Payment Method
    payment_methods = {
        "Credit Card": ["credit card", "credit", "cc"],
        "Debit Card": ["debit card", "debit", "dc"],
        "Cash": ["cash"],
        "UPI": ["upi", "gpay", "google pay", "phonepe", "paytm"],
        "Net Banking": ["bank transfer", "net banking", "wire", "transfer"],
        "Digital Wallet": ["apple pay", "paypal", "venmo"]
    }
    
    for method, aliases in payment_methods.items():
        for alias in aliases:
            pattern = r"\b(?:via|by|with|using|on)?\s*" + re.escape(alias) + r"\b"
            if re.search(pattern, clean_prompt, re.IGNORECASE):
                result["payment_method"] = method
                clean_prompt = re.sub(pattern, "", clean_prompt, flags=re.IGNORECASE)
                break

    # 4. Clean up title from filler words
    cleaned_title = re.sub(
        r"^(?:spent|paid|bought|expense of|purchased|for|on)\s+",
        "",
        clean_prompt.strip(),
        flags=re.IGNORECASE
    )
    cleaned_title = re.sub(r"\s+(?:for|on|at|via|with|using)\s*$", "", cleaned_title, flags=re.IGNORECASE)
    cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip()
    
    result["title"] = cleaned_title.capitalize() if cleaned_title else "Expense"
    result["category"] = predict_category(prompt)
    return result


def generate_insights(expenses, budgets, incomes, current_month=None):
    """
    Analyze spending patterns, budget adherence, and generate smart actionable financial insights.
    """
    now = datetime.now()
    if not current_month:
        current_month = now.strftime("%Y-%m")

    month_expenses = [e for e in expenses if str(e.date).startswith(current_month)]
    total_spent = sum(e.amount for e in month_expenses)
    
    # Calculate category spending
    cat_spending = {}
    for e in month_expenses:
        cat_name = e.category.name if hasattr(e, "category") and e.category else e.category_name
        cat_spending[cat_name] = cat_spending.get(cat_name, 0.0) + e.amount

    total_income = sum(i.amount for i in incomes if str(i.date).startswith(current_month))
    
    insights = []
    
    # 1. Savings Rate / Cashflow
    if total_income > 0:
        savings = total_income - total_spent
        savings_rate = (savings / total_income) * 100
        if savings_rate >= 20:
            insights.append({
                "type": "success",
                "icon": "fa-circle-check",
                "title": "Healthy Savings Rate",
                "message": f"You are saving {savings_rate:.1f}% of your monthly income (Net savings: ${savings:,.2f}). Great job maintaining fiscal discipline!"
            })
        elif savings_rate > 0:
            insights.append({
                "type": "info",
                "icon": "fa-info-circle",
                "title": "Modest Savings",
                "message": f"You have saved {savings_rate:.1f}% (${savings:,.2f}) this month. Consider cutting non-essential entertainment or dining to boost your savings buffer."
            })
        else:
            insights.append({
                "type": "danger",
                "icon": "fa-triangle-exclamation",
                "title": "Cash Flow Deficit",
                "message": f"Spending exceeds current recorded income by ${abs(savings):,.2f}. Review high-spend categories immediately."
            })

    # 2. Budget Alerts
    budget_map = {b.category.name if hasattr(b, "category") and b.category else b.category_name: b.amount for b in budgets}
    for cat_name, spent in cat_spending.items():
        if cat_name in budget_map:
            limit = budget_map[cat_name]
            pct = (spent / limit) * 100 if limit > 0 else 0
            if pct >= 100:
                insights.append({
                    "type": "danger",
                    "icon": "fa-fire",
                    "title": f"Budget Exceeded: {cat_name}",
                    "message": f"You have spent ${spent:,.2f} against your ${limit:,.2f} budget ({pct:.0f}% used). Limit further expenses here."
                })
            elif pct >= 80:
                insights.append({
                    "type": "warning",
                    "icon": "fa-triangle-exclamation",
                    "title": f"Budget Warning: {cat_name}",
                    "message": f"You've reached {pct:.0f}% of your ${limit:,.2f} budget with ${(limit - spent):,.2f} remaining."
                })

    # 3. Top Spending Category
    if cat_spending:
        top_cat = max(cat_spending, key=cat_spending.get)
        top_amount = cat_spending[top_cat]
        pct_of_total = (top_amount / total_spent * 100) if total_spent > 0 else 0
        if pct_of_total >= 35 and total_spent > 50:
            insights.append({
                "type": "info",
                "icon": "fa-pie-chart",
                "title": f"Heavy Concentration: {top_cat}",
                "message": f"{top_cat} accounts for {pct_of_total:.1f}% (${top_amount:,.2f}) of your total expenses this month."
            })

    # 4. Projected Month-End Spend
    day_of_month = now.day
    days_in_month = 30  # approximation
    if day_of_month > 2 and total_spent > 0:
        daily_avg = total_spent / day_of_month
        projected = daily_avg * days_in_month
        insights.append({
            "type": "neutral",
            "icon": "fa-wand-magic-sparkles",
            "title": "Projected Spending",
            "message": f"At your current pace of ${daily_avg:.2f}/day, your estimated total expenditure this month will be ~${projected:,.2f}."
        })

    # Default fallback insight if list is empty
    if not insights:
        insights.append({
            "type": "info",
            "icon": "fa-lightbulb",
            "title": "Welcome to Smart Expense Tracker",
            "message": "Add your first expense or import transactions to begin generating AI spending diagnostics and automated budget checks."
        })

    return insights
