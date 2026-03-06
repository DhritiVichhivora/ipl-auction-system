from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Use your Render Postgres URL
app.config["SQLALCHEMY_DATABASE_URI"] = "Database_url"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    base_price = db.Column(db.Integer)
    team = db.Column(db.String(50))
    bid = db.Column(db.Integer)

# --- LOGIN PAGE ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user:
            if user.password == password:
                return redirect(url_for("index"))
            else:
                flash("Incorrect password")
        else:
            new_user = User(name=name, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("index"))
    return render_template("login.html")

# --- AUCTION PAGE ---
@app.route("/auction")
def index():
    search = request.args.get('search', '')
    if search:
        players = Player.query.filter(Player.name.ilike(f"%{search}%")).all()
    else:
        players = Player.query.all()
    return render_template("index.html", players=players, search=search)

# --- UPDATE BID ---
@app.route("/update_bid/<int:player_id>", methods=["POST"])
def update_bid(player_id):
    player = Player.query.get(player_id)
    new_bid = int(request.form['bid'])
    if new_bid > (player.bid or player.base_price):
        player.bid = new_bid
        db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
