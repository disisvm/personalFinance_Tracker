from flask import Flask, render_template, request, redirect

import db_connection as mongo

app = Flask(__name__)


# Collection variables
users = mongo.db.users


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
                return redirect('/dashboard')
        except TypeError:
            return render_template('login.html', error_message=error_message)

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


@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    # If not logged in, redirect to login page
    # Perform login check logic here

    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)
