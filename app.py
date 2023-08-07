import csv
from datetime import datetime, date
from io import BytesIO, StringIO

from flask import Flask, send_file, Response
from flask import request, redirect, url_for, render_template
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import db_connection as mongo

app = Flask(__name__)

# Collection variables
users = mongo.db.users
transactionsCollection = mongo.db.transactions
incomeCategoryCollection = mongo.db.incomeCategory
expenseCategoryCollection = mongo.db.expenseCategory
goalCollection = mongo.db.goals


def accounts_list(username):
    accountsList = list(mongo.db.accounts.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in accountsList if 'name' in d]

    return values_list


def income_category(username):
    income_categoryList = list(incomeCategoryCollection.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in income_categoryList if 'name' in d]

    return values_list


def expense_category(username):
    expense_categoryList = list(expenseCategoryCollection.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in expense_categoryList if 'name' in d]

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
        transactionsCollection.insert_one({'user': username,
                                           'amount': amount,
                                           'description': description,
                                           'account': account,
                                           'income_category': category,
                                           'expense_category': '',
                                           'transaction_type': 'income',
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
        transactionsCollection.insert_one({'user': username,
                                           'amount': amount,
                                           'description': description,
                                           'account': account,
                                           'income_category': '',
                                           'expense_category': category,
                                           'transaction_type': 'expense',
                                           'date': datetime.now()})

        return redirect(url_for('dashboard', username=username))

    return render_template('expenses.html', accounts=accounts_list(username), username=username,
                           categories=expense_category(username))


@app.route('/dashboard/<username>')
def dashboard(username):
    # Retrieve user's financial information from the database
    list_of_accounts = accounts_list(username)
    incomeRecords = list(transactionsCollection.find({"user": username, "transaction_type": "income"}))
    expenseRecords = list(transactionsCollection.find({"user": username, "transaction_type": "expense"}))

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
    income_records = list(transactionsCollection.find({
        "$and": [
            {"user": username},
            {"transaction_type": "income"},
            {"date": {"$gte": datetime.combine(date.today(), datetime.min.time()),
                      "$lt": datetime.combine(date.today(), datetime.max.time())}}
        ]
    }))
    expense_records = list(transactionsCollection.find({
        "$and": [
            {"user": username},
            {"transaction_type": "expense"},
            {"date": {"$gte": datetime.combine(date.today(), datetime.min.time()),
                      "$lt": datetime.combine(date.today(), datetime.max.time())}}
        ]
    }))

    return render_template('dashboard.html', username=username, accounts_summary=accounts_summary,
                           income_records=income_records, expense_records=expense_records)


@app.route('/export/<username>', methods=['GET', 'POST'])
def export_data(username):
    accounts = accounts_list(username)

    if request.method == 'POST':
        # Handle form submission
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        account = request.form['account']
        transaction_type = request.form['transaction_type']

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

        # Get filtered income and expense records from the database
        records = list(transactionsCollection.find({
            "$and": [
                {"user": username},
                {"transaction_type": transaction_type} if transaction_type else {},
                {"date": {"$gte": start_date, "$lte": end_date}} if start_date and end_date else {},
                {"account": account} if account else {}
            ]
        }))

        if request.form.get('export_csv') == 'true':
            # Generate CSV
            csv_data = generate_csv(records)

            # Prepare the response as a downloadable file
            response = Response(
                csv_data,
                headers={
                    "Content-Disposition": "attachment; filename=financial_data.csv",
                    "Content-Type": "text/csv",
                }
            )
            return response

    return render_template('export.html', accounts=accounts, username=username)


def generate_csv(records):
    # Prepare the CSV data using StringIO
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write header row
    csv_writer.writerow(["Type", "Amount", "Description", "Account", "Income Category", "Expense Category", "Date"])

    # Write transaction records
    for record in records:
        csv_writer.writerow(
            [record["transaction_type"], record["amount"], record["description"], record["account"],

             record["income_category"], record["expense_category"], record["date"]])

    # Get the CSV data as a string
    csv_data = csv_buffer.getvalue()

    return csv_data


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    # Redirect the user to the login page
    return redirect(url_for('login'))


@app.route('/settings', methods=['POST', 'GET'])
def settings():
    # Redirect the user to the login page
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
