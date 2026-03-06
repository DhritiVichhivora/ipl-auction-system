from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Database connection (Postgres on Render)
DATABASE_URL = os.getenv("Database_url")
if not DATABASE_URL:
    raise ValueError("Database_url environment variable not set")

# Fix for SQLAlchemy + Postgres
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    team = db.Column(db.String(50))
    role = db.Column(db.String(50))
    country = db.Column(db.String(50))
    base_price = db.Column(db.Integer)
    current_price = db.Column(db.Integer)
    sold = db.Column(db.Boolean)

# --- Initialize DB and load CSV if empty ---
with app.app_context():
    db.create_all()
    if Player.query.count() == 0:
        df = pd.read_csv("players.csv")
        for _, row in df.iterrows():
            player = Player(
                id=int(row["id"]),
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

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user:
            # Login existing user
            if check_password_hash(user.password_hash, password):
                session["user_id"] = user.id
                return redirect(url_for("auction"))
            else:
                flash("Incorrect password!", "error")
        else:
            # Register new user
            new_user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            return redirect(url_for("auction"))

    return render_template("login.html")

@app.route("/auction")
def auction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search")
    role_filter = request.args.get("role")

    players = Player.query

    if search:
        players = players.filter(Player.name.ilike(f"%{search}%"))
    if role_filter and role_filter != "All":
        players = players.filter_by(role=role_filter)

    players = players.all()
    return render_template("index.html", players=players)

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
        flash(f"Bid updated for {player.name}!", "success")
    else:
        flash("Bid must be higher than current price!", "error")

    return redirect(url_for("auction"))

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

# --- Run App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
