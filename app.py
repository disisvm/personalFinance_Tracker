import csv
import os
from datetime import datetime, date
from io import StringIO

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from bson import ObjectId
from flask import Flask, Response, flash
from flask import request, redirect, url_for, render_template

import db_connection as mongo

matplotlib.use('Agg')

app = Flask(__name__)
app.secret_key = '3308'

# Collection variables
users = mongo.db.users
transactionsCollection = mongo.db.transactions
accountsCollection = mongo.db.accounts
incomeCategoryCollection = mongo.db.incomeCategory
expenseCategoryCollection = mongo.db.expenseCategory
goalCollection = mongo.db.goals
settingsCollection = mongo.db.settings


def accounts_list(username):
    accountsList = list(accountsCollection.find({"$or": [{"user": username}, {"default": True}]}))
    values_list = [d['name'] for d in accountsList if 'name' in d]

    return values_list


def income_category(username):
    income_categoryList = list(incomeCategoryCollection.find({
        "$and": [
            {"$or": [{"user": username}, {"default": True}]},
            {"is_active": True}
        ]
    }))

    values_list = [d['name'] for d in income_categoryList if 'name' in d]

    return values_list


def expense_category(username):
    expense_categoryList = list(expenseCategoryCollection.find({
        "$and": [
            {"$or": [{"user": username}, {"default": True}]},
            {"is_active": True}
        ]
    }))
    values_list = [d['name'] for d in expense_categoryList if 'name' in d]

    return values_list


def budget_goal(username):
    settingsList = settingsCollection.find_one({"user": username})
    budget_value = settingsList.get("budget")
    goal_value = settingsList.get("goal")

    return budget_value, goal_value


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
        settingsCollection.insert_one({'user': username, 'budget': 0, 'goal': 0})

        # Redirect to login page
        return redirect('/login')

    return render_template('register.html')


@app.route('/income/<username>', methods=['GET', 'POST'])
def add_income(username):
    # Get current month and year
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    # Fetch income for the current month
    income_records = transactionsCollection.find({
        'user': username,
        'transaction_type': 'income',
        'date': {'$gte': datetime.combine(datetime(current_year, current_month, 1), datetime.min.time()),
                 '$lt': datetime.combine(datetime(current_year, current_month + 1, 1), datetime.min.time())}
    })

    # Fetch budget
    budget_value, goal_value = budget_goal(username)

    # Calculate total income and remaining goal
    total_income = sum([d['amount'] for d in income_records if 'amount' in d])
    remaining_goal = goal_value - total_income

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
                                           'expense_category': "",
                                           'transaction_type': 'income',
                                           'date': datetime.now()})

        return redirect(url_for('dashboard', username=username))

    return render_template('income.html', accounts=accounts_list(username), username=username,
                           categories=income_category(username), remaining_goal=remaining_goal)


@app.route('/expenses/<username>', methods=['GET', 'POST'])
def add_expense(username):
    # Get current month and year
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    # Fetch expenses for the current month
    expense_records = transactionsCollection.find({
        'user': username,
        'transaction_type': 'expense',
        'date': {'$gte': datetime.combine(datetime(current_year, current_month, 1), datetime.min.time()),
                 '$lt': datetime.combine(datetime(current_year, current_month + 1, 1), datetime.min.time())}
    })

    # Fetch budget
    budget_value, goal_value = budget_goal(username)

    # Calculate total expenses and remaining budget
    total_expenses = sum([d['amount'] for d in expense_records if 'amount' in d])
    remaining_budget = budget_value - total_expenses

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
                                           'expense_category': category,
                                           'income_category': "",
                                           'transaction_type': 'expense',
                                           'date': datetime.now()})

        return redirect(url_for('dashboard', username=username))

    return render_template('expenses.html', accounts=accounts_list(username), username=username,
                           categories=expense_category(username), remaining_budget=remaining_budget)


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


