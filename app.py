import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production

# DATABASE SETUP
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODELS
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))  # Plain password for simplicity

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    team = db.Column(db.String(50))
    base_price = db.Column(db.Integer)
    current_bid = db.Column(db.Integer)

# ROUTES
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search_query = request.args.get("search", "")
    if search_query:
        players = Player.query.filter(Player.name.ilike(f"%{search_query}%")).all()
    else:
        players = Player.query.all()

    if request.method == "POST":
        player_id = request.form.get("player_id")
        new_bid = request.form.get("new_bid")
        player = Player.query.get(player_id)
        if player and new_bid.isdigit():
            player.current_bid = int(new_bid)
            db.session.commit()
            flash(f"Bid updated for {player.name}", "success")
        return redirect(url_for("index"))

    return render_template("index.html", players=players)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    # Create tables if not exists
    with app.app_context():
        db.create_all()
    app.run(debug=True)
