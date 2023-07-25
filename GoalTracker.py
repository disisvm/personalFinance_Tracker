from flask import Flask, render_template, request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy

# init Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqllite:///'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

goals=[]

# create a class
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)


# flask server routes

@app.route('/')
def home():
    return render_template('home.html')


@app.route("/goal")
def goal():
    return

@app.route("/add",methods=["POST"])

def add_goal():
    title = request.form.get("title")
    amount1 = int(request.form.get("amount", 0))  # to place the amount , if the field is empty then default 0 will be placed
    amount2 = int(request.form.get("amount2",0))

# new unique ID for the new goal
      goal_id = max(goal["id"] for goal in goals) + 1

        # Create the new goal and add it to the list
        new_goal = {"id": goal_id, "name": title, "target_amount": amount1, "current_amount":amount2}
        goals.append(new_goal)

        return redirect(url_for(""))
        return render_template("")


def find_goal(goal_id):
    for match_goals in goals:
        if match_goals["id"] == goal_id:
            return goal
    return None

def view_goal(goal_id):
    matched_goal=find_goal(goal_id)
    if not matched_goal:
        return "Goal not found"

@app.route("/goal/<int:goal_id>/update", methods=["GET", "POST"])
def update_goal(goal_id):
    matched_goal = find_goal(goal_id)
    if not matched_goal:
        return "Goal not found",

    if request.method == "POST":
        title = request.form.get("title")
        amount1 = int(request.form.get("amount1", 0))
        amount2 = int(request.form.get("amount2", 0))

        matched_goal["title"] = title
        matched_goal["amount1"] = amount1
        matched_goal["amount2"] = amount2

        return redirect(url_for("view_goal", goal_id=goal_id))

    return render_template(".html", goal=matched_goal)

@app.route(" ", methods=["POST"])
def delete_goal(goal_id):
    matched_goal = find_goal(goal_id)
    if not matched_goal:
        return "Goal not found"
        goals.remove(matched_goal)

    return redirect(url_for(" ")

# run server
if __name__ == "__main__":
    app.run(debug=True)  # debug for showing the error