@app.route('/data_visualization/<username>', methods=['GET'])
def data_visualization(username):
    # Fetch accounts, income categories, and expense categories
    accounts = accounts_list(username)
    income_categories = income_category(username)
    expense_categories = expense_category(username)
    transactions = list(transactionsCollection.find({"user": username}))
    transactions_df = pd.DataFrame(transactions)

    # Apply Filters
    transaction_type = request.args.get('transaction_type')
    expense_categoryFilter = request.args.get('expense_categoryFilter')
    income_categoryFilter = request.args.get('income_categoryFilter')
    account_filter = request.args.get('account')
    num_months = int(request.args.get('num_months', default=6))

    if transaction_type:
        transactions_df = transactions_df[transactions_df['transaction_type'] == transaction_type]

    if income_categoryFilter or expense_categoryFilter:

        if income_categoryFilter:
            transactions_df = transactions_df[transactions_df['income_category'] == income_categoryFilter]
        else:
            transactions_df = transactions_df[transactions_df['expense_category'] == expense_categoryFilter]

    if account_filter:
        transactions_df = transactions_df[transactions_df['account'] == account_filter]

    start_date = transactions_df['date'].max() - pd.DateOffset(months=num_months)
    transactions_df = transactions_df[transactions_df['date'] >= start_date]

    transactions_df['date'] = pd.to_datetime(transactions_df['date'])  # Convert 'date' column to datetime
    transactions_df['month-year'] = transactions_df['date'].dt.to_period('M').astype(str)  # Convert to string

    # Plot 1: Income and Expense over Months (Line Graph)

    plt.plot(transactions_df[transactions_df['transaction_type'] == 'income']['month-year'],
             transactions_df[transactions_df['transaction_type'] == 'income']['amount'],
             label='Income', marker='o')
    plt.plot(transactions_df[transactions_df['transaction_type'] == 'expense']['month-year'],
             transactions_df[transactions_df['transaction_type'] == 'expense']['amount'],
             label='Expense', marker='o')
    plt.xlabel('Year-Month')
    plt.ylabel('Amount')
    plt.title('Income and Expense over Months')
    plt.legend()
    save_plots("plot_1.png")

    # Plot 2: Income Categories (Pie Chart)

    income_data = transactions_df[transactions_df['income_category'] != ""].groupby('income_category')['amount'].sum()
    plt.pie(income_data, labels=income_data.index, autopct='%1.1f%%')
    plt.title('Income Categories')
    save_plots("plot_2.png")

    # Plot 3: Expense Categories (Pie Chart)

    expense_data = transactions_df[transactions_df['expense_category'] != ""].groupby('expense_category')[
        'amount'].sum()
    plt.pie(expense_data, labels=expense_data.index, autopct='%1.1f%%')
    plt.title('Expense Categories')
    save_plots("plot_3.png")

    # Plot 4: Income and Expense by Accounts

    account_data = transactions_df.groupby(['account', 'transaction_type'])['amount'].sum().unstack()
    ax = account_data.plot(kind='bar', stacked=True)

    plt.title('Income and Expense by Accounts')
    plt.xlabel('Account')
    plt.ylabel('Amount')
    plt.legend()

    # Add values on top of the bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', label_type='edge', fontsize=10, color='black')

    save_plots("plot_4.png")

    plot_filenames = ['plot_1.png', 'plot_2.png', 'plot_3.png', 'plot_4.png']

    return render_template('data_visualization.html',
                           username=username,
                           accounts=accounts,
                           income_categories=income_categories,
                           expense_categories=expense_categories,
                           expense_categoryFilter=expense_categoryFilter,
                           income_categoryFilter=income_categoryFilter,
                           transactions=transactions,
                           plot_filenames=plot_filenames)


def save_plots(filename):
    plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    chart_path = os.path.join(plots_dir, filename)
    plt.savefig(chart_path, bbox_inches='tight', dpi=500)
    plt.close()


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


