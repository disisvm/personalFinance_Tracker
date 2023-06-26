# Personal Finance Tracker

The Personal Finance Tracker is a web application built using Python and MongoDB to help users track their income,
expenses, and budgets. It provides a user-friendly interface for managing financial information and offers features such
as expense tracking, income tracking, budget management, goal setting, and data visualization.

## Features

- User registration and login: Users can create an account and log in securely to access their financial data.
- Dashboard: Provides an overview of the user's financial information, including account balances, income, expenses, and
  budget progress.
- Expense tracking: Allows users to enter and categorize their expenses, storing details such as amount, category, date,
  and description.
- Income tracking: Enables users to record their income sources and amounts, storing details such as source, amount, and
  date.
- Budget management: Assists users in creating and managing budgets for different expense categories, tracking progress
  and providing alerts if exceeded.
- Transaction history: Provides a record of all income and expense transactions, allowing users to search, filter, and
  sort transactions based on various criteria.
- Goal setting and tracking: Allows users to set financial goals and tracks progress towards those goals, providing
  visual feedback.
- Data visualization and reporting: Generates charts and graphs to visualize financial data, such as expenses by
  category or income trends over time, using Seaborn.
- Settings and preferences: Allows users to customize account settings and preferences, including currency selection,
  date format, and notification settings.
- Data backup and export: Provides options for users to back up their data and export it in various formats, such as CSV
  or Excel.

## Installation

1. Clone the repository:
   gh repo clone disisvm/personalFinance_Tracker


2. Install the required packages:
   pip install -r requirements.txt


3. Set up MongoDB:

- Install MongoDB: [https://docs.mongodb.com/manual/installation/](https://docs.mongodb.com/manual/installation/)
- Create a MongoDB database for the project.

4. Configure the application:

- Update the MongoDB connection details in `db_connection.py`.

5. Run the application:
   python app.py


6. Access the application in your web browser:
   http://localhost:5000

## Technologies Used

- Python: Programming language used for backend development.
- Flask: Web framework used for building the application.
- MongoDB: NoSQL database used for storing financial data.
- Seaborn: Data visualization library used for generating charts and graphs.
- HTML: Mark-up language used for templates in Flask.

## Screenshots
