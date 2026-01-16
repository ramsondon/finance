"""
Test for analytics category expense breakdown.
Ensures pie chart shows all categories including uncategorized expenses.
"""
import pytest
from datetime import date
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from finance_project.apps.banking.models import BankAccount, Category, Transaction


@pytest.mark.django_db
def test_category_expense_breakdown_includes_all_categories():
    """Test that category breakdown includes both categorized and uncategorized expenses."""
    # Setup
    user = User.objects.create_user(username='testuser', password='pw')
    client = APIClient()
    client.login(username='testuser', password='pw')

    # Create account
    account = BankAccount.objects.create(
        user=user,
        name='Test Account',
        currency='EUR',
        opening_balance=1000
    )

    # Create categories
    groceries = Category.objects.create(user=user, name='Groceries', color='#10b981')
    coffee = Category.objects.create(user=user, name='Coffee', color='#f59e0b')

    # Create transactions
    # Categorized expenses
    Transaction.objects.create(
        account=account,
        date=date(2026, 1, 1),
        amount=-50,
        description='Grocery store',
        category=groceries,
        type='expense'
    )
    Transaction.objects.create(
        account=account,
        date=date(2026, 1, 2),
        amount=-5,
        description='Coffee',
        category=coffee,
        type='expense'
    )
    # Uncategorized expense
    Transaction.objects.create(
        account=account,
        date=date(2026, 1, 3),
        amount=-20,
        description='Unknown expense',
        category=None,  # NULL category
        type='expense'
    )

    # Test all_time period
    resp = client.get('/api/analytics/category-expense/?period=all_time')
    assert resp.status_code == 200

    data = resp.json()

    # Should have 3 entries: groceries, coffee, and unknown (uncategorized)
    assert len(data['labels']) == 3, f"Expected 3 categories, got {len(data['labels'])}: {data['labels']}"
    assert 'Groceries' in data['labels']
    assert 'Coffee' in data['labels']
    assert 'Unknown' in data['labels']

    # Verify values are correct
    assert len(data['values']) == 3
    assert 50 in data['values']  # Groceries
    assert 5 in data['values']   # Coffee
    assert 20 in data['values']  # Unknown

    # Verify items structure
    assert len(data['items']) == 3
    unknown_item = [item for item in data['items'] if item['name'] == 'Unknown'][0]
    assert unknown_item['value'] == 20
    assert unknown_item['id'] is None  # Uncategorized has no category ID


@pytest.mark.django_db
def test_category_expense_breakdown_current_month():
    """Test that period filtering works correctly for current month."""
    user = User.objects.create_user(username='testuser2', password='pw')
    client = APIClient()
    client.login(username='testuser2', password='pw')

    account = BankAccount.objects.create(
        user=user,
        name='Test Account',
        currency='EUR',
        opening_balance=1000
    )

    cat1 = Category.objects.create(user=user, name='Category 1', color='#3b82f6')

    # Create transaction in current month
    current_today = date.today()
    Transaction.objects.create(
        account=account,
        date=current_today,
        amount=-100,
        description='Current month expense',
        category=cat1,
        type='expense'
    )

    # Create transaction outside current month
    Transaction.objects.create(
        account=account,
        date=date(2025, 1, 1),
        amount=-200,
        description='Last year expense',
        category=cat1,
        type='expense'
    )

    # Test current month
    resp = client.get('/api/analytics/category-expense/?period=current_month')
    assert resp.status_code == 200

    data = resp.json()
    # Should only show current month expense
    assert len(data['labels']) == 1
    assert data['values'][0] == 100  # Only the current month one


@pytest.mark.django_db
def test_category_expense_breakdown_no_expenses():
    """Test that endpoint returns empty data when there are no expenses."""
    user = User.objects.create_user(username='testuser3', password='pw')
    client = APIClient()
    client.login(username='testuser3', password='pw')

    # Create account but no transactions
    BankAccount.objects.create(
        user=user,
        name='Test Account',
        currency='EUR',
        opening_balance=1000
    )

    resp = client.get('/api/analytics/category-expense/?period=all_time')
    assert resp.status_code == 200

    data = resp.json()
    assert len(data['labels']) == 0
    assert len(data['values']) == 0
    assert len(data['items']) == 0