@app.route('/budget_management/<username>')
def budget_management(username):
    # Get current month and year
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    # Fetch budget and goal value
    budget_value, goal_value = budget_goal(username)

    # Fetch expenses for the current month
    expense_records = transactionsCollection.find({
        'user': username,
        'transaction_type': 'expense',
        'date': {'$gte': datetime.combine(datetime(current_year, current_month, 1), datetime.min.time()),
                 '$lt': datetime.combine(datetime(current_year, current_month + 1, 1), datetime.min.time())}
    })

    # Calculate total expenses and remaining budget
    total_expenses = sum([d['amount'] for d in expense_records if 'amount' in d])
    remaining_budget = budget_value - total_expenses

    # Create a pie chart
    labels = ['Expenses', 'Remaining Budget']
    values = [total_expenses, remaining_budget]
    colors = ['#FF9999', '#66B2FF']
    plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Save the pie chart to the static directory
    chart_filename = 'budget_pie-chart.png'
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    budget_chart_path = os.path.join(static_dir, chart_filename)
    plt.savefig(budget_chart_path, dpi=1000)
    plt.close()

    # Fetch income for the current month
    income_records = transactionsCollection.find({
        'user': username,
        'transaction_type': 'income',
        'date': {'$gte': datetime.combine(datetime(current_year, current_month, 1), datetime.min.time()),
                 '$lt': datetime.combine(datetime(current_year, current_month + 1, 1), datetime.min.time())}
    })

    # Calculate total income and remaining goal
    total_income = sum([d['amount'] for d in income_records if 'amount' in d])
    remaining_goal = budget_value - total_income

    # Create a pie chart
    labels = ['Income', 'Remaining Goal']
    values = [total_income, remaining_goal]
    colors = ['#FF9999', '#66B2FF']
    plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Save the pie chart to the static directory
    chart_filename = 'goal_pie-chart.png'
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    goal_chart_path = os.path.join(static_dir, chart_filename)
    plt.savefig(goal_chart_path, dpi=1000)
    plt.close()

    return render_template('budget_management.html',
                           username=username,
                           budgets=budget_value,
                           total_expenses=total_expenses,
                           remaining_budget=remaining_budget,
                           goals=goal_value,
                           total_income=total_income,
                           remaining_goal=remaining_goal
                           )


