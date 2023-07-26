import csv
from datetime import datetime, date
from io import BytesIO, StringIO

from flask import Flask, render_template, request, redirect, url_for, send_file, Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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


@app.route('/export/<username>', methods=['GET', 'POST'])
def export_data(username):
    accounts = accounts_list(username)

    if request.method == 'POST':
        # Handle form submission
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        account = request.form['account']

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

        # Get filtered income and expense records from the database
        income_records = list(incomeCollection.find({
            "$and": [
                {"user": username},
                {"date": {"$gte": start_date, "$lte": end_date}} if start_date and end_date else {},
                {"account": account} if account else {}
            ]
        }))

        expense_records = list(expenseCollection.find({
            "$and": [
                {"user": username},
                {"date": {"$gte": start_date, "$lte": end_date}} if start_date and end_date else {},
                {"account": account} if account else {}
            ]
        }))

        if request.form.get('export_pdf') == 'true':
            # Generate PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)

            # Add income records to PDF
            c.drawString(100, 800, 'Income Records:')
            y_offset = 780
            for record in income_records:
                c.drawString(100, y_offset, f"Amount: {record['amount']}, Description: {record['description']}")
                y_offset -= 15

            # Add expense records to PDF
            c.drawString(100, y_offset, 'Expense Records:')
            y_offset -= 20
            for record in expense_records:
                c.drawString(100, y_offset, f"Amount: {record['amount']}, Description: {record['description']}")
                y_offset -= 15

            c.save()
            buffer.seek(0)

            return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                             download_name=f'export_{username}.pdf')

        else:
            # Generate CSV
            csv_data = generate_csv(income_records, expense_records)

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


def generate_csv(income_records, expense_records):
    # Prepare the CSV data using StringIO
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write header row
    csv_writer.writerow(["Type", "Amount", "Description", "Account", "Category", "Date"])

    # Write income records
    for record in income_records:
        csv_writer.writerow(["Income", record["amount"], record["description"], record["account"], record["category"], record["date"]])

    # Write expense records
    for record in expense_records:
        csv_writer.writerow(["Expense", record["amount"], record["description"], record["account"], record["category"], record["date"]])

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
