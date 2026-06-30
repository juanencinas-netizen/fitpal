from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import db
from app.models import User, Plan, News, Subscription
from app.plan_utils import get_plan_display_name, get_plan_display_price
from app.models import Exercise, RoutineDay, RoutineExercise
from app.routines.routes import WEEK_DAYS, _ensure_days_for_user

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            flash("Acceso restringido.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────────────────

@admin_bp.route("/")
@admin_required
def dashboard():
    total_users = User.query.filter_by(role="user").count()
    total_plans = Plan.query.filter_by(active=True).count()
    total_news = News.query.count()
    active_subs = Subscription.query.filter_by(active=True).count()
    recent_users = User.query.filter_by(role="user").order_by(User.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_plans=total_plans,
        total_news=total_news,
        active_subs=active_subs,
        recent_users=recent_users,
    )


# ── USUARIOS ──────────────────────────────────────────────────────────────

@admin_bp.route("/usuarios")
@admin_required
def users_list():
    users = User.query.filter_by(role="user").order_by(User.created_at.desc()).all()
    return render_template("admin/users/list.html", users=users)


@admin_bp.route("/usuarios/crear", methods=["GET", "POST"])
@admin_required
def user_create():
    planes = Plan.query.filter_by(active=True).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        plan_id = request.form.get("plan_id")

        if not name or not email or not password:
            flash("Completá todos los campos obligatorios.", "warning")
            return redirect(url_for("admin.user_create"))

        if User.query.filter_by(email=email).first():
            flash("Ya existe un usuario con ese email.", "warning")
            return redirect(url_for("admin.user_create"))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.flush()

        if plan_id:
            plan = Plan.query.get(int(plan_id))
            if plan:
                sub = Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    end_date=datetime.utcnow() + timedelta(days=30),
                )
                db.session.add(sub)

        db.session.commit()
        return redirect(url_for("admin.users_list"))

    return render_template("admin/users/form.html", user=None, planes=planes)


@admin_bp.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@admin_required
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    planes = Plan.query.filter_by(active=True).all()

    if request.method == "POST":
        # (debug prints removed)
        user.name = request.form.get("name", user.name).strip()
        user.email = request.form.get("email", user.email).strip().lower()
        new_password = request.form.get("password", "")
        if new_password:
            user.password = generate_password_hash(new_password)
        # Actualizar estado de cuenta según el checkbox (presente cuando está checado)
        user.active = bool(request.form.get("active"))

        plan_id = request.form.get("plan_id")
        plan_id = request.form.get("plan_id")
        # Si se selecciona un plan, crear/actualizar la suscripción; si se deja en "Sin plan", removerla.
        if plan_id:
            plan = Plan.query.get(int(plan_id))
            if plan:
                if user.subscription:
                    user.subscription.plan_id = plan.id
                    user.subscription.end_date = datetime.utcnow() + timedelta(days=30)
                    user.subscription.active = True
                else:
                    sub = Subscription(
                        user_id=user.id,
                        plan_id=plan.id,
                        end_date=datetime.utcnow() + timedelta(days=30),
                    )
                    db.session.add(sub)
        else:
            # "Sin plan" seleccionado: remover suscripción existente si la hubiera
            if user.subscription:
                db.session.delete(user.subscription)

        db.session.commit()
        return redirect(url_for("admin.users_list"))

    return render_template("admin/users/form.html", user=user, planes=planes)


@admin_bp.route("/usuarios/<int:user_id>/quitar_suscripcion", methods=["POST"])
@admin_required
def user_remove_subscription(user_id):
    user = User.query.get_or_404(user_id)
    if not user.subscription:
        flash("El usuario no tiene suscripción.", "info")
        return redirect(url_for("admin.user_edit", user_id=user.id))
    # Eliminar la suscripción (administrador puede quitarla)
    db.session.delete(user.subscription)
    db.session.commit()
    flash("Suscripción removida.", "success")
    return redirect(url_for("admin.user_edit", user_id=user.id))


