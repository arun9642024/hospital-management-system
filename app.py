import os
import io
import base64
from datetime import date, datetime
from functools import wraps

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
from mysql.connector import Error

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "development-only-change-this-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DEMO_USERNAME = os.getenv("APP_USERNAME", "admin")
DEMO_PASSWORD = os.getenv("APP_PASSWORD", "ChangeMe123!")
PASSWORD_HASH = generate_password_hash(DEMO_PASSWORD)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "hospital_analytics"),
    )

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def fetch_dataframe(query, params=None):
    connection = get_db()
    try:
        return pd.read_sql(query, connection, params=params)
    finally:
        connection.close()

def build_chart(labels, values, title, ylabel="Visits", kind="bar"):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    if kind == "line":
        ax.plot(labels, values, marker="o", linewidth=2)
    else:
        ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def get_analytics(start_date=None, end_date=None):
    filters = []
    params = []
    if start_date:
        filters.append("v.visit_date >= %s")
        params.append(start_date)
    if end_date:
        filters.append("v.visit_date <= %s")
        params.append(end_date)
    where_sql = (" WHERE " + " AND ".join(filters)) if filters else ""
    base_query = """
        SELECT v.visit_id, v.patient_id, p.age_band, d.department_name,
               v.visit_date, v.visit_type
        FROM visits v
        JOIN patients p ON p.patient_id = v.patient_id
        JOIN departments d ON d.department_id = v.department_id
    """
    visits = fetch_dataframe(base_query + where_sql + " ORDER BY v.visit_date", params)
    if visits.empty:
        return visits, {}, {}
    visits["visit_date"] = pd.to_datetime(visits["visit_date"])
    visits["month"] = visits["visit_date"].dt.to_period("M").astype(str)
    dept = visits.groupby("department_name").size().sort_values(ascending=False)
    monthly = visits.groupby("month").size().sort_index()
    age = visits.groupby("age_band").size().reindex(
        ["0-17", "18-29", "30-44", "45-59", "60+"], fill_value=0
    )
    daily = visits.groupby(visits["visit_date"].dt.date).size().sort_index()
    stats = {
        "total_visits": int(len(visits)),
        "departments": int(visits["department_name"].nunique()),
        "unique_patients": int(visits["patient_id"].nunique()),
        "avg_visits_per_day": round(float(daily.mean()), 2) if len(daily) else 0,
        "peak_day": str(daily.idxmax()) if len(daily) else "—",
        "peak_day_visits": int(daily.max()) if len(daily) else 0,
        "numpy_mean": round(float(np.mean(visits.groupby("visit_date").size().to_numpy())), 2),
        "numpy_std": round(float(np.std(visits.groupby("visit_date").size().to_numpy())), 2),
    }
    charts = {
        "department": build_chart(dept.index.tolist(), dept.values.tolist(), "Visits by Department"),
        "monthly": build_chart(monthly.index.tolist(), monthly.values.tolist(), "Monthly Visit Trend", kind="line"),
        "age": build_chart(age.index.tolist(), age.values.tolist(), "Visits by Age Band"),
    }
    tables = {
        "department": [(str(k), int(v)) for k, v in dept.items()],
        "monthly": [(str(k), int(v)) for k, v in monthly.items()],
        "age": [(str(k), int(v)) for k, v in age.items()],
    }
    return visits, stats, {"charts": charts, "tables": tables}

