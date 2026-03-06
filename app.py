from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# Database connection (Render PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///players.db")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


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


# Create database and load CSV
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


# Home Page
@app.route("/")
def index():

    search = request.args.get("search")

    if search:
        players = Player.query.filter(Player.name.ilike(f"%{search}%")).all()
    else:
        players = Player.query.all()

    return render_template("index.html", players=players)


# Bid Route
@app.route("/bid", methods=["POST"])
def bid():

    player_id = request.form["player_id"]
    new_price = int(request.form["price"])

    player = Player.query.get(player_id)

    if new_price > player.current_price:

        player.current_price = new_price
        db.session.commit()

        print("Bid Updated")

    else:

        print("Bid must be higher than current price")

    return redirect("/")


# Run app
if __name__ == "__main__":
    app.run(debug=True)