from flask import Flask, render_template, request, redirect, session
import json
import os
import numpy as np
from sklearn.linear_model import LogisticRegression

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= ML MODEL =================

X = np.array([
    [30, 20, 10],
    [10, 40, 20],
    [15, 10, 50],
    [25, 30, 10],
    [40, 10, 5]
])

y = np.array([0, 1, 2, 1, 0])

model = LogisticRegression()
model.fit(X, y)

# ================= FILE FUNCTIONS =================

def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f)

def load_votes():
    if not os.path.exists("votes.json"):
        return {"A":0, "B":0, "C":0, "total_votes":0, "voted_users":[]}
    with open("votes.json", "r") as f:
        return json.load(f)

def save_votes(data):
    with open("votes.json", "w") as f:
        json.dump(data, f)

# ================= HOME =================

@app.route('/')
def home():
    return render_template("home.html")

# ================= REGISTER =================

@app.route('/register', methods=['GET', 'POST'])
def register():
    users = load_users()

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return "User already exists!"

        users[username] = {
            "name": name,
            "password": password
        }

        save_users(users)
        return redirect('/login')

    return render_template('register.html')

# ================= LOGIN =================

@app.route('/login', methods=['GET','POST'])
def login():
    users = load_users()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ✅ FIXED HERE
        if username in users and users[username]['password'] == password:
            session['user'] = username
            return redirect('/vote')
        else:
            return "Invalid Voter ID or Key"

    return render_template("login.html")

# ================= VOTE =================

@app.route('/vote', methods=['GET','POST'])
def vote():

    if 'user' not in session:
        return redirect('/login')

    votes = load_votes()

    if votes["total_votes"] >= 5:
        return render_template("vote.html",
                           total_votes=votes["total_votes"],
                           msg="Voting completed. See results.")

    if request.method == 'POST':

        if 'candidate' not in request.form:
            return redirect('/vote')

        choice = request.form['candidate']

        if session['user'] in votes['voted_users']:
            return render_template("vote.html",
                                   total_votes=votes["total_votes"],
                                   msg="⚠️ You already voted!")

        votes[choice] += 1
        votes["total_votes"] += 1
        votes["voted_users"].append(session['user'])

        save_votes(votes)

        return render_template("vote.html",
                               total_votes=votes["total_votes"],
                               msg="✅ Vote submitted successfully!")

    return render_template("vote.html", total_votes=votes["total_votes"])

# ================= RESULT =================

# ================= RESULT =================

@app.route('/result')
def result():

    votes = load_votes()
    total = votes["total_votes"]

    if total == 0:
        return "No votes yet"

    a, b, c = votes["A"], votes["B"], votes["C"]

    # ✅ FIXED (use probability, not percentage)
    pA = a / total
    pB = b / total
    pC = c / total
    
    # ML winner
    winner_index = model.predict([[a, b, c]])[0]
    winner = ["A", "B", "C"][winner_index]

    # ✅ FIXED confidence interval (correct formula)
    z = 1.96
    margin = z * np.sqrt((pA * (1 - pA)) / total)
    low = max(0, pA - margin)
    high = min(1, pA + margin)

    return render_template("result.html",
                           pA=round(pA*100,2),
                           pB=round(pB*100,2),
                           pC=round(pC*100,2),
                           winner=winner,
                           low=round(low*100,2),
                           high=round(high*100,2))

# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# ================= RESET =================

@app.route('/reset')
def reset():
    votes = {"A":0, "B":0, "C":0, "total_votes":0, "voted_users":[]}
    save_votes(votes)
    return redirect('/vote')

# ================= RESET USERS =================

@app.route('/reset_users')
def reset_users():
    save_users({})
    save_votes({"A":0, "B":0, "C":0, "total_votes":0, "voted_users":[]})
    return redirect('/')

# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)