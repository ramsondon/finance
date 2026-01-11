import pytest
from django.contrib.auth.models import User
from finance_project.apps.banking.models import BankAccount, Category, Transaction

@pytest.mark.django_db
def test_create_account_and_transaction():
    u = User.objects.create_user(username='u1')
    acc = BankAccount.objects.create(user=u, name='Checking', institution='MyBank')
    cat = Category.objects.create(user=u, name='Groceries')
    tx = Transaction.objects.create(account=acc, date='2024-01-01', amount=100, description='Test', type='expense', category=cat)
    assert tx.account == acc
    assert tx.category == cat

