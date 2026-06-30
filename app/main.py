from flask import Blueprint, render_template
from app.models import News, Plan
from app.plan_utils import get_plan_display_name, get_plan_display_price, get_plan_key, get_plan_feature_items

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    noticias = News.query.filter_by(published=True).order_by(News.created_at.desc()).limit(3).all()
    planes = Plan.query.filter_by(active=True).all()
    for p in planes:
        p._display_name = get_plan_display_name(p)
        p._display_price = get_plan_display_price(p)
        p._plan_key = get_plan_key(p)
    return render_template(
        "index.html",
        noticias=noticias,
        planes=planes,
        get_plan_feature_items=get_plan_feature_items,
    )
