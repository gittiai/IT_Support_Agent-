from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json, os

app = Flask(__name__)
app.secret_key = "it-admin-secret"


USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {
        "john@company.com": {"name": "John Doe", "role": "Employee", "active": True, "license": "Basic"},
        "alice@company.com": {"name": "Alice Smith", "role": "Manager", "active": True, "license": "Pro"},
        "bob@company.com": {"name": "Bob Johnson", "role": "Employee", "active": False, "license": "None"},
    }

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

@app.route("/")
def index():
    users = load_users()
    return render_template("index.html", users=users)

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    users = load_users()
    message = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        new_password = request.form.get("new_password", "").strip()
        if email in users:
            message = f"✅ Password successfully reset for {email}"
            flash(message, "success")
        else:
            message = f"❌ User {email} not found"
            flash(message, "error")
        return redirect(url_for("reset_password"))
    return render_template("reset_password.html", users=users)

@app.route("/create-user", methods=["GET", "POST"])
def create_user():
    users = load_users()
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "Employee").strip()
        license_type = request.form.get("license", "Basic").strip()
        if not email or not name:
            flash("❌ Email and name are required", "error")
        elif email in users:
            flash(f"❌ User {email} already exists", "error")
        else:
            users[email] = {"name": name, "role": role, "active": True, "license": license_type}
            save_users(users)
            flash(f"✅ User {name} ({email}) created successfully", "success")
        return redirect(url_for("create_user"))
    return render_template("create_user.html")

@app.route("/manage-users", methods=["GET", "POST"])
def manage_users():
    users = load_users()
    if request.method == "POST":
        action = request.form.get("action")
        email = request.form.get("email")
        if email in users:
            if action == "activate":
                users[email]["active"] = True
                flash(f"✅ User {email} activated", "success")
            elif action == "deactivate":
                users[email]["active"] = False
                flash(f"✅ User {email} deactivated", "success")
            elif action == "delete":
                del users[email]
                flash(f"✅ User {email} deleted", "success")
            elif action == "assign_license":
                license_type = request.form.get("license", "Basic")
                users[email]["license"] = license_type
                flash(f"✅ License '{license_type}' assigned to {email}", "success")
            save_users(users)
        return redirect(url_for("manage_users"))
    return render_template("manage_users.html", users=users)

@app.route("/api/users")
def api_users():
    return jsonify(load_users())

if __name__ == "__main__":
    app.run(debug=True, port=5050)