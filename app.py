from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for

import db_connection as mongo

app = Flask(__name__)

# Collection variables
users = mongo.db.users
incomeCollection = mongo.db.income
expenseCollection = mongo.db.expense


def accounts_list(username):
    accountsList = list(mongo.db.accounts.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in accountsList if 'name' in d]

    return values_list


def income_category(username):
    income_categoryList = list(mongo.db.incomeCategory.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in income_categoryList if 'name' in d]

    return values_list


def expense_category(username):
    income_categoryList = list(mongo.db.incomeCategory.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in income_categoryList if 'name' in d]

    return values_list


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists and password matches
        user_details = users.find_one({"user": username, "password": password})
        try:
            if user_details['user'] == username and user_details['password'] == password:
                return redirect('/dashboard/' + username)
        except TypeError:
            return render_template('login.html')

        # Invalid credentials, show error message
        error_message = 'Invalid username or password.'
        return render_template('login.html', error_message=error_message)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if username is already taken
        user_details = users.find_one({"user": username, "password": password})
        try:
            if user_details['user'] == username:
                error_message = 'Username already taken. Please choose a different username.'
                return render_template('register.html', error_message=error_message)
        except TypeError:
            print(user_details)

        # Check if password and confirm password match
        if password != confirm_password:
            error_message = 'Passwords do not match. Please try again.'
            return render_template('register.html', error_message=error_message)

        # store user in database
        users.insert_one({'user': username, 'password': password})

        # Redirect to login page
        return redirect('/login')

    return render_template('register.html')


@app.route('/income/<username>', methods=['GET', 'POST'])
def add_income(username):
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        account = request.form['account']
        category = request.form['category']

        # Insert income record into the database
        incomeCollection.insert_one({'user': username,
                                     'amount': amount,
                                     'description': description,
                                     'account': account,
                                     'category': category,
                                     'date': datetime.now()})

        return redirect(url_for('dashboard', username=username))

    return render_template('income.html', accounts=accounts_list(username), username=username,
                           categories=income_category(username))


@app.route('/expenses/<username>', methods=['GET', 'POST'])
def add_expense(username):
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        account = request.form['account']
        category = request.form['category']

        # Insert income record into the database
        expenseCollection.insert_one({'user': username,
                                      'amount': amount,
                                      'description': description,
                                      'account': account,
                                      'category': category,
                                      'date': datetime.now()})

        return redirect(url_for('dashboard', username=username))

    return render_template('expenses.html', accounts=accounts_list(username), username=username,
                           categories=expense_category(username))


@app.route('/dashboard/<username>')
def dashboard(username):
    # Retrieve user's financial information from the database
    list_of_accounts = accounts_list(username)
    incomeRecords = list(incomeCollection.find({"user": username}))
    expenseRecords = list(expenseCollection.find({"user": username}))

    accounts_summary = {}
    for account in list_of_accounts:
        account_income = sum(record['amount'] for record in incomeRecords if record['account'] == account)
        account_expense = sum(record['amount'] for record in expenseRecords if record['account'] == account)
        accounts_summary[account] = {
            'income': account_income,
            'expense': account_expense,
            'balance': account_income - account_expense
        }

    # Retrieve income and expense records from the database for the specific user
    income_records = list(incomeCollection.find({
        "$and": [
            {"user": username},
            {"date": {"$gte": datetime.combine(date.today(), datetime.min.time()),
                      "$lt": datetime.combine(date.today(), datetime.max.time())}}
        ]
    }))
    expense_records = list(expenseCollection.find({
        "$and": [
            {"user": username},
            {"date": {"$gte": datetime.combine(date.today(), datetime.min.time()),
                      "$lt": datetime.combine(date.today(), datetime.max.time())}}
        ]
    }))

    return render_template('dashboard.html', username=username, accounts_summary=accounts_summary,
                           income_records=income_records, expense_records=expense_records)


if __name__ == '__main__':
    app.run(debug=True)
