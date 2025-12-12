from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from parking.manager import ParkingManager, REPORTLAB_AVAILABLE
from parking.billing import BillingEngine
from parking.models import db, init_db, VehicleRecord
from pathlib import Path
from datetime import date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "devkey")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///parking.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    init_db()

# Default settings
DEFAULT_SETTINGS = {
    "total_slots": 24,
    "vip_slots": [1, 2],
    "first_hours": 2,
    "first_hours_fee": 20.0,
    "per_hour_fee": 10.0,
    "vehicle_type_multiplier": {"car": 1.0, "bike": 0.5, "ev": 1.2, "heavy": 1.5}
}

# Manager & Billing Engine
manager = ParkingManager(app, DEFAULT_SETTINGS)
billing = BillingEngine(DEFAULT_SETTINGS)

# --------------------------
# ROUTES
# --------------------------

@app.route("/")
def index():
    status = manager.current_status()
    return render_template("index.html", status=status)


@app.route("/admin")
def admin():
    status = manager.current_status()
    today_summary = manager.daily_revenue_summary(date.today())

    return render_template(
        "admin.html",
        status=status,
        summary=today_summary,
        reportlab_available=REPORTLAB_AVAILABLE
    )


# API: Vehicle Entry
@app.route("/api/entry", methods=["POST"])
def api_entry():
    data = request.json or request.form

    number = data.get("number")
    vtype = data.get("vtype", "car").lower()
    vip_flag = data.get("vip", False)

    vip_flag = str(vip_flag).lower() in ("true", "1", "yes")

    if not number:
        return jsonify({"success": False, "error": "Vehicle number required."}), 400

    try:
        vehicle = manager.park_vehicle(number, vtype, is_vip=vip_flag)
        return jsonify({"success": True, "vehicle": vehicle})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# API: Vehicle Exit
@app.route("/api/exit", methods=["POST"])
def api_exit():
    data = request.json or request.form

    number = data.get("number")
    if not number:
        return jsonify({"success": False, "error": "Vehicle number required."}), 400

    try:
        record = manager.exit_vehicle(number, billing)
        return jsonify({"success": True, "record": record})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# Status API
@app.route("/api/status")
def api_status():
    return jsonify(manager.current_status())


# Revenue Summary API
@app.route("/api/revenue")
def api_revenue():
    d = request.args.get("date")
    if d:
        try:
            y, m, day = map(int, d.split("-"))
            query_date = date(y, m, day)
        except:
            return jsonify({"success": False, "error": "Invalid date format"}), 400
    else:
        query_date = date.today()

    return jsonify(manager.daily_revenue_summary(query_date))


# PDF Report
@app.route("/report/pdf")
def report_pdf():
    try:
        path = manager.generate_pdf_daily_report(date.today())
        return send_file(path, as_attachment=True)
    except RuntimeError as e:
        flash(str(e), "danger")
        return redirect(url_for("admin"))
    except Exception as e:
        flash("Report generation failed: " + str(e), "danger")
        return redirect(url_for("admin"))


# Run app
if __name__ == "__main__":
    Path("reports").mkdir(exist_ok=True)
    app.run(debug=True)
