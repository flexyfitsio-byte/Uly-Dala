import json
import os
import uuid
from flask import Blueprint, request, session, jsonify, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

auth_bp = Blueprint("auth", __name__)

AUTH_FILE = os.path.join(Config.DATA_DIR, "auth_users.json")


def _read_auth_users():
    if not os.path.exists(AUTH_FILE):
        return {}
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_auth_users(data):
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth.html", mode="register")

    data = request.form if request.form else request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Укажите email и пароль"}), 400

    users = _read_auth_users()
    if email in users:
        return jsonify({"error": "Пользователь с таким email уже существует"}), 409

    user_id = str(uuid.uuid4())
    users[email] = {
        "user_id": user_id,
        "password_hash": generate_password_hash(password),
    }
    _write_auth_users(users)

    session["user_id"] = user_id
    session["email"] = email
    return redirect(url_for("main.index")) if request.form else jsonify({"user_id": user_id})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth.html", mode="login")

    data = request.form if request.form else request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    users = _read_auth_users()
    user = users.get(email)

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Неверный email или пароль"}), 401

    session["user_id"] = user["user_id"]
    session["email"] = email
    return redirect(url_for("main.index")) if request.form else jsonify({"user_id": user["user_id"]})


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@auth_bp.route("/api/session")
def current_session():
    return jsonify({
        "logged_in": "user_id" in session,
        "email": session.get("email"),
    })
