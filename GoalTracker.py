
import seaborn as sns
from bson.objectid import ObjectId
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import matplotlib.pyplot as plt
import pandas as pd
from pymongo.cursor import Cursor

# init Flask app
app = Flask(__name__)

#MongoDB connection
client=MongoClient('')
db=client['']
goals_list=db['goals']

# flask server routes

@app.route("/add",methods=["GET","POST"])

def set_goals(username):
    if request.method == 'POST':
        goal_name = request.form['goal.name']
        goal_amount = float(request.form['goal_amount'])
        target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d')
        goal_description = request.form['goal_description']

goals_list.insert_one({
    "user": username,
    "goal_name": goal_name,
    "goal_amount": goal_amount,
    "target_date": target_date,
    "description": goal_description,
    "current_amount": 0.0
})

return redirect(url_for('view_goals', username=username))
return render_template('add_goal.html')


@app.route("", methods=['GET', 'POST'])
def fetch_goal(username):
    goals_u= list(goals_list.find({'user': username}))
    return goals_u


@app.route("", methods=['GET'])
def view_goals(username):
    goals_u = fetch_goal(username)
    return render_template('',username=username,goals=goals_u)

@app.route("/goal/<int:goal_id>/update", methods=['GET', 'POST'])
def update_goal(goal_id):
    if request.method == 'POST':
        goal_amount = float(request.form['goal_amount'])
        target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d')

    goals_list.update_one(
        {"_id": ObjectId(goal_id)},
        {"$set": {
            "goal_amount": goal_amount,
            "target_date": target_date
        }}
    )
    return redirect(url_for('view_goals',username='current_user'))
    goal = goals_list.find_one({"_id": ObjectId(goal_id)})
    return render_template('update_goal.html', goal=goal)
@app.route(" ", methods=["POST"])
def delete_goal(goal_id):
    goals_list.delete_one({"_id": ObjectId(goal_id)})
    return redirect(url_for('view_goals',username=''))


app.route('/visualization')
def bar_plot():
    goals_list = fetch_goal('current_user')
    user_goals_count = pd.Series([len(goals) for goals in goals_list])
    sns.countplot(x=user_goals_count)
    plt.title('Number of Goals Set by Each User')
    plt.xlabel('Number of Goals')
    plt.ylabel('Count')
    plt.show()
    return render_template('bar_plot.html')

@app.route('/visualization/bar_plot1', methods=['GET'])
def bar_plot1():
    goals_u = fetch_goal('current_user')
    df = pd.DataFrame(goals_list, columns=['goal_name', 'goal_amount'])
    plt.figure(figsize=(10, 6))
    sns.barplot(x='goal_name', y='goal_amount', data=df)
    plt.title('Amount per Goal')
    plt.xlabel('Goal')
    plt.ylabel('Amount')
    plt.xticks(rotation=45)
    plt.show()
    return render_template('bar_plot1.html')

@app.route('/visualization/pie_plot', methods=['GET'])
def plot_pie():
    goals_u= fetch_goal('current_user')
    completed_goals = sum(1 for goal in goals_u if goal['completed'])
    in_progress_goals = sum(1 for goal in goals_u if not goal['completed'])

    goal_data = {
        'Status': ['Completed', 'In Progress'],
        'Count': [completed_goals, in_progress_goals]
    }
    data = pd.DataFrame(goal_data)

    # Plot the pie chart
    plt.figure(figsize=(6, 6))
    plt.pie(data['Count'], labels=data['Status'], autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title('Goal Distribution')
    plt.show()
    return render_template('pie_plot.html')

def scatter_plot(goals_u):
    df = pd.DataFrame(goals_list, columns=['goal_amount', 'current_amount'])
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='goal_amount', y='current_amount', data=df)
    plt.title('Goal Amount vs. Current Amount')
    plt.xlabel('Goal Amount')
    plt.ylabel('Current Amount')
    plt.show()

if __name__ == "__main__":
    app.run(debug=True)
