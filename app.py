from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from dotenv import load_dotenv
import os
import requests

app = Flask(__name__)
app.secret_key = "farmer_assistant_secret"

# Load API key
load_dotenv()
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


# ---------- DATABASE ----------

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            location TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            season TEXT NOT NULL,
            soil TEXT NOT NULL,
            description TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS diseases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            solution TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            market_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            date TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS farming_tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            tip TEXT NOT NULL
        )
    """)


    # ---------- SAMPLE CROPS ----------

    if conn.execute("SELECT COUNT(*) FROM crops").fetchone()[0] == 0:

        conn.executemany("""
            INSERT INTO crops
            (crop_name, season, soil, description)
            VALUES (?, ?, ?, ?)
        """, [
            ("Wheat", "Rabi", "Loamy Soil",
             "Wheat is mainly grown during the Rabi season."),

            ("Rice", "Kharif", "Clay Soil",
             "Rice requires sufficient water and suitable soil."),

            ("Cotton", "Kharif", "Black Soil",
             "Cotton grows well in black soil."),

            ("Tomato", "All Season", "Loamy Soil",
             "Tomato requires proper sunlight and watering.")
        ])


    # ---------- SAMPLE DISEASES ----------

    if conn.execute("SELECT COUNT(*) FROM diseases").fetchone()[0] == 0:

        conn.executemany("""
            INSERT INTO diseases
            (disease_name, symptoms, solution)
            VALUES (?, ?, ?)
        """, [
            ("Leaf Spot",
             "Spots appear on leaves.",
             "Remove affected leaves and maintain proper crop care."),

            ("Powdery Mildew",
             "White powder-like patches appear on leaves.",
             "Maintain proper air circulation and use suitable treatment."),

            ("Root Rot",
             "Roots become damaged due to excess moisture.",
             "Provide proper drainage.")
        ])


    # ---------- SAMPLE MARKET PRICES ----------

    if conn.execute("SELECT COUNT(*) FROM market_prices").fetchone()[0] == 0:

        conn.executemany("""
            INSERT INTO market_prices
            (crop_name, market_name, price, date)
            VALUES (?, ?, ?, ?)
        """, [
            ("Wheat", "Nashik", 2500, "2026-08-14"),
            ("Cotton", "Jalgaon", 7000, "2026-08-14"),
            ("Onion", "Nashik", 1800, "2026-08-14"),
            ("Soybean", "Dhule", 4500, "2026-08-14")
        ])


    # ---------- SAMPLE FARMING TIPS ----------

    if conn.execute("SELECT COUNT(*) FROM farming_tips").fetchone()[0] == 0:

        conn.executemany("""
            INSERT INTO farming_tips
            (title, tip)
            VALUES (?, ?)
        """, [
            ("Use Good Seeds",
             "Use good quality seeds for better crop production."),

            ("Proper Watering",
             "Give crops the required amount of water."),

            ("Control Weeds",
             "Keep the field clean and remove unwanted weeds."),

            ("Check Diseases",
             "Check crops regularly for diseases and pests."),

            ("Use Fertilizers Carefully",
             "Use fertilizers according to crop requirements."),

            ("Choose Proper Season",
             "Follow the suitable season for planting each crop.")
        ])


    conn.commit()
    conn.close()


# ---------- HOME ----------

@app.route("/")
def home():
    return render_template("home.html")


# ---------- REGISTER ----------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        email = request.form["email"]
        location = request.form["location"]
        password = request.form["password"]

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO farmers
                (name, mobile, email, location, password)
                VALUES (?, ?, ?, ?, ?)
            """, (name, mobile, email, location, password))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered!"

    return render_template("register.html")


# ---------- FARMER LOGIN ----------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        farmer = conn.execute("""
            SELECT * FROM farmers
            WHERE email = ? AND password = ?
        """, (email, password)).fetchone()

        conn.close()

        if farmer:

            session["farmer_id"] = farmer["id"]
            session["farmer_name"] = farmer["name"]

            return redirect(url_for("dashboard"))

        return "Invalid Email or Password!"

    return render_template("login.html")


# ---------- FARMER DASHBOARD ----------

@app.route("/dashboard")
def dashboard():

    if "farmer_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        farmer_name=session["farmer_name"]
    )


# ---------- CROP ----------

@app.route("/crop")
def crop():

    if "farmer_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")

    conn = get_db()

    if search:

        crops = conn.execute("""
            SELECT * FROM crops
            WHERE crop_name LIKE ?
        """, ("%" + search + "%",)).fetchall()

    else:

        crops = conn.execute("""
            SELECT * FROM crops
        """).fetchall()

    conn.close()

    return render_template(
        "crop.html",
        crops=crops,
        search=search
    )


# ---------- DISEASE ----------

@app.route("/disease")
def disease():

    if "farmer_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")

    conn = get_db()

    if search:

        diseases = conn.execute("""
            SELECT * FROM diseases
            WHERE disease_name LIKE ?
        """, ("%" + search + "%",)).fetchall()

    else:

        diseases = conn.execute("""
            SELECT * FROM diseases
        """).fetchall()

    conn.close()

    return render_template(
        "disease.html",
        diseases=diseases,
        search=search
    )


# ---------- WEATHER ----------

@app.route("/weather", methods=["GET", "POST"])
def weather():

    if "farmer_id" not in session:
        return redirect(url_for("login"))

    weather_data = None
    error = None

    if request.method == "POST":

        city = request.form["city"]

        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:

            data = response.json()

            weather_data = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["description"]
            }

        else:

            error = "City not found. Please check the city name."

    return render_template(
        "weather.html",
        weather_data=weather_data,
        error=error
    )


# ---------- MARKET PRICE ----------

@app.route("/market")
def market():

    if "farmer_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")

    conn = get_db()

    if search:

        prices = conn.execute("""
            SELECT * FROM market_prices
            WHERE crop_name LIKE ?
        """, ("%" + search + "%",)).fetchall()

    else:

        prices = conn.execute("""
            SELECT * FROM market_prices
        """).fetchall()

    conn.close()

    return render_template(
        "market.html",
        prices=prices,
        search=search
    )


# ---------- FARMING TIPS ----------

@app.route("/tips")
def tips():

    if "farmer_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    tips = conn.execute("""
        SELECT * FROM farming_tips
    """).fetchall()

    conn.close()

    return render_template(
        "tips.html",
        tips=tips
    )


# =====================================================
#                     ADMIN SECTION
# =====================================================


# ---------- ADMIN LOGIN ----------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["admin_logged_in"] = True

            return redirect(url_for("dashboard"))

        return "Invalid Admin Username or Password!"

    return render_template("admin_login.html")


# ---------- ADMIN DASHBOARD ----------

@app.route("/admin")
def admin():

    # Only Admin can access
    if not session.get("admin_logged_in"):

        return redirect(url_for("admin_login"))

    conn = get_db()

    farmers = conn.execute("""
        SELECT id, name, mobile, email, location
        FROM farmers
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        farmers=farmers
    )


# ---------- DELETE FARMER ----------

@app.route("/delete-farmer/<int:farmer_id>", methods=["POST"])
def delete_farmer(farmer_id):

    # Only Admin can delete
    if not session.get("admin_logged_in"):

        return redirect(url_for("admin_login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM farmers
        WHERE id = ?
    """, (farmer_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ---------- ADMIN LOGOUT ----------

@app.route("/admin-logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


# ---------- FARMER LOGOUT ----------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ---------- RUN ----------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)
    
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)