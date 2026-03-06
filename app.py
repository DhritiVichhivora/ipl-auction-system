from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")  # For session management

# Database connection
DATABASE_URL = os.getenv("Database_url")
if not DATABASE_URL:
    raise RuntimeError("Database_url not set")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

# Player Table
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    team = db.Column(db.String(50))
    role = db.Column(db.String(50))
    country = db.Column(db.String(50))
    base_price = db.Column(db.Integer)
    current_price = db.Column(db.Integer)
    sold = db.Column(db.Boolean)

# Initialize DB and load CSV
with app.app_context():
    db.create_all()
    if Player.query.count() == 0:
        df = pd.read_csv("players.csv")
        for _, row in df.iterrows():
            player = Player(
                name=row["name"],
                team=row["team"],
                role=row["role"],
                country=row["country"],
                base_price=int(row["base_price"]),
                current_price=int(row["current_price"]),
                sold=bool(row["sold"])
            )
            db.session.add(player)
        db.session.commit()
        print("Players imported from CSV")

# Login Route
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if not user:
            # New user → create account
            user = User(name=name, email=email, password=password)
            db.session.add(user)
            db.session.commit()

        # Save session and redirect
        session["user_id"] = user.id
        session["user_name"] = user.name
        return redirect(url_for("auction"))

    return render_template("login.html")

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Auction Page
@app.route("/auction")
def auction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search")
    if search:
        players = Player.query.filter(Player.name.ilike(f"%{search}%")).all()
    else:
        players = Player.query.all()

    return render_template("index.html", players=players, user_name=session.get("user_name"))

# Bid Route
@app.route("/bid", methods=["POST"])
def bid():
    if "user_id" not in session:
        return redirect(url_for("login"))

    player_id = request.form["player_id"]
    new_price = int(request.form["price"])
    player = Player.query.get(player_id)

    if new_price > player.current_price:
        player.current_price = new_price
        db.session.commit()
        flash(f"Bid updated! {player.name} new price: {new_price}")
    else:
        flash("Bid must be higher than current price")

    return redirect(url_for("auction"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
