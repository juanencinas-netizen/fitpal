from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Plan, Subscription
from app.plan_utils import get_plan_display_name, get_plan_display_price, get_plan_key, get_plan_feature_items

plans_bp = Blueprint("plans", __name__)


@plans_bp.route("/")
def index():
    planes = Plan.query.filter_by(active=True).all()
    for p in planes:
        p._display_name = get_plan_display_name(p)
        p._display_price = get_plan_display_price(p)
        p._plan_key = get_plan_key(p)
    return render_template(
        "plans/index.html",
        planes=planes,
        get_plan_feature_items=get_plan_feature_items,
    )


@plans_bp.route("/<int:plan_id>/suscribirse")
@login_required
def subscribe(plan_id):
    plan = Plan.query.get_or_404(plan_id)

    if current_user.subscription:
        flash("Ya tenés una suscripción activa. Contactá al administrador para cambiarla.", "info")
        return redirect(url_for("plans.index"))

    sub = Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        end_date=datetime.utcnow() + timedelta(days=30),
    )
    db.session.add(sub)
    db.session.commit()
    flash(f"¡Te suscribiste al plan {plan.name}!", "success")
    return redirect(url_for("user.space"))