@admin_bp.route("/usuarios/<int:user_id>/cancelar_suscripcion", methods=["POST"])
@admin_required
def admin_cancel_subscription(user_id):
    user = User.query.get_or_404(user_id)
    if not user.subscription or not user.subscription.active:
        flash("El usuario no tiene una suscripción activa para cancelar.", "info")
        return redirect(url_for("admin.user_edit", user_id=user.id))
    sub = user.subscription
    sub.active = False
    sub.end_date = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash("Se programó la cancelación de la suscripción del usuario. Terminará en 30 días.", "success")
    return redirect(url_for("admin.user_edit", user_id=user.id))


@admin_bp.route("/usuarios/<int:user_id>/reactivar_suscripcion", methods=["POST"])
@admin_required
def admin_reactivate_subscription(user_id):
    user = User.query.get_or_404(user_id)
    if not user.subscription:
        flash("El usuario no tiene suscripción para reactivar.", "info")
        return redirect(url_for("admin.user_edit", user_id=user.id))
    from datetime import datetime, timedelta
    sub = user.subscription
    sub.active = True
    sub.end_date = datetime.utcnow() + timedelta(days=30)
    db.session.add(sub)
    db.session.commit()
    flash("Suscripción reactivada.", "success")
    return redirect(url_for("admin.user_edit", user_id=user.id))



@admin_bp.route("/usuarios/<int:user_id>/eliminar", methods=["POST"])
@admin_required
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin():
        flash("No podés eliminar al administrador.", "warning")
        return redirect(url_for("admin.users_list"))
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/usuarios/<int:user_id>/rutina")
@admin_required
def user_routine(user_id):
    user = User.query.get_or_404(user_id)
    days = _ensure_days_for_user(user)
    routines = []
    for name in WEEK_DAYS:
        rd = days[name]
        exercises = RoutineExercise.query.filter_by(routine_day_id=rd.id).join(Exercise).all()
        routines.append((name, rd, exercises))
    return render_template("admin/users/routine.html", user=user, routines=routines)


@admin_bp.route("/usuarios/<int:user_id>/rutina/borrar", methods=["POST"])
@admin_required
def user_routine_delete_all(user_id):
    user = User.query.get_or_404(user_id)
    days = _ensure_days_for_user(user)
    for rd in days.values():
        RoutineExercise.query.filter_by(routine_day_id=rd.id).delete(synchronize_session=False)
    db.session.commit()
    flash("Se eliminaron todos los ejercicios de la rutina del usuario.", "success")
    return redirect(url_for("admin.user_routine", user_id=user.id))


# ── PLANES ────────────────────────────────────────────────────────────────

@admin_bp.route("/planes")
@admin_required
def plans_list():
    planes = Plan.query.order_by(Plan.created_at.desc()).all()
    # attach display helpers so the admin list shows recommended names/prices
    for p in planes:
        try:
            p._display_name = get_plan_display_name(p)
            p._display_price = get_plan_display_price(p)
        except Exception:
            p._display_name = p.name
            p._display_price = p.price
    return render_template("admin/plans/list.html", planes=planes)


@admin_bp.route("/planes/normalizar", methods=["POST"])
@admin_required
def plans_normalize():
    # Mapea nombres históricos a los nombres recomendados y ajusta precio/duración
    mapping = {
        "1 MES": ("Plan Básico", 25000, 30, "Acceso a la sede principal. Ideal para comenzar."),
        "3 MESES": ("Plan Fit", 34990, 90, "Mejor equilibrio: clases y 1 sesión personalizada/mes."),
        "6 MESES": ("Plan Black", 49990, 180, "Acceso a todas las sedes, 4 sesiones personalizadas/mes."),
    }
    updated = 0
    for old_name, (new_name, price, duration, desc) in mapping.items():
        plan = Plan.query.filter(Plan.name.ilike(old_name)).first()
        if plan:
            plan.name = new_name
            plan.price = price
            # duración fija mensual
            plan.duration_days = 30
            plan.description = desc
            db.session.add(plan)
            updated += 1
    if updated:
        db.session.commit()
        flash(f"Planes actualizados: {updated}", "success")
    else:
        flash("No se encontraron planes a normalizar.", "info")
    return redirect(url_for("admin.plans_list"))


