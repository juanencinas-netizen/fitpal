from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, oauth
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.password and check_password_hash(user.password, password):
            if not user.active:
                flash("Tu cuenta está desactivada.", "danger")
                return redirect(url_for("auth.login"))
            login_user(user, remember=True)
            next_page = request.args.get("next")
            flash(f"Bienvenido/a, {user.name}!", "success")
            return redirect(next_page or url_for("main.index"))
        else:
            flash("Credenciales incorrectas.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Completá todos los campos.", "warning")
            return redirect(url_for("auth.register"))

        if password != confirm:
            flash("Las contraseñas no coinciden.", "warning")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Ya existe una cuenta con ese email.", "warning")
            return redirect(url_for("auth.register"))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Cuenta creada exitosamente. ¡Bienvenido/a a FitPal!", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión.", "info")
    return redirect(url_for("main.index"))


# ── Google OAuth ────────────────────────────────────────────────────────────

@auth_bp.route("/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")

    if not userinfo:
        flash("Error al obtener información de Google.", "danger")
        return redirect(url_for("auth.login"))

    google_id = userinfo["sub"]
    email = userinfo["email"].lower()
    name = userinfo.get("name", email)
    avatar = userinfo.get("picture")

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            user.avatar_url = avatar
        else:
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                avatar_url=avatar,
            )
            db.session.add(user)

    db.session.commit()

    if not user.active:
        flash("Tu cuenta está desactivada.", "danger")
        return redirect(url_for("auth.login"))

    login_user(user, remember=True)
    flash(f"Bienvenido/a, {user.name}!", "success")
    return redirect(url_for("main.index"))
