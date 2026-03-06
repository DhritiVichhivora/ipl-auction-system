from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Player model
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(50))
    role = db.Column(db.String(50))
    country = db.Column(db.String(50))
    base_price = db.Column(db.Integer)
    current_price = db.Column(db.Integer)
    sold = db.Column(db.Boolean, default=False)

# Create table and import CSV if empty
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

# Home route
@app.route("/")
def index():
    search = request.args.get("search")
    if search:
        players = Player.query.filter(Player.name.ilike(f"%{search}%")).all()
    else:
        players = Player.query.all()
    return render_template("index.html", players=players)

# Bid route
@app.route("/bid", methods=["POST"])
def bid():
    player_id = request.form.get("player_id")
    new_price = request.form.get("price")

    if not new_price or not player_id:
        return jsonify({"success": False, "message": "Invalid input"})

    try:
        new_price = int(new_price)
    except:
        return jsonify({"success": False, "message": "Price must be a number"})

    player = Player.query.get(player_id)
    if not player:
        return jsonify({"success": False, "message": "Player not found"})

    if new_price > player.current_price:
        player.current_price = new_price
        db.session.commit()
        return jsonify({"success": True, "message": f"Bid updated! New bid for {player.name}: {new_price}"})
    else:
        return jsonify({"success": False, "message": f"Bid must be higher than current bid ({player.current_price})"})

if __name__ == "__main__":
    app.run(debug=True)