@app.route('/transaction_history/<username>', methods=['GET'])
def transaction_history(username):
    search = request.args.get('search', '')
    filter_type = request.args.get('filter_type', '')
    filter_account = request.args.get('filter_account', '')
    filter_income_category = request.args.get('filter_income_category', '')
    filter_expense_category = request.args.get('filter_expense_category', '')
    min_amount = request.args.get('min_amount', '')
    max_amount = request.args.get('max_amount', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort = request.args.get('sort', '')
    # The $or operator provides flexibility by allowing you to search across multiple field.
    query = {
        'user': username,
        '$or': [
            {'description': {'$regex': search, '$options': 'i'}},
            {'account': {'$regex': search, '$options': 'i'}},
            {'income_category': {'$regex': search, '$options': 'i'}},
            {'expense_category': {'$regex': search, '$options': 'i'}}
        ]
    }

    if filter_type:
        query['transaction_type'] = filter_type

    if filter_account:
        query['account'] = filter_account

    if filter_income_category:
        query['income_category'] = filter_income_category

    if filter_expense_category:
        query['expense_category'] = filter_expense_category

    if min_amount:
        query['amount'] = {'$gte': float(min_amount)}

    if max_amount:
        query['amount']['$lte'] = float(max_amount)

    if start_date:
        query['date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')

    if end_date:
        query['date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

    sort_query = []
    if sort == 'date_asc':
        sort_query.append(('date', 1))
    elif sort == 'date_desc':
        sort_query.append(('date', -1))

    transactions = transactionsCollection.find(query)
    if sort_query:
        transactions = transactions.sort(sort_query)

    income_categories = income_category(username)
    expense_categories = expense_category(username)
    accounts = accounts_list(username)

    return render_template('transaction_history.html', username=username, transactions=transactions,
                           search=search, filter_type=filter_type, filter_account=filter_account,
                           filter_income_category=filter_income_category,
                           filter_expense_category=filter_expense_category, min_amount=min_amount,
                           max_amount=max_amount, start_date=start_date, end_date=end_date,
                           sort=sort, income_categories=income_categories, expense_categories=expense_categories,
                           accounts=accounts)


@app.route('/account_settings/<username>', methods=['GET', 'POST'])
def account_settings(username):
    settings = settingsCollection.find_one({'user': username})
    accounts = accountsCollection.find({"$and": [{"user": username}, {"is_active": True}]})

    income_categories = incomeCategoryCollection.find({
        "$and": [
            {"user": username},
            {"is_active": True}
        ]
    })
    expense_categories = expenseCategoryCollection.find({
        "$and": [
            {"user": username},
            {"is_active": True}
        ]
    })

    if request.method == 'POST':

        action = request.form.get("action")

        if action == "update_goal_budget":
            # Update Goal Value
            new_goal = int(request.form.get('new_goal'))
            settingsCollection.update_one({'user': username}, {'$set': {'goal': new_goal}})

            # Update Budget Value
            new_budget = int(request.form.get('new_budget'))
            settingsCollection.update_one({'user': username}, {'$set': {'budget': new_budget}})

        elif action == 'add_income':
            new_income_category = request.form.get('new_income_category')
            incomeCategoryCollection.insert_one({
                'name': new_income_category,
                'user': username,
                'is_active': True
            })

        elif action == 'add_expense':
            new_expense_category = request.form.get('new_expense_category')
            expenseCategoryCollection.insert_one({
                'name': new_expense_category,
                'user': username,
                'is_active': True
            })

        elif action == 'delete_income':
            category_id = request.form.get('income_category')
            incomeCategoryCollection.update_one({'_id': ObjectId(category_id)}, {"$set": {'is_active': False}})

        elif action == 'delete_expense':
            category_id = request.form.get('expense_category')
            expenseCategoryCollection.update_one({'_id': ObjectId(category_id)}, {"$set": {'is_active': False}})

        elif action == 'edit_income':
            category_id = request.form.get('income_category')
            updated_name = request.form.get('edited_income_category')
            incomeCategoryCollection.update_one({'_id': ObjectId(category_id)}, {"$set": {'name': updated_name}})

        elif action == 'edit_expense':
            category_id = request.form.get('expense_category')
            updated_name = request.form.get('edited_expense_category')
            expenseCategoryCollection.update_one({'_id': ObjectId(category_id)}, {"$set": {'name': updated_name}})

        elif action == 'add_account':
            new_account_name = request.form.get('new_account_name')
            accountsCollection.insert_one({
                'name': new_account_name,
                'user': username,
                'is_active': True,
            })

        elif action == 'delete_account':
            account_id = request.form.get('account')
            accountsCollection.update_one({'_id': ObjectId(account_id)}, {"$set": {'is_active': False}})

    return render_template('account_settings.html',
                           username=username,
                           settings=settings,
                           income_categories=income_categories,
                           expense_categories=expense_categories,
                           accounts=accounts)


@app.route('/change_password/<username>', methods=['POST', 'GET'])
def change_password(username):
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Check if the old password matches the one in the database
        user = users.find_one({'user': username, 'password': old_password})
        if user:
            if new_password == confirm_password:
                # Update the password in the database
                users.update_one({'user': username}, {"$set": {'password': new_password}})
                flash('Password updated successfully!', 'success')
                return render_template('change_password.html', username=username)
            else:
                flash('New password and confirm password do not match.', 'error')
        else:
            flash('Incorrect old password.', 'error')

    return render_template('change_password.html', username=username)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    # Redirect the user to the login page
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
