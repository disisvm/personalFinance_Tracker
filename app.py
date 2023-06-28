from flask import Flask, render_template, request, redirect, url_for

import db_connection as mongo

app = Flask(__name__)

# Collection variables
users = mongo.db.users
incomeCollection = mongo.db.income
expenseCollection = mongo.db.expense


def accountsCollection(username):

    accountsList = list(mongo.db.accounts.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in accountsList if 'name' in d]

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

        # Insert income record into the database
        incomeCollection.insert_one(
            {'user': username, 'amount': amount, 'description': description, 'account': account})

        return redirect(url_for('dashboard', username=username))

    return render_template('income.html', accounts=accountsCollection(username), username=username)


@app.route('/expenses/<username>', methods=['GET', 'POST'])
def add_expense(username):
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        account = request.form['account']

        # Insert expense record into the database
        expenseCollection.insert_one(
            {'user': username, 'amount': amount, 'description': description, 'account': account})

        return redirect(url_for('dashboard', username=username))

    return render_template('expenses.html', accounts=accountsCollection(username), username=username)


@app.route('/dashboard/<username>')
def dashboard(username):
    # Retrieve user's financial information from the database
    # Replace the placeholders below with the actual data retrieval logic
    account_balances = {'Savings': 5000, 'Checking': 2500, 'Investments': 10000}

    # Retrieve income and expense records from the database for the specific user
    income_records = list(incomeCollection.find({'username': username}))
    expense_records = list(expenseCollection.find({'username': username}))

    return render_template('dashboard.html', username=username, account_balances=account_balances,
                           income_records=income_records, expense_records=expense_records)


if __name__ == '__main__':
    app.run(debug=True)
