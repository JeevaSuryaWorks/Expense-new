import sys
from app import app
from smart_categorizer import parse_natural_expense

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_tests():
    client = app.test_client()
    
    # 1. Test Routes
    endpoints = ['/', '/expenses', '/budgets', '/incomes', '/analytics', '/api/stats/monthly-chart', '/api/stats/category-breakdown']
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, f"Route {ep} failed with {resp.status_code}"
        print(f"PASS: {ep} -> 200")

    # 2. Test Smart Natural Language Parsing
    test_cases = [
        "Spent ₹650 at Barbeque Nation yesterday via Credit Card",
        "Paid Rs. 1850 for electricity bill today",
        "Uber ride ₹240 yesterday with UPI",
        "Netflix subscription INR 649"
    ]
    for tc in test_cases:
        parsed = parse_natural_expense(tc)
        print(f"Input: '{tc}' -> Parsed: Amount={parsed['amount']}, Cat={parsed['category']}, Date={parsed['date']}, Method={parsed['payment_method']}")
        assert parsed['amount'] is not None, f"Amount extraction failed for {tc}"

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == '__main__':
    run_tests()
