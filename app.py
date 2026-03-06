from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # for popup/flash safety

# -------------------------
# DATABASE CONFIG
# -------------------------
DATABASE_URL = os.getenv("Database_url")  # Use exact env var from Render

if not DATABASE_URL:
    raise RuntimeError("Database_url environment variable not set!")

# Fix for SQLAlchemy if Render gives postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------
# DATABASE MODEL
# -------------------------
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(50))
    role = db.Column(db.String(50))
    country = db.Column(db.String(50))
    base_price = db.Column(db.Integer)
    current_price = db.Column(db.Integer)
    sold = db.Column(db.Boolean, default=False)

# -------------------------
# CREATE TABLE AND IMPORT CSV IF EMPTY
# -------------------------
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

# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def index():
    search = request.args.get("search")
    if search:
        players = Player.query.filter(Player.name.ilike(f"%{search}%")).all()
    else:
        players = Player.query.all()
    return render_template("index.html", players=players)

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

# -------------------------
# RUN APP (Render port binding)
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
