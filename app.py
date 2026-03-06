from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# Database connection (Render PostgreSQL)
DATABASE_URL = os.getenv("Database_url")  # Ensure your Render DB URL is named exactly like this

# Fix for postgres URI in SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or "sqlite:///players.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------
# Player Table
# -------------------
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    team = db.Column(db.String(50))
    role = db.Column(db.String(50))
    country = db.Column(db.String(50))
    base_price = db.Column(db.Integer)
    current_price = db.Column(db.Integer)
    sold = db.Column(db.Boolean)

# -------------------
# Create DB and load CSV if empty
# -------------------
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

# -------------------
# Home / Auction Page
# -------------------
@app.route("/")
def index():
    players = Player.query.all()
    return render_template("index.html", players=players)

# -------------------
# Update Bid (AJAX)
# -------------------
@app.route("/bid", methods=["POST"])
def bid():
    player_id = request.form["player_id"]
    new_price = int(request.form["price"])
    player = Player.query.get(player_id)
    if player:
        if new_price > player.current_price:
            player.current_price = new_price
            db.session.commit()
            return jsonify({"status": "success", "message": "Bid updated!", "new_price": new_price})
        else:
            return jsonify({"status": "error", "message": "Bid must be higher than current price"})
    return jsonify({"status": "error", "message": "Player not found"})

# -------------------
# Run App
# -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