@app.route("/")
def index():
    return redirect(url_for("dashboard" if session.get("logged_in") else "login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        # Hash the configured password on startup; use environment variables for real deployments.
        if username == DEMO_USERNAME and check_password_hash(PASSWORD_HASH, password):
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    start_date = request.args.get("start_date") or None
    end_date = request.args.get("end_date") or None
    visits, stats, analytics = get_analytics(start_date, end_date)
    return render_template(
        "dashboard.html", stats=stats, analytics=analytics,
        start_date=start_date or "", end_date=end_date or "",
        has_data=not visits.empty
    )

@app.route("/patients")
@login_required
def patients():
    # Only synthetic patient IDs and non-identifying age bands are shown.
    df = fetch_dataframe(
        "SELECT patient_id, age_band, gender_optional FROM patients ORDER BY patient_id"
    )
    return render_template("patients.html", records=df.to_dict(orient="records"))

@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        age_band = request.form.get("age_band", "")
        gender = request.form.get("gender_optional", "") or None
        allowed_bands = {"0-17", "18-29", "30-44", "45-59", "60+"}
        if age_band not in allowed_bands or gender not in {None, "Female", "Male", "Other", "Prefer not to say"}:
            flash("Please select valid values.", "danger")
            return render_template("patient_form.html")
        connection = get_db()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO patients (age_band, gender_optional) VALUES (%s, %s)",
                (age_band, gender)
            )
            connection.commit()
            flash("Synthetic patient record added.", "success")
        except Error as exc:
            connection.rollback()
            flash(f"Could not add record: {exc}", "danger")
        finally:
            connection.close()
        return redirect(url_for("patients"))
    return render_template("patient_form.html")

@app.route("/visits")
@login_required
def visits():
    df = fetch_dataframe("""
        SELECT v.visit_id, v.patient_id, d.department_name, v.visit_date, v.visit_type
        FROM visits v
        JOIN departments d ON d.department_id = v.department_id
        ORDER BY v.visit_date DESC, v.visit_id DESC
        LIMIT 500
    """)
    return render_template("visits.html", records=df.to_dict(orient="records"))

@app.route("/visits/add", methods=["GET", "POST"])
@login_required
def add_visit():
    patients_df = fetch_dataframe("SELECT patient_id, age_band FROM patients ORDER BY patient_id")
    departments_df = fetch_dataframe("SELECT department_id, department_name FROM departments ORDER BY department_name")
    if request.method == "POST":
        patient_id = request.form.get("patient_id", type=int)
        department_id = request.form.get("department_id", type=int)
        visit_date = request.form.get("visit_date", "")
        visit_type = request.form.get("visit_type", "")
        if not patient_id or not department_id or visit_type not in {"Routine", "Follow-up", "Emergency", "Other"}:
            flash("Please complete all fields with valid values.", "danger")
        else:
            try:
                parsed_date = datetime.strptime(visit_date, "%Y-%m-%d").date()
                if parsed_date > date.today():
                    raise ValueError("Visit date cannot be in the future.")
                connection = get_db()
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO visits (patient_id, department_id, visit_date, visit_type) VALUES (%s, %s, %s, %s)",
                    (patient_id, department_id, parsed_date, visit_type)
                )
                connection.commit()
                connection.close()
                flash("Visit record added.", "success")
                return redirect(url_for("visits"))
            except (ValueError, Error) as exc:
                flash(f"Could not add visit: {exc}", "danger")
    return render_template(
        "visit_form.html", patients=patients_df.to_dict(orient="records"),
        departments=departments_df.to_dict(orient="records"),
        today=date.today().isoformat()
    )

@app.route("/reports/visits.csv")
@login_required
def export_csv():
    start_date = request.args.get("start_date") or None
    end_date = request.args.get("end_date") or None
    visits_df, _, _ = get_analytics(start_date, end_date)
    # Export only aggregate operational statistics, never row-level records.
    if visits_df.empty:
        summary = pd.DataFrame(columns=["department", "visit_count"])
    else:
        summary = visits_df.groupby("department_name").size().reset_index(name="visit_count")
        summary.rename(columns={"department_name": "department"}, inplace=True)
    output = io.StringIO()
    summary.to_csv(output, index=False)
    return Response(
        output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=department_workload_summary.csv"}
    )

@app.errorhandler(Error)
def database_error(error):
    app.logger.exception("Database error")
    return render_template("error.html", message="Unable to connect to the database. Check your .env settings and MySQL service."), 500

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