@admin_bp.route("/planes/<int:plan_id>/aplicar_recomendado", methods=["POST"])
@admin_required
def plan_apply_recommended(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    from app.plan_utils import apply_recommended_to_plan
    changed = apply_recommended_to_plan(plan)
    if changed:
        db.session.add(plan)
        db.session.commit()
        flash("Valores recomendados aplicados al plan.", "success")
    else:
        flash("No existe una recomendación para este plan.", "info")
    return redirect(url_for("admin.plan_edit", plan_id=plan.id))


@admin_bp.route("/planes/crear", methods=["GET", "POST"])
@admin_required
def plan_create():
    if request.method == "POST":
        plan = Plan(
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip(),
            price=float(request.form.get("price", 0)),
            # duration is fixed monthly
            duration_days=30,
            active="active" in request.form,
        )
        db.session.add(plan)
        db.session.commit()
        flash("Plan creado.", "success")
        return redirect(url_for("admin.plans_list"))
    return render_template("admin/plans/form.html", plan=None)


@admin_bp.route("/planes/<int:plan_id>/editar", methods=["GET", "POST"])
@admin_required
def plan_edit(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    if request.method == "POST":
        plan.name = request.form.get("name", plan.name).strip()
        plan.description = request.form.get("description", "").strip()
        plan.price = float(request.form.get("price", plan.price))
        # duration is fixed monthly
        plan.duration_days = 30
        plan.active = "active" in request.form
        db.session.commit()
        flash("Plan actualizado.", "success")
        return redirect(url_for("admin.plans_list"))
    return render_template("admin/plans/form.html", plan=plan)


@admin_bp.route("/planes/<int:plan_id>/eliminar", methods=["POST"])
@admin_required
def plan_delete(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    plan.active = False
    db.session.commit()
    flash("Plan desactivado.", "success")
    return redirect(url_for("admin.plans_list"))


# ── NOTICIAS ──────────────────────────────────────────────────────────────

@admin_bp.route("/noticias")
@admin_required
def news_list():
    noticias = News.query.order_by(News.created_at.desc()).all()
    return render_template("admin/news/list.html", noticias=noticias)


@admin_bp.route("/noticias/crear", methods=["GET", "POST"])
@admin_required
def news_create():
    if request.method == "POST":
        noticia = News(
            title=request.form.get("title", "").strip(),
            content=request.form.get("content", "").strip(),
            image_url=request.form.get("image_url", "").strip() or None,
            author_id=current_user.id,
            published="published" in request.form,
        )
        db.session.add(noticia)
        db.session.commit()
        flash("Noticia creada.", "success")
        return redirect(url_for("admin.news_list"))
    return render_template("admin/news/form.html", noticia=None)


@admin_bp.route("/noticias/<int:news_id>/editar", methods=["GET", "POST"])
@admin_required
def news_edit(news_id):
    noticia = News.query.get_or_404(news_id)
    if request.method == "POST":
        noticia.title = request.form.get("title", noticia.title).strip()
        noticia.content = request.form.get("content", noticia.content).strip()
        noticia.image_url = request.form.get("image_url", "").strip() or None
        noticia.published = "published" in request.form
        db.session.commit()
        flash("Noticia actualizada.", "success")
        return redirect(url_for("admin.news_list"))
    return render_template("admin/news/form.html", noticia=noticia)


@admin_bp.route("/noticias/<int:news_id>/eliminar", methods=["POST"])
@admin_required
def news_delete(news_id):
    noticia = News.query.get_or_404(news_id)
    db.session.delete(noticia)
    db.session.commit()
    flash("Noticia eliminada.", "success")
    return redirect(url_for("admin.news_list"))


"""Admin routes are grouped above. The duplicate `user_routine` endpoint is removed to avoid endpoint conflicts."""

